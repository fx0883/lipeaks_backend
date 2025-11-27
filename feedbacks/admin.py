"""
User Feedback System Admin Configuration

This module configures the Django admin interface for feedback management.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q

from .models import (
    Feedback, FeedbackReply, FeedbackStatusHistory,
    FeedbackAttachment, FeedbackVote,
    FeedbackEmailLog, EmailTemplate,
    FeedbackNotificationConfig, FeedbackNotificationRecipient
)


# ===================== Application Management Admin =====================
# Application相关Admin已移至applications模块
# 应用管理请使用 applications.admin


# ===================== Feedback Management Admin =====================

# 继续保留原FeedbackAdmin配置...


# ===================== Feedback Management Admin =====================

class FeedbackReplyInline(admin.StackedInline):
    """Inline admin for Feedback Replies"""
    model = FeedbackReply
    extra = 0
    fields = ['user', 'content', 'is_internal_note', 'email_sent', 'email_sent_at']
    readonly_fields = ['email_sent', 'email_sent_at', 'created_at']
    ordering = ['created_at']


class FeedbackAttachmentInline(admin.TabularInline):
    """Inline admin for Feedback Attachments"""
    model = FeedbackAttachment
    extra = 0
    fields = ['file', 'filename', 'file_size', 'mime_type', 'uploaded_by']
    readonly_fields = ['filename', 'file_size', 'mime_type', 'uploaded_by']


class FeedbackStatusHistoryInline(admin.TabularInline):
    """Inline admin for Status History"""
    model = FeedbackStatusHistory
    extra = 0
    fields = ['from_status', 'to_status', 'changed_by', 'reason', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback"""
    list_display = [
        'title_truncated', 'application', 'feedback_type', 'priority', 'status',
        'submitter_info', 'vote_count', 'reply_count', 'created_at'
    ]
    list_filter = [
        'feedback_type', 'priority', 'status', 
        'email_verified', 'created_at'
    ]
    search_fields = ['title', 'description', 'contact_email', 'contact_name']
    readonly_fields = [
        'user', 'ip_address', 'user_agent', 'email_verified',
        'email_verification_token', 'email_verification_sent_at',
        'view_count', 'vote_count', 'reply_count',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    inlines = [FeedbackReplyInline, FeedbackAttachmentInline, FeedbackStatusHistoryInline]
    
    fieldsets = (
        (_('Feedback Information'), {
            'fields': ('title', 'description', 'feedback_type', 'priority', 'status')
        }),
        (_('Application Association'), {
            'fields': ('application', 'application_version')
        }),
        (_('Submitter Information'), {
            'fields': ('user', 'contact_email', 'contact_name', 'email_verified')
        }),
        (_('Processing Information'), {
            'fields': ('assigned_to', 'resolved_at', 'resolution_notes')
        }),
        (_('Environment Information'), {
            'fields': ('environment_info', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('Email Settings'), {
            'fields': (
                'email_notification_enabled', 'email_verification_token',
                'email_verification_sent_at'
            ),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('view_count', 'vote_count', 'reply_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_reviewing', 'mark_as_confirmed', 'mark_as_in_progress',
        'mark_as_resolved', 'mark_as_closed', 'mark_as_rejected'
    ]
    
    def title_truncated(self, obj):
        """Truncate long titles"""
        if len(obj.title) > 50:
            return obj.title[:50] + '...'
        return obj.title
    title_truncated.short_description = _('Title')
    
    def submitter_info(self, obj):
        """Get submitter information"""
        if obj.user:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:users_user_change', args=[obj.user.id]),
                obj.user.username
            )
        return f"{obj.contact_name or 'Anonymous'} ({obj.contact_email})"
    submitter_info.short_description = _('Submitter')
    
    def mark_as_reviewing(self, request, queryset):
        """Mark feedback as reviewing"""
        queryset.update(status='reviewing')
        self.message_user(request, _('Feedback marked as reviewing.'))
    mark_as_reviewing.short_description = _('Mark as Reviewing')
    
    def mark_as_confirmed(self, request, queryset):
        """Mark feedback as confirmed"""
        queryset.update(status='confirmed')
        self.message_user(request, _('Feedback marked as confirmed.'))
    mark_as_confirmed.short_description = _('Mark as Confirmed')
    
    def mark_as_in_progress(self, request, queryset):
        """Mark feedback as in progress"""
        queryset.update(status='in_progress')
        self.message_user(request, _('Feedback marked as in progress.'))
    mark_as_in_progress.short_description = _('Mark as In Progress')
    
    def mark_as_resolved(self, request, queryset):
        """Mark feedback as resolved"""
        from django.utils import timezone
        queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, _('Feedback marked as resolved.'))
    mark_as_resolved.short_description = _('Mark as Resolved')
    
    def mark_as_closed(self, request, queryset):
        """Mark feedback as closed"""
        queryset.update(status='closed')
        self.message_user(request, _('Feedback marked as closed.'))
    mark_as_closed.short_description = _('Mark as Closed')
    
    def mark_as_rejected(self, request, queryset):
        """Mark feedback as rejected"""
        queryset.update(status='rejected')
        self.message_user(request, _('Feedback marked as rejected.'))
    mark_as_rejected.short_description = _('Mark as Rejected')


@admin.register(FeedbackReply)
class FeedbackReplyAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback Replies"""
    list_display = [
        'feedback_title', 'user', 'content_truncated', 
        'is_internal_note', 'email_sent', 'created_at'
    ]
    list_filter = ['is_internal_note', 'email_sent', 'created_at']
    search_fields = ['feedback__title', 'content', 'user__username']
    readonly_fields = ['email_sent', 'email_sent_at', 'email_error', 'email_retry_count']
    date_hierarchy = 'created_at'
    
    def feedback_title(self, obj):
        """Get feedback title with link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:feedbacks_feedback_change', args=[obj.feedback.id]),
            obj.feedback.title[:50]
        )
    feedback_title.short_description = _('Feedback')
    
    def content_truncated(self, obj):
        """Truncate long content"""
        if len(obj.content) > 100:
            return obj.content[:100] + '...'
        return obj.content
    content_truncated.short_description = _('Content')


@admin.register(FeedbackVote)
class FeedbackVoteAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback Votes"""
    list_display = ['feedback_title', 'user', 'vote_type_display', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['feedback__title', 'user__username']
    date_hierarchy = 'created_at'
    
    def feedback_title(self, obj):
        """Get feedback title"""
        return obj.feedback.title[:50]
    feedback_title.short_description = _('Feedback')
    
    def vote_type_display(self, obj):
        """Display vote type with emoji"""
        return "👍 Upvote" if obj.vote_type == 1 else "👎 Downvote"
    vote_type_display.short_description = _('Vote')


# ===================== Email Management Admin =====================

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for Email Templates"""
    list_display = ['name', 'template_type', 'subject', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'body_html', 'body_text']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'template_type', 'is_active')
        }),
        (_('Email Content'), {
            'fields': ('subject', 'body_html', 'body_text')
        }),
        (_('Variables'), {
            'fields': ('variables',),
            'classes': ('collapse',),
            'description': _('Available template variables for this email type')
        }),
    )


