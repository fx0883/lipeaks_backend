"""
RBAC系统管理员界面配置
"""
import logging
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django import forms
from django.db.models import Count, Q

from .models import Permission, Role, RolePermission, UserRole

logger = logging.getLogger(__name__)

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """权限管理"""
    list_display = ('id', 'name', 'code', 'category', 'description_short', 'is_system', 'created_at')
    list_filter = ('is_system', 'category')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('category', 'code')
    list_per_page = 20
    
    fieldsets = (
        (_("基本信息"), {
            'fields': ('code', 'name', 'category', 'description', 'is_system')
        }),
        (_("时间信息"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        """截取描述展示"""
        if obj.description and len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description
    description_short.short_description = _("描述")
    
    def save_model(self, request, obj, form, change):
        """保存模型时记录操作日志"""
        if change:
            logger.info(f"管理员 {request.user.username} 修改权限: {obj.code}")
        else:
            logger.info(f"管理员 {request.user.username} 创建权限: {obj.code}")
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """删除模型时记录操作日志"""
        if obj.is_system:
            logger.warning(f"管理员 {request.user.username} 尝试删除系统权限: {obj.code}，已阻止")
            return
        logger.info(f"管理员 {request.user.username} 删除权限: {obj.code}")
        super().delete_model(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """检查是否有删除权限"""
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


class RolePermissionInline(admin.TabularInline):
    """角色权限内联管理"""
    model = RolePermission
    extra = 1
    autocomplete_fields = ['permission']
    verbose_name = _("角色权限")
    verbose_name_plural = _("角色权限")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理"""
    list_display = ('id', 'name', 'code', 'tenant_name', 'permission_count', 'is_system', 'created_at')
    list_filter = ('is_system', 'tenant')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20
    inlines = [RolePermissionInline]
    
    fieldsets = (
        (_("基本信息"), {
            'fields': ('name', 'code', 'description', 'tenant', 'is_system')
        }),
        (_("时间信息"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        """显示租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return _("系统角色")
    tenant_name.short_description = _("所属租户")
    
    def permission_count(self, obj):
        """显示权限数量"""
        return obj.permissions.count()
    permission_count.short_description = _("权限数量")
    
    def get_queryset(self, request):
        """优化查询，预加载权限数量"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            permission_count=Count('permissions')
        )
        return queryset
    
    def save_model(self, request, obj, form, change):
        """保存模型时记录操作日志"""
        if change:
            logger.info(f"管理员 {request.user.username} 修改角色: {obj.name}")
        else:
            tenant_name = obj.tenant.name if obj.tenant else "系统"
            logger.info(f"管理员 {request.user.username} 创建角色: {obj.name} (租户: {tenant_name})")
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """删除模型时记录操作日志"""
        if obj.is_system:
            logger.warning(f"管理员 {request.user.username} 尝试删除系统角色: {obj.name}，已阻止")
            return
        logger.info(f"管理员 {request.user.username} 删除角色: {obj.name}")
        super().delete_model(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """检查是否有删除权限"""
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """用户角色关联管理"""
    list_display = ('id', 'user_info', 'role_name', 'is_active', 'time_range', 'created_at')
    list_filter = ('user_type', 'is_active', 'role__tenant')
    search_fields = ('user_id', 'role__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20
    
    fieldsets = (
        (_("基本信息"), {
            'fields': ('user_type', 'user_id', 'role', 'is_active')
        }),
        (_("生效时间"), {
            'fields': ('start_date', 'end_date'),
        }),
        (_("时间信息"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_info(self, obj):
        """显示用户信息"""
        user = obj.user
        if user:
            user_info = f"{user.username}"
            if hasattr(user, 'nick_name') and user.nick_name:
                user_info += f" ({user.nick_name})"
            return user_info
        return f"{obj.get_user_type_display()} ID:{obj.user_id} (用户不存在)"
    user_info.short_description = _("用户")
    
    def role_name(self, obj):
        """显示角色信息"""
        tenant_name = obj.role.tenant.name if obj.role.tenant else "系统"
        return f"{obj.role.name} ({tenant_name})"
    role_name.short_description = _("角色")
    
    def time_range(self, obj):
        """显示生效时间范围"""
        if obj.start_date and obj.end_date:
            return f"{obj.start_date} ~ {obj.end_date}"
        elif obj.start_date:
            return f"{obj.start_date} 起"
        elif obj.end_date:
            return f"截至 {obj.end_date}"
        return _("永久")
    time_range.short_description = _("生效时间")
    
    def save_model(self, request, obj, form, change):
        """保存模型时记录操作日志"""
        if change:
            logger.info(f"管理员 {request.user.username} 修改用户角色关联: {obj}")
        else:
            logger.info(f"管理员 {request.user.username} 创建用户角色关联: {obj}")
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """删除模型时记录操作日志"""
        logger.info(f"管理员 {request.user.username} 删除用户角色关联: {obj}")
        super().delete_model(request, obj)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """角色权限关联管理"""
    list_display = ('id', 'role_info', 'permission_info', 'created_at')
    list_filter = ('role__tenant', 'permission__category')
    search_fields = ('role__name', 'permission__name', 'permission__code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    
    fieldsets = (
        (_("关联信息"), {
            'fields': ('role', 'permission')
        }),
        (_("时间信息"), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def role_info(self, obj):
        """显示角色信息"""
        tenant_name = obj.role.tenant.name if obj.role.tenant else "系统"
        return f"{obj.role.name} ({tenant_name})"
    role_info.short_description = _("角色")
    
    def permission_info(self, obj):
        """显示权限信息"""
        return f"{obj.permission.name} ({obj.permission.code})"
    permission_info.short_description = _("权限")
    
    def save_model(self, request, obj, form, change):
        """保存模型时记录操作日志"""
        if change:
            logger.info(f"管理员 {request.user.username} 修改角色权限关联: {obj}")
        else:
            logger.info(f"管理员 {request.user.username} 创建角色权限关联: {obj}")
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """删除模型时记录操作日志"""
        logger.info(f"管理员 {request.user.username} 删除角色权限关联: {obj}")
        super().delete_model(request, obj)
