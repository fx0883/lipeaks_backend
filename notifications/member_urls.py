"""
通知系统成员端 URL 配置
"""
from rest_framework.routers import DefaultRouter

from .member_views import MemberNotificationViewSet

app_name = 'member-notifications'

router = DefaultRouter()
router.register('', MemberNotificationViewSet, basename='member-notification')

urlpatterns = router.urls
