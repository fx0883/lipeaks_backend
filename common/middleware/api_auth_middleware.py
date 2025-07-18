"""
API请求认证中间件

在API请求中优先使用JWT令牌中的用户身份，覆盖会话中的用户
"""
import logging
import jwt
import json
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from users.models import User, Member

logger = logging.getLogger(__name__)

class APIAuthMiddleware(MiddlewareMixin):
    """
    API请求认证中间件
    
    如果是API请求且包含有效的JWT令牌，则覆盖request.user为JWT令牌中的用户
    这可确保API请求总是使用JWT令牌中的用户身份，而不是session中的用户
    如果请求包含Bearer令牌但令牌无效或过期，则直接返回401响应
    """
    
    def process_request(self, request):
        # 只处理API请求
        if not request.path.startswith('/api/'):
            logger.debug(f"非API路径，跳过JWT认证中间件: {request.path}")
            return None
            
        # 跳过静态文件和媒体文件的JWT认证
        if request.path.startswith(('/static/', '/media/')):
            logger.info(f"[API认证中间件] 静态/媒体资源路径，跳过JWT认证: {request.path}")
            return None
            
        logger.info(f"[API认证中间件] 处理API请求: {request.path}")
            
        # 从请求头获取令牌
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.info(f"[API认证中间件] API请求没有Bearer认证头: {request.path}")
            return None
            
        token = auth_header.split(' ')[1]
        logger.info(f"[API认证中间件] 获取到Bearer令牌: {token[:10]}...")
        
        try:
            # 解析令牌
            payload = jwt.decode(
                token,
                settings.JWT_AUTH['JWT_SECRET_KEY'],
                algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']]
            )
            
            logger.info(f"[API认证中间件] JWT令牌解析成功，payload: {payload}")
            
            # 获取用户
            user_id = payload.get('user_id')
            model_type = payload.get('model_type', 'user')  # 默认为User模型
            
            logger.info(f"[API认证中间件] JWT令牌中的用户信息 - ID: {user_id}, 类型: {model_type}")
            
            if user_id:
                try:
                    # 根据model_type判断获取哪种用户
                    if model_type == 'member' and Member:
                        jwt_user = Member.objects.get(pk=user_id, is_active=True, is_deleted=False)
                        logger.info(f"[API认证中间件] 从JWT令牌获取到Member用户: {jwt_user.username} (ID: {jwt_user.id})")
                    else:
                        jwt_user = User.objects.get(pk=user_id, is_active=True, is_deleted=False)
                        logger.info(f"[API认证中间件] 从JWT令牌获取到User用户: {jwt_user.username} (ID: {jwt_user.id})")
                        
                    # 记录用户角色信息
                    is_super_admin = getattr(jwt_user, 'is_super_admin', False)
                    is_admin = getattr(jwt_user, 'is_admin', False)
                    is_tenant_admin = is_admin and not is_super_admin
                    logger.info(f"[API认证中间件] 用户角色 - 超级管理员: {is_super_admin}, 管理员: {is_admin}, 租户管理员: {is_tenant_admin}")
                    
                    # 确保用户类型正确
                    if hasattr(jwt_user, 'is_super_admin'):
                        # 如果用户是超级管理员，确保没有关联租户
                        if is_super_admin and getattr(jwt_user, 'tenant', None) is not None:
                            logger.warning(f"[API认证中间件] 警告：超级管理员 {jwt_user.username} 不应关联租户，但当前关联了租户")
                        
                        # 如果用户是租户管理员，确保关联了租户
                        if is_tenant_admin and getattr(jwt_user, 'tenant', None) is None:
                            logger.warning(f"[API认证中间件] 警告：租户管理员 {jwt_user.username} 应关联租户，但当前未关联租户")
                    
                    # 记录用户租户信息
                    user_tenant = getattr(jwt_user, 'tenant', None)
                    if user_tenant:
                        logger.info(f"[API认证中间件] 用户关联的租户: ID={user_tenant.id}, 名称={user_tenant.name}, 状态={user_tenant.status}")
                    else:
                        logger.warning(f"[API认证中间件] 用户 {jwt_user.username} 未关联租户")
                        
                    # 检查用户状态
                    if jwt_user.status != 'active':
                        logger.warning(f"[API认证中间件] JWT令牌中的用户状态异常: {jwt_user.username} ({jwt_user.status})")
                        # 返回401未授权响应
                        error_response = {
                            "success": False,
                            "code": 4001,
                            "message": "认证失败：用户已被禁用或状态异常",
                            "data": None
                        }
                        
                        # 如果请求头中包含X-Debug-Log，则添加调试日志
                        if request.headers.get('X-Debug-Log') == 'true':
                            error_response["debug_logs"] = [{
                                "level": "error",
                                "message": f"[API认证中间件] JWT令牌中的用户状态异常: {jwt_user.username} ({jwt_user.status})",
                                "timestamp": json.dumps(jwt_user.status),
                                "user_id": user_id
                            }]
                        
                        return JsonResponse(error_response, status=401)
                    
                    # 记录原始用户和新用户，方便调试
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        original_user = request.user.username
                        logger.info(f"[API认证中间件] 用户已从 {original_user} 替换为JWT用户 {jwt_user.username}")
                    else:
                        logger.info(f"[API认证中间件] 用户已设置为JWT用户 {jwt_user.username}")
                    
                    # 替换request.user为JWT令牌中的用户
                    request.user = jwt_user
                    # 标记使用的是JWT认证
                    request.auth_type = 'jwt'
                    
                except (User.DoesNotExist, Member.DoesNotExist) if Member else User.DoesNotExist:
                    logger.warning(f"[API认证中间件] JWT令牌中的用户ID {user_id} 不存在或已被禁用")
                    # 返回401未授权响应
                    error_response = {
                        "success": False,
                        "code": 4001,
                        "message": "认证失败：用户不存在或已被禁用",
                        "data": None
                    }
                    
                    # 如果请求头中包含X-Debug-Log，则添加调试日志
                    if request.headers.get('X-Debug-Log') == 'true':
                        error_response["debug_logs"] = [{
                            "level": "error",
                            "message": f"[API认证中间件] JWT令牌中的用户ID {user_id} 不存在或已被禁用",
                            "timestamp": json.dumps(user_id),
                            "model_type": model_type
                        }]
                    
                    return JsonResponse(error_response, status=401)
                    
        except jwt.ExpiredSignatureError:
            logger.warning(f"[API认证中间件] JWT令牌已过期")
            # 返回401未授权响应
            error_response = {
                "success": False,
                "code": 4001,
                "message": "认证失败：令牌已过期，请重新登录",
                "data": None
            }
            
            # 如果请求头中包含X-Debug-Log，则添加调试日志
            if request.headers.get('X-Debug-Log') == 'true':
                error_response["debug_logs"] = [{
                    "level": "error",
                    "message": "[API认证中间件] JWT令牌已过期",
                    "timestamp": None,
                    "path": request.path
                }]
            
            return JsonResponse(error_response, status=401)
            
        except Exception as e:
            logger.warning(f"[API认证中间件] JWT令牌解析错误: {str(e)}")
            # 返回401未授权响应
            error_response = {
                "success": False,
                "code": 4001,
                "message": f"认证失败：令牌无效 ({str(e)})",
                "data": None
            }
            
            # 如果请求头中包含X-Debug-Log，则添加调试日志
            if request.headers.get('X-Debug-Log') == 'true':
                error_response["debug_logs"] = [{
                    "level": "error",
                    "message": f"[API认证中间件] JWT令牌解析错误: {str(e)}",
                    "timestamp": None,
                    "path": request.path,
                    "error": str(e)
                }]
            
            return JsonResponse(error_response, status=401)
            
        return None 