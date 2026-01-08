"""
通知系统后台管理
"""
from django.contrib import admin
from .models import Notification, NotificationRecipient


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """通知管理"""
    list_display = ['id', 'title', 'scope', 'notification_type', 'priority', 'status', 'tenant', 'created_at']
    list_filter = ['scope', 'notification_type', 'priority', 'status', 'tenant']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'email_sent_at']
    raw_id_fields = ['application', 'tenant', 'created_by']
    ordering = ['-created_at']


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    """通知接收者管理"""
    list_display = ['id', 'notification', 'member', 'is_read', 'read_at', 'created_at']
    list_filter = ['is_read', 'tenant']
    search_fields = ['notification__title', 'member__username']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    raw_id_fields = ['notification', 'member', 'tenant']
    ordering = ['-created_at']
