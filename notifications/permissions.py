"""
通知系统权限控制

权限规则：
- GET请求允许匿名访问（需要租户ID，通过 X-Tenant-ID header）
- POST/PATCH/DELETE 需要认证 + 租户管理员权限
"""
import logging
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def is_tenant_admin(user):
    """
    检查用户是否是租户管理员或超级管理员
    
    Args:
        user: 用户对象
        
    Returns:
        bool: 是否是管理员
    """
    if not user or not user.is_authenticated:
        return False
    
    # 超级管理员
    if getattr(user, 'is_super_admin', False):
        return True
    
    # 租户管理员
    if getattr(user, 'is_admin', False):
        return True
    
    return False


class NotificationPermission(permissions.BasePermission):
    """
    通知系统权限类
    
    - GET请求允许匿名访问（租户ID通过 X-Tenant-ID header 获取）
    - POST 请求需要认证（成员和管理员都可以）
    - PATCH/DELETE 需要认证 + 租户管理员权限
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问视图
        """
        path = request.path
        
        # GET请求允许匿名访问
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"[NotificationPermission] GET请求允许访问: {path}")
            return True
        
        # 非GET请求需要认证
        user = request.user
        if not user or not user.is_authenticated:
            logger.warning(f"[NotificationPermission] 未认证用户尝试访问: {path}")
            return False
        
        # POST请求（如标记已读）允许认证用户访问
        if request.method == 'POST':
            # 检查是否是特定的成员操作
            if any(action in path for action in ['/read', '/read-all']):
                logger.info(f"[NotificationPermission] 认证用户 {user.username} 执行读操作: {path}")
                return True
        
        # PATCH/DELETE和其他POST操作需要管理员权限
        if not is_tenant_admin(user):
            logger.warning(
                f"[NotificationPermission] 用户 {user.username} 尝试访问需要管理员权限的资源: {path}"
            )
            return False
        
        logger.info(f"[NotificationPermission] 管理员 {user.username} 访问: {path}")
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作特定对象
        """
        # GET请求允许访问
        if request.method in permissions.SAFE_METHODS:
            return True
        
        user = request.user
        
        # 超级管理员可以操作任何对象
        if getattr(user, 'is_super_admin', False):
            return True
        
        # 租户管理员只能操作自己租户的对象
        if hasattr(obj, 'tenant') and hasattr(user, 'tenant'):
            if obj.tenant != user.tenant:
                logger.warning(
                    f"[NotificationPermission] 用户 {user.username} 尝试操作不属于其租户的对象"
                )
                return False
        
        return True


class MemberNotificationPermission(permissions.BasePermission):
    """
    成员端通知权限类
    
    - GET请求允许匿名访问（需要member_id参数）
    - POST请求需要 Member 用户认证
    - 只能操作自己的通知状态
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问视图
        """
        # GET请求允许匿名访问
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"[MemberNotificationPermission] GET请求允许访问: {request.path}")
            return True
        
        # POST请求需要认证
        user = request.user
        
        if not user or not user.is_authenticated:
            logger.warning(f"[MemberNotificationPermission] 未认证用户尝试访问成员通知")
            return False
        
        # 检查是否是 Member 用户
        from users.models import Member
        try:
            if isinstance(user, Member):
                return True
            # 尝试查询是否是 Member
            if Member.objects.filter(id=user.id).exists():
                return True
        except Exception:
            pass
        
        logger.warning(f"[MemberNotificationPermission] 非Member用户 {user.username} 尝试访问成员通知")
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        检查成员是否有权限操作特定通知接收记录
        """
        user = request.user
        
        # 检查是否是该通知的接收者
        if hasattr(obj, 'member') and obj.member_id == user.id:
            return True
        
        # 检查是否是该通知的接收者（通过 NotificationRecipient 查询）
        if hasattr(obj, 'recipients'):
            from .models import NotificationRecipient
            if NotificationRecipient.objects.filter(
                notification=obj,
                member_id=user.id
            ).exists():
                return True
        
        logger.warning(
            f"[MemberNotificationPermission] 成员 {user.username} 尝试访问不属于他的通知"
        )
        return False
