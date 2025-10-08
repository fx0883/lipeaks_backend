"""
权限检查服务

负责验证用户对租户资源的访问权限
"""
import logging
from common.utils.error_response_builder import TenantErrorResponseBuilder, TenantErrorTypes

logger = logging.getLogger(__name__)


class TenantPermissionChecker:
    """
    租户权限检查器
    
    根据用户类型、请求方法、租户ID等条件验证访问权限
    """
    
    def __init__(self, request):
        """
        初始化权限检查器
        
        Args:
            request: HTTP请求对象
        """
        self.request = request
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def check_permissions(self, effective_tenant_id, user_tenant_id):
        """
        检查用户权限
        
        Args:
            effective_tenant_id: 最终确定的租户ID
            user_tenant_id: 用户关联的租户ID
        
        Returns:
            JsonResponse|None: 权限检查失败时返回错误响应，成功时返回None
        """
        # 获取用户信息
        user = getattr(self.request, 'user', None)
        if not user:
            self.logger.info("请求对象中没有用户信息")
            return None
            
        # 识别用户类型
        user_type_info = self._identify_user_type(user)
        
        # 根据请求方法进行不同的权限检查
        if self.request.method == 'GET':
            return self._check_get_permissions(effective_tenant_id, user_type_info)
        else:
            return self._check_non_get_permissions(effective_tenant_id, user_tenant_id, user_type_info)
    
    def _identify_user_type(self, user):
        """
        识别用户类型
        
        Args:
            user: 用户对象
        
        Returns:
            dict: 用户类型信息
        """
        if not user.is_authenticated:
            return {
                'is_authenticated': False,
                'is_super_admin': False,
                'is_tenant_admin': False,
                'username': 'anonymous'
            }
        
        # 检查认证类型，只有JWT认证的用户才能被识别为超级管理员
        auth_type = getattr(self.request, 'auth_type', 'unknown')
        is_jwt_auth = auth_type == 'jwt'
        
        is_super_admin = False
        is_tenant_admin = False
        
        if is_jwt_auth:
            is_super_admin = getattr(user, 'is_super_admin', False)
            is_admin = getattr(user, 'is_admin', False)
            is_tenant_admin = is_admin and not is_super_admin
            
            self.logger.info(
                f"JWT认证用户类型检查 - 用户名: {user.username}, "
                f"超级管理员: {is_super_admin}, 租户管理员: {is_tenant_admin}"
            )
        else:
            self.logger.info(f"非JWT认证用户 {user.username}，不信任超级管理员标识")
        
        user_type_info = {
            'is_authenticated': True,
            'is_super_admin': is_super_admin,
            'is_tenant_admin': is_tenant_admin,
            'username': user.username,
            'auth_type': auth_type,
        }
        
        # 记录用户租户信息
        user_tenant = getattr(user, 'tenant', None)
        if user_tenant:
            self.logger.info(
                f"用户关联的租户: ID={user_tenant.id}, 名称={user_tenant.name}, 状态={user_tenant.status}"
            )
            user_type_info['user_tenant'] = user_tenant
        else:
            self.logger.warning(f"用户 {user.username} 未关联租户")
            user_type_info['user_tenant'] = None
        
        return user_type_info
    
    def _check_get_permissions(self, effective_tenant_id, user_type_info):
        """
        检查GET请求权限
        
        GET请求允许匿名访问，但需要租户ID（从X-Tenant-ID或用户token获取）
        超级管理员可以无租户ID访问系统级资源
        
        Args:
            effective_tenant_id: 有效的租户ID
            user_type_info: 用户类型信息
        
        Returns:
            JsonResponse|None: 权限检查失败时返回错误响应，成功时返回None
        """
        self.logger.info(f"检查GET请求权限 - 租户ID: {effective_tenant_id}")
        
        # 如果没有有效的租户ID
        if not effective_tenant_id:
            # 检查是否为超级管理员
            if user_type_info['is_super_admin']:
                # 超级管理员可以没有租户ID，允许访问系统级资源
                self.logger.info(
                    f"超级管理员 {user_type_info['username']} GET请求未提供租户ID，允许访问: {self.request.path}"
                )
                # 设置标志，表示这是超级管理员的无租户访问
                self.request.is_super_admin_no_tenant = True
                self.request.tenant_id = None
                self.request.tenant_source = 'super_admin_no_tenant'
                return None
            else:
                # 非超级管理员必须提供租户ID
                self.logger.warning(f"GET请求未提供租户ID: {self.request.path}")
                return TenantErrorResponseBuilder.build_error_response(
                    TenantErrorTypes.TENANT_ID_REQUIRED,
                    self.request
                )
        
        # 有租户ID的情况，允许访问
        return None
    
    def _check_non_get_permissions(self, effective_tenant_id, user_tenant_id, user_type_info):
        """
        检查非GET请求权限
        
        非GET请求需要认证和关联租户
        
        Args:
            effective_tenant_id: 有效的租户ID
            user_tenant_id: 用户关联的租户ID
            user_type_info: 用户类型信息
        
        Returns:
            JsonResponse|None: 权限检查失败时返回错误响应，成功时返回None
        """
        self.logger.info(f"检查非GET请求权限 - 租户ID: {effective_tenant_id}")
        
        # 检查用户是否已认证
        if not user_type_info['is_authenticated']:
            self.logger.warning(f"未认证用户尝试执行非GET请求: {self.request.path}")
            # 这里不抛出异常，让后续的认证中间件处理
            return None
        
        # 超级管理员特殊处理
        if user_type_info['is_super_admin']:
            return self._handle_super_admin_non_get_request(effective_tenant_id, user_type_info)
        
        # 普通用户检查是否关联租户
        if not user_tenant_id:
            self.logger.warning(
                f"用户 {user_type_info['username']} 未关联租户，尝试执行非GET请求: {self.request.path}"
            )
            return TenantErrorResponseBuilder.build_error_response(
                TenantErrorTypes.USER_NOT_ASSOCIATED_WITH_TENANT,
                self.request
            )
        
        # 普通用户访问成功
        return None
    
    def _handle_super_admin_non_get_request(self, effective_tenant_id, user_type_info):
        """
        处理超级管理员的非GET请求
        
        Args:
            effective_tenant_id: 有效的租户ID
            user_type_info: 用户类型信息
        
        Returns:
            JsonResponse|None: 权限检查失败时返回错误响应，成功时返回None
        """
        username = user_type_info['username']
        self.logger.info(f"检测到超级管理员: {username}")
        
        # 检查是否通过请求头指定了租户ID
        header_tenant_id = self.request.headers.get('X-Tenant-ID')
        
        if header_tenant_id:
            self.logger.info(f"超级管理员 {username} 通过请求头指定租户ID: {header_tenant_id}")
            
            # 验证指定的租户是否存在
            return self._validate_super_admin_tenant_id(header_tenant_id)
        else:
            # 超级管理员必须指定租户ID才能进行CMS操作
            self.logger.warning(f"超级管理员 {username} 尝试执行CMS操作但未指定租户ID")
            return TenantErrorResponseBuilder.build_error_response(
                TenantErrorTypes.SUPER_ADMIN_TENANT_ID_REQUIRED,
                self.request
            )
    
    def _validate_super_admin_tenant_id(self, tenant_id):
        """
        验证超级管理员指定的租户ID是否存在
        
        Args:
            tenant_id: 租户ID字符串
        
        Returns:
            JsonResponse|None: 验证失败时返回错误响应，成功时返回None
        """
        try:
            from tenants.models import Tenant
            tenant = Tenant.objects.get(id=int(tenant_id))
            
            # 为超级管理员设置临时租户上下文
            from common.utils.tenant_context import set_current_tenant
            set_current_tenant(tenant)
            
            # 设置请求属性
            self.request.tenant_id = tenant_id
            
            self.logger.info(
                f"已为超级管理员 {self.request.user.username} 设置临时租户上下文: "
                f"{tenant.name} (ID: {tenant_id})"
            )
            
            return None
            
        except Tenant.DoesNotExist:
            self.logger.warning(f"超级管理员指定的租户ID不存在: {tenant_id}")
            return TenantErrorResponseBuilder.build_error_response(
                TenantErrorTypes.TENANT_NOT_FOUND,
                self.request,
                tenant_id=tenant_id
            )
