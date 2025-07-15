"""
打卡系统管理界面配置
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import TaskCategory, Task, CheckRecord, TaskTemplate


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    """打卡类型管理配置"""
    list_display = ('name', 'is_system', 'user', 'tenant', 'created_at')
    list_filter = ('is_system', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'description', 'icon', 'is_system')
        }),
        (_('关联信息'), {
            'fields': ('user', 'tenant')
        }),
        (_('多语言翻译'), {
            'fields': ('translations',)
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """打卡任务管理配置"""
    list_display = ('name', 'category', 'user', 'tenant', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'category', 'created_at', 'start_date')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'description', 'category', 'status')
        }),
        (_('关联信息'), {
            'fields': ('user', 'tenant')
        }),
        (_('时间信息'), {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
        (_('提醒设置'), {
            'fields': ('reminder', 'reminder_time')
        }),
    )


@admin.register(CheckRecord)
class CheckRecordAdmin(admin.ModelAdmin):
    """打卡记录管理配置"""
    list_display = ('user', 'task', 'check_date', 'check_time', 'completion_time', 'remarks', 'comment', 'created_at')
    list_filter = ('check_date', 'created_at')
    search_fields = ('task__name', 'user__username', 'remarks', 'comment')
    readonly_fields = ('created_at',)
    fieldsets = (
        (_('关联信息'), {
            'fields': ('user', 'task')
        }),
        (_('打卡信息'), {
            'fields': ('check_date', 'check_time', 'completion_time', 'remarks', 'comment')
        }),
        (_('时间信息'), {
            'fields': ('created_at',)
        }),
    )


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    """任务模板管理配置"""
    list_display = ('name', 'is_system', 'category', 'user', 'tenant', 'reminder', 'created_at')
    list_filter = ('is_system', 'category', 'reminder', 'created_at')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'description', 'category', 'is_system')
        }),
        (_('关联信息'), {
            'fields': ('user', 'tenant')
        }),
        (_('提醒设置'), {
            'fields': ('reminder', 'reminder_time')
        }),
        (_('多语言翻译'), {
            'fields': ('translations',)
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
