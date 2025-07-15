"""
打卡系统URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TaskCategoryViewSet, TaskViewSet, 
    CheckRecordViewSet, TaskTemplateViewSet
)

# 设置应用命名空间
app_name = 'check-system'

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'task-categories', TaskCategoryViewSet, basename='task-category')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'check-records', CheckRecordViewSet, basename='check-record')
router.register(r'task-templates', TaskTemplateViewSet, basename='task-template')

# API URLs
urlpatterns = [
    path('', include(router.urls)),
]
