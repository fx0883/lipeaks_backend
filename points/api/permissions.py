# points/api/permissions.py
"""
多租户积分系统的API权限控制
"""

from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied
from points.models import TenantUserProfile, TenantUserTypeTag


class TenantAwarePermission(BasePermission):
    """
    租户感知权限基类
    确保用户只能访问自己租户下的数据
    """
    
    def has_permission(self, request, view):
        """检查用户是否有访问权限"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 超级管理员跨租户放行
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        
        # 检查用户是否属于某个租户
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return True
        
        # 对于Member用户，检查是否有有效的租户关联
        if hasattr(request.user, 'tenant_user_profiles'):
            return request.user.tenant_user_profiles.exists()
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有访问特定对象的权限"""
        return self.check_tenant_access(request.user, obj)
    
    def check_tenant_access(self, user, obj):
        """检查租户访问权限"""
        if getattr(user, 'is_super_admin', False) or user.is_superuser:
            return True
        
        user_tenant = getattr(user, 'tenant', None)
        if not user_tenant:
            return False
        
        # 如果对象有tenant字段，直接比较
        if hasattr(obj, 'tenant'):
            return obj.tenant == user_tenant
        
        # 如果对象有member字段，检查member的租户
        if hasattr(obj, 'member'):
            return getattr(obj.member, 'tenant', None) == user_tenant
        
        # 如果对象有tenant_user_profile字段，检查档案的租户
        if hasattr(obj, 'tenant_user_profile'):
            return getattr(obj.tenant_user_profile, 'tenant', None) == user_tenant
        
        return False


class TenantUserProfilePermission(TenantAwarePermission):
    """租户用户档案权限"""
    
    def has_permission(self, request, view):
        """检查基本权限"""
        if not super().has_permission(request, view):
            return False
        
        # 仅超级管理员可跨租户访问所有租户的数据
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        
        # 租户管理员只能在所属租户内访问
        if getattr(request.user, 'is_admin', False) or request.user.is_staff:
            return bool(getattr(request.user, 'tenant', None))
        
        # 普通用户只能访问自己的数据
        return True
    
    def has_object_permission(self, request, view, obj):
        """检查对象级权限"""
        if not super().has_object_permission(request, view, obj):
            return False
        
        # 仅超级管理员可以跨租户访问所有对象
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        
        # 租户管理员可访问本租户对象（super已保证租户一致性）
        if getattr(request.user, 'is_admin', False) or request.user.is_staff:
            return True
        
        # 用户只能访问自己的档案
        if hasattr(request.user, 'tenant_user_profiles'):
            return obj in request.user.tenant_user_profiles.all()
        
        return getattr(obj, 'member', None) == request.user


class PointsManagementPermission(TenantAwarePermission):
    """积分管理权限"""
    
    def has_permission(self, request, view):
        """检查基本权限"""
        if not super().has_permission(request, view):
            return False
        
        # 只读操作（GET）：所有认证用户都可以查看自己的积分
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # 写操作：需要特殊权限
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # 仅超级管理员可以跨租户进行所有操作
            if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
                return True
            
            # 租户管理员在本租户内可操作
            user_tenant = getattr(request.user, 'tenant', None)
            if user_tenant and (getattr(request.user, 'is_admin', False) or request.user.is_staff):
                return True
            
            # 检查普通用户是否有积分管理权限
            if user_tenant:
                from points.services.permission_service import TenantAwarePermissionService
                perms = TenantAwarePermissionService.get_effective_permissions(
                    request.user, user_tenant
                )
                return perms.get('can_manage_points', False)
        
        return False


class VipManagementPermission(TenantAwarePermission):
    """VIP标签管理权限"""
    
    def has_permission(self, request, view):
        """检查基本权限"""
        if not super().has_permission(request, view):
            return False
        
        # 只读操作：用户可以查看自己的VIP状态
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # 写操作：需要管理员权限或特殊权限
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # 仅超级管理员可以跨租户进行所有操作
            if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
                return True
            
            # 租户管理员在本租户内可操作
            user_tenant = getattr(request.user, 'tenant', None)
            if user_tenant and (getattr(request.user, 'is_admin', False) or request.user.is_staff):
                return True
            
            # 检查普通用户是否有VIP管理权限
            if user_tenant:
                from points.services.permission_service import TenantAwarePermissionService
                perms = TenantAwarePermissionService.get_effective_permissions(
                    request.user, user_tenant
                )
                return perms.get('can_manage_vip_tags', False)
        
        return False


