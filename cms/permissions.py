"""
CMS系统权限控制
"""
import logging
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from common.exceptions import CMSException

logger = logging.getLogger(__name__)


class CMSBasePermission(permissions.BasePermission):
    """
    CMS系统基础权限类
    
    权限控制规则：
    - GET请求允许匿名访问，但需要租户ID
    - 非GET请求需要认证，并且用户必须关联租户
    - 超级管理员可以通过X-Tenant-ID请求头指定租户进行操作
    - 租户管理员可以管理其租户内的所有资源
    - 普通用户只能操作自己的资源
    - 只有URL路径中包含"cms"的API才需要进行租户ID验证
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问视图
        
        - 允许所有GET请求访问（租户ID验证已在中间件中完成）
        - 非安全方法需要认证和租户关联
        - 超级管理员可以通过X-Tenant-ID请求头指定租户进行操作
        """
        # 检查请求路径是否为Admin路径，如果是则跳过租户验证
        if request.path.startswith('/admin/'):
            logger.debug(f"Admin路径，跳过租户验证: {request.path}")
            return True
            
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in request.path:
            logger.debug(f"非CMS路径，跳过租户验证: {request.path}")
            return True
            
        # 允许所有GET请求访问（租户ID验证已在中间件中完成）
        if request.method in permissions.SAFE_METHODS:
            # 确保请求中有租户ID
            if not hasattr(request, 'tenant_id') or not request.tenant_id:
                logger.warning(f"GET请求未提供租户ID: {request.path}")
                raise CMSException(
                    error_code='TENANT_ID_REQUIRED',
                    detail='未提供租户ID，无法访问CMS资源',
                    request_path=request.path,
                    request_method=request.method
                )
            return True
            
        # 非安全方法需要认证
        user = request.user
        
        # 未认证用户无权限执行非安全方法
        if not user or not user.is_authenticated:
            logger.warning(f"未认证用户尝试访问 {request.path}")
            return False
        
        # 超级管理员特殊处理：允许通过X-Tenant-ID请求头指定租户进行操作
        if getattr(user, 'is_super_admin', False):
            # 确保请求中有租户ID（由中间件设置）
            if not hasattr(request, 'tenant_id') or not request.tenant_id:
                logger.warning(f"超级管理员 {user.username} 尝试操作CMS数据但未指定租户ID")
                raise CMSException(
                    error_code='SUPER_ADMIN_TENANT_ID_REQUIRED',
                    detail='超级管理员需要通过X-Tenant-ID请求头指定租户ID',
                    user_id=user.id,
                    username=user.username
                )
            return True
        
        # 检查普通用户是否关联租户
        if not hasattr(user, 'tenant') or not user.tenant:
            logger.warning(f"用户 {user.username} 未关联租户，拒绝访问 {request.path}")
            raise PermissionDenied("User has no associated tenant and cannot access CMS system")
        
        # 租户管理员可以操作其租户内的所有资源
        if getattr(user, 'is_admin', False):
            return True
        
        # 普通用户只能操作自己的资源
        if hasattr(view, 'get_object'):
            try:
                obj = view.get_object()
                return self.has_object_permission(request, view, obj)
            except:
                pass
        
        # 普通用户创建资源时，自动设置为自己的资源
        if request.method == 'POST':
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作特定对象
        
        - 租户管理员可以操作其租户内的所有资源
        - 普通用户只能操作自己的资源
        """
        # 检查请求路径是否为Admin路径，如果是则跳过租户验证
        if request.path.startswith('/admin/'):
            logger.debug(f"Admin路径，跳过租户验证: {request.path}")
            return True
            
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in request.path:
            logger.debug(f"非CMS路径，跳过租户验证: {request.path}")
            return True
            
        user = request.user
        
        # GET请求允许匿名访问（但需要租户ID，这在中间件中已验证）
        if request.method in permissions.SAFE_METHODS:
            # 验证对象所属租户与请求租户一致
            if hasattr(obj, 'tenant') and str(obj.tenant.id) != str(request.tenant_id):
                logger.warning(f"尝试访问不属于current租户的资源: {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
                raise PermissionDenied("Cannot access resources of other tenants")
            return True
        
        # 超级管理员特殊处理：允许通过X-Tenant-ID请求头指定租户进行操作
        if getattr(user, 'is_super_admin', False):
            # 验证对象所属租户与请求租户一致
            if hasattr(obj, 'tenant') and str(obj.tenant.id) != str(request.tenant_id):
                logger.warning(f"超级管理员 {user.username} 尝试操作不属于指定租户的对象")
                raise PermissionDenied("Cannot operate resources of other tenants")
            return True
        
        # 检查普通用户是否关联租户
        if not hasattr(user, 'tenant') or not user.tenant:
            logger.warning(f"用户 {user.username} 未关联租户，拒绝访问对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
            raise PermissionDenied("User has no associated tenant and cannot access CMS system")
        
        # 验证对象所属租户与用户租户一致
        if hasattr(obj, 'tenant') and obj.tenant != user.tenant:
            logger.warning(f"用户 {user.username} 尝试操作不属于其租户的对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
            raise PermissionDenied("Cannot operate resources of other tenants")
        
        # 租户管理员可以操作其租户内的所有资源
        if getattr(user, 'is_admin', False) and hasattr(obj, 'tenant') and obj.tenant == user.tenant:
            return True
        
        # 获取对象的所有者（支持GenericForeignKey）
        obj_author = None
        if hasattr(obj, 'author'):
            obj_author = obj.author
        elif hasattr(obj, 'user'):
            obj_author = obj.user
        
        # 检查是否是自己的资源（直接比较对象，支持不同用户类型）
        if obj_author and obj_author == user:
            return True
        
        logger.warning(f"用户 {user.username} 尝试访问不属于他的对象 {obj.__class__.__name__} #{getattr(obj, 'id', 'unknown')}")
        return False


class ArticlePermission(CMSBasePermission):
    """
    文章权限控制
    
    额外规则：
    - 所有GET请求允许匿名访问
    - 草稿、待审核和私有文章，只有作者和管理员可以查看
    """
    
    def has_object_permission(self, request, view, obj):
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in request.path:
            logger.debug(f"非CMS路径，跳过租户验证: {request.path}")
            return True
            
        # GET请求允许匿名访问已发布且公开的文章
        if request.method in permissions.SAFE_METHODS:
            # 验证对象所属租户与请求租户一致
            if hasattr(obj, 'tenant') and str(obj.tenant.id) != str(request.tenant_id):
                logger.warning(f"尝试访问不属于current租户的文章: #{getattr(obj, 'id', 'unknown')}")
                raise PermissionDenied("Cannot access resources of other tenants")
                
            if obj.status == 'published' and obj.visibility == 'public':
                return True
            
            # 非公开文章需要认证
            if not request.user or not request.user.is_authenticated:
                logger.warning(f"未认证用户尝试访问非公开文章: #{getattr(obj, 'id', 'unknown')}")
                return False
                
        # 首先检查基本权限
        if super().has_object_permission(request, view, obj):
            return True
        
        return False


class CategoryPermission(CMSBasePermission):
    """
    分类权限控制
    """
    pass


class TagPermission(CMSBasePermission):
    """
    标签权限控制
    """
    pass


class CommentPermission(CMSBasePermission):
    """
    评论权限控制
    
    额外规则：
    - 所有认证用户都可以给开放评论的文章添加评论
    - 评论作者可以编辑或删除自己的评论
    - 文章作者可以管理其文章下的所有评论
    """
    
    def has_permission(self, request, view):
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in request.path:
            logger.debug(f"非CMS路径，跳过租户验证: {request.path}")
            return True
            
        # 添加评论需要检查文章是否允许评论
        if request.method == 'POST':
            article_id = request.data.get('article') or request.data.get('article_id')
            if article_id:
                from .models import Article
                try:
                    article = Article.objects.get(id=article_id, tenant_id=request.tenant_id)
                    if not article.allow_comment:
                        return False
                except Article.DoesNotExist:
                    return False
        
        return super().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in request.path:
            logger.debug(f"非CMS路径，跳过租户验证: {request.path}")
            return True
            
        # 首先检查基本权限
        if super().has_object_permission(request, view, obj):
            return True
        
        # 文章作者可以管理其文章下的所有评论
        user = request.user
        if hasattr(obj, 'article') and obj.article.author_id == user.id:
            return True
        
        return False


class ArticleVersionPermission(CMSBasePermission):
    """
    文章版本权限控制
    """
    pass


class ArticleMetaPermission(CMSBasePermission):
    """
    文章元数据权限控制
    """
    pass


class ArticleStatisticsPermission(CMSBasePermission):
    """
    文章统计权限控制
    """
    pass


class InteractionPermission(CMSBasePermission):
    """
    用户互动权限控制
    """
    pass 