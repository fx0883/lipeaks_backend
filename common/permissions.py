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
        
        # 检查对象是否属于current用户
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


class IsMemberUser(permissions.BasePermission):
    """
    检查用户是否是Member用户（普通成员）
    """
    def has_permission(self, request, view):
        """
        检查用户是否是Member用户
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            
        Returns:
            布尔值，指示用户是否具有权限
        """
        user = request.user
        path = request.path
        
        # 检查用户是否已认证
        is_authenticated = bool(user and user.is_authenticated)
        
        # 检查用户是否是Member类型
        is_member_user = False
        if is_authenticated:
            # 通过检查用户类型来判断是否是Member
            # Member用户的特征：不是管理员，且属于Member表
            try:
                from users.models import Member
                is_member_user = (
                    isinstance(user, Member) or 
                    Member.objects.filter(id=user.id).exists()
                ) and not getattr(user, 'is_admin', False) and not getattr(user, 'is_super_admin', False)
            except ImportError:
                # 如果Member模型不存在，回退到基本检查
                is_member_user = (
                    not getattr(user, 'is_admin', False) and 
                    not getattr(user, 'is_super_admin', False) and
                    not getattr(user, 'is_staff', False)
                )
        
        # 检查用户状态
        is_active = bool(is_member_user and user.is_active and getattr(user, 'status', 'active') == 'active')
        
        # 检查租户状态
        has_valid_tenant = False
        if is_active and hasattr(user, 'tenant') and user.tenant:
            has_valid_tenant = user.tenant.is_active
        
        # 最终权限检查结果
        has_permission = is_authenticated and is_member_user and is_active and has_valid_tenant
        
        logger.info(f"权限检查 [IsMemberUser] - 路径: {path}")
        logger.info(f"  用户: {user.username if is_authenticated else 'Anonymous'}")
        logger.info(f"  已认证: {is_authenticated}")
        logger.info(f"  是Member用户: {is_member_user}")
        logger.info(f"  用户状态活跃: {is_active}")
        logger.info(f"  租户有效: {has_valid_tenant}")
        logger.info(f"  权限检查结果: {'通过' if has_permission else '拒绝'}")
        
        if not has_permission:
            if not is_authenticated:
                reason = "User is not authenticated"
            elif not is_member_user:
                reason = "不是Member用户"
            elif not is_active:
                reason = "用户状态非活跃"
            elif not has_valid_tenant:
                reason = "租户无效"
            else:
                reason = "未知原因"
            
            logger.warning(
                f"用户 {user.username if is_authenticated else 'Anonymous'} "
                f"尝试访问需要Member权限的资源 {path}，被拒绝，原因: {reason}"
            )
        
        return has_permission


class CanApplyTrialLicense(permissions.BasePermission):
    """
    检查Member用户是否可以申请试用许可证
    """
    def has_permission(self, request, view):
        """
        检查用户是否可以申请试用许可证
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            
        Returns:
            布尔值，指示用户是否具有权限
        """
        user = request.user
        path = request.path
        
        # 首先检查是否是Member用户
        member_permission = IsMemberUser()
        if not member_permission.has_permission(request, view):
            return False
        
        # 检查用户是否被禁止申请许可证
        is_application_allowed = True
        if hasattr(user, 'license_application_banned') and user.license_application_banned:
            is_application_allowed = False
            logger.warning(f"用户 {user.username} 被禁止申请许可证")
        
        # 检查租户许可证申请状态
        tenant_allows_application = True
        if hasattr(user, 'tenant') and user.tenant:
            # 这里可以添加租户级别的许可证申请控制逻辑
            # 例如：检查租户是否达到配额上限等
            pass
        
        has_permission = is_application_allowed and tenant_allows_application
        
        logger.info(f"权限检查 [CanApplyTrialLicense] - 路径: {path}")
        logger.info(f"  用户: {user.username}")
        logger.info(f"  申请权限允许: {is_application_allowed}")
        logger.info(f"  租户允许申请: {tenant_allows_application}")
        logger.info(f"  权限检查结果: {'通过' if has_permission else '拒绝'}")
        
        return has_permission


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