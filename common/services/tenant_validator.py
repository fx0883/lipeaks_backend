"""
租户验证服务

负责验证租户存在性和状态，设置租户上下文
"""
import logging
from django.conf import settings
from common.utils.error_response_builder import TenantErrorResponseBuilder, TenantErrorTypes
from common.utils.tenant_context import set_current_tenant

logger = logging.getLogger(__name__)


class TenantValidator:
    """
    租户验证器
    
    验证租户是否存在并设置租户上下文
    """
    
    def __init__(self, request):
        """
        初始化租户验证器
        
        Args:
            request: HTTP请求对象
        """
        self.request = request
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_and_set_tenant_context(self, effective_tenant_id, user_tenant=None):
        """
        验证租户并设置租户上下文
        
        Args:
            effective_tenant_id: 要验证的租户ID
            user_tenant: 用户关联的租户对象（可选，用于优化）
        
        Returns:
            JsonResponse|None: 验证失败时返回错误响应，成功时返回None
        """
        if not effective_tenant_id:
            # 如果没有租户ID但有用户租户，设置用户租户上下文
            if user_tenant:
                self.logger.info(
                    f"用户 {self.request.user.username} 属于租户 {user_tenant.name}, 已设置租户上下文"
                )
                set_current_tenant(user_tenant)
            return None
        
        # 验证租户是否存在
        tenant = self._get_tenant_by_id(effective_tenant_id)
        if not tenant:
            return TenantErrorResponseBuilder.build_error_response(
                TenantErrorTypes.TENANT_NOT_FOUND,
                self.request,
                tenant_id=effective_tenant_id
            )
        
        # 设置租户上下文
        self.logger.info(f"设置租户上下文: {tenant.name} (ID: {effective_tenant_id})")
        set_current_tenant(tenant)
        
        return None
    
    def _get_tenant_by_id(self, tenant_id):
        """
        根据ID获取租户对象
        
        Args:
            tenant_id: 租户ID字符串
        
        Returns:
            Tenant|None: 租户对象，不存在时返回None
        """
        try:
            from tenants.models import Tenant
            tenant = Tenant.objects.get(id=int(tenant_id))
            self.logger.info(f"找到租户: {tenant.name} (ID: {tenant_id}, 状态: {tenant.status})")
            return tenant
        except Tenant.DoesNotExist:
            self.logger.warning(f"指定的租户ID不存在: {tenant_id}")
            return None
        except (ValueError, TypeError) as e:
            self.logger.error(f"租户ID格式错误: {tenant_id}, 错误: {e}")
            return None
    
    def set_request_attributes(self, tenant_info):
        """
        设置请求对象上的租户相关属性
        
        Args:
            tenant_info: 租户信息字典，包含各种租户ID和来源
        """
        # 设置租户信息到请求对象，方便视图使用
        self.request.tenant_id = tenant_info['effective_tenant_id']
        self.request.tenant_source = tenant_info['tenant_source']
        self.request.query_tenant_id = tenant_info['query_tenant_id']
        self.request.header_tenant_id = tenant_info['header_tenant_id']
        
        self.logger.info(
            f"已设置请求的租户信息: tenant_id={tenant_info['effective_tenant_id']}, "
            f"source={tenant_info['tenant_source']}"
        )


class TenantPathChecker:
    """
    租户路径检查器
    
    判断请求路径是否需要租户验证
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def requires_tenant_verification(self, path):
        """
        判断路径是否需要租户验证
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否需要租户验证
        """
        # Admin路径不需要租户验证（由Django Admin自己处理）
        if path.startswith('/admin/'):
            self.logger.debug(f"Admin路径，跳过租户验证: {path}")
            return False
        
        # 静态资源不需要租户验证
        if path.startswith(('/static/', '/media/')):
            self.logger.debug(f"静态资源路径，跳过租户验证: {path}")
            return False
        
        # API文档不需要租户验证
        if path.startswith(('/api/v1/schema/', '/api/v1/docs/', '/api/v1/redoc/')):
            self.logger.debug(f"API文档路径，跳过租户验证: {path}")
            return False
        
        # 系统级API不需要租户验证（菜单、系统配置等）
        if path.startswith('/api/v1/menus/'):
            self.logger.debug(f"系统级API路径，跳过租户验证: {path}")
            return False
        
        # 从配置中获取公开API路径（不需要租户验证）
        public_api_paths = getattr(
            settings,
            'TENANT_PUBLIC_API_PATHS',
            [
                '/api/v1/licenses/status/',
                '/api/v1/licenses/activate/',
                '/api/v1/licenses/verify/',
                '/api/v1/licenses/heartbeat/',
                '/api/v1/licenses/unbind/',
                '/api/v1/licenses/info/',
            ]
        )
        
        # 检查是否匹配公开API路径（支持前缀匹配）
        for public_path in public_api_paths:
            # 精确匹配（带或不带末尾斜杠）
            if path == public_path or path == public_path.rstrip('/'):
                self.logger.debug(f"公开API路径，跳过租户验证: {path}")
                return False
            # 前缀匹配（用于带参数的路径如 /api/v1/licenses/info/{key}/）
            if path.startswith(public_path):
                self.logger.debug(f"公开API路径（前缀匹配），跳过租户验证: {path}")
                return False
        
        # 只对真正的业务API路径进行租户验证
        # 从配置中获取需要租户隔离的路径，如果未配置则使用默认值
        business_api_prefixes = getattr(
            settings, 
            'TENANT_ISOLATED_API_PATHS',
            [
                '/api/v1/cms/',
                '/api/v1/customers/',
                '/api/v1/licenses/'
            ]
        )
        
        requires_verification = any(path.startswith(prefix) for prefix in business_api_prefixes)
        
        if requires_verification:
            self.logger.info(f"业务API路径，需要租户验证: {path}")
        else:
            self.logger.debug(f"路径不需要租户验证: {path}")
            
        return requires_verification
