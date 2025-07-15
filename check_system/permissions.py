"""
打卡系统权限控制
"""
import logging
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class CheckSystemBasePermission(permissions.BasePermission):
    """
    打卡系统基础权限类
    - 超级管理员不允许操作打卡系统业务
    - 用户必须关联租户才能访问API
    - 租户管理员可以查看和管理其租户内的所有资源
    - 主member可以管理自己和子账号的资源
    - 普通member只能操作自己的资源
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问该视图
        
        所有已认证且关联了租户的用户都可以访问列表和详情视图
        创建/更新/删除操作需要检查角色和参数
        """
        user = request.user
        
        # 未认证用户无权限
        if not user or not user.is_authenticated:
            logger.warning(f"未认证用户尝试访问 {request.path}")
            return False
        
        # 检查用户是否关联租户
        if not hasattr(user, 'tenant') or not user.tenant:
            logger.warning(f"用户 {user.username} 未关联租户，拒绝访问 {request.path}")
            raise PermissionDenied("用户未关联租户，无法访问打卡系统")
        
        # 超级管理员不允许操作打卡系统业务
        if user.is_super_admin:
            logger.warning(f"超级管理员 {user.username} 尝试访问打卡系统 {request.path}")
            raise PermissionDenied("超级管理员不允许操作打卡系统业务")
        
        # 区分安全方法和非安全方法
        if request.method in permissions.SAFE_METHODS:
            # 安全方法(GET, HEAD, OPTIONS)，所有认证且关联租户的用户都可以访问
            return True
        else:
            # 非安全方法(POST, PUT, PATCH, DELETE)，需要检查参数和角色
            
            # 租户管理员
            if user.is_admin:
                # 租户管理员必须提供user_id
                if 'user_id' not in request.data and 'user' not in request.data and request.data.get('is_system') is False:
                    logger.warning(f"租户管理员 {user.username} 尝试创建/修改资源时未提供user_id")
                    return False
                
                return True
            
            # 主member(有子账号的普通成员)
            elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
                # 主member必须提供user_id
                user_id = request.data.get('user_id') or request.data.get('user')
                if not user_id:
                    logger.warning(f"主member {user.username} 尝试创建/修改资源时未提供user_id")
                    return False
                
                # 检查提供的user_id是否是自己或其子账号
                try:
                    user_id = int(user_id)
                    # 如果是自己的ID，允许操作
                    if user_id == user.id:
                        return True
                    
                    # 检查是否为子账号
                    is_sub_account = user.sub_accounts.filter(id=user_id).exists()
                    if not is_sub_account:
                        logger.warning(f"主member {user.username} 尝试操作非子账号用户的资源")
                        return False
                    return True
                except (ValueError, TypeError):
                    logger.warning(f"主member {user.username} 提供的user_id格式不正确")
                    return False
            
            # 普通member
            else:
                # 普通member不能提供user_id，只能操作自己的资源
                user_id = request.data.get('user_id') or request.data.get('user')
                if user_id and int(user_id) != user.id:
                    logger.warning(f"普通member {user.username} 尝试操作其他用户的资源")
                    return False
                return True
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作特定对象
        
        - 超级管理员不允许操作打卡系统业务
        - 租户管理员可以操作其租户内的所有资源
        - 主member可以操作自己和子账号的资源
        - 普通member只能操作自己的资源
        """
        user = request.user
        
        # 检查用户是否关联租户
        if not hasattr(user, 'tenant') or not user.tenant:
            logger.warning(f"用户 {user.username} 未关联租户，拒绝访问对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
            raise PermissionDenied("用户未关联租户，无法访问打卡系统")
        
        # 超级管理员不允许操作打卡系统业务
        if user.is_super_admin:
            logger.warning(f"超级管理员 {user.username} 尝试操作打卡系统对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
            raise PermissionDenied("超级管理员不允许操作打卡系统业务")
        
        # 验证对象所属租户与用户租户一致
        if hasattr(obj, 'tenant') and obj.tenant != user.tenant:
            logger.warning(f"用户 {user.username} 尝试操作不属于其租户的对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
            raise PermissionDenied("不能操作其他租户的资源")
        
        # 租户管理员可以操作其租户内的所有资源
        if user.is_admin and hasattr(obj, 'tenant') and obj.tenant == user.tenant:
            return True
        
        # 获取对象的所有者
        obj_user_id = None
        if hasattr(obj, 'user_id'):
            obj_user_id = obj.user_id
        elif hasattr(obj, 'user'):
            obj_user_id = obj.user.id if obj.user else None
        
        # 自己的资源
        if obj_user_id == user.id:
            return True
        
        # 主member可以操作子账号的资源
        if hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            if obj_user_id and user.sub_accounts.filter(id=obj_user_id).exists():
                return True
        
        logger.warning(f"用户 {user.username} 尝试访问不属于他的对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
        return False


class TaskCategoryPermission(CheckSystemBasePermission):
    """
    打卡类型权限控制
    """
    pass


class TaskPermission(CheckSystemBasePermission):
    """
    打卡任务权限控制
    """
    pass


class CheckRecordPermission(CheckSystemBasePermission):
    """
    打卡记录权限控制
    """
    pass


class TaskTemplatePermission(CheckSystemBasePermission):
    """
    任务模板权限控制
    """
    pass
