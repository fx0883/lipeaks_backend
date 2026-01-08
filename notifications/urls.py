"""
通知系统 URL 配置 - 管理端
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet

app_name = 'notifications'

# 管理端路由
admin_router = DefaultRouter()
admin_router.register('', NotificationViewSet, basename='notification')

# 管理端 API: /api/v1/admin/notifications/
urlpatterns = admin_router.urls
