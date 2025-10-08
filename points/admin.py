"""
多租户积分系统 Django Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TenantUserProfile,
    TenantUserPoints,
    UserLevel,
    UserTypeTag,
    TenantUserTypeTag
)


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    """用户等级管理"""
    list_display = ['level_name', 'level_code', 'level_order', 'min_points', 'max_points', 
                   'colored_badge', 'is_active', 'is_default']
    list_filter = ['is_active', 'is_default', 'created_at']
    search_fields = ['level_name', 'level_code', 'level_description']
    ordering = ['level_order']
    readonly_fields = ['created_at', 'updated_at']
    
    def colored_badge(self, obj):
        """显示彩色等级徽章"""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.level_color,
            obj.level_name
        )
    colored_badge.short_description = '等级徽章'


@admin.register(UserTypeTag)
class UserTypeTagAdmin(admin.ModelAdmin):
    """用户标签管理"""
    list_display = ['tag_name', 'tag_code', 'tag_type', 'tag_level', 'colored_badge', 
                   'requires_payment', 'is_active', 'is_assignable']
    list_filter = ['tag_type', 'requires_payment', 'is_active', 'is_assignable', 'created_at']
    search_fields = ['tag_name', 'tag_code', 'tag_description']
    ordering = ['-tag_level', 'tag_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def colored_badge(self, obj):
        """显示彩色标签徽章"""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.tag_color,
            obj.tag_name
        )
    colored_badge.short_description = '标签徽章'


@admin.register(TenantUserProfile)
class TenantUserProfileAdmin(admin.ModelAdmin):
    """租户用户档案管理"""
    list_display = ['profile_info', 'current_level_badge', 'total_points', 'available_points', 
                   'points_multiplier', 'is_points_enabled', 'last_points_update']
    list_filter = ['current_level', 'is_points_enabled', 'tenant', 'created_at']
    search_fields = ['member__username', 'member__email', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at', 'last_points_update', 'last_level_check']
    raw_id_fields = ['member', 'tenant', 'current_level']
    
    def profile_info(self, obj):
        """显示档案基础信息"""
        return f"{obj.member.username} @ {obj.tenant.name}"
    profile_info.short_description = '用户@租户'
    
    def current_level_badge(self, obj):
        """显示当前等级徽章"""
        if obj.current_level:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
                obj.current_level.level_color,
                obj.current_level.level_name
            )
        return '-'
    current_level_badge.short_description = '当前等级'


@admin.register(TenantUserPoints)
class TenantUserPointsAdmin(admin.ModelAdmin):
    """积分记录管理"""
    list_display = ['record_info', 'point_type', 'category', 'points_display', 
                   'balance_after', 'status', 'earned_at']
    list_filter = ['point_type', 'category', 'status', 'source_type', 'tenant', 'earned_at']
    search_fields = ['member__username', 'tenant__name', 'operation_reason']
    readonly_fields = ['earned_at', 'expired_at', 'balance_before', 'balance_after', 
                      'tenant_multiplier', 'original_points']
    raw_id_fields = ['tenant_user_profile', 'tenant', 'member']
    date_hierarchy = 'earned_at'
    
    def record_info(self, obj):
        """显示记录基础信息"""
        return f"{obj.member.username} @ {obj.tenant.name}"
    record_info.short_description = '用户@租户'
    
    def points_display(self, obj):
        """显示积分变动"""
        if obj.points > 0:
            return format_html('<span style="color: green;">+{}</span>', obj.points)
        else:
            return format_html('<span style="color: red;">{}</span>', obj.points)
    points_display.short_description = '积分变动'
    
    def has_add_permission(self, request):
        return False  # 积分记录通过业务逻辑创建


@admin.register(TenantUserTypeTag)
class TenantUserTypeTagAdmin(admin.ModelAdmin):
    """租户用户标签关联管理"""
    list_display = ['user_tag_info', 'tag_badge', 'status', 'granted_at', 'expires_at', 'usage_count']
    list_filter = ['tag__tag_type', 'status', 'grant_method', 'auto_renewal', 'tenant', 'granted_at']
    search_fields = ['member__username', 'tenant__name', 'tag__tag_name']
    readonly_fields = ['granted_at', 'last_used_at', 'usage_count', 'renewal_count']
    raw_id_fields = ['tenant_user_profile', 'tag', 'tenant', 'member']
    date_hierarchy = 'granted_at'
    
    def user_tag_info(self, obj):
        """显示用户标签基础信息"""
        return f"{obj.member.username} @ {obj.tenant.name}"
    user_tag_info.short_description = '用户@租户'
    
    def tag_badge(self, obj):
        """显示标签徽章"""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.tag.tag_color,
            obj.tag.tag_name
        )
    tag_badge.short_description = '标签'


# 注册许可证分配管理
from licenses.models import LicenseAssignment

@admin.register(LicenseAssignment)
class LicenseAssignmentAdmin(admin.ModelAdmin):
    """许可证分配管理"""
    list_display = ['assignment_info', 'license_key_short', 'status', 'assignment_type', 
                   'can_activate', 'assigned_at', 'usage_count']
    list_filter = ['status', 'assignment_type', 'can_activate', 'tenant', 'assigned_at']
    search_fields = ['member__username', 'license__license_key', 'tenant__name']
    readonly_fields = ['assigned_at', 'activated_at', 'last_used_at', 'revoked_at', 
                      'usage_count', 'last_heartbeat']
    raw_id_fields = ['member', 'license', 'tenant', 'assigned_by', 'revoked_by']
    
    def assignment_info(self, obj):
        """显示分配基础信息"""
        return obj.member.username
    assignment_info.short_description = '分配用户'
    
    def license_key_short(self, obj):
        """显示许可证密钥简短版本"""
        if obj.license and obj.license.license_key:
            key = obj.license.license_key
            return f"{key[:8]}***{key[-4:]}" if len(key) > 12 else key
        return '-'
    license_key_short.short_description = '许可证密钥'