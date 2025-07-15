"""
租户中间件，用于处理请求中的租户上下文
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from django.http import JsonResponse
from common.utils.tenant_context import get_current_tenant, set_current_tenant, clear_current_tenant
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class TenantMiddleware(MiddlewareMixin):
    """
    租户中间件，用于从请求中提取租户信息并设置租户上下文
    
    处理以下租户信息来源:
    1. X-Tenant-ID 请求头
    2. 用户关联的租户
    
    权限控制规则：
    - GET请求允许匿名访问，但需要租户ID（从X-Tenant-ID或用户token获取）
    - 非GET请求需要认证，并且用户必须关联租户
    - 超级管理员可以通过X-Tenant-ID请求头指定租户进行操作
    - 只有URL路径中包含"cms"的API才需要进行租户ID验证
    """
    
    def process_request(self, request):
        """
        处理请求，设置当前租户
        
        Args:
            request: HTTP请求对象
        
        Returns:
            None
        """
        # 清除之前的租户上下文
        clear_current_tenant()
        
        # 检查请求路径是否包含"cms"，如果不包含，则不需要进行租户验证
        if "/cms/" not in request.path:
            logger.debug(f"非CMS路径，跳过租户验证: {request.path}")
            return None
        
        logger.info(f"[租户中间件] 开始处理路径: {request.path}, 方法: {request.method}")
        
        # 记录当前用户认证类型，帮助调试
        auth_type = getattr(request, 'auth_type', 'unknown')
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(f"[租户中间件] 用户已认证 - {request.user.username}, 认证类型: {auth_type}, 用户ID: {request.user.id}")
            logger.info(f"[租户中间件] 用户详情 - 超管: {getattr(request.user, 'is_super_admin', False)}, 管理员: {getattr(request.user, 'is_admin', False)}")
            
            # 记录用户租户信息
            user_tenant = getattr(request.user, 'tenant', None)
            if user_tenant:
                logger.info(f"[租户中间件] 用户关联的租户: ID={user_tenant.id}, 名称={user_tenant.name}, 状态={user_tenant.status}")
            else:
                logger.warning(f"[租户中间件] 用户 {request.user.username} 未关联租户")
        else:
            logger.info("[租户中间件] 用户未认证")
        
        # 从请求头获取租户ID并验证
        header_tenant_id = request.headers.get('X-Tenant-ID')
        logger.info(f"[租户中间件] 从请求头获取的X-Tenant-ID: {header_tenant_id}")
        
        # 验证租户ID是否为有效整数
        if header_tenant_id:
            try:
                header_tenant_id = int(header_tenant_id)
                # 转换为字符串以便后续比较
                header_tenant_id = str(header_tenant_id)
                logger.info(f"[租户中间件] 从请求头获取到有效租户ID: {header_tenant_id}")
            except (ValueError, TypeError):
                logger.warning(f"[租户中间件] 无效的租户ID格式: {header_tenant_id}")
                raise ValidationError({"detail": f"无效的租户ID格式: {header_tenant_id}，租户ID必须是整数"})
        
        # 获取用户关联的租户
        user_tenant = None
        user_tenant_id = None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_tenant = getattr(request.user, 'tenant', None)
            user_tenant_id = str(user_tenant.id) if user_tenant else None
            if user_tenant:
                logger.info(f"[租户中间件] 用户关联的租户ID: {user_tenant_id}, 租户名称: {user_tenant.name}")
            else:
                logger.info(f"[租户中间件] 用户 {request.user.username} 未关联租户")
        
        # 确定最终使用的租户ID
        # 检查用户类型
        is_super_admin = False
        is_tenant_admin = False
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            # 明确检查用户类型，避免错误识别
            # 只有通过JWT认证的用户才能被识别为超级管理员
            if getattr(request, 'auth_type', None) == 'jwt':
                is_super_admin = getattr(request.user, 'is_super_admin', False)
                is_tenant_admin = (getattr(request.user, 'is_admin', False) and not is_super_admin)
                logger.info(f"[租户中间件] JWT认证用户类型检查 - 用户名: {request.user.username}, 超级管理员: {is_super_admin}, 租户管理员: {is_tenant_admin}")
            else:
                # 对于非JWT认证的用户，如会话认证，不信任其超级管理员标识
                logger.info(f"[租户中间件] 非JWT认证用户 {request.user.username}，不信任超级管理员标识")
                is_super_admin = False
                is_tenant_admin = False
        
        # 如果是租户管理员且没有提供X-Tenant-ID，则使用其关联的租户ID
        if is_tenant_admin and not header_tenant_id and user_tenant_id:
            effective_tenant_id = user_tenant_id
            logger.info(f"[租户中间件] 租户管理员 {request.user.username} 未提供X-Tenant-ID，自动使用关联的租户ID: {effective_tenant_id}")
        else:
            # 优先使用用户关联的租户ID，如果没有则使用请求头中的租户ID
            effective_tenant_id = user_tenant_id or header_tenant_id
            logger.info(f"[租户中间件] 最终使用的租户ID: {effective_tenant_id}, 来源: {'用户关联' if user_tenant_id else '请求头' if header_tenant_id else '无'}")
        
        # 处理GET请求（允许匿名访问，但需要租户ID）
        if request.method == 'GET':
            # 超级管理员特殊处理：即使是GET请求，如果没有提供租户ID，也需要提示
            # 重新确认用户是否是通过JWT认证的超级管理员
            is_super_admin = False
            if hasattr(request, 'user') and request.user.is_authenticated and getattr(request, 'auth_type', None) == 'jwt':
                is_super_admin = getattr(request.user, 'is_super_admin', False)
            
            # 如果没有有效的租户ID，返回错误（超级管理员除外）
            if not effective_tenant_id:
                if is_super_admin:
                    # 超级管理员需要明确指定租户ID
                    logger.warning(f"[租户中间件] 超级管理员 {request.user.username} GET请求未提供租户ID: {request.path}")
                    
                    # 返回标准JSON错误响应
                    error_response = {
                        "success": False,
                        "code": 4001,
                        "message": "超级管理员需要通过X-Tenant-ID请求头指定租户ID",
                        "data": None
                    }
                    
                    # 如果请求头中包含X-Debug-Log，则添加调试日志
                    if request.headers.get('X-Debug-Log') == 'true':
                        error_response["debug_logs"] = [{
                            "level": "error",
                            "message": f"[租户中间件] 超级管理员 {request.user.username} GET请求未提供租户ID: {request.path}",
                            "timestamp": time.time(),
                            "path": request.path,
                            "user": request.user.username,
                            "is_super_admin": True
                        }]
                    
                    return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.warning(f"[租户中间件] GET请求未提供租户ID: {request.path}")
                    
                    # 返回标准JSON错误响应
                    error_response = {
                        "success": False,
                        "code": 4001,
                        "message": "未提供租户ID，无法访问CMS资源",
                        "data": None
                    }
                    
                    # 如果请求头中包含X-Debug-Log，则添加调试日志
                    if request.headers.get('X-Debug-Log') == 'true':
                        error_response["debug_logs"] = [{
                            "level": "error",
                            "message": f"[租户中间件] GET请求未提供租户ID: {request.path}",
                            "timestamp": time.time(),
                            "path": request.path,
                            "user": getattr(request.user, 'username', 'anonymous')
                        }]
                    
                    return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
        # 处理非GET请求（需要认证和关联租户）
        else:
            # 检查用户是否已认证
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                logger.warning(f"[租户中间件] 未认证用户尝试执行非GET请求: {request.path}")
                # 这里不抛出异常，让后续的认证中间件处理
                return None
            
            # 超级管理员特殊处理：允许通过X-Tenant-ID请求头指定租户进行操作
            # 重新检查用户是否是超级管理员，只信任JWT认证的超级管理员
            is_super_admin = False
            if getattr(request, 'auth_type', None) == 'jwt':
                is_super_admin = getattr(request.user, 'is_super_admin', False)
                logger.info(f"[租户中间件] 非GET请求JWT用户类型检查 - 用户名: {request.user.username}, 超级管理员: {is_super_admin}")
            else:
                logger.info(f"[租户中间件] 非GET请求非JWT认证用户 {request.user.username}，不信任超级管理员标识")
            
            if is_super_admin:
                logger.info(f"[租户中间件] 检测到超级管理员: {request.user.username}")
                if header_tenant_id:
                    logger.info(f"[租户中间件] 超级管理员 {request.user.username} 通过请求头指定租户ID: {header_tenant_id}")
                    effective_tenant_id = header_tenant_id
                    # 为超级管理员临时设置租户上下文，但不改变其用户数据
                    from tenants.models import Tenant
                    try:
                        temp_tenant = Tenant.objects.get(id=int(header_tenant_id))
                        set_current_tenant(temp_tenant)
                        request.tenant_id = header_tenant_id
                        logger.info(f"[租户中间件] 已为超级管理员 {request.user.username} 设置临时租户上下文: {temp_tenant.name} (ID: {header_tenant_id})")
                        return None
                    except Tenant.DoesNotExist:
                        logger.warning(f"[租户中间件] 超级管理员指定的租户ID不存在: {header_tenant_id}")
                        
                        # 返回标准JSON错误响应
                        error_response = {
                            "success": False,
                            "code": 4001,
                            "message": f"指定的租户ID不存在: {header_tenant_id}",
                            "data": None
                        }
                        
                        # 如果请求头中包含X-Debug-Log，则添加调试日志
                        if request.headers.get('X-Debug-Log') == 'true':
                            error_response["debug_logs"] = [{
                                "level": "error",
                                "message": f"[租户中间件] 超级管理员指定的租户ID不存在: {header_tenant_id}",
                                "timestamp": time.time(),
                                "path": request.path,
                                "user": request.user.username,
                                "is_super_admin": True,
                                "tenant_id": header_tenant_id
                            }]
                        
                        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.warning(f"[租户中间件] 超级管理员 {request.user.username} 尝试执行CMS操作但未指定租户ID")
                    
                    # 返回标准JSON错误响应
                    error_response = {
                        "success": False,
                        "code": 4001,
                        "message": "超级管理员需要通过X-Tenant-ID请求头指定租户ID，即使是GET请求也需要",
                        "data": None
                    }
                    
                    # 如果请求头中包含X-Debug-Log，则添加调试日志
                    if request.headers.get('X-Debug-Log') == 'true':
                        error_response["debug_logs"] = [{
                            "level": "error",
                            "message": f"[租户中间件] 超级管理员 {request.user.username} 尝试执行CMS操作但未指定租户ID",
                            "timestamp": time.time(),
                            "path": request.path,
                            "user": request.user.username,
                            "is_super_admin": True,
                            "method": request.method
                        }]
                    
                    return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
            
            # 普通用户检查是否关联租户
            if not user_tenant:
                logger.warning(f"[租户中间件] 用户 {request.user.username} 未关联租户，尝试执行非GET请求: {request.path}")
                
                # 返回标准JSON错误响应
                error_response = {
                    "success": False,
                    "code": 4003,
                    "message": "用户未关联租户，无法执行修改操作",
                    "data": None
                }
                
                # 如果请求头中包含X-Debug-Log，则添加调试日志
                if request.headers.get('X-Debug-Log') == 'true':
                    error_response["debug_logs"] = [{
                        "level": "error",
                        "message": f"[租户中间件] 用户 {request.user.username} 未关联租户，尝试执行非GET请求: {request.path}",
                        "timestamp": time.time(),
                        "path": request.path,
                        "user": request.user.username,
                        "method": request.method
                    }]
                
                return JsonResponse(error_response, status=status.HTTP_403_FORBIDDEN)
        
        # 如果请求头中有租户ID，验证与用户租户是否匹配
        if header_tenant_id and user_tenant_id and header_tenant_id != user_tenant_id:
            # 只有非超级管理员才需要验证租户匹配
            if not is_super_admin:
                logger.warning(f"[租户中间件] 用户 {request.user.username} 尝试访问不属于其租户的资源，租户ID不匹配: 用户租户={user_tenant_id}, 请求头租户={header_tenant_id}")
                
                # 返回标准JSON错误响应
                error_response = {
                    "success": False,
                    "code": 4003,
                    "message": "无法访问其他租户的资源",
                    "data": None
                }
                
                # 如果请求头中包含X-Debug-Log，则添加调试日志
                if request.headers.get('X-Debug-Log') == 'true':
                    error_response["debug_logs"] = [{
                        "level": "error",
                        "message": f"[租户中间件] 用户 {request.user.username} 尝试访问不属于其租户的资源，租户ID不匹配: 用户租户={user_tenant_id}, 请求头租户={header_tenant_id}",
                        "timestamp": time.time(),
                        "path": request.path,
                        "user": request.user.username,
                        "user_tenant_id": user_tenant_id,
                        "header_tenant_id": header_tenant_id
                    }]
                
                return JsonResponse(error_response, status=status.HTTP_403_FORBIDDEN)
        
        # 将租户ID保存到请求对象，方便视图使用
        request.tenant_id = effective_tenant_id
        logger.info(f"[租户中间件] 已设置请求的tenant_id: {effective_tenant_id}")
        
        # 设置当前线程的租户上下文
        if user_tenant:
            logger.info(f"[租户中间件] 用户 {request.user.username} 属于租户 {user_tenant.name}, 已设置租户上下文")
            set_current_tenant(user_tenant)
        elif header_tenant_id:
            # 如果有请求头租户ID但没有用户租户，尝试设置租户上下文
            from tenants.models import Tenant
            try:
                temp_tenant = Tenant.objects.get(id=int(header_tenant_id))
                logger.info(f"[租户中间件] 从请求头设置租户上下文: {temp_tenant.name} (ID: {header_tenant_id})")
                set_current_tenant(temp_tenant)
            except Tenant.DoesNotExist:
                logger.warning(f"[租户中间件] 请求头指定的租户ID不存在: {header_tenant_id}")
        
        return None
    
    def process_response(self, request, response):
        """
        处理响应，清除当前租户
        
        Args:
            request: HTTP请求对象
            response: HTTP响应对象
        
        Returns:
            HTTP响应对象
        """
        # 请求结束后清除租户上下文
        clear_current_tenant()
        return response