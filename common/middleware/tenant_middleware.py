"""
租户中间件，用于处理请求中的租户上下文

重构后的安全版本：
1. 全面基于 ContextVar 上下文管理；
2. 在 sync/async 生命周期、正常响应与异常分支均保证可靠执行 clear_current_tenant()。
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
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.path_checker = TenantPathChecker()
        logger.info("租户中间件：已初始化（使用新架构）")

    def __call__(self, request):
        """
        同步请求入口：
        如果处于 async 模式，直接转交 __acall__ 处理，避免在同步栈提前触发 finally；
        如果处于 sync 模式，通过 try...finally 确保不论正常返回还是未捕获异常均清理租户。
        """
        if self.async_mode:
            return self.__acall__(request)
        try:
            return super().__call__(request)
        finally:
            clear_current_tenant()

    async def __acall__(self, request):
        """
        异步请求入口：
        等待异步响应完全生成后，通过 finally 可靠清理租户。
        """
        try:
            return await super().__acall__(request)
        finally:
            clear_current_tenant()
    
    def process_request(self, request):
        """
        处理请求，设置current租户
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
            clear_current_tenant()
            raise
        except Exception as e:
            logger.error(f"租户中间件处理异常: {str(e)}", exc_info=True)
            clear_current_tenant()
            raise

    def process_exception(self, request, exception):
        """
        异常处理钩子：当视图或后续中间件抛出未捕获异常时触发清理
        """
        logger.debug(f"TenantMiddleware - 捕获未处理异常，清理租户上下文: {str(exception)}")
        clear_current_tenant()
        return None
    
    def process_response(self, request, response):
        """
        处理响应，清除current租户
        """
        clear_current_tenant()
        return response