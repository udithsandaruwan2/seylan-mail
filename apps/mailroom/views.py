from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from apps.mail.models import MailRecord, MailStatusLog
from apps.mailroom.forms import MailroomReceiveForm, MailroomApproveForm, MailroomRouteForm
from apps.core.mixins import MailroomStaffMixin
from apps.departments.models import Department


class MailroomDashboardView(MailroomStaffMixin, TemplateView):
    template_name = 'mailroom/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Incoming queue (created or dispatched)
        context['incoming_queue'] = MailRecord.objects.filter(
            status__in=['created', 'dispatched']
        ).select_related('sender_branch', 'sender_department').order_by('-created_at')[:10]
        
        # Pending approval
        context['pending_approval'] = MailRecord.objects.filter(
            status__in=['received_mailroom', 'sorted']
        ).order_by('-created_at')[:10]
        
        # Recent scans
        context['recent_scans'] = MailStatusLog.objects.filter(
            status='received_mailroom'
        ).select_related('mail', 'changed_by').order_by('-timestamp')[:10]
        
        return context


class MailroomReceiveView(MailroomStaffMixin, DetailView):
    model = MailRecord
    template_name = 'mailroom/receive.html'
    context_object_name = 'mail'

    def post(self, request, *args, **kwargs):
        mail = self.get_object()
        
        if mail.status != 'created':
            messages.error(request, 'Mail cannot be received in current status')
            return redirect('mail:detail', pk=mail.pk)
        
        mail.status = 'received_mailroom'
        mail.physical_received = True
        
        notes = request.POST.get('notes', '')
        if notes:
            mail.notes = (mail.notes + '\n\n' + notes).strip()
        
        mail.save()
        
        MailStatusLog.objects.create(
            mail=mail,
            status='received_mailroom',
            changed_by=request.user,
            note='Physical document received at mailroom'
        )
        
        messages.success(request, f'Mail {mail.reference_number} received successfully')
        return redirect('mailroom:dashboard')


class MailroomApproveView(MailroomStaffMixin, DetailView):
    model = MailRecord
    template_name = 'mailroom/approve.html'
    context_object_name = 'mail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        mail = self.get_object()
        
        if mail.status not in ['received_mailroom', 'sorted']:
            messages.error(request, 'Mail cannot be approved in current status')
            return redirect('mail:detail', pk=mail.pk)
        
        dept_id = request.POST.get('recipient_department')
        if not dept_id:
            messages.error(request, 'Please select a recipient department')
            return redirect('mailroom:approve', pk=mail.pk)
        
        mail.status = 'routed'
        mail.recipient_department = Department.objects.get(pk=dept_id)
        
        notes = request.POST.get('notes', '')
        if notes:
            mail.notes = (mail.notes + '\n\n' + notes).strip()
        
        mail.save()
        
        MailStatusLog.objects.create(
            mail=mail,
            status='routed',
            changed_by=request.user,
            note=f'Routed to {mail.recipient_department.name}'
        )
        
        messages.success(request, f'Mail {mail.reference_number} approved and routed')
        return redirect('mailroom:dashboard')


class MailroomRouteView(MailroomStaffMixin, DetailView):
    model = MailRecord
    template_name = 'mailroom/route.html'
    context_object_name = 'mail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.exclude(is_cau=True)
        return context

    def post(self, request, *args, **kwargs):
        mail = self.get_object()
        
        if mail.status not in ['received_mailroom', 'sorted', 'approved']:
            messages.error(request, 'Mail cannot be routed in current status')
            return redirect('mail:detail', pk=mail.pk)
        
        form = MailroomRouteForm(request.POST)
        if form.is_valid():
            mail.status = 'routed'
            mail.recipient_department = form.cleaned_data['recipient_department']
            
            if form.cleaned_data['notes']:
                mail.notes = (mail.notes + '\n\n' + form.cleaned_data['notes']).strip()
            
            mail.save()
            
            MailStatusLog.objects.create(
                mail=mail,
                status='routed',
                changed_by=request.user,
                note=f'Routed to {mail.recipient_department.name}'
            )
            
            messages.success(request, f'Mail {mail.reference_number} routed successfully')
            return redirect('mailroom:dashboard')
        
        return self.render_to_response(self.get_context_data(form=form))
