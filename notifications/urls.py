"""
通知系统 URL 配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet
from .member_views import MemberNotificationViewSet

app_name = 'notifications'

# 管理端路由
admin_router = DefaultRouter()
admin_router.register('', NotificationViewSet, basename='notification')

# 成员端路由
member_router = DefaultRouter()
member_router.register('', MemberNotificationViewSet, basename='member-notification')

# 管理端 API: /api/v1/notifications/
urlpatterns = admin_router.urls

# 成员端 API: /api/v1/member/notifications/
member_urlpatterns = member_router.urls
