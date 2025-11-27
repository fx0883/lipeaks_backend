"""
应用管理Admin配置
"""
from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """应用管理"""
    list_display = ['name', 'code', 'tenant', 'status', 'current_version', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('tenant', 'name', 'code', 'description')
        }),
        ('展示信息', {
            'fields': ('logo', 'website', 'contact_email')
        }),
        ('版本和团队', {
            'fields': ('current_version', 'owner', 'team')
        }),
        ('状态', {
            'fields': ('status', 'is_active')
        }),
        ('元数据', {
            'fields': ('tags', 'metadata'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
