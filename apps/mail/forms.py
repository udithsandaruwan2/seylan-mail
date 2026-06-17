from django import forms
from apps.mail.models import MailRecord, MailStatusLog
from apps.branches.models import Branch
from apps.departments.models import Department


class MailCreateForm(forms.ModelForm):
    recipient_type = forms.ChoiceField(
        choices=[('department', 'Department'), ('branch', 'Branch')],
        widget=forms.RadioSelect,
        initial='department'
    )

    class Meta:
        model = MailRecord
        fields = ['origin_type', 'subject', 'description', 'notes']
        widgets = {
            'origin_type': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'subject': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'description': forms.Textarea(attrs={'class': 'border rounded px-3 py-2 w-full', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'border rounded px-3 py-2 w-full', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-set sender based on user role
        if self.user and hasattr(self.user, 'profile'):
            profile = self.user.profile
            if profile.branch:
                self.fields['sender_branch'] = forms.ModelChoiceField(
                    queryset=Branch.objects.filter(pk=profile.branch.pk),
                    required=False,
                    widget=forms.HiddenInput()
                )
            if profile.department:
                self.fields['sender_department'] = forms.ModelChoiceField(
                    queryset=Department.objects.filter(pk=profile.department.pk),
                    required=False,
                    widget=forms.HiddenInput()
                )


class MailFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + MailRecord.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )
    origin_type = forms.ChoiceField(
        choices=[('', 'All Types')] + MailRecord.ORIGIN_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2'})
    )
