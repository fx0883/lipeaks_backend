"""
订单应用URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from orders.views import OrderViewSet, OrderHistoryViewSet, CustomerOrderViewSet, ContactOrderViewSet

# 应用名称，用于URL命名空间
app_name = 'orders'

# 主路由
router = DefaultRouter()

# 注意：路由注册顺序很重要，更具体的路径应该在前面
# 先注册特定路径的视图集
router.register(r'contacts/(?P<contact_id>\d+)/orders', ContactOrderViewSet, basename='contact-order')
router.register(r'customers/(?P<customer_id>\d+)/orders', CustomerOrderViewSet, basename='customer-order')
router.register(r'(?P<order_id>\d+)/history', OrderHistoryViewSet, basename='order-history')
# 最后注册通用路径的视图集
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
] 