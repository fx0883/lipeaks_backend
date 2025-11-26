"""
Member用户文章管理视图
"""
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse, OpenApiTypes
import logging
from rest_framework import serializers

from common.viewsets import TenantModelViewSet
from common.pagination import StandardResultsSetPagination
from common.utils.user_permissions import is_member
from users.models import Member
from .models import (
    Article, ArticleCategory, ArticleTag, ArticleMeta,
    ArticleStatistics, OperationLog
)
from .serializers import (
    ArticleListSerializer, ArticleDetailSerializer, MemberArticleCreateUpdateSerializer
)
from .permissions import ArticlePermission

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="[Member] 获取我的文章列表",
        description="Member用户获取自己创建的文章列表，支持分页、过滤和搜索",
        tags=["CMS-Member文章管理"],
        parameters=[
            OpenApiParameter(name="page", description="页码，默认1", required=False, type=int),
            OpenApiParameter(name="status", description="文章状态过滤", required=False, type=str, enum=["draft", "pending", "published", "archived"]),
            OpenApiParameter(name="search", description="搜索关键词，在标题和内容中匹配", required=False, type=str),
            OpenApiParameter(name="sort", description="排序字段，默认created_at", required=False, type=str, 
                             enum=["created_at", "updated_at", "published_at", "title"]),
            OpenApiParameter(name="sort_direction", description="排序方向，默认desc", required=False, type=str, enum=["asc", "desc"]),
            OpenApiParameter(name="application", description="应用ID过滤，可选", required=False, type=int),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        examples=[
            OpenApiExample(
                'List My Articles Example',
                summary='获取我的文章列表示例',
                description='获取当前Member用户的文章列表',
                value={
                    'page': 1,
                    'status': 'published',
                    'search': '示例文章'
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary="[Member] 获取我的单篇文章",
        description="获取当前Member用户的单篇文章详情",
        tags=["CMS-Member文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        examples=[
            OpenApiExample(
                'Retrieve My Article Example',
                summary='获取我的单篇文章示例',
                description='获取ID为1的文章详情',
                value={
                    'id': 1
                }
            )
        ]
    ),
    create=extend_schema(
        summary="[Member] 创建文章",
        description="Member用户创建新文章",
        tags=["CMS-Member文章管理"],
        request=MemberArticleCreateUpdateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: ArticleDetailSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Create Article Example',
                summary='创建文章示例',
                description='Member用户创建一篇新文章',
                value={
                    'title': '我的第一篇文章',
                    'content': '这是文章内容...',
                    'content_type': 'markdown',
                    'excerpt': '文章摘要',
                    'status': 'draft',
                    'application': 6,
                    'category_ids': [2, 5],
                    'tag_ids': [3, 8],
                    'visibility': 'public',
                    'allow_comment': True
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        summary="[Member] 更新文章",
        description="Member用户更新自己的文章",
        tags=["CMS-Member文章管理"],
        request=MemberArticleCreateUpdateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: ArticleDetailSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        },
        examples=[
            OpenApiExample(
                'Update Article Example',
                summary='更新文章示例',
                description='Member用户更新文章内容',
                value={
                    'title': '更新后的标题',
                    'content': '更新后的内容...',
                    'status': 'published'
                },
                request_only=True,
            )
        ]
    ),
    partial_update=extend_schema(
        summary="[Member] 部分更新文章",
        description="Member用户部分更新自己的文章",
        tags=["CMS-Member文章管理"],
        request=MemberArticleCreateUpdateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: ArticleDetailSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        }
    ),
    destroy=extend_schema(
        summary="[Member] 删除文章",
        description="Member用户删除自己的文章（软删除，设置状态为archived）",
        tags=["CMS-Member文章管理"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        }
    ),
)
class MemberArticleViewSet(TenantModelViewSet):
    """
    Member用户文章管理ViewSet
    
    提供Member用户的文章CRUD功能
    - 只能操作自己创建的文章
    - 支持草稿、发布、归档等状态管理
    """
    queryset = Article.objects.all()
    permission_classes = [ArticlePermission]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        获取查询集
        
        Member用户只能看到自己创建的文章
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Member用户只能看到自己的文章
        if is_member(user):
            queryset = queryset.filter(member_id=user.id)
        
        # 优化查询：预加载member关系
        queryset = queryset.select_related('member', 'tenant')
        
        # 处理搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        
        # 处理状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 处理应用过滤（可选）
        application = self.request.query_params.get('application')
        if application:
            from .models import ArticleApplication
            article_ids = ArticleApplication.objects.filter(
                application_id=application
            ).values_list('article_id', flat=True)
            queryset = queryset.filter(id__in=article_ids)
        
        # 处理排序
        sort = self.request.query_params.get('sort', 'created_at')
        sort_direction = self.request.query_params.get('sort_direction', 'desc')
        
        order_field = f"-{sort}" if sort_direction == 'desc' else sort
        queryset = queryset.order_by(order_field)
        
        return queryset
    
    def get_serializer_class(self):
        """
        根据请求方法返回不同的序列化器
        """
        if self.action == 'list':
            return ArticleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MemberArticleCreateUpdateSerializer
        else:
            return ArticleDetailSerializer
    
    def perform_create(self, serializer):
        """
        创建文章时设置作者为当前Member用户
        """
        user = self.request.user
        
        # 确保是Member用户
        if not isinstance(user, Member):
            raise serializers.ValidationError(_("只有Member用户可以通过此接口创建文章"))
        
        # 设置member字段为当前Member用户
        serializer.save(member=user)
        
        # 记录操作日志
        self._record_operation_log('create', serializer.instance)
    
    def perform_update(self, serializer):
        """
        更新文章
        """
        user = self.request.user
        instance = self.get_object()
        
        # 确保是文章作者（直接检查member_id更高效）
        if instance.member_id != user.id:
            raise serializers.ValidationError(_("你只能编辑自己的文章"))
        
        # 更新文章
        article = serializer.save()
        
        # 记录操作日志
        self._record_operation_log('update', article)
        
        return article
    
    def perform_destroy(self, instance):
        """
        删除文章（软删除）
        """
        user = self.request.user
        
        # 确保是文章作者（直接检查member_id更高效）
        if instance.member_id != user.id:
            raise serializers.ValidationError(_("你只能删除自己的文章"))
        
        # 软删除：将状态改为archived
        instance.status = 'archived'
        instance.save(update_fields=['status'])
        
        # 记录操作日志
        self._record_operation_log('delete', instance)
    
    def _record_operation_log(self, action, article):
        """
        记录文章操作日志（暂时跳过Member用户，因为OperationLog.user仅支持User类型）
        """
        user = self.request.user
        tenant = user.tenant
        
        # 暂时跳过Member用户的操作日志，因为OperationLog.user字段仅支持User类型
        # TODO: 升级OperationLog模型支持GenericForeignKey
        from users.models import User
        if not isinstance(user, User):
            logger.info(f"Member用户 {user.username} 执行了 {action} 操作，文章ID: {article.id}")
            return
        
        try:
            OperationLog.objects.create(
                user=user,
                action=action,
                entity_type='article',
                entity_id=article.id,
                details=f"用户{action}文章: {article.title}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录文章{action}操作日志失败: {str(e)}")
    
    @extend_schema(
        summary="[Member] 发布文章",
        description="将草稿文章发布",
        tags=["CMS-Member文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: ArticleDetailSerializer,
            400: OpenApiResponse(description="文章状态不允许发布"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        }
    )
    @action(detail=True, methods=['post'], url_path='publish')
    def publish_article(self, request, pk=None):
        """发布文章"""
        article = self.get_object()
        user = request.user
        
        # 确保是文章作者（直接检查member_id更高效）
        if article.member_id != user.id:
            return Response(
                {"detail": _("你只能发布自己的文章")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查文章状态
        if article.status not in ['draft', 'pending']:
            return Response(
                {"detail": _("只有草稿或待审核状态的文章可以发布")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 发布文章
        article.status = 'published'
        article.published_at = timezone.now()
        article.save(update_fields=['status', 'published_at'])
        
        # 记录操作日志
        self._record_operation_log('publish', article)
        
        # 返回成功响应
        serializer = self.get_serializer(article)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="[Member] 获取文章统计",
        description="获取文章的统计信息",
        tags=["CMS-Member文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(description="统计数据"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        }
    )
    @action(detail=True, methods=['get'], url_path='statistics')
    def get_statistics(self, request, pk=None):
        """获取文章统计信息"""
        article = self.get_object()
        user = request.user
        
        # 确保是文章作者（直接检查member_id更高效）
        if article.member_id != user.id:
            return Response(
                {"detail": _("你只能查看自己文章的统计信息")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 获取统计数据
        try:
            stats = ArticleStatistics.objects.get(article=article)
        except ArticleStatistics.DoesNotExist:
            stats = ArticleStatistics.objects.create(
                article=article,
                tenant=article.tenant
            )
        
        return Response({
            'views_count': stats.views_count,
            'unique_views_count': stats.unique_views_count,
            'likes_count': stats.likes_count,
            'comments_count': stats.comments_count,
            'shares_count': stats.shares_count,
            'bookmarks_count': stats.bookmarks_count
        })
