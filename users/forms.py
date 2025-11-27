"""
Member 密码重置表单
"""
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from tenants.models import Tenant


class MemberPasswordResetRequestForm(forms.Form):
    """
    Member 密码重置请求表单
    用户输入邮箱请求密码重置
    tenant_id 通过 URL 参数传递（隐藏字段）
    """
    email = forms.EmailField(
        label=_('Email Address'),
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email'
        })
    )
    
    # tenant_id 作为隐藏字段，从 URL 参数获取
    tenant_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        # 提取URL参数传递的tenant_id
        initial_tenant_id = kwargs.pop('initial_tenant_id', None)
        super().__init__(*args, **kwargs)
        
        # 设置 placeholder（支持多语言）
        self.fields['email'].widget.attrs['placeholder'] = str(_('Enter your email address'))
        
        # 设置 tenant_id 初始值
        if initial_tenant_id:
            self.fields['tenant_id'].initial = initial_tenant_id
    
    def clean_tenant_id(self):
        """验证租户ID"""
        tenant_id = self.cleaned_data.get('tenant_id')
        if not tenant_id:
            raise ValidationError(_('Tenant ID is required'))
        try:
            tenant_id = int(tenant_id)
            # 验证租户是否存在且活跃
            Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
        except (ValueError, Tenant.DoesNotExist):
            raise ValidationError(_('Invalid tenant'))
        return tenant_id


class MemberPasswordResetConfirmForm(forms.Form):
    """
    Member 密码重置确认表单
    用户输入新密码完成密码重置
    """
    new_password = forms.CharField(
        label=_('New Password'),
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        })
    )
    
    new_password_confirm = forms.CharField(
        label=_('Confirm New Password'),
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set placeholders dynamically to support i18n
        self.fields['new_password'].widget.attrs['placeholder'] = str(_('Enter new password'))
        self.fields['new_password_confirm'].widget.attrs['placeholder'] = str(_('Confirm new password'))
    
    def clean_new_password(self):
        """验证新密码强度"""
        password = self.cleaned_data.get('new_password')
        if password:
            validate_password(password)
        return password
    
    def clean(self):
        """验证两次密码输入是否一致"""
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        password_confirm = cleaned_data.get('new_password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError({
                    'new_password_confirm': _('Passwords do not match')
                })
        
        return cleaned_data
