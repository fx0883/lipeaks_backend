"""
应用管理视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsTenantAdmin
from common.viewsets import TenantModelViewSet

from .models import Application
from .serializers import (
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationCreateSerializer,
    ApplicationStatisticsSerializer
)


class ApplicationViewSet(TenantModelViewSet):
    """
    应用管理ViewSet
    支持：列表、创建、详情、更新、删除、统计
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    
    权限：
    - GET请求：所有认证用户（包括member）
    - POST/PUT/PATCH/DELETE：仅租户管理员
    """
    permission_classes = [IsAuthenticated]
    queryset = Application.objects.all()
    
    def get_permissions(self):
        """根据操作类型设置权限"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # 写操作需要管理员权限
            return [IsAuthenticated(), IsTenantAdmin()]
        # 读操作只需要认证
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ApplicationCreateSerializer
        elif self.action == 'statistics':
            return ApplicationStatisticsSerializer
        return ApplicationDetailSerializer
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        获取应用统计信息
        GET /api/applications/{id}/statistics/
        """
        application = self.get_object()
        
        stats = {
            'licenses': {
                'total': application.get_license_count(),
                'active': application.get_active_license_count(),
            },
            'feedbacks': {
                'total': application.get_feedback_count(),
                'open': application.get_open_feedback_count(),
            },
            'articles': {
                'total': application.get_article_count(),
            }
        }
        
        serializer = ApplicationStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def articles(self, request, pk=None):
        """
        获取应用关联的文章
        GET /api/applications/{id}/articles/
        """
        from cms.models import Article
        from cms.serializers import ArticleListSerializer
        
        application = self.get_object()
        
        # 使用application的租户ID进行过滤
        articles = Article.objects.filter(
            tenant_id=application.tenant_id,
            articleapplication__application=application
        ).select_related('user', 'member')
        
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)


