"""
租户ID解析服务

负责从HTTP请求中提取和验证租户ID
"""
import logging
from rest_framework.exceptions import ValidationError
from common.utils.error_response_builder import TenantErrorResponseBuilder, TenantErrorTypes

logger = logging.getLogger(__name__)


class TenantIdResolver:
    """
    租户ID解析器
    
    从请求的不同来源提取租户ID并进行验证
    支持的来源：查询参数、请求头、用户关联的租户
    """
    
    def __init__(self, request):
        """
        初始化解析器
        
        Args:
            request: HTTP请求对象
        """
        self.request = request
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def resolve_tenant_ids(self):
        """
        解析所有可能的租户ID来源
        
        Returns:
            dict: 包含各种租户ID的字典
                {
                    'query_tenant_id': str|None,
                    'header_tenant_id': str|None, 
                    'user_tenant_id': str|None,
                    'effective_tenant_id': str|None,
                    'tenant_source': str
                }
        
        Raises:
            ValidationError: 租户ID格式无效时抛出
        """
        # 1. 从查询参数获取租户ID
        query_tenant_id = self._extract_query_tenant_id()
        
        # 2. 从请求头获取租户ID
        header_tenant_id = self._extract_header_tenant_id()
        
        # 3. 从用户关联获取租户ID
        user_tenant_id = self._extract_user_tenant_id()
        
        # 4. 确定最终使用的租户ID（优先级：查询参数 > 请求头 > 用户租户）
        effective_tenant_id, tenant_source = self._determine_effective_tenant_id(
            query_tenant_id, header_tenant_id, user_tenant_id
        )
        
        result = {
            'query_tenant_id': query_tenant_id,
            'header_tenant_id': header_tenant_id,
            'user_tenant_id': user_tenant_id,
            'effective_tenant_id': effective_tenant_id,
            'tenant_source': tenant_source,
        }
        
        self.logger.info(f"租户ID解析结果: {result}")
        return result
    
    def _extract_query_tenant_id(self):
        """
        从查询参数中提取租户ID
        
        Returns:
            str|None: 有效的租户ID字符串，无效或不存在时返回None
            
        Raises:
            ValidationError: 租户ID格式无效时抛出
        """
        query_tenant_id = self.request.GET.get('tenant_id')
        self.logger.info(f"从查询参数获取的tenant_id: {query_tenant_id}")
        
        if not query_tenant_id:
            return None
            
        try:
            # 验证是否为有效整数
            validated_id = int(query_tenant_id)
            # 转换为字符串以便后续比较
            result = str(validated_id)
            self.logger.info(f"从查询参数获取到有效租户ID: {result}")
            return result
        except (ValueError, TypeError):
            self.logger.warning(f"无效的查询参数租户ID格式: {query_tenant_id}")
            raise ValidationError({
                "detail": f"无效的查询参数租户ID格式: {query_tenant_id}，租户ID必须是整数"
            })
    
    def _extract_header_tenant_id(self):
        """
        从请求头中提取租户ID
        
        Returns:
            str|None: 有效的租户ID字符串，无效或不存在时返回None
            
        Raises:
            ValidationError: 租户ID格式无效时抛出
        """
        header_tenant_id = self.request.headers.get('X-Tenant-ID')
        self.logger.info(f"从请求头获取的X-Tenant-ID: {header_tenant_id}")
        
        if not header_tenant_id:
            return None
            
        try:
            # 验证是否为有效整数
            validated_id = int(header_tenant_id)
            # 转换为字符串以便后续比较
            result = str(validated_id)
            self.logger.info(f"从请求头获取到有效租户ID: {result}")
            return result
        except (ValueError, TypeError):
            self.logger.warning(f"无效的请求头租户ID格式: {header_tenant_id}")
            raise ValidationError({
                "detail": f"无效的请求头租户ID格式: {header_tenant_id}，租户ID必须是整数"
            })
    
    def _extract_user_tenant_id(self):
        """
        从用户关联中获取租户ID
        
        Returns:
            str|None: 用户关联的租户ID字符串，未关联时返回None
        """
        if not hasattr(self.request, 'user') or not self.request.user.is_authenticated:
            self.logger.info("用户未认证，无法获取用户租户ID")
            return None
            
        user_tenant = getattr(self.request.user, 'tenant', None)
        if not user_tenant:
            self.logger.info(f"用户 {self.request.user.username} 未关联租户")
            return None
            
        user_tenant_id = str(user_tenant.id)
        self.logger.info(f"用户关联的租户ID: {user_tenant_id}, 租户名称: {user_tenant.name}")
        return user_tenant_id
    
    def _determine_effective_tenant_id(self, query_tenant_id, header_tenant_id, user_tenant_id):
        """
        根据优先级确定最终使用的租户ID
        
        优先级：查询参数 > 请求头 > 用户关联租户
        
        Args:
            query_tenant_id: 查询参数中的租户ID
            header_tenant_id: 请求头中的租户ID
            user_tenant_id: 用户关联的租户ID
        
        Returns:
            tuple: (effective_tenant_id, tenant_source)
        """
        if query_tenant_id:
            self.logger.info(f"使用查询参数中的租户ID: {query_tenant_id}")
            return query_tenant_id, 'query_param'
        elif header_tenant_id:
            self.logger.info(f"使用请求头中的租户ID: {header_tenant_id}")
            return header_tenant_id, 'header'
        elif user_tenant_id:
            self.logger.info(f"使用用户关联的租户ID: {user_tenant_id}")
            return user_tenant_id, 'user_tenant'
        else:
            self.logger.info("未获取到任何租户ID")
            return None, 'none'
    
    def validate_tenant_access(self, effective_tenant_id, header_tenant_id, user_tenant_id, user):
        """
        验证用户对租户的访问权限
        
        Args:
            effective_tenant_id: 最终确定的租户ID
            header_tenant_id: 请求头中的租户ID
            user_tenant_id: 用户关联的租户ID
            user: 用户对象
        
        Returns:
            JsonResponse|None: 如果验证失败返回错误响应，成功返回None
        """
        # 检查用户类型
        is_super_admin = self._is_super_admin(user)
        
        # 如果请求头中有租户ID，验证与用户租户是否匹配
        if header_tenant_id and user_tenant_id and header_tenant_id != user_tenant_id:
            # 只有非超级管理员才需要验证租户匹配
            if not is_super_admin:
                self.logger.warning(
                    f"用户 {user.username} 尝试访问不属于其租户的资源，"
                    f"租户ID不匹配: 用户租户={user_tenant_id}, 请求头租户={header_tenant_id}"
                )
                
                return TenantErrorResponseBuilder.build_error_response(
                    TenantErrorTypes.TENANT_ACCESS_DENIED,
                    self.request,
                    user_tenant_id=user_tenant_id,
                    header_tenant_id=header_tenant_id
                )
        
        return None
    
    def _is_super_admin(self, user):
        """
        检查用户是否为超级管理员
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否为通过JWT认证的超级管理员
        """
        if not user or not user.is_authenticated:
            return False
            
        # 只有通过JWT认证的用户才能被识别为超级管理员
        if getattr(self.request, 'auth_type', None) != 'jwt':
            self.logger.info(f"非JWT认证用户 {user.username}，不信任超级管理员标识")
            return False
            
        is_super_admin = getattr(user, 'is_super_admin', False)
        self.logger.info(f"用户 {user.username} 超级管理员状态: {is_super_admin}")
        return is_super_admin
