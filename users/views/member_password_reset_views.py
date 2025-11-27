"""
Member 密码重置视图（服务端页面）
提供基于 HTML 表单的密码重置流程

URL: /api/v1/members/password-reset/
必需参数: tenant_id (URL参数)
支持多语言: 通过 Accept-Language Header
"""
import logging
import secrets
import string
from django.views.generic import FormView, TemplateView
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.cache import cache

from django.utils.translation import gettext_lazy as _

from users.forms import MemberPasswordResetRequestForm, MemberPasswordResetConfirmForm
from users.models import Member, PasswordResetToken
from tenants.models import Tenant

logger = logging.getLogger(__name__)


class MemberPasswordResetRequestPageView(FormView):
    """
    Member 密码重置请求页面视图
    GET: 显示邮箱输入表单
    POST: 处理请求，生成token并发送邮件
    必需URL参数: ?tenant_id=xxx
    """
    template_name = 'members/password_reset_request.html'
    form_class = MemberPasswordResetRequestForm
    
    def dispatch(self, request, *args, **kwargs):
        """验证必需的URL参数"""
        self.tenant_id = request.GET.get('tenant_id')
        self.tenant = None
        
        # 验证 tenant_id 必须存在
        if not self.tenant_id:
            messages.error(request, _('Missing required parameter: tenant_id'))
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Invalid access. Please use the correct link with tenant_id parameter.')
            })
        
        # 验证租户是否存在且活跃
        try:
            self.tenant = Tenant.objects.get(id=self.tenant_id, status='active', is_deleted=False)
        except (Tenant.DoesNotExist, ValueError):
            messages.error(request, _('Invalid tenant'))
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Tenant not found or inactive.')
            })
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        """成功后跳转时保留 tenant_id 参数"""
        return reverse('member_password_reset:sent') + f'?tenant_id={self.tenant_id}'
    
    def get_form_kwargs(self):
        """传递URL参数中的tenant_id给表单"""
        kwargs = super().get_form_kwargs()
        kwargs['initial_tenant_id'] = self.tenant_id
        return kwargs
    
    def get_context_data(self, **kwargs):
        """添加租户信息到上下文"""
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.tenant
        context['tenant_id'] = self.tenant_id
        return context
    
    def get_client_ip(self):
        """获取客户端IP地址"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def form_valid(self, form):
        """处理有效的表单提交"""
        email = form.cleaned_data['email']
        # tenant_id 已经在表单中处理（来自用户选择或URL参数）
        tenant_id = int(form.cleaned_data['tenant_id'])
        
        # Rate limiting: 同一IP每10分钟最多3次请求
        ip = self.get_client_ip()
        cache_key = f"password_reset_request:{ip}"
        request_count = cache.get(cache_key, 0)
        
        if request_count >= 13:
            messages.error(self.request, _('Too many requests. Please try again later.'))
            logger.warning(f"IP {ip} 密码重置请求过于频繁")
            return self.form_invalid(form)
        
        # 增加请求计数
        cache.set(cache_key, request_count + 1, 6)  # 10分钟
        
        # 查找Member用户（必须指定租户）
        member = Member.objects.filter(
            email=email,
            tenant_id=tenant_id,
            is_active=True,
            is_deleted=False,
            status='active',
            parent__isnull=True  # 排除子账号
        ).first()
        
        if member:
            try:
                # 生成安全令牌
                token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
                expires_at = timezone.now() + timezone.timedelta(hours=1)
                
                # 创建密码重置令牌
                reset_token = PasswordResetToken.objects.create(
                    member=member,
                    token=token,
                    expires_at=expires_at
                )
                
                # 构建重置链接（服务端URL，包含 tenant_id）
                # 优先使用 SITE_URL 配置，否则从请求中获取
                reset_path = reverse('member_password_reset:form', kwargs={'token': token}) + f'?tenant_id={tenant_id}'
                if settings.SITE_URL:
                    reset_url = settings.SITE_URL.rstrip('/') + reset_path
                else:
                    reset_url = self.request.build_absolute_uri(reset_path)
                
                # 发送邮件
                context = {
                    'user': member,
                    'reset_link': reset_url,
                    'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 邮件主题和内容支持多语言
                subject = str(_('Password Reset')) + f' - {self.tenant.name}'
                context['tenant'] = self.tenant
                html_message = render_to_string('email/password_reset.html', context, request=self.request)
                plain_message = str(_('Dear %(name)s,\n\nYou have requested to reset your password.\n\nPlease click the following link to reset your password:\n%(url)s\n\nThis link will expire at %(expires)s.\n\nIf you did not request a password reset, please ignore this email.')) % {
                    'name': member.display_name or member.username,
                    'url': reset_url,
                    'expires': expires_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 记录邮件配置信息
                logger.debug(
                    "准备发送密码重置邮件",
                    extra={
                        'member_email': member.email,
                        'tenant_id': tenant_id,
                        'subject': subject,
                        'reset_url': reset_url,
                        'expires_at': context['expires_at'],
                        'email_backend': settings.EMAIL_BACKEND,
                        'smtp_host': getattr(settings, 'EMAIL_HOST', 'N/A'),
                        'smtp_port': getattr(settings, 'EMAIL_PORT', 'N/A'),
                        'from_email': settings.DEFAULT_FROM_EMAIL,
                    }
                )
                
                # 发送邮件
                result = send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[member.email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                logger.info(
                    f"密码重置邮件发送完成 - Member: {member.email} (租户:{tenant_id}), "
                    f"Backend: {settings.EMAIL_BACKEND}, 发送结果: {result}"
                )
                
            except Exception as e:
                logger.error(f"发送密码重置邮件失败: {str(e)}")
                # 删除已创建的令牌
                if 'reset_token' in locals():
                    reset_token.delete()
                messages.error(self.request, _('Failed to send email. Please try again later.'))
                return self.form_invalid(form)
        else:
            # 不暴露用户是否存在，记录日志用于调试
            logger.info(f"密码重置请求：邮箱 {email}，租户 {tenant_id}（可能不存在或不匹配）")
        
        # 无论是否找到用户，都显示成功消息（防止账号枚举）
        return super().form_valid(form)


class MemberPasswordResetFormView(FormView):
    """
    Member 密码重置表单页面视图
    GET: 验证token，显示密码输入表单
    POST: 验证并更新密码
    必需URL参数: ?tenant_id=xxx
    """
    template_name = 'members/password_reset_form.html'
    form_class = MemberPasswordResetConfirmForm
    
    def dispatch(self, request, *args, **kwargs):
        """验证必需的URL参数和token"""
        self.tenant_id = request.GET.get('tenant_id')
        self.tenant = None
        self.token = kwargs.get('token')
        
        # 验证 tenant_id 必须存在
        if not self.tenant_id:
            messages.error(request, _('Missing required parameter: tenant_id'))
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Invalid access. Please use the correct link with tenant_id parameter.')
            })
        
        # 验证租户是否存在且活跃
        try:
            self.tenant = Tenant.objects.get(id=self.tenant_id, status='active', is_deleted=False)
        except (Tenant.DoesNotExist, ValueError):
            messages.error(request, _('Invalid tenant'))
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Tenant not found or inactive.')
            })
        
        # 验证token
        self.token_obj = PasswordResetToken.objects.filter(
            token=self.token,
            is_used=False,
            member__isnull=False  # 确保是Member的token
        ).select_related('member', 'member__tenant').first()
        
        if not self.token_obj:
            logger.warning(f"无效的密码重置token: {self.token}")
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('This reset link does not exist or has already been used.')
            })
        
        if self.token_obj.is_expired():
            logger.warning(f"过期的密码重置token: {self.token}")
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('This reset link has expired. Please request a new password reset.')
            })
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        """成功后跳转时保留 tenant_id 参数"""
        return reverse('member_password_reset:complete') + f'?tenant_id={self.tenant_id}'
    
    def get_context_data(self, **kwargs):
        """添加member和租户信息到上下文"""
        context = super().get_context_data(**kwargs)
        context['member'] = self.token_obj.member
        context['tenant'] = self.tenant
        context['tenant_id'] = self.tenant_id
        context['token'] = self.token
        return context
    
    def form_valid(self, form):
        """处理有效的密码重置表单"""
        new_password = form.cleaned_data['new_password']
        member = self.token_obj.member
        
        try:
            # 更新密码
            member.set_password(new_password)
            member.save(update_fields=['password'])
            
            # 标记token为已使用
            self.token_obj.mark_as_used()
            
            logger.info(f"Member {member.username} (租户:{member.tenant_id}) 密码重置成功")
            messages.success(self.request, _('Password reset successful. Please login with your new password.'))
            
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f"密码重置失败: {str(e)}")
            messages.error(self.request, _('Password reset failed. Please try again.'))
            return self.form_invalid(form)


class MemberPasswordResetRequestSentView(TemplateView):
    """密码重置邮件发送成功页面"""
    template_name = 'members/password_reset_request_sent.html'
    
    def dispatch(self, request, *args, **kwargs):
        """验证必需的URL参数"""
        self.tenant_id = request.GET.get('tenant_id')
        self.tenant = None
        
        # 验证 tenant_id 必须存在
        if not self.tenant_id:
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Invalid access. Please use the correct link with tenant_id parameter.')
            })
        
        # 验证租户是否存在且活跃
        try:
            self.tenant = Tenant.objects.get(id=self.tenant_id, status='active', is_deleted=False)
        except (Tenant.DoesNotExist, ValueError):
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Tenant not found or inactive.')
            })
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.tenant
        context['tenant_id'] = self.tenant_id
        return context


class MemberPasswordResetCompleteView(TemplateView):
    """密码重置完成页面"""
    template_name = 'members/password_reset_complete.html'
    
    def dispatch(self, request, *args, **kwargs):
        """验证必需的URL参数"""
        self.tenant_id = request.GET.get('tenant_id')
        self.tenant = None
        
        # 验证 tenant_id 必须存在
        if not self.tenant_id:
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Invalid access. Please use the correct link with tenant_id parameter.')
            })
        
        # 验证租户是否存在且活跃
        try:
            self.tenant = Tenant.objects.get(id=self.tenant_id, status='active', is_deleted=False)
        except (Tenant.DoesNotExist, ValueError):
            return render(request, 'members/password_reset_invalid.html', {
                'error_message': _('Tenant not found or inactive.')
            })
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.tenant
        context['tenant_id'] = self.tenant_id
        return context
