"""
打卡系统URL配置

路由设计:
- Admin API: /task-categories/, /tasks/, /check-records/, /task-templates/, /cycles/
- Member API: /member/themes/, /member/tasks/, /member/checkins/, /member/cycles/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TaskCategoryViewSet, TaskViewSet, 
    CheckRecordViewSet, TaskTemplateViewSet, CheckinCycleViewSet
)
from .member_views import (
    MemberThemeViewSet, MemberTaskViewSet,
    MemberCheckinViewSet, MemberCycleViewSet
)

# 设置应用命名空间
app_name = 'check-system'

# Admin 路由
router = DefaultRouter()
router.register(r'task-categories', TaskCategoryViewSet, basename='task-category')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'check-records', CheckRecordViewSet, basename='check-record')
router.register(r'task-templates', TaskTemplateViewSet, basename='task-template')
router.register(r'cycles', CheckinCycleViewSet, basename='checkin-cycle')

# Member 路由
router.register(r'member/themes', MemberThemeViewSet, basename='member-theme')
router.register(r'member/tasks', MemberTaskViewSet, basename='member-task')
router.register(r'member/checkins', MemberCheckinViewSet, basename='member-checkin')
router.register(r'member/cycles', MemberCycleViewSet, basename='member-cycle')

# API URLs
urlpatterns = [
    path('', include(router.urls)),
]
