"""
Account Deletion Forms for Member users
Allows members to delete their account and all associated data
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from tenants.models import Tenant


class AccountDeletionLoginForm(forms.Form):
    """
    Account deletion login form
    User enters username/email and password to verify identity
    tenant_id is passed via URL parameter (hidden field)
    """
    username = forms.CharField(
        label='Username or Email',
        max_length=254,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'username',
            'placeholder': 'Enter your username or email'
        })
    )
    
    password = forms.CharField(
        label='Password',
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
            'placeholder': 'Enter your password'
        })
    )
    
    # tenant_id as hidden field, from URL parameter
    tenant_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        # Extract tenant_id from URL parameter
        initial_tenant_id = kwargs.pop('initial_tenant_id', None)
        super().__init__(*args, **kwargs)
        
        # Set tenant_id initial value
        if initial_tenant_id:
            self.fields['tenant_id'].initial = initial_tenant_id
    
    def clean_tenant_id(self):
        """Validate tenant ID"""
        tenant_id = self.cleaned_data.get('tenant_id')
        if not tenant_id:
            raise ValidationError('Tenant ID is required')
        try:
            tenant_id = int(tenant_id)
            # Verify tenant exists and is active
            Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
        except (ValueError, Tenant.DoesNotExist):
            raise ValidationError('Invalid tenant')
        return tenant_id


class AccountDeletionConfirmForm(forms.Form):
    """
    Account deletion confirmation form
    User must check the confirmation checkbox to proceed
    """
    confirm_delete = forms.BooleanField(
        label='I understand that all my data will be permanently deleted and this action cannot be undone.',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'confirm-delete-checkbox'
        })
    )
    
    # Hidden field to pass member_id securely
    member_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    # Hidden field for verification token
    token = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
