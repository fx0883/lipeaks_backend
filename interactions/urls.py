"""
用户互动URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleFavoriteViewSet

router = DefaultRouter()
router.register(r'favorites', ArticleFavoriteViewSet, basename='article-favorite')

app_name = 'interactions'

urlpatterns = [
    path('', include(router.urls)),
]
