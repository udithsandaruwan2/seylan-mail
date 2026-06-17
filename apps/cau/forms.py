from django import forms
from apps.cau.models import CAUMailDetail, DiscrepancyLog, WalletDocument
from apps.departments.models import DocumentType


class CAUIntakeForm(forms.ModelForm):
    document_types = forms.ModelMultipleChoiceField(
        queryset=DocumentType.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'}),
        required=False
    )

    class Meta:
        model = CAUMailDetail
        fields = ['assigned_officer', 'document_types', 'additional_notes']
        widgets = {
            'assigned_officer': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'additional_notes': forms.Textarea(attrs={'class': 'border rounded px-3 py-2 w-full', 'rows': 4}),
        }


class DiscrepancyForm(forms.ModelForm):
    class Meta:
        model = DiscrepancyLog
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'border rounded px-3 py-2 w-full',
                'rows': 4,
                'placeholder': 'Describe the discrepancy...'
            }),
        }


class DiscrepancyResolveForm(forms.ModelForm):
    resolution_note = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'border rounded px-3 py-2 w-full', 'rows': 3}),
        required=False
    )

    class Meta:
        model = DiscrepancyLog
        fields = []

    def save(self, commit=True, resolved_by=None):
        instance = super().save(commit=False)
        instance.resolved = True
        instance.resolved_by = resolved_by
        if commit:
            instance.save()
        return instance


class WalletRetrieveForm(forms.ModelForm):
    class Meta:
        model = WalletDocument
        fields = ['retrieval_note']
        widgets = {
            'retrieval_note': forms.Textarea(attrs={
                'class': 'border rounded px-3 py-2 w-full',
                'rows': 3,
                'placeholder': 'Optional note about retrieval...'
            }),
        }


class WalletReturnForm(forms.ModelForm):
    class Meta:
        model = WalletDocument
        fields = ['return_reason']
        widgets = {
            'return_reason': forms.Textarea(attrs={
                'class': 'border rounded px-3 py-2 w-full',
                'rows': 3,
                'placeholder': 'Reason for returning to wallet...'
            }),
        }


class WalletFilterForm(forms.Form):
    branch = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )
    officer = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        cau_officers = User.objects.filter(profile__role='cau_officer')
        self.fields['officer'].queryset = cau_officers
        self.fields['branch'].queryset = None  # Will be set in view if needed
