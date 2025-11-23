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
    用户输入邮箱和租户ID请求密码重置
    """
    email = forms.EmailField(
        label=_('邮箱地址'),
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入您的邮箱地址'),
            'autocomplete': 'email'
        })
    )
    
    tenant_id = forms.ChoiceField(
        label=_('所属租户'),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        # 提取URL参数传递的tenant_id
        initial_tenant_id = kwargs.pop('initial_tenant_id', None)
        super().__init__(*args, **kwargs)
        
        # 如果有URL参数tenant_id，将字段改为隐藏的CharField
        if initial_tenant_id:
            # 重新定义为 CharField 以便隐藏提交
            self.fields['tenant_id'] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=initial_tenant_id,
                required=True
            )
        else:
            # 动态加载活跃的租户列表
            tenants = Tenant.objects.filter(status='active', is_deleted=False).order_by('name')
            self.fields['tenant_id'].choices = [('', _('—— 请选择租户 ——'))] + [
                (tenant.id, tenant.name) for tenant in tenants
            ]
    
    def clean_tenant_id(self):
        """验证租户ID"""
        tenant_id = self.cleaned_data.get('tenant_id')
        if not tenant_id:
            raise ValidationError(_('请选择租户'))
        try:
            tenant_id = int(tenant_id)
            # 验证租户是否存在且活跃
            Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
        except (ValueError, Tenant.DoesNotExist):
            raise ValidationError(_('无效的租户'))
        return tenant_id


class MemberPasswordResetConfirmForm(forms.Form):
    """
    Member 密码重置确认表单
    用户输入新密码完成密码重置
    """
    new_password = forms.CharField(
        label=_('新密码'),
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        })
    )
    
    new_password_confirm = forms.CharField(
        label=_('确认新密码'),
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set placeholders dynamically to support i18n
        self.fields['new_password'].widget.attrs['placeholder'] = _('请输入新密码')
        self.fields['new_password_confirm'].widget.attrs['placeholder'] = _('请再次输入新密码')
    
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
                    'new_password_confirm': _('两次输入的密码不一致')
                })
        
        return cleaned_data