@admin.register(FeedbackEmailLog)
class FeedbackEmailLogAdmin(admin.ModelAdmin):
    """Admin configuration for Email Logs"""
    list_display = [
        'email_type', 'recipient', 'subject_truncated', 
        'status', 'sent_at', 'retry_count'
    ]
    list_filter = ['email_type', 'status', 'sent_at']
    search_fields = ['recipient', 'subject', 'content']
    readonly_fields = ['sent_at', 'error_message', 'retry_count', 'celery_task_id']
    date_hierarchy = 'sent_at'
    
    def subject_truncated(self, obj):
        """Truncate long subjects"""
        if len(obj.subject) > 50:
            return obj.subject[:50] + '...'
        return obj.subject
    subject_truncated.short_description = _('Subject')
    
    actions = ['resend_email']
    
    def resend_email(self, request, queryset):
        """Resend failed emails"""
        # TODO: Implement email resending logic
        self.message_user(request, _('Email resending initiated.'))
    resend_email.short_description = _('Resend failed emails')


# ===================== Notification Configuration Admin =====================

class FeedbackNotificationRecipientInline(admin.TabularInline):
    """Inline admin for Notification Recipients"""
    model = FeedbackNotificationRecipient
    extra = 1
    fields = ['email', 'name', 'is_active', 'created_at']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(FeedbackNotificationConfig)
class FeedbackNotificationConfigAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback Notification Config"""
    list_display = [
        'application_name', 'is_enabled', 'recipient_count', 
        'active_recipient_count', 'tenant_name', 'created_at'
    ]
    list_filter = ['is_enabled', 'tenant', 'created_at']
    search_fields = ['application__name', 'application__code']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [FeedbackNotificationRecipientInline]
    autocomplete_fields = ['application']
    
    fieldsets = (
        (_('基本信息'), {
            'fields': ('application', 'tenant', 'is_enabled')
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            is_deleted=False
        ).select_related('application', 'tenant')
    
    def application_name(self, obj):
        """显示应用名称"""
        return obj.application.name
    application_name.short_description = _('应用名称')
    application_name.admin_order_field = 'application__name'
    
    def tenant_name(self, obj):
        """显示租户名称"""
        return obj.tenant.name if obj.tenant else '-'
    tenant_name.short_description = _('租户')
    tenant_name.admin_order_field = 'tenant__name'
    
    def recipient_count(self, obj):
        """显示接收者总数"""
        return obj.recipients.filter(is_deleted=False).count()
    recipient_count.short_description = _('接收者数量')
    
    def active_recipient_count(self, obj):
        """显示活跃接收者数量"""
        return obj.get_active_recipients().count()
    active_recipient_count.short_description = _('活跃接收者')


@admin.register(FeedbackNotificationRecipient)
class FeedbackNotificationRecipientAdmin(admin.ModelAdmin):
    """Admin configuration for Notification Recipients"""
    list_display = [
        'email', 'name', 'config_application', 'is_active', 
        'tenant_name', 'created_at'
    ]
    list_filter = ['is_active', 'config__application', 'tenant', 'created_at']
    search_fields = ['email', 'name', 'config__application__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            is_deleted=False
        ).select_related('config__application', 'tenant')
    
    def config_application(self, obj):
        """显示关联的应用"""
        return obj.config.application.name
    config_application.short_description = _('应用')
    config_application.admin_order_field = 'config__application__name'
    
    def tenant_name(self, obj):
        """显示租户名称"""
        return obj.tenant.name if obj.tenant else '-'
    tenant_name.short_description = _('租户')
    tenant_name.admin_order_field = 'tenant__name'