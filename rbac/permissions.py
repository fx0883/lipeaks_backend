"""
RBAC权限检查相关功能
"""
import logging
import functools
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions
from rest_framework import exceptions

from .models import UserRole, Permission

logger = logging.getLogger(__name__)

# 缓存过期时间(秒)
RBAC_CACHE_TIMEOUT = 60 * 10  # 10分钟


def get_user_permissions(user):
    """
    获取用户所有权限代码
    
    Args:
        user: 用户对象
    
    Returns:
        set: 权限代码集合
    """
    if not user or not user.is_authenticated:
        return set()
        
    # 超级管理员拥有所有权限
    if hasattr(user, 'is_super_admin') and user.is_super_admin:
        # 返回所有权限代码
        return set(Permission.objects.all().values_list('code', flat=True))
    
    # 从缓存获取用户权限
    if hasattr(user, 'id'):
        user_type = 'user' if hasattr(user, 'is_admin') else 'member'
        cache_key = f"rbac_user_permissions_{user_type}_{user.id}"
        cached_permissions = cache.get(cache_key)
        
        if cached_permissions is not None:
            logger.debug(f"从缓存获取用户 {user.username} 的权限")
            return cached_permissions
    
    # 查询用户角色
    current_date = timezone.now().date()
    user_type = 'user' if hasattr(user, 'is_admin') else 'member'
    
    user_roles = UserRole.objects.filter(
        user_type=user_type,
        user_id=user.id,
        is_active=True
    ).filter(
        # 筛选有效期内的角色
        (
            # 开始日期和结束日期都为空，表示永久有效
            (models.Q(start_date__isnull=True) & models.Q(end_date__isnull=True)) |
            # 只有开始日期，表示从开始日期起永久有效
            (models.Q(start_date__lte=current_date) & models.Q(end_date__isnull=True)) |
            # 只有结束日期，表示直到结束日期止有效
            (models.Q(start_date__isnull=True) & models.Q(end_date__gte=current_date)) |
            # 开始日期和结束日期都有，表示在日期范围内有效
            (models.Q(start_date__lte=current_date) & models.Q(end_date__gte=current_date))
        )
    )
    
    # 获取角色关联的权限
    permissions = set()
    for user_role in user_roles:
        role_permissions = user_role.role.permissions.values_list('code', flat=True)
        permissions.update(role_permissions)
    
    # 将权限集合缓存
    if hasattr(user, 'id'):
        cache_key = f"rbac_user_permissions_{user_type}_{user.id}"
        cache.set(cache_key, permissions, RBAC_CACHE_TIMEOUT)
        
    return permissions


def has_permission(user, permission_code):
    """
    检查用户是否拥有指定权限
    
    Args:
        user: 用户对象
        permission_code: 权限代码
    
    Returns:
        bool: 是否拥有权限
    """
    if not user or not user.is_authenticated:
        return False
        
    # 超级管理员拥有所有权限
    if hasattr(user, 'is_super_admin') and user.is_super_admin:
        return True
        
    # 获取用户权限集合
    permissions = get_user_permissions(user)
    return permission_code in permissions


def invalidate_permissions_cache(user):
    """
    使指定用户的权限缓存失效
    
    Args:
        user: 用户对象
    """
    if not hasattr(user, 'id'):
        return
        
    user_type = 'user' if hasattr(user, 'is_admin') else 'member'
    cache_key = f"rbac_user_permissions_{user_type}_{user.id}"
    cache.delete(cache_key)
    logger.debug(f"已清除用户 {user.username} 的权限缓存")


class HasRBACPermission(permissions.BasePermission):
    """
    RBAC权限检查类
    """
    def __init__(self, required_permission):
        self.required_permission = required_permission
        
    def has_permission(self, request, view):
        """
        检查用户是否有指定权限
        """
        user = request.user
        return has_permission(user, self.required_permission)


def rbac_permission_required(permission_code):
    """
    权限检查装饰器，用于基于函数的视图
    
    Args:
        permission_code: 权限代码
    
    Returns:
        装饰器函数
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if has_permission(request.user, permission_code):
                return view_func(request, *args, **kwargs)
            else:
                logger.warning(
                    f"用户 {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                    f"尝试访问需要 {permission_code} 权限的视图，但权限检查未通过"
                )
                raise exceptions.PermissionDenied(f"Required permission: {permission_code} ")
        return wrapped_view
    return decorator


class RBACPermissionRequired(permissions.BasePermission):
    """
    RBAC权限检查类，用于基于类的视图
    
    Example:
        class UserViewSet(viewsets.ModelViewSet):
            permission_classes = [RBACPermissionRequired]
            rbac_permissions = {
                'list': 'user:view',
                'retrieve': 'user:view',
                'create': 'user:create',
                'update': 'user:edit',
                'partial_update': 'user:edit',
                'destroy': 'user:delete'
            }
    """
    def has_permission(self, request, view):
        """
        检查用户是否有指定权限
        """
        # 获取视图方法对应的权限代码
        rbac_permissions = getattr(view, 'rbac_permissions', {})
        action = getattr(view, 'action', request.method.lower())
        
        # 如果没有定义对应动作的权限，默认使用HTTP方法作为键
        if action not in rbac_permissions:
            action = request.method.lower()
            
        permission_code = rbac_permissions.get(action)
        
        # 如果没有定义权限，允许访问
        if not permission_code:
            return True
            
        # 检查权限
        has_perm = has_permission(request.user, permission_code)
        
        if not has_perm:
            logger.warning(
                f"用户 {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                f"尝试访问需要 {permission_code} 权限的操作 {action}，但权限检查未通过"
            )
            
        return has_perm 