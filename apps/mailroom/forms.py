from django import forms
from apps.mail.models import MailRecord
from apps.departments.models import Department


class MailroomReceiveForm(forms.ModelForm):
    class Meta:
        model = MailRecord
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'border rounded px-3 py-2 w-full',
                'rows': 3,
                'placeholder': 'Additional notes about physical receipt...'
            }),
        }


class MailroomApproveForm(forms.ModelForm):
    class Meta:
        model = MailRecord
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'border rounded px-3 py-2 w-full',
                'rows': 3,
                'placeholder': 'Approval notes...'
            }),
        }


class MailroomRouteForm(forms.Form):
    recipient_department = forms.ModelChoiceField(
        queryset=Department.objects.exclude(is_cau=True),
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'border rounded px-3 py-2 w-full',
            'rows': 3,
            'placeholder': 'Routing notes...'
        })
    )
