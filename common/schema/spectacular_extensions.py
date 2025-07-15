"""
DRF Spectacular扩展配置
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from common.authentication.jwt_auth import JWTAuthentication
from common.authentication.api_auth import APIJWTAuthentication

class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    为DRF Spectacular提供JWT认证的扩展
    """
    target_class = JWTAuthentication
    name = 'Bearer'  # 在OpenAPI文档中显示的认证方式名称

    def get_security_definition(self, auto_schema):
        """
        返回安全定义
        """
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': '输入JWT令牌: Bearer [token]'
        }

class APIJWTAuthenticationScheme(JWTAuthenticationScheme):
    """
    为API专用JWT认证提供OpenAPI扩展
    """
    target_class = APIJWTAuthentication

# 打印日志确认扩展被加载
import logging
logger = logging.getLogger('drf_spectacular')
logger.debug('JWTAuthenticationScheme扩展已加载') 