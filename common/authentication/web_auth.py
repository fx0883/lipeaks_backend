"""
Web请求专用会话认证
"""
import logging
from rest_framework.authentication import SessionAuthentication

logger = logging.getLogger(__name__)

class WebSessionAuthentication(SessionAuthentication):
    """
    仅用于Web请求的会话认证
    
    此类继承自SessionAuthentication，但只对非API路径下的请求进行认证
    对于API路径，直接返回None，避免与JWT认证冲突
    """
    
    def authenticate(self, request):
        """
        重写authenticate方法，只对非API路径下的请求进行会话认证
        
        Args:
            request: HTTP请求对象
        
        Returns:
            (user, None): 如果是非API请求且会话认证成功，返回用户
            None: 如果是API请求或认证失败
        """
        # 检查是否为API请求
        if request.path.startswith('/api/'):
            logger.debug(f"API路径请求，跳过会话认证: {request.path}")
            return None
        
        # 对非API请求进行会话认证
        return super().authenticate(request) 