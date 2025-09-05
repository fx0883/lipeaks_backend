"""
权限控制相关功能
"""
import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)

class IsSuperAdminUser(permissions.BasePermission):
    """
    检查用户是否是超级管理员
    """
    def has_permission(self, request, view):
        """
        检查用户是否是超级管理员
        
        Args:
            request: HTTP请求对象
            view: 视图对象
        
        Returns:
            布尔值，指示用户是否具有权限
        """
        is_super_admin = bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_super_admin
        )
        
        if not is_super_admin:
            logger.warning(
                f"用户 {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                f"尝试访问需要超级管理员权限的资源 {request.path}"
            )
        
        return is_super_admin


class IsAdminUser(permissions.BasePermission):
    """
    检查用户是否是管理员（包括超级管理员和租户管理员）
    """
    def has_permission(self, request, view):
        """
        检查用户是否是管理员
        
        Args:
            request: HTTP请求对象
            view: 视图对象
        
        Returns:
            布尔值，指示用户是否具有权限
        """
        is_admin = bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_super_admin)
        )
        
        if not is_admin:
            logger.warning(
                f"用户 {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                f"尝试访问需要管理员权限的资源 {request.path}"
            )
        
        return is_admin


# 与视图文件中使用的类名保持一致
class IsSuperAdmin(IsSuperAdminUser):
    """
    检查用户是否是超级管理员（别名，保持与视图代码一致）
    """
    pass


# 与视图文件中使用的类名保持一致
class IsAdmin(IsAdminUser):
    """
    检查用户是否是管理员（别名，保持与视图代码一致）
    """
    def has_permission(self, request, view):
        """
        检查用户是否是管理员
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            
        Returns:
            布尔值，指示用户是否具有权限
        """
        user = request.user
        path = request.path
        
        # 增强日志以便诊断问题
        is_authenticated = bool(user and user.is_authenticated)
        is_admin = bool(is_authenticated and user.is_admin)
        is_super_admin = bool(is_authenticated and user.is_super_admin)
        has_permission = bool(is_authenticated and (is_admin or is_super_admin))
        
        logger.info(f"权限检查 [IsAdmin] - 路径: {path}")
        logger.info(f"  用户: {user.username if is_authenticated else 'Anonymous'}")
        logger.info(f"  已认证: {is_authenticated}")
        logger.info(f"  是管理员: {is_admin}")
        logger.info(f"  是超级管理员: {is_super_admin}")
        logger.info(f"  权限检查结果: {'通过' if has_permission else '拒绝'}")
        
        if not has_permission:
            logger.warning(
                f"用户 {user.username if is_authenticated else 'Anonymous'} "
                f"尝试访问需要管理员权限的资源 {path}，但权限检查未通过"
            )
        
        return has_permission


class IsTenantAdmin(permissions.BasePermission):
    """
    检查用户是否是租户管理员
    """
    def has_permission(self, request, view):
        """
        检查用户是否是租户管理员
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            
        Returns:
            布尔值，指示用户是否具有权限
        """
        user = request.user
        path = request.path
        
        # 检查用户是否是租户管理员
        is_authenticated = bool(user and user.is_authenticated)
        is_tenant_admin = bool(is_authenticated and user.is_admin and not user.is_super_admin)
        
        logger.info(f"权限检查 [IsTenantAdmin] - 路径: {path}")
        logger.info(f"  用户: {user.username if is_authenticated else 'Anonymous'}")
        logger.info(f"  已认证: {is_authenticated}")
        logger.info(f"  是租户管理员: {is_tenant_admin}")
        logger.info(f"  权限检查结果: {'通过' if is_tenant_admin else '拒绝'}")
        
        if not is_tenant_admin:
            logger.warning(
                f"用户 {user.username if is_authenticated else 'Anonymous'} "
                f"尝试访问需要租户管理员权限的资源 {path}，但权限检查未通过"
            )
        
        return is_tenant_admin


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    对象级权限，只允许对象的所有者或管理员访问
    """
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否是对象所有者或管理员
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            obj: 被访问的对象
        
        Returns:
            布尔值，指示用户是否具有权限
        """
        # 超级管理员始终有权限
        if request.user and request.user.is_super_admin:
            return True
        
        # 租户管理员可以访问其租户内的所有对象
        if (
            request.user and 
            request.user.is_admin and 
            hasattr(obj, 'tenant') and 
            obj.tenant == request.user.tenant
        ):
            return True
        
        # 检查对象是否属于当前用户
        is_owner = False
        if hasattr(obj, 'user_id'):
            is_owner = obj.user_id == request.user.id
        elif hasattr(obj, 'user'):
            is_owner = obj.user == request.user
        elif hasattr(obj, 'created_by'):
            is_owner = obj.created_by == request.user
        
        if not is_owner:
            logger.warning(
                f"用户 {request.user.username} 尝试访问不属于他的对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}"
            )
        
        return is_owner


