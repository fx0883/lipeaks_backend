"""
打卡系统管理界面配置

租户隔离架构：
- TaskCategory/TaskTemplate: 由租户管理员管理，无 member 字段
- Task/CheckRecord/CheckinCycle: 关联到 Member
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import TaskCategory, Task, CheckRecord, TaskTemplate, CheckinCycle
from .admin_mixins import CheckSystemAdminMixin


@admin.register(TaskCategory)
class TaskCategoryAdmin(CheckSystemAdminMixin, admin.ModelAdmin):
    """打卡类型管理配置 - 由租户管理员管理"""
    list_display = ('name', 'is_system', 'form_type', 'sort_order', 'tenant', 'created_at')
    list_filter = ('is_system', 'form_type', 'tenant', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'description', 'icon', 'color', 'is_system')
        }),
        (_('21天打卡配置'), {
            'fields': ('form_type', 'goal', 'tip', 'quote', 'sort_order')
        }),
        (_('多语言翻译'), {
            'fields': ('translations',)
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Task)
class TaskAdmin(CheckSystemAdminMixin, admin.ModelAdmin):
    """打卡任务管理配置 - 关联到 Member"""
    list_display = ('name', 'category', 'member', 'tenant', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'category', 'tenant', 'created_at', 'start_date')
    search_fields = ('name', 'description', 'member__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('member',)
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'description', 'category', 'status')
        }),
        (_('关联信息'), {
            'fields': ('member', 'tenant')
        }),
        (_('时间信息'), {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
        (_('提醒设置'), {
            'fields': ('reminder', 'reminder_time')
        }),
        (_('打卡频率'), {
            'fields': ('frequency_type', 'frequency_days')
        }),
    )


@admin.register(CheckRecord)
class CheckRecordAdmin(CheckSystemAdminMixin, admin.ModelAdmin):
    """打卡记录管理配置 - 关联到 Member"""
    list_display = ('member', 'task', 'theme', 'check_date', 'check_time', 'delayed', 'created_at')
    list_filter = ('check_date', 'delayed', 'tenant', 'created_at')
    search_fields = ('task__name', 'theme__name', 'member__username', 'remarks')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('member', 'task', 'theme')
    fieldsets = (
        (_('关联信息'), {
            'fields': ('member', 'task', 'theme', 'tenant')
        }),
        (_('打卡信息'), {
            'fields': ('check_date', 'check_time', 'completion_time', 'delayed')
        }),
        (_('内容'), {
            'fields': ('remarks', 'comment', 'extra_data')
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(TaskTemplate)
class TaskTemplateAdmin(CheckSystemAdminMixin, admin.ModelAdmin):
    """任务模板管理配置 - 由租户管理员管理"""
    list_display = ('name', 'is_system', 'category', 'tenant', 'reminder', 'created_at')
    list_filter = ('is_system', 'category', 'tenant', 'reminder', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'description', 'category', 'is_system')
        }),
        (_('租户信息'), {
            'fields': ('tenant',)
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


@admin.register(CheckinCycle)
class CheckinCycleAdmin(CheckSystemAdminMixin, admin.ModelAdmin):
    """打卡周期管理配置 - 关联到 Member"""
    list_display = ('member', 'start_date', 'end_date', 'is_active', 'tenant', 'created_at')
    list_filter = ('is_active', 'tenant', 'start_date', 'created_at')
    search_fields = ('member__username',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('member',)
    fieldsets = (
        (_('关联信息'), {
            'fields': ('member', 'tenant')
        }),
        (_('周期信息'), {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        (_('主题选择'), {
            'fields': ('selected_themes',)
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
