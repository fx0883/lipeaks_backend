"""
URL Configuration
"""
import logging
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from drf_spectacular.utils import extend_schema

# 导入admin模块，确保所有模型被注册
import core.admin

# 设置日志记录器
logger = logging.getLogger(__name__)

# 定义Spectacular视图类，添加日志记录
@extend_schema(
    summary="获取OpenAPI模式",
    description="获取API的OpenAPI 3.0标准模式定义",
    tags=["API文档"],
    responses={200: {}}
)
class LoggingSpectacularAPIView(SpectacularAPIView):
    def get(self, request, *args, **kwargs):
        logger.info("访问 SpectacularAPIView schema endpoint")
        try:
            response = super().get(request, *args, **kwargs)
            logger.info("Schema生成成功")
            return response
        except Exception as e:
            logger.error(f"Schema生成失败: {str(e)}", exc_info=True)
            raise

@extend_schema(
    summary="Swagger UI文档",
    description="使用Swagger UI展示API文档",
    tags=["API文档"],
    responses={200: {}}
)
class LoggingSpectacularSwaggerView(SpectacularSwaggerView):
    def get(self, request, *args, **kwargs):
        logger.info("访问 Swagger UI 文档页面")
        try:
            response = super().get(request, *args, **kwargs)
            logger.info("Swagger UI页面渲染成功")
            return response
        except Exception as e:
            logger.error(f"Swagger UI页面渲染失败: {str(e)}", exc_info=True)
            raise

@extend_schema(
    summary="ReDoc文档",
    description="使用ReDoc展示API文档",
    tags=["API文档"],
    responses={200: {}}
)
class LoggingSpectacularRedocView(SpectacularRedocView):
    def get(self, request, *args, **kwargs):
        logger.info("访问 ReDoc 文档页面")
        try:
            response = super().get(request, *args, **kwargs)
            logger.info("ReDoc页面渲染成功")
            return response
        except Exception as e:
            logger.error(f"ReDoc页面渲染失败: {str(e)}", exc_info=True)
            raise

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 文档查看应用路由
    path('docs/', include('docs_view.urls')),
    
    # API版本1路由
    path('api/v1/', include([
        # 认证相关路由
        path('auth/', include('users.urls.auth_urls', namespace='auth')),
        
        # 用户相关路由 - 更新为包含所有用户URL
        path('', include('users.urls')),
        
        # 租户相关路由
        path('tenants/', include('tenants.urls', namespace='tenants')),
        
        # RBAC权限系统路由
        path('rbac/', include('rbac.urls', namespace='rbac')),
        
        # 通用功能路由
        path('common/', include('common.urls', namespace='common')),
        
        # 打卡系统路由
        path('check-system/', include('check_system.urls', namespace='check-system')),
        
        # CMS系统路由
        path('cms/', include('cms.urls', namespace='cms')),
        
        # 菜单管理系统路由
        path('menus/', include('menus.urls', namespace='menus')),
        
        # 客户管理系统路由
        path('customers/', include('customers.urls', namespace='customers')),
        
        # 订单管理系统路由
        path('orders/', include('orders.urls', namespace='orders')),
        
        # 许可证系统路由
        path('licenses/', include('licenses.urls', namespace='licenses')),
        
        # 多租户积分系统路由
        path('points/', include('points.api.urls', namespace='points')),
        
        # 图表数据API
        path('admin/charts/', include('charts.urls', namespace='charts')),
        
        # API 文档
        path('schema/', LoggingSpectacularAPIView.as_view(), name='schema'),
        path('docs/', LoggingSpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('redoc/', LoggingSpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ])),
]

# 在开发环境中提供静态和媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 记录URL模式已加载
logger.info(f"已加载 {len(urlpatterns)} 个URL模式")