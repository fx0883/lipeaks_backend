"""
用户互动URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleFavoriteViewSet, MemberLikeViewSet, MemberFollowViewSet, ArticleLikeViewSet

router = DefaultRouter()
router.register(r'favorites', ArticleFavoriteViewSet, basename='article-favorite')
router.register(r'likes', MemberLikeViewSet, basename='member-like')
router.register(r'follows', MemberFollowViewSet, basename='member-follow')
router.register(r'article-likes', ArticleLikeViewSet, basename='article-like')

app_name = 'interactions'

urlpatterns = [
    path('', include(router.urls)),
]
