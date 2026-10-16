"""
API请求认证中间件

保留路径白名单，消除冗余双重JWT解码与查库，认证统一交由DRF视图层处理
"""
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class APIAuthMiddleware(MiddlewareMixin):
    """
    API请求认证中间件

    保留白名单路径过滤，实际JWT认证与查库交由DRF视图层认证类（APIJWTAuthentication）统一处理，
    消除中间件层冗余的二次JWT解码与数据库查询。
    """

    def process_request(self, request):
        logger.info(f"[进入中间件] APIAuthMiddleware - 处理请求: {request.path}")
        # 只处理API请求
        if not request.path.startswith('/api/'):
            logger.debug(f"非API路径，跳过JWT认证中间件: {request.path}")
            return None

        # 跳过静态文件和媒体文件的JWT认证
        if request.path.startswith(('/static/', '/media/')):
            logger.info(f"[API认证中间件] 静态/媒体资源路径，跳过JWT认证: {request.path}")
            return None

        # 跳过API文档的JWT认证
        if request.path.startswith(('/api/v1/schema/', '/api/v1/docs/', '/api/v1/redoc/')):
            logger.info(f"[API认证中间件] API文档路径，跳过JWT认证: {request.path}")
            return None

        # 跳过公开的表单页面（非API接口，是HTML页面）
        if request.path.startswith('/api/v1/feedbacks/submit'):
            logger.info(f"[API认证中间件] 公开表单页面，跳过JWT认证: {request.path}")
            return None

        # 跳过 Member 密码重置页面（公开HTML页面）
        if request.path.startswith('/api/v1/members/password-reset'):
            logger.info(f"[API认证中间件] 密码重置页面，跳过JWT认证: {request.path}")
            return None

        logger.info(f"[API认证中间件] 放行API请求至视图层认证: {request.path}")
        return None