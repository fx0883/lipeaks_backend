"""
许可证系统Django Admin管理后台配置
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from licenses.models import (
    LicensePlan, License, MachineBinding,
    LicenseActivation, LicenseUsageLog, TenantLicenseQuota, SecurityAuditLog
)
from applications.models import Application


# SoftwareProductAdmin已删除，应用管理请使用applications模块的ApplicationAdmin


@admin.register(LicensePlan)
class LicensePlanAdmin(admin.ModelAdmin):
    """许可证方案管理"""
    list_display = ['name', 'plan_type', 'default_max_activations', 'default_validity_days', 'price', 'status', 'application']
    list_filter = ['plan_type', 'status', 'application', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'application', 'plan_type', 'status')
        }),
        ('模板配置', {
            'fields': ('default_max_activations', 'default_validity_days')
        }),
        ('功能配置', {
            'fields': ('features',)
        }),
        ('价格信息', {
            'fields': ('price', 'currency')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        elif hasattr(request.user, 'tenant'):
            return qs.filter(application__tenant=request.user.tenant)
        return qs.none()


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    """许可证管理"""
    list_display = ['license_key_display', 'application', 'plan', 'status', 'customer_name', 'expires_at', 'activation_count']
    list_filter = ['status', 'application', 'plan', 'issued_at', 'expires_at']
    search_fields = ['license_key', 'customer_name', 'customer_email', 'notes']
    readonly_fields = ['license_key', 'license_hash', 'created_at', 'updated_at', 'last_verified_at']
    date_hierarchy = 'issued_at'
    
    fieldsets = (
        ('许可证信息', {
            'fields': ('license_key', 'license_hash', 'application', 'plan', 'status')
        }),
        ('客户信息', {
            'fields': ('customer_name', 'customer_email', 'encrypted_customer_info')
        }),
        ('限制配置', {
            'fields': ('max_activations', 'issued_at', 'expires_at')
        }),
        ('备注信息', {
            'fields': ('notes',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'last_verified_at'),
            'classes': ('collapse',)
        })
    )
    
    def license_key_display(self, obj):
        """显示格式化的许可证密钥"""
        if obj.license_key:
            return obj.license_key[:8] + '...' + obj.license_key[-8:]
        return '-'
    license_key_display.short_description = '许可证密钥'
    
    def activation_count(self, obj):
        """显示激活次数"""
        count = obj.activations.filter(result='success').count()
        max_count = obj.max_activations or 0
        if count >= max_count and max_count > 0:
            return format_html('<span style="color: red;">{}/{}</span>', count, max_count)
        return f'{count}/{max_count}'
    activation_count.short_description = '激活次数'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        elif hasattr(request.user, 'tenant'):
            return qs.filter(tenant=request.user.tenant)
        return qs.none()


@admin.register(MachineBinding)
class MachineBindingAdmin(admin.ModelAdmin):
    """机器绑定管理"""
    list_display = ['machine_id_display', 'license', 'status', 'os_info', 'last_seen_at', 'first_seen_at']
    list_filter = ['status', 'first_seen_at', 'last_seen_at']
    search_fields = ['machine_id', 'license__license_key']
    readonly_fields = ['machine_fingerprint', 'first_seen_at', 'last_seen_at']
    date_hierarchy = 'first_seen_at'
    
    fieldsets = (
        ('机器信息', {
            'fields': ('machine_id', 'machine_fingerprint', 'status')
        }),
        ('许可证信息', {
            'fields': ('license',)
        }),
        ('系统信息', {
            'fields': ('os_info', 'hardware_summary', 'encrypted_hardware_info'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('first_seen_at', 'last_seen_at')
        })
    )
    
    def machine_id_display(self, obj):
        """显示格式化的机器ID"""
        if obj.machine_id:
            return obj.machine_id[:12] + '...'
        return '-'
    machine_id_display.short_description = '机器ID'
    
    def os_info(self, obj):
        """显示操作系统信息"""
        if obj.os_info:
            return f"{obj.os_info.get('os_version', 'Unknown')} ({obj.os_info.get('architecture', 'Unknown')})"
        return '-'
    os_info.short_description = '操作系统'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        elif hasattr(request.user, 'tenant'):
            return qs.filter(license__tenant=request.user.tenant)
        return qs.none()


@admin.register(LicenseActivation)
class LicenseActivationAdmin(admin.ModelAdmin):
    """许可证激活记录管理"""
    list_display = ['license', 'machine_binding', 'result', 'activated_at', 'ip_address', 'user_agent_display']
    list_filter = ['result', 'activated_at']
    search_fields = ['license__license_key', 'machine_binding__machine_id', 'ip_address']
    readonly_fields = ['activated_at']
    date_hierarchy = 'activated_at'
    
    fieldsets = (
        ('激活信息', {
            'fields': ('license', 'machine_binding', 'activation_code', 'result')
        }),
        ('请求信息', {
            'fields': ('ip_address', 'user_agent', 'client_version')
        }),
        ('错误信息', {
            'fields': ('error_message',)
        }),
        ('时间信息', {
            'fields': ('activated_at',)
        })
    )
    
    def user_agent_display(self, obj):
        """显示简化的User-Agent"""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return '-'
    user_agent_display.short_description = 'User Agent'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        elif hasattr(request.user, 'tenant'):
            return qs.filter(license__tenant=request.user.tenant)
        return qs.none()


@admin.register(LicenseUsageLog)
class LicenseUsageLogAdmin(admin.ModelAdmin):
    """许可证使用日志管理"""
    list_display = ['license', 'event_type', 'timestamp', 'software_version', 'ip_address', 'session_id_display']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['license__license_key', 'session_id', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('license', 'machine_binding', 'event_type', 'software_version')
        }),
        ('会话信息', {
            'fields': ('session_id', 'ip_address')
        }),
        ('系统状态', {
            'fields': ('cpu_usage', 'memory_usage')
        }),
        ('事件数据', {
            'fields': ('event_data',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('timestamp',)
        })
    )
    
    def session_id_display(self, obj):
        """显示简化的会话ID"""
        if obj.session_id:
            return obj.session_id[:8] + '...'
        return '-'
    session_id_display.short_description = '会话ID'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        elif hasattr(request.user, 'tenant'):
            return qs.filter(license__tenant=request.user.tenant)
        return qs.none()


@admin.register(TenantLicenseQuota)
class TenantLicenseQuotaAdmin(admin.ModelAdmin):
    """租户许可证配额管理"""
    list_display = ['tenant', 'application', 'max_licenses', 'current_licenses', 'usage_percentage', 'is_active']
    list_filter = ['application', 'is_active', 'created_at']
    search_fields = ['tenant__name', 'application__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('配额信息', {
            'fields': ('tenant', 'application', 'max_licenses', 'current_licenses', 'quota_start_date', 'quota_end_date', 'is_active')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def usage_percentage(self, obj):
        """显示使用百分比"""
        if obj.max_licenses > 0:
            percentage = (obj.current_licenses / obj.max_licenses) * 100
            if percentage >= 90:
                return format_html('<span style="color: red;">{:.1f}%</span>', percentage)
            elif percentage >= 70:
                return format_html('<span style="color: orange;">{:.1f}%</span>', percentage)
            else:
                return format_html('<span style="color: green;">{:.1f}%</span>', percentage)
        return '0%'
    usage_percentage.short_description = '使用率'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        elif hasattr(request.user, 'tenant'):
            return qs.filter(tenant=request.user.tenant)
        return qs.none()


@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    """安全审计日志管理"""
    list_display = ['event_type', 'severity', 'timestamp', 'ip_address', 'user_agent_display', 'tenant']
    list_filter = ['event_type', 'severity', 'timestamp', 'tenant']
    search_fields = ['ip_address', 'user_agent', 'details']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('事件信息', {
            'fields': ('event_type', 'severity', 'tenant')
        }),
        ('请求信息', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('详细信息', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('timestamp',)
        })
    )
    
    def user_agent_display(self, obj):
        """显示简化的User-Agent"""
        if obj.user_agent:
            return obj.user_agent[:30] + '...' if len(obj.user_agent) > 30 else obj.user_agent
        return '-'
    user_agent_display.short_description = 'User Agent'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        elif hasattr(request.user, 'tenant'):
            return qs.filter(tenant=request.user.tenant)
        return qs.none()


# 自定义Admin站点配置
admin.site.site_header = '许可证管理系统'
admin.site.site_title = '许可证管理'
admin.site.index_title = '许可证系统管理'