class IsSameTenantUser(permissions.BasePermission):
    """
    检查用户是否与被访问的对象属于同一租户
    """
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否与被访问的对象属于同一租户
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            obj: 被访问的对象
        
        Returns:
            布尔值，指示用户是否具有权限
        """
        # 超级管理员始终有权限
        if request.user and request.user.is_super_admin:
            return True
        
        # 检查对象和用户是否属于同一租户
        if not request.user.tenant:
            return False
        
        same_tenant = False
        if hasattr(obj, 'tenant'):
            same_tenant = obj.tenant == request.user.tenant
        elif hasattr(obj, 'user') and hasattr(obj.user, 'tenant'):
            same_tenant = obj.user.tenant == request.user.tenant
        
        if not same_tenant:
            logger.warning(
                f"用户 {request.user.username} 尝试跨租户访问对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}"
            )
        
        return same_tenant


class ReadOnly(permissions.BasePermission):
    """
    只允许GET, HEAD, OPTIONS请求
    """
    def has_permission(self, request, view):
        """
        检查是否是只读请求
        
        Args:
            request: HTTP请求对象
            view: 视图对象
        
        Returns:
            布尔值，指示用户是否具有权限
        """
        return request.method in permissions.SAFE_METHODS


class IsSuperAdminOrTenantAdmin(permissions.BasePermission):
    """
    检查用户是否是超级管理员或租户管理员
    """
    def has_permission(self, request, view):
        """
        检查用户是否是超级管理员或租户管理员
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            
        Returns:
            布尔值，指示用户是否具有权限
        """
        user = request.user
        path = request.path
        
        # 检查用户是否是管理员（包括超级管理员和租户管理员）
        is_authenticated = bool(user and user.is_authenticated)
        is_admin = bool(is_authenticated and (user.is_super_admin or user.is_admin))
        
        logger.info(f"权限检查 [IsSuperAdminOrTenantAdmin] - 路径: {path}")
        logger.info(f"  用户: {user.username if is_authenticated else 'Anonymous'}")
        logger.info(f"  已认证: {is_authenticated}")
        logger.info(f"  是超级管理员: {getattr(user, 'is_super_admin', False) if is_authenticated else False}")
        logger.info(f"  是管理员: {getattr(user, 'is_admin', False) if is_authenticated else False}")
        logger.info(f"  权限检查结果: {'通过' if is_admin else '拒绝'}")
        
        if not is_admin:
            logger.warning(
                f"用户 {user.username if is_authenticated else 'Anonymous'} "
                f"尝试访问需要管理员权限的资源 {path}，但权限检查未通过"
            )
        
        return is_admin


class TenantApiPermission(permissions.BasePermission):
    """
    专门用于租户相关API的权限控制
    确保只有超级管理员可以访问租户管理API
    """
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问租户相关API
        
        Args:
            request: HTTP请求对象
            view: 视图对象
        
        Returns:
            布尔值，指示用户是否具有权限
        """
        # 添加详细日志
        logger.warning(f"TenantApiPermission.has_permission被调用: 用户={request.user}, 已认证={request.user.is_authenticated}, 路径={request.path}")
        logger.warning(f"认证信息: {request.auth}")
        logger.warning(f"请求头: {request.headers}")
        
        # 检查Authorization头部
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        logger.warning(f"Authorization头: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("请求缺少有效的Bearer token")
            # 返回False表示权限被拒绝
            return False
            
        # 验证用户是否是超级管理员
        is_super_admin = bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_super_admin
        )
        
        logger.warning(f"用户超级管理员状态: {getattr(request.user, 'is_super_admin', False)}")
        logger.warning(f"权限检查结果: {is_super_admin}")
        
        if not is_super_admin:
            logger.warning(
                f"用户 {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                f"尝试访问租户API {request.path}，但不是超级管理员"
            )
            
        return is_super_admin
    
    def has_object_permission(self, request, view, obj):
        """
        对象级权限检查
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            obj: 被访问的对象
        
        Returns:
            布尔值，指示用户是否具有对象级权限
        """
        # 对象级别权限同样只允许超级管理员
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_super_admin
        ) 