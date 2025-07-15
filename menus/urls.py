"""
菜单应用URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from menus.views import MenuViewSet, AdminMenuViewSet, UserMenuViewSet, AdminRoutesView

# 应用名称，用于URL命名空间
app_name = 'menus'

# 主路由
router = DefaultRouter()

# 注意：路由注册顺序很重要，更具体的路径应该在前面
# 先注册特定路径的视图集
router.register(r'admins/(?P<user_id>\d+)/menus', AdminMenuViewSet, basename='admin-menu')
router.register(r'user', UserMenuViewSet, basename='user-menu')
# 最后注册通用路径的视图集
router.register(r'', MenuViewSet, basename='menu')

urlpatterns = [
    # 管理员菜单路由
    path('admin/routes/', AdminRoutesView.as_view(), name='admin-routes'),
    path('', include(router.urls)),
] 