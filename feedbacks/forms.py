"""
Feedback Submission Forms
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from applications.models import Application


class FeedbackSubmitForm(forms.Form):
    """
    Member Feedback Submission Form
    用户提交反馈的表单
    """
    FEEDBACK_TYPE_CHOICES = [
        ('bug', _('Bug Report')),
        ('feature', _('Feature Request')),
        ('improvement', _('Improvement')),
        ('question', _('Question')),
        ('other', _('Other')),
    ]
    
    PRIORITY_CHOICES = [
        ('critical', _('Critical')),
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]
    
    title = forms.CharField(
        label=_('Title'),
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )
    
    description = forms.CharField(
        label=_('Description'),
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'autocomplete': 'off'
        })
    )
    
    feedback_type = forms.ChoiceField(
        label=_('Feedback Type'),
        choices=FEEDBACK_TYPE_CHOICES,
        initial='bug',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    priority = forms.ChoiceField(
        label=_('Priority'),
        choices=PRIORITY_CHOICES,
        initial='medium',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    contact_email = forms.EmailField(
        label=_('Contact Email'),
        max_length=254,
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email'
        })
    )
    
    contact_name = forms.CharField(
        label=_('Contact Name'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'name'
        })
    )
    
    # Hidden fields for URL parameters
    tenant_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    software_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        # Extract URL parameters
        initial_tenant_id = kwargs.pop('initial_tenant_id', None)
        initial_software_id = kwargs.pop('initial_software_id', None)
        has_member_info = kwargs.pop('has_member_info', False)
        
        super().__init__(*args, **kwargs)
        
        # Set placeholders for i18n
        self.fields['title'].widget.attrs['placeholder'] = _('Brief description of the issue')
        self.fields['description'].widget.attrs['placeholder'] = _('Please describe the issue in detail')
        self.fields['contact_email'].widget.attrs['placeholder'] = _('Your email address for updates')
        self.fields['contact_name'].widget.attrs['placeholder'] = _('Your name')
        
        # Set initial values from URL parameters
        if initial_tenant_id:
            self.fields['tenant_id'].initial = initial_tenant_id
        
        if initial_software_id:
            self.fields['software_id'].initial = initial_software_id
        
        # Hide contact fields if user is authenticated
        if has_member_info:
            self.fields['contact_email'].widget = forms.HiddenInput()
            self.fields['contact_name'].widget = forms.HiddenInput()
    
    def clean_tenant_id(self):
        """Validate tenant ID"""
        from tenants.models import Tenant
        
        tenant_id = self.cleaned_data.get('tenant_id')
        if not tenant_id:
            raise ValidationError(_('Tenant ID is required'))
        
        try:
            Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
        except Tenant.DoesNotExist:
            raise ValidationError(_('Invalid tenant or tenant is inactive'))
        
        return tenant_id
    
    def clean_software_id(self):
        """Validate software ID"""
        software_id = self.cleaned_data.get('software_id')
        if not software_id:
            raise ValidationError(_('Application ID is required'))
        
        try:
            Application.objects.get(id=software_id, is_active=True, is_deleted=False)
        except Application.DoesNotExist:
            raise ValidationError(_('Invalid software'))
        
        return software_id
    
    def clean(self):
        """Cross-field validation: ensure application belongs to the tenant"""
        cleaned_data = super().clean()
        tenant_id = cleaned_data.get('tenant_id')
        software_id = cleaned_data.get('software_id')
        
        if tenant_id and software_id:
            try:
                app = Application.objects.get(
                    id=software_id,
                    tenant_id=tenant_id,
                    is_active=True,
                    is_deleted=False
                )
            except Application.DoesNotExist:
                raise ValidationError(
                    _('The specified application does not belong to this tenant.')
                )
        
        return cleaned_data