class LicenseAssignmentPermission(TenantAwarePermission):
    """许可证分配权限"""
    
    def has_permission(self, request, view):
        """检查基本权限"""
        if not super().has_permission(request, view):
            return False
        
        # 只读操作：用户可以查看自己的许可证分配
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # 写操作：需要许可证管理权限
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # 仅超级管理员可以跨租户进行所有操作
            if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
                return True
            
            # 租户管理员在本租户内可操作
            user_tenant = getattr(request.user, 'tenant', None)
            if user_tenant and (getattr(request.user, 'is_admin', False) or request.user.is_staff):
                return True
            
            # 检查普通用户是否有许可证管理权限
            if user_tenant:
                from points.services.permission_service import TenantAwarePermissionService
                perms = TenantAwarePermissionService.get_effective_permissions(
                    request.user, user_tenant
                )
                return perms.get('can_manage_licenses', False)
        
        return False


class SelfOrAdminPermission(BasePermission):
    """
    自己或管理员权限
    超级管理员可跨租户访问所有对象，租户管理员仅限本租户，用户只能访问自己的数据
    """
    
    def has_permission(self, request, view):
        """检查基本权限"""
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        """检查对象级权限"""
        # 超级管理员可以访问所有对象
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        
        # 租户管理员只能访问本租户对象
        if getattr(request.user, 'is_admin', False) or request.user.is_staff:
            user_tenant = getattr(request.user, 'tenant', None)
            if user_tenant:
                if hasattr(obj, 'tenant') and obj.tenant == user_tenant:
                    return True
                if hasattr(obj, 'member') and getattr(obj.member, 'tenant', None) == user_tenant:
                    return True
                if hasattr(obj, 'tenant_user_profile') and getattr(obj.tenant_user_profile, 'tenant', None) == user_tenant:
                    return True
            return False
        
        # 用户只能访问自己相关的对象
        if hasattr(obj, 'member'):
            return obj.member == request.user
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # 如果对象就是用户本身
        if obj == request.user:
            return True
        
        return False


class ReadOnlyOrAdminPermission(BasePermission):
    """
    只读或管理员权限
    普通用户只能读取，超级管理员可跨租户操作，租户管理员可在本租户内操作
    """
    
    def has_permission(self, request, view):
        """检查基本权限"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 只读操作：所有认证用户都可以
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # 写操作：超级管理员或本租户管理员
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        if getattr(request.user, 'is_admin', False) or request.user.is_staff:
            return getattr(request.user, 'tenant', None) is not None
        return False


class PointsOperationPermission(BasePermission):
    """
    积分操作权限
    根据操作类型检查不同的权限
    """
    
    def has_permission(self, request, view):
        """检查基本权限"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        action = getattr(view, 'action', None)
        
        # 查询操作：所有认证用户
        if action in ['list', 'retrieve', 'summary']:
            return True
        
        # 积分操作：需要特殊权限
        if action in ['earn_points', 'spend_points', 'adjust_points']:
            # 仅超级管理员可以跨租户进行所有操作
            if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
                return True
            
            # 租户管理员在本租户内可以进行操作
            user_tenant = getattr(request.user, 'tenant', None)
            if user_tenant and (getattr(request.user, 'is_admin', False) or request.user.is_staff):
                return True
            
            # 检查普通用户的积分操作权限
            if user_tenant:
                from points.services.permission_service import TenantAwarePermissionService
                perms = TenantAwarePermissionService.get_effective_permissions(
                    request.user, user_tenant
                )
                
                # 根据操作类型检查权限
                if action == 'earn_points':
                    return perms.get('can_earn_points', True)  # 默认允许获得积分
                elif action == 'spend_points':
                    return perms.get('can_spend_points', True)  # 默认允许消费积分
                elif action == 'adjust_points':
                    return perms.get('can_adjust_points', False)  # 默认不允许调整积分
        
        return False


def get_user_tenant(user):
    """获取用户的租户"""
    if hasattr(user, 'tenant') and user.tenant:
        return user.tenant
    
    # 对于Member用户，获取第一个关联的租户
    if hasattr(user, 'tenant_user_profiles'):
        profile = user.tenant_user_profiles.first()
        if profile:
            return profile.tenant
    
    return None


def ensure_tenant_isolation(request, queryset):
    """
    确保查询集只包含current用户租户的数据
    """
    # 仅超级管理员可以跨租户查看所有租户的数据
    if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
        return queryset
    
    user_tenant = get_user_tenant(request.user)
    if not user_tenant:
        return queryset.none()
    
    # 普通用户或租户管理员只能查看自己租户的数据
    if hasattr(queryset.model, 'tenant'):
        return queryset.filter(tenant=user_tenant)
    
    # 如果模型通过其他关系关联到租户
    if hasattr(queryset.model, 'member'):
        return queryset.filter(member__tenant=user_tenant)
    
    if hasattr(queryset.model, 'tenant_user_profile'):
        return queryset.filter(tenant_user_profile__tenant=user_tenant)
    
    return queryset
