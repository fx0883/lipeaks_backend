from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class IsSuperAdminOnly(permissions.BasePermission):
    """
    仅允许超级管理员访问的权限类
    """
    def has_permission(self, request, view):
        is_super_admin = bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_super_admin
        )
        
        if not is_super_admin:
            logger.warning(
                f"用户 {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                f"尝试访问仅限超级管理员的图表API {request.path}"
            )
        
        return is_super_admin 