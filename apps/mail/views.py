from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.utils import timezone
import hmac
import hashlib

from apps.mail.models import MailRecord, MailStatusLog
from apps.mail.forms import MailCreateForm, MailFilterForm
from apps.core.mixins import BranchOfficerMixin, MailroomStaffMixin
from apps.branches.models import Branch
from apps.departments.models import Department


class MailCreateView(LoginRequiredMixin, CreateView):
    model = MailRecord
    form_class = MailCreateForm
    template_name = 'mail/create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.created_by = self.request.user
        
        # Set sender based on user profile
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            if profile.branch:
                instance.sender_branch = profile.branch
                instance.origin_type = 'branch_to_hq'
            elif profile.department:
                instance.sender_department = profile.department
                instance.origin_type = 'hq_internal'
        
        # Handle recipient type from form
        recipient_type = form.cleaned_data.get('recipient_type')
        if recipient_type == 'department':
            # Get department from POST or default
            dept_id = self.request.POST.get('recipient_department')
            if dept_id:
                instance.recipient_department = Department.objects.get(pk=dept_id)
        else:
            branch_id = self.request.POST.get('recipient_branch')
            if branch_id:
                instance.recipient_branch = Branch.objects.get(pk=branch_id)
                instance.origin_type = 'hq_to_branch'
        
        instance.save()
        
        # Create status log
        MailStatusLog.objects.create(
            mail=instance,
            status=instance.status,
            changed_by=self.request.user,
            note='Mail record created'
        )
        
        messages.success(self.request, f'Mail created successfully! Reference: {instance.reference_number}')
        return redirect('mail:qr_print', pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        context['branches'] = Branch.objects.all()
        return context


class MailDetailView(LoginRequiredMixin, DetailView):
    model = MailRecord
    template_name = 'mail/detail.html'
    context_object_name = 'mail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_logs'] = self.object.status_logs.all()
        context['can_approve'] = (
            hasattr(self.request.user, 'profile') and
            self.request.user.profile.role in ['mailroom_staff', 'mailroom_admin', 'system_admin'] and
            self.object.status in ['received_mailroom', 'sorted']
        )
        context['can_receive'] = (
            hasattr(self.request.user, 'profile') and
            self.request.user.profile.role in ['mailroom_staff', 'mailroom_admin', 'system_admin'] and
            self.object.status == 'created'
        )
        return context


class MailQRPrintView(LoginRequiredMixin, DetailView):
    model = MailRecord
    template_name = 'mail/qr_print.html'
    context_object_name = 'mail'


class MailScanView(LoginRequiredMixin, TemplateView):
    template_name = 'mail/scan.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ref = self.request.GET.get('ref', '')
        mail = None
        error = None
        
        if ref:
            # Parse reference and hash
            parts = ref.split('|')
            if len(parts) == 2:
                reference_number, provided_hash = parts
                if MailRecord.validate_qr(reference_number, provided_hash):
                    try:
                        mail = MailRecord.objects.get(reference_number=reference_number)
                        messages.success(self.request, 'QR code validated successfully!')
                    except MailRecord.DoesNotExist:
                        error = 'Invalid QR code - mail not found'
                else:
                    error = 'Invalid QR code - security validation failed'
            else:
                # Try to find by reference number only (manual entry)
                try:
                    mail = MailRecord.objects.get(reference_number=ref)
                    messages.info(self.request, 'Manual reference entry - no hash validation')
                except MailRecord.DoesNotExist:
                    error = 'Mail not found with that reference number'
        
        context['mail'] = mail
        context['error'] = error
        context['ref'] = ref
        return context

    def post(self, request, *args, **kwargs):
        ref = request.POST.get('reference_number', '')
        return redirect(f'{reverse_lazy("mail:scan")}?ref={ref}')


class MailListView(LoginRequiredMixin, ListView):
    model = MailRecord
    template_name = 'mail/list.html'
    context_object_name = 'mails'
    paginate_by = 20

    def get_queryset(self):
        queryset = MailRecord.objects.select_related(
            'sender_branch', 'sender_department',
            'recipient_branch', 'recipient_department',
            'created_by'
        ).all()
        
        # Apply filters
        status = self.request.GET.get('status')
        origin_type = self.request.GET.get('origin_type')
        branch_id = self.request.GET.get('branch')
        dept_id = self.request.GET.get('department')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status:
            queryset = queryset.filter(status=status)
        if origin_type:
            queryset = queryset.filter(origin_type=origin_type)
        if branch_id:
            queryset = queryset.filter(
                models.Q(sender_branch_id=branch_id) | 
                models.Q(recipient_branch_id=branch_id)
            )
        if dept_id:
            queryset = queryset.filter(
                models.Q(sender_department_id=dept_id) | 
                models.Q(recipient_department_id=dept_id)
            )
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Role-based filtering
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            if profile.role == 'branch_officer':
                if profile.branch:
                    queryset = queryset.filter(
                        models.Q(sender_branch=profile.branch) |
                        models.Q(recipient_branch=profile.branch)
                    )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = MailFilterForm(self.request.GET or None)
        return context


# Import models at the end to avoid circular imports
from django.db import models
