"""
API请求专用JWT认证
"""
import logging
from common.authentication.jwt_auth import JWTAuthentication

logger = logging.getLogger(__name__)

class APIJWTAuthentication(JWTAuthentication):
    """
    仅用于API请求的JWT认证
    
    此类继承自JWTAuthentication，但只对API路径下的请求进行认证
    对于非API路径（如后台管理界面），直接返回None，交由其他认证类处理
    """
    
    # 重写认证scheme名称，避免与JWTAuthentication冲突
    def authenticate_header(self, request):
        """
        返回认证头字符串，使用API-Bearer避免与基础Bearer冲突
        """
        return 'Bearer'
    
    def authenticate(self, request):
        """
        重写authenticate方法，只对API路径下的请求进行JWT认证
        
        Args:
            request: HTTP请求对象
        
        Returns:
            (user, token): 如果是API请求且JWT认证成功，返回用户与令牌
            None: 如果是非API请求或认证失败
        """
        # 检查是否为API请求
        if not request.path.startswith('/api/'):
            logger.debug(f"非API路径请求，跳过JWT认证: {request.path}")
            return None
        
        # 对API请求进行JWT认证
        return super().authenticate(request) 