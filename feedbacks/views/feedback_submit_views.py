"""
Member Feedback Submission Views (Server-side Pages)
提供基于 HTML 表单的反馈提交流程
"""
import logging
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from feedbacks.forms import FeedbackSubmitForm
from feedbacks.models import Feedback
from applications.models import Application
from users.models import Member
from tenants.models import Tenant

logger = logging.getLogger(__name__)


class FeedbackSubmitPageView(FormView):
    """
    Member 反馈提交页面视图
    GET: 显示反馈提交表单
    POST: 处理反馈提交
    支持URL参数: ?tenant_id=1&application_id=2&member_token=xxx
    """
    template_name = 'feedbacks/feedback_submit.html'
    form_class = FeedbackSubmitForm
    success_url = reverse_lazy('feedbacks:feedback-submit-success')
    
    def dispatch(self, request, *args, **kwargs):
        """验证必需的URL参数"""
        # 初始化所有属性，避免 AttributeError
        self.tenant_id = request.GET.get('tenant_id')
        self.application_id = request.GET.get('application_id')
        self.member_token = request.GET.get('member_token')
        self.tenant = None
        self.application = None
        self.member = None
        self.member_email = None
        self.member_name = None
        
        # 验证 tenant_id 和 application_id
        if not self.tenant_id or not self.application_id:
            messages.error(request, _('Missing required parameters: tenant_id and application_id'))
            return self.render_to_response(self.get_context_data(
                form=None,
                error_message=_('Invalid access. Please use the correct link.')
            ))
        
        # 验证租户
        try:
            self.tenant = Tenant.objects.get(id=self.tenant_id, status='active', is_deleted=False)
        except Tenant.DoesNotExist:
            messages.error(request, _('Invalid tenant'))
            return self.render_to_response(self.get_context_data(
                form=None,
                error_message=_('Tenant not found or inactive.')
            ))
        
        # 验证软件
        try:
            self.application = Application.objects.get(
                id=self.application_id,
                tenant=self.tenant,
                is_active=True,
                is_deleted=False
            )
        except Application.DoesNotExist:
            messages.error(request, _('Invalid software'))
            return self.render_to_response(self.get_context_data(
                form=None,
                error_message=_('Application not found or inactive.')
            ))
        
        # 处理 member_token（可选）
        if self.member_token:
            try:
                # 解析 JWT Token
                token = AccessToken(self.member_token)
                member_id = token.get('user_id')
                
                # 获取 Member 用户
                self.member = Member.objects.get(
                    id=member_id,
                    tenant=self.tenant,
                    is_active=True,
                    is_deleted=False,
                    status='active'
                )
                self.member_email = self.member.email
                self.member_name = self.member.display_name or self.member.username
                
                logger.info(f"Member authenticated: {self.member.email}")
                
            except (TokenError, InvalidToken, Member.DoesNotExist) as e:
                logger.warning(f"Invalid member token: {str(e)}")
                # Token 无效，按匿名用户处理
                self.member_token = None
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """传递参数给表单"""
        kwargs = super().get_form_kwargs()
        kwargs['initial_tenant_id'] = self.tenant_id
        kwargs['initial_application_id'] = self.application_id
        kwargs['has_member_info'] = bool(self.member)
        
        # 如果有 member 信息，预填充表单
        if self.member:
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            kwargs['initial']['contact_email'] = self.member_email
            kwargs['initial']['contact_name'] = self.member_name
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        """添加额外上下文"""
        context = super().get_context_data(**kwargs)
        context['software'] = self.application
        context['tenant'] = self.tenant
        context['member'] = self.member
        context['has_member_info'] = bool(self.member)
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
        try:
            # 获取表单数据
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            feedback_type = form.cleaned_data['feedback_type']
            priority = form.cleaned_data['priority']
            contact_email = form.cleaned_data.get('contact_email')
            contact_name = form.cleaned_data.get('contact_name')
            
            # 创建反馈记录
            feedback = Feedback.objects.create(
                tenant=self.tenant,
                application=self.application,
                title=title,
                description=description,
                feedback_type=feedback_type,
                priority=priority,
                contact_email=contact_email or self.member_email,
                contact_name=contact_name or self.member_name,
                user=None,  # Member 不设置 user 字段
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='submitted'
            )
            
            logger.info(
                f"Feedback submitted: ID={feedback.id}, "
                f"Software={self.application.name}, "
                f"Type={feedback_type}, "
                f"Member={self.member.email if self.member else 'Anonymous'}"
            )
            
            # 触发新反馈通知邮件（异步处理，不影响用户体验）
            try:
                from feedbacks.services import EmailService
                notification_result = EmailService.send_new_feedback_notification(feedback)
                logger.info(f"New feedback notification triggered: {notification_result}")
            except Exception as notify_error:
                # 通知失败不影响反馈提交成功
                logger.warning(f"Failed to trigger notification for feedback {feedback.id}: {notify_error}")
            
            messages.success(
                self.request,
                _('Thank you for your feedback! We will review it shortly.')
            )
            
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f"Failed to submit feedback: {str(e)}")
            messages.error(self.request, _('Failed to submit feedback. Please try again.'))
            return self.form_invalid(form)


class FeedbackSubmitSuccessView(TemplateView):
    """反馈提交成功页面"""
    template_name = 'feedbacks/feedback_submit_success.html'
