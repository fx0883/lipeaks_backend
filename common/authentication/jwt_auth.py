"""
JWT认证相关模块
"""
import jwt
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework import exceptions
from django.db.models import Q

# 获取User模型和Member模型
User = get_user_model()
# 导入Member模型
try:
    from users.models import Member
except ImportError:
    Member = None

logger = logging.getLogger(__name__)

class JWTAuthentication(authentication.BaseAuthentication):
    """
    自定义JWT认证类
    """
    
    def authenticate(self, request):
        """
        尝试认证请求的用户
        
        Args:
            request: HTTP请求对象
        
        Returns:
            (user, token): 用户对象和令牌元组，如果认证失败则返回None
        
        Raises:
            AuthenticationFailed: 认证失败异常
        """
        # 从请求头获取认证信息
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        # 提取令牌
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        token = parts[1]
        
        # 验证令牌
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_AUTH['JWT_SECRET_KEY'],
                algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']]
            )
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            raise exceptions.AuthenticationFailed('令牌已过期')
        except jwt.InvalidTokenError:
            logger.warning("无效的令牌")
            raise exceptions.AuthenticationFailed('无效的令牌')
        
        # 获取用户
        try:
            user_id = payload.get('user_id')
            model_type = payload.get('model_type', 'user')  # 默认为User模型
            
            if model_type == 'member' and Member:
                user = Member.objects.get(pk=user_id, is_active=True, is_deleted=False)
            else:
                user = User.objects.get(pk=user_id, is_active=True, is_deleted=False)
                
        except (User.DoesNotExist, Member.DoesNotExist) if Member else User.DoesNotExist:
            logger.warning(f"用户不存在或已被禁用: {user_id}")
            raise exceptions.AuthenticationFailed('用户不存在或已被禁用')
        
        # 检查用户状态
        if user.status != 'active':
            logger.warning(f"用户状态异常: {user.username} ({user.status})")
            raise exceptions.AuthenticationFailed('用户状态异常')
            
        # 检查是否为子账号
        if hasattr(user, 'parent') and user.parent:
            logger.warning(f"子账号尝试认证: {user.username}")
            raise exceptions.AuthenticationFailed('子账号不允许登录')
        
        # 检查用户的租户状态
        if user.tenant and not getattr(user, 'is_super_admin', False):
            if user.tenant.status != 'active' or user.tenant.is_deleted:
                logger.warning(f"用户 {user.username} 的租户 {user.tenant.name} 状态异常")
                raise exceptions.AuthenticationFailed('您所属的租户已被禁用或删除')
        
        return (user, token)
    
    def authenticate_header(self, request):
        """
        返回认证头字符串
        
        Args:
            request: HTTP请求对象
        
        Returns:
            认证头字符串
        """
        return 'Bearer'
    
    # 添加drf-spectacular兼容方法
    @classmethod
    def extend_schema(cls):
        """
        为drf-spectacular提供认证模式信息
        """
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': '输入JWT令牌: Bearer [token]'
        }


def generate_jwt_token(user):
    """
    为用户生成JWT令牌
    
    Args:
        user: 用户对象
    
    Returns:
        dict: 包含访问令牌和刷新令牌的字典
    """
    # 令牌过期时间
    token_expiry = datetime.now() + timedelta(seconds=settings.JWT_AUTH['JWT_EXPIRATION_DELTA'])
    refresh_expiry = datetime.now() + timedelta(seconds=settings.JWT_AUTH['JWT_REFRESH_EXPIRATION_DELTA'])
    
    # 确定用户模型类型
    from users.models import Member, User as AdminUser
    model_type = 'member' if isinstance(user, Member) else 'user'
    
    # 创建访问令牌
    access_payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': token_expiry,
        'model_type': model_type,
        'is_admin': getattr(user, 'is_admin', False),
        'is_super_admin': getattr(user, 'is_super_admin', False)
    }
    
    # 创建刷新令牌
    refresh_payload = {
        'user_id': user.id,
        'model_type': model_type,
        'exp': refresh_expiry,
        'token_type': 'refresh'
    }
    
    # 编码令牌
    access_token = jwt.encode(
        access_payload,
        settings.JWT_AUTH['JWT_SECRET_KEY'],
        algorithm=settings.JWT_AUTH['JWT_ALGORITHM']
    )
    
    refresh_token = jwt.encode(
        refresh_payload,
        settings.JWT_AUTH['JWT_SECRET_KEY'],
        algorithm=settings.JWT_AUTH['JWT_ALGORITHM']
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
    }


def verify_jwt_token(token):
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        dict: 令牌payload
    
    Raises:
        jwt.InvalidTokenError: 令牌无效异常
    """
    return jwt.decode(
        token,
        settings.JWT_AUTH['JWT_SECRET_KEY'],
        algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']]
    )


def refresh_jwt_token(refresh_token):
    """
    使用刷新令牌生成新的访问令牌
    
    Args:
        refresh_token: 刷新令牌字符串
    
    Returns:
        dict: 包含新访问令牌的字典
    
    Raises:
        jwt.InvalidTokenError: 令牌无效异常
        ValidationError: 令牌验证失败异常
    """
    try:
        # 解码刷新令牌
        payload = jwt.decode(
            refresh_token,
            settings.JWT_AUTH['JWT_SECRET_KEY'],
            algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']]
        )
        
        # 检查令牌类型
        if payload.get('token_type') != 'refresh':
            logger.warning("非刷新令牌被用于刷新操作")
            raise exceptions.ValidationError('无效的刷新令牌')
        
        # 获取用户
        try:
            user_id = payload.get('user_id')
            model_type = payload.get('model_type', 'user')  # 默认为User模型
            
            if model_type == 'member' and Member:
                user = Member.objects.get(pk=user_id, is_active=True, is_deleted=False)
            else:
                user = User.objects.get(pk=user_id, is_active=True, is_deleted=False)
                
        except (User.DoesNotExist, Member.DoesNotExist) if Member else User.DoesNotExist:
            logger.warning(f"刷新令牌对应的用户不存在或已被禁用: {user_id}")
            raise exceptions.ValidationError('用户不存在或已被禁用')
        
        # 检查用户状态
        if user.status != 'active':
            logger.warning(f"刷新令牌对应的用户状态异常: {user.username} ({user.status})")
            raise exceptions.ValidationError('用户状态异常')
        
        # 生成新令牌
        token_expiry = datetime.now() + timedelta(seconds=settings.JWT_AUTH['JWT_EXPIRATION_DELTA'])
        
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': token_expiry,
            'model_type': model_type,
            'is_admin': getattr(user, 'is_admin', False),
            'is_super_admin': getattr(user, 'is_super_admin', False)
        }
        
        access_token = jwt.encode(
            access_payload,
            settings.JWT_AUTH['JWT_SECRET_KEY'],
            algorithm=settings.JWT_AUTH['JWT_ALGORITHM']
        )
        
        return {
            'access_token': access_token,
            'expires_in': settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("刷新令牌已过期")
        raise exceptions.ValidationError('刷新令牌已过期')
    except jwt.InvalidTokenError:
        logger.warning("无效的刷新令牌")
        raise exceptions.ValidationError('无效的刷新令牌') 