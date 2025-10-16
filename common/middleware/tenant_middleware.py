"""
租户中间件，用于处理请求中的租户上下文

重构后的简化版本，使用服务类架构
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import ValidationError
from common.utils.tenant_context import clear_current_tenant

# 新版本服务类导入
from common.services.tenant_resolver import TenantIdResolver
from common.services.permission_checker import TenantPermissionChecker
from common.services.tenant_validator import TenantValidator, TenantPathChecker

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    租户中间件，用于从请求中提取租户信息并设置租户上下文
    
    使用服务类架构，职责清晰：
    - TenantIdResolver: 解析租户ID
    - TenantPermissionChecker: 检查权限
    - TenantValidator: 验证租户并设置上下文
    
    处理以下租户信息来源:
    1. X-Tenant-ID 请求头
    2. 用户关联的租户
    
    权限控制规则：
    - GET请求允许匿名访问，但需要租户ID（从X-Tenant-ID或用户token获取）
    - 非GET请求需要认证，并且用户必须关联租户
    - 超级管理员可以通过X-Tenant-ID请求头指定租户进行操作
    - 只有真正的API路径才需要进行租户ID验证，Admin路径不需要
    """
    
    def __init__(self, get_response):
        """
        初始化中间件
        
        Args:
            get_response: Django中间件响应函数
        """
        super().__init__(get_response)
        self.path_checker = TenantPathChecker()
        logger.info("租户中间件：已初始化（使用新架构）")
    
    def process_request(self, request):
        """
        处理请求，设置current租户
        
        Args:
            request: HTTP请求对象
        
        Returns:
            JsonResponse|None: 处理失败时返回错误响应，成功时返回None
        """
        logger.info(f"TenantMiddleware - 处理请求: {request.path}")
        
        # 清除之前的租户上下文
        clear_current_tenant()
        
        # 检查路径是否需要租户验证
        if not self.path_checker.requires_tenant_verification(request.path):
            logger.debug(f"路径不需要租户验证，跳过: {request.path}")
            return None
        
        logger.info(f"开始处理需要租户验证的路径: {request.path}, 方法: {request.method}")
        
        try:
            # 1. 解析租户ID
            resolver = TenantIdResolver(request)
            tenant_info = resolver.resolve_tenant_ids()
            
            # 2. 验证用户对租户的访问权限
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                error_response = resolver.validate_tenant_access(
                    tenant_info['effective_tenant_id'],
                    tenant_info['header_tenant_id'], 
                    tenant_info['user_tenant_id'],
                    user
                )
                if error_response:
                    return error_response
            
            # 3. 检查权限
            permission_checker = TenantPermissionChecker(request)
            error_response = permission_checker.check_permissions(
                tenant_info['effective_tenant_id'],
                tenant_info['user_tenant_id']
            )
            if error_response:
                return error_response
            
            # 4. 验证租户并设置上下文
            validator = TenantValidator(request)
            user_tenant = getattr(user, 'tenant', None) if user and user.is_authenticated else None
            error_response = validator.validate_and_set_tenant_context(
                tenant_info['effective_tenant_id'],
                user_tenant
            )
            if error_response:
                return error_response
            
            # 5. 设置请求属性
            validator.set_request_attributes(tenant_info)
            
            logger.info(f"租户验证成功: {request.path}")
            return None
            
        except ValidationError as e:
            logger.warning(f"租户验证失败: {str(e)}")
            # ValidationError会被后续中间件处理
            raise
        except Exception as e:
            logger.error(f"租户中间件处理异常: {str(e)}", exc_info=True)
            # 重新抛出异常，让Django处理
            raise
    
    def process_response(self, request, response):
        """
        处理响应，清除current租户
        
        Args:
            request: HTTP请求对象
            response: HTTP响应对象
        
        Returns:
            HTTP响应对象
        """
        # 请求结束后清除租户上下文
        clear_current_tenant()
        return response