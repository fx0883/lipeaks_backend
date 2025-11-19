"""
CMS系统视图
"""
from django.db.models import Q, Count, Avg
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import Http404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse, OpenApiTypes
import logging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.permissions import IsSuperAdmin, IsAdmin
from common.pagination import StandardResultsSetPagination
from common.authentication.jwt_auth import JWTAuthentication
from common.viewsets import TenantModelViewSet
from common.exceptions import CMSException, TenantException
from common.utils.user_permissions import (
    is_super_admin, is_admin, is_member, can_create_content,
    can_edit_content, can_delete_content, can_moderate_comments,
    filter_queryset_by_user_permissions
)
from users.models import User
from .models import (
    Article, Category, Tag, TagGroup, Comment, 
    ArticleCategory, ArticleTag, ArticleMeta,
    ArticleStatistics, ArticleVersion, Interaction,
    UserLevel, UserLevelRelation, AccessLog, OperationLog
)
from .serializers import (
    ArticleListSerializer, ArticleDetailSerializer, ArticleCreateUpdateSerializer,
    CategorySerializer, TagSerializer, TagGroupSerializer,
    CommentSerializer, ArticleVersionSerializer, ArticleMetaSerializer,
    ArticleStatisticsSerializer, InteractionSerializer
)
from .permissions import (
    ArticlePermission, CategoryPermission, TagPermission,
    CommentPermission, ArticleVersionPermission, ArticleMetaPermission,
    ArticleStatisticsPermission, InteractionPermission
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取文章列表",
        description="获取文章列表，支持分页、过滤和搜索",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="page", description="页码，默认1", required=False, type=int),
            OpenApiParameter(name="status", description="文章状态过滤", required=False, type=str, enum=["draft", "pending", "published", "archived"]),
            OpenApiParameter(name="category_id", description="按分类ID过滤", required=False, type=int),
            OpenApiParameter(name="tag_id", description="按标签ID过滤", required=False, type=int),
            OpenApiParameter(name="author_id", description="按作者ID过滤", required=False, type=int),
            OpenApiParameter(name="search", description="搜索关键词，在标题和内容中匹配", required=False, type=str),
            OpenApiParameter(name="sort", description="排序字段，默认published_at", required=False, type=str, 
                             enum=["created_at", "updated_at", "published_at", "title", "views_count"]),
            OpenApiParameter(name="sort_direction", description="排序方向，默认desc", required=False, type=str, enum=["asc", "desc"]),
            OpenApiParameter(name="is_featured", description="是否只返回特色文章", required=False, type=bool),
            OpenApiParameter(name="is_pinned", description="是否只返回置顶文章", required=False, type=bool),
            OpenApiParameter(name="visibility", description="可见性过滤", required=False, type=str, enum=["public", "private", "password"]),
            OpenApiParameter(name="date_from", description="发布日期起始，格式YYYY-MM-DD", required=False, type=str),
            OpenApiParameter(name="date_to", description="发布日期截止，格式YYYY-MM-DD", required=False, type=str),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        examples=[
            OpenApiExample(
                'List Articles Example',
                summary='获取文章列表示例',
                description='获取文章列表，支持分页、过滤和搜索',
                value={
                    'page': 1,
                    'status': 'published',
                    'category_id': 3,
                    'search': '示例文章'
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary="获取单篇文章",
        description="通过ID获取单篇文章的详细信息",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="password", description="访问密码，当文章可见性为password时需提供", required=False, type=str),
            OpenApiParameter(name="version", description="文章版本号，默认返回最新版本", required=False, type=int),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        examples=[
            OpenApiExample(
                'Retrieve Article Example',
                summary='获取单篇文章示例',
                description='获取ID为1的文章详情',
                value={
                    'id': 1
                }
            )
        ]
    ),
    create=extend_schema(
        summary="创建文章",
        description="创建新文章，需要提供标题和内容",
        tags=["CMS-文章管理"],
        request=ArticleCreateUpdateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
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
                description='创建一篇新文章',
                value={
                    'title': '示例文章标题',
                    'content': '文章详细内容...',
                    'content_type': 'markdown',
                    'excerpt': '文章摘要...',
                    'status': 'draft',
                    'category_ids': [2, 5],
                    'tag_ids': [3, 8, 12],
                    'meta': {
                        'seo_title': 'SEO标题',
                        'seo_description': 'SEO描述'
                    }
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        summary="更新文章",
        description="更新现有文章的所有字段",
        tags=["CMS-文章管理"],
        request=ArticleCreateUpdateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
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
                description='更新现有文章的内容和元数据',
                value={
                    'title': '更新后的文章标题',
                    'content': '更新后的文章内容...',
                    'category_ids': [2, 7],
                    'tag_ids': [3, 9],
                    'create_new_version': True,
                    'change_description': '更新了文章内容和标签'
                },
                request_only=True,
            )
        ]
    ),
    partial_update=extend_schema(
        summary="部分更新文章",
        description="更新现有文章的部分字段",
        tags=["CMS-文章管理"],
        request=ArticleCreateUpdateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: ArticleDetailSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        },
        examples=[
            OpenApiExample(
                'Partial Update Article Example',
                summary='部分更新文章示例',
                description='只更新文章的状态和特色标记',
                value={
                    'status': 'published',
                    'is_featured': True,
                    'publish_now': True
                },
                request_only=True,
            )
        ]
    ),
    destroy=extend_schema(
        summary="删除文章",
        description="删除指定ID的文章",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="force", description="是否强制删除，默认false (false时为软删除)", required=False, type=bool),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        }
    ),
    batch_delete=extend_schema(
        summary="批量删除文章",
        description="批量删除多篇文章",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'article_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': '要删除的文章ID列表'
                    },
                    'force': {
                        'type': 'boolean',
                        'description': '是否强制删除，默认false'
                    }
                },
                'required': ['article_ids']
            }
        },
        responses={
            200: OpenApiResponse(description="批量删除成功"),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Batch Delete Articles Example',
                summary='批量删除文章示例',
                description='批量删除多篇文章',
                value={
                    'article_ids': [1, 2, 3],
                    'force': False
                },
                request_only=True,
            )
        ]
    ),
)
class ArticleViewSet(TenantModelViewSet):
    """
    文章视图集，提供增删改查API

    继承自TenantModelViewSet，自动处理租户隔离
    支持按作者类型过滤：author_type=member（Member作者）或author_type=admin（管理员作者）
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [ArticlePermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'status', 'visibility', 'is_featured', 'is_pinned', 'content_type']
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['created_at', 'updated_at', 'published_at', 'title']
    ordering = ['-is_pinned', '-created_at']
    queryset = Article.objects.all().select_related('user', 'member', 'tenant')  # 优化查询：预加载user和member
    
    def get_queryset(self):
        """
        获取文章查询集，支持多种过滤条件

        已通过TenantModelViewSet处理租户过滤
        支持的查询参数：
        - author_type: 按作者类型过滤 ('member' 或 'admin')
        - status: 按状态过滤
        - content_type: 按内容类型过滤
        - category_id: 按分类过滤
        - tag_id: 按标签过滤
        - user_id/member_id: 按具体作者过滤
        - has_parent: 按是否有父文章过滤
        - date_from/date_to: 按日期范围过滤
        """
        # 获取基础查询集，已经按照租户过滤
        queryset = super().get_queryset()
        
        # 处理状态过滤
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # 处理分类过滤
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(article_categories__category_id=category_id)
        
        # 处理标签过滤
        tag_id = self.request.query_params.get('tag_id')
        if tag_id:
            queryset = queryset.filter(article_tags__tag_id=tag_id)
        
        # 处理作者过滤（支持user_id和member_id）
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        member_id = self.request.query_params.get('member_id')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        
        # 兼容旧的author_id参数（同时搜索user_id和member_id）
        author_id = self.request.query_params.get('author_id')
        if author_id:
            queryset = queryset.filter(Q(user_id=author_id) | Q(member_id=author_id))

        # 处理作者类型过滤
        author_type = self.request.query_params.get('author_type')
        if author_type:
            if author_type == 'member':
                queryset = queryset.filter(member_id__isnull=False)
            elif author_type == 'admin':
                queryset = queryset.filter(user_id__isnull=False)
        
        # 处理特色和置顶过滤
        is_featured = self.request.query_params.get('is_featured')
        if is_featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        is_pinned = self.request.query_params.get('is_pinned')
        if is_pinned == 'true':
            queryset = queryset.filter(is_pinned=True)
        
        # 处理可见性过滤
        visibility = self.request.query_params.get('visibility')
        if visibility:
            queryset = queryset.filter(visibility=visibility)
        
        # 处理日期范围过滤
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(published_at__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(published_at__date__lte=date_to)
        
        # 处理排序
        sort = self.request.query_params.get('sort')
        sort_direction = self.request.query_params.get('sort_direction', 'desc')
        
        if sort:
            if sort == 'views_count':
                # 特殊处理浏览量排序，因为它在关联表中
                queryset = queryset.annotate(views=models.F('statistics__views_count'))
                order_field = 'views'
            else:
                order_field = sort
                
            if sort_direction == 'desc':
                order_field = f"-{order_field}"
                
            queryset = queryset.order_by(order_field)
        
        # 处理父文章过滤
        parent_id = self.request.query_params.get('parent_id')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        
        has_parent = self.request.query_params.get('has_parent')
        if has_parent == 'true':
            queryset = queryset.filter(parent__isnull=False)
        elif has_parent == 'false':
            queryset = queryset.filter(parent__isnull=True)
        
        return queryset
    
    def get_serializer_class(self):
        """
        根据请求方法返回不同的序列化器
        """
        if self.action == 'list':
            return ArticleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ArticleCreateUpdateSerializer
        else:
            return ArticleDetailSerializer
    
    def perform_create(self, serializer):
        """
        创建文章时设置作者为current用户
        
        租户ID已通过TenantModelViewSet自动处理
        """
        user = self.request.user
        
        # 检查用户是否有创建权限
        if not can_create_content(user):
            raise serializers.ValidationError(_("You do not have permission to create articles"))
        
        # 根据用户类型设置对应的外键字段
        from users.models import Member
        if isinstance(user, Member):
            serializer.save(member=user)
        else:
            serializer.save(user=user)
        
        # 记录操作日志
        self._record_operation_log('create', serializer.instance)
        
    def _process_relations(self, article, validated_data):
        """
        处理文章与分类、标签的关系
        
        Args:
            article: 文章实例
            validated_data: 验证后的数据
        """
        tenant = article.tenant
        
        # 处理分类关联
        if 'category_ids' in validated_data:
            # 删除旧关联
            ArticleCategory.objects.filter(article=article).delete()
            # 创建新关联
            for category_id in validated_data['category_ids']:
                ArticleCategory.objects.create(
                    article=article,
                    category_id=category_id,
                    tenant=tenant
                )
        
        # 处理标签关联
        if 'tag_ids' in validated_data:
            # 删除旧关联
            ArticleTag.objects.filter(article=article).delete()
            # 创建新关联
            for tag_id in validated_data['tag_ids']:
                ArticleTag.objects.create(
                    article=article,
                    tag_id=tag_id,
                    tenant=tenant
                )
                
    def _record_operation_log(self, action, article):
        """
        记录文章操作日志
        
        Args:
            action: 操作类型，如'create', 'update', 'delete'
            article: 文章实例
        """
        user = self.request.user
        tenant = user.tenant
        
        try:
            OperationLog.objects.create(
                user=user,
                action=action,
                entity_type='article',
                entity_id=article.id,
                details=f"{action}文章: {article.title}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录文章{action}操作日志失败: {str(e)}")
    
    def perform_update(self, serializer):
        """
        执行文章更新操作
        
        - 验证用户权限
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        instance = self.get_object()
        
        # 检查用户是否有编辑权限
        if not can_edit_content(user, instance.author):
            raise serializers.ValidationError(_("You do not have permission to edit this article"))
        
        # 验证作者权限（不允许修改user或member字段）
        if 'user' in serializer.validated_data or 'member' in serializer.validated_data:
            if not (is_super_admin(user) or is_admin(user)):
                raise serializers.ValidationError(_("You do not have permission to change article author"))
        
        # 更新文章
        article = serializer.save()
        
        # 记录操作日志
        try:
            # OperationLog只支持User类型，Member类型跳过
            from users.models import User as AdminUser
            if isinstance(user, AdminUser):
                OperationLog.objects.create(
                    user=user,
                    action='update',
                    entity_type='article',
                    entity_id=article.id,
                    details=f"更新文章: {article.title}",
                    ip_address=self.request.META.get('REMOTE_ADDR'),
                    user_agent=self.request.META.get('HTTP_USER_AGENT'),
                    tenant=tenant
                )
        except Exception as e:
            logger.error(f"记录文章更新操作日志失败: {str(e)}")
        
        return article
    
    def perform_destroy(self, instance):
        """
        执行文章删除操作
        
        - 支持软删除和强制删除
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 检查用户是否有删除权限
        if not can_delete_content(user, instance.author):
            raise serializers.ValidationError(_("You do not have permission to delete this article"))
        
        # 检查是否强制删除
        force_delete = self.request.query_params.get('force', 'false').lower() == 'true'
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='delete',
                entity_type='article',
                entity_id=instance.id,
                details=f"删除文章: {instance.title} (强制删除: {force_delete})",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录文章删除操作日志失败: {str(e)}")
        
        if force_delete:
            # 强制删除：真实删除数据库记录
            super().perform_destroy(instance)
        else:
            # 软删除：将状态改为archived
            instance.status = 'archived'
            instance.save(update_fields=['status'])
    
    @extend_schema(
        summary="获取文章版本历史",
        description="获取文章的所有历史版本",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: ArticleVersionSerializer(many=True),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        }
    )
    @action(detail=True, methods=['get'], url_path='versions')
    def versions(self, request, pk=None):
        """获取文章的所有历史版本"""
        article = self.get_object()
        versions = ArticleVersion.objects.filter(article=article).order_by('-version_number')
        serializer = ArticleVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取特定版本的文章内容",
        description="获取文章的指定版本内容",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="version_number", description="版本号", required=True, type=int, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: ArticleVersionSerializer,
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章或版本不存在"),
        }
    )
    @action(detail=True, methods=['get'], url_path='versions/(?P<version_number>[0-9]+)')
    def get_version(self, request, pk=None, version_number=None):
        """获取文章的指定版本"""
        article = self.get_object()
        try:
            version = ArticleVersion.objects.get(article=article, version_number=version_number)
        except ArticleVersion.DoesNotExist:
            return Response(
                {"detail": _("指定版本不存在")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ArticleVersionSerializer(version)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取文章统计数据",
        description="获取文章的详细统计数据，包括浏览量、点赞数等",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="period", description="统计周期", required=False, type=str, enum=["day", "week", "month", "year", "all"]),
            OpenApiParameter(name="start_date", description="统计起始日期，格式YYYY-MM-DD", required=False, type=str),
            OpenApiParameter(name="end_date", description="统计结束日期，格式YYYY-MM-DD", required=False, type=str),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(description="统计数据"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        }
    )
    @action(detail=True, methods=['get'], url_path='statistics')
    def statistics(self, request, pk=None):
        """获取文章的统计数据"""
        article = self.get_object()
        
        # 获取基础统计数据
        try:
            stats = ArticleStatistics.objects.get(article=article)
        except ArticleStatistics.DoesNotExist:
            # 如果统计记录不存在，创建一个空记录
            stats = ArticleStatistics.objects.create(
                article=article,
                tenant=article.tenant
            )
        
        # 基础统计数据
        basic_stats = {
            'views_count': stats.views_count,
            'unique_views_count': stats.unique_views_count,
            'likes_count': stats.likes_count,
            'dislikes_count': stats.dislikes_count,
            'comments_count': stats.comments_count,
            'shares_count': stats.shares_count,
            'bookmarks_count': stats.bookmarks_count,
            'avg_reading_time': stats.avg_reading_time,
            'bounce_rate': stats.bounce_rate
        }
        
        # 获取查询参数
        period = request.query_params.get('period', 'all')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # 根据周期过滤访问日志
        logs_query = AccessLog.objects.filter(article=article)
        
        if period != 'all':
            if period == 'day':
                logs_query = logs_query.filter(created_at__gte=timezone.now() - timezone.timedelta(days=1))
            elif period == 'week':
                logs_query = logs_query.filter(created_at__gte=timezone.now() - timezone.timedelta(weeks=1))
            elif period == 'month':
                logs_query = logs_query.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
            elif period == 'year':
                logs_query = logs_query.filter(created_at__gte=timezone.now() - timezone.timedelta(days=365))
        
        if start_date:
            logs_query = logs_query.filter(created_at__gte=start_date)
        
        if end_date:
            logs_query = logs_query.filter(created_at__lte=end_date)
        
        # 时间序列数据（按天统计）
        time_series_data = {}
        if logs_query.exists():
            # 按天分组统计访问量
            views_by_date = logs_query.values('check_date') \
                            .annotate(count=Count('id')) \
                            .order_by('check_date')
            
            time_series_data['views'] = [
                {'date': item['check_date'], 'count': item['count']} 
                for item in views_by_date
            ]
            
            # 地域分析
            countries = logs_query.values('country') \
                        .annotate(count=Count('id')) \
                        .order_by('-count')[:10]
            
            demographics = {
                'countries': [
                    {'name': item['country'] or _('未知'), 'count': item['count']} 
                    for item in countries
                ],
                'devices': [],
                'browsers': []
            }
            
            # 设备类型分析
            devices = logs_query.values('device') \
                     .annotate(count=Count('id')) \
                     .order_by('-count')[:5]
            demographics['devices'] = [
                {'name': item['device'] or _('未知'), 'count': item['count']} 
                for item in devices
            ]
            
            # 浏览器分析
            browsers = logs_query.values('browser') \
                      .annotate(count=Count('id')) \
                      .order_by('-count')[:5]
            demographics['browsers'] = [
                {'name': item['browser'] or _('未知'), 'count': item['count']} 
                for item in browsers
            ]
            
            # 来源分析
            referrers = logs_query.values('referer') \
                       .annotate(count=Count('id')) \
                       .order_by('-count')[:10]
            referrers_data = [
                {'source': item['referer'] or _('直接访问'), 'count': item['count']} 
                for item in referrers
            ]
        else:
            # 没有数据时返回空结果
            time_series_data = {'views': []}
            demographics = {
                'countries': [],
                'devices': [],
                'browsers': []
            }
            referrers_data = []
        
        # 返回完整统计数据
        response_data = {
            'basic_stats': basic_stats,
            'time_series': time_series_data,
            'demographics': demographics,
            'referrers': referrers_data
        }
        
        return Response(response_data)
    
    @extend_schema(
        summary="记录文章阅读",
        description="记录文章的阅读行为，更新阅读统计。不需要认证，每次调用将增加文章阅读数1次。",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(description="记录成功"),
            404: OpenApiResponse(description="文章不存在"),
        }
    )
    @action(detail=True, methods=['post'], url_path='view', permission_classes=[])
    def record_view(self, request, pk=None):
        """记录文章阅读行为"""
        article = self.get_object()
        
        # 创建访问日志
        access_log = AccessLog.objects.create(
            article=article,
            tenant=article.tenant,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # 更新文章统计
        try:
            stats, created = ArticleStatistics.objects.get_or_create(
                article=article,
                tenant=article.tenant
            )
            
            # 更新阅读次数
            stats.views_count += 1
            stats.save()
            
        except Exception as e:
            logger.error(f"更新文章统计数据失败: {str(e)}")
        
        return Response({"message": _("阅读记录已保存")}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="发布文章",
        description="""将文章状态改为已发布。
        
**权限要求**:
- 需要认证（登录）
- Member: 只能发布自己的文章
- Admin: 可以发布本租户所有文章
- Super Admin: 需通过X-Tenant-ID指定租户，可发布该租户文章

**业务规则**:
- 文章当前状态必须不是'published'
- 发布成功后自动设置published_at为当前时间
- 会记录操作日志

**使用场景**: Member创建草稿后，可以调用此接口将文章发布到前台展示
        """,
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="发布成功",
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'example': '文章已成功发布'},
                        'id': {'type': 'integer', 'example': 15},
                        'status': {'type': 'string', 'example': 'published'},
                        'published_at': {'type': 'string', 'format': 'date-time', 'example': '2024-01-20T10:30:00Z'}
                    }
                }
            ),
            400: OpenApiResponse(description="请求错误，例如文章已经是发布状态"),
            403: OpenApiResponse(description="权限不足，例如Member尝试发布别人的文章"),
            404: OpenApiResponse(description="文章不存在或不属于当前租户"),
        },
        examples=[
            OpenApiExample(
                'Publish Article Success',
                summary='发布文章成功示例',
                description='Member发布自己的文章',
                value={
                    'message': '文章已成功发布',
                    'id': 15,
                    'status': 'published',
                    'published_at': '2024-01-20T10:30:00Z'
                },
                response_only=True,
            )
        ]
    )
    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """发布文章"""
        article = self.get_object()
        user = request.user
        
        # 权限检查：Member只能发布自己的文章，Admin可以发布本租户所有文章
        if is_member(user) and article.author_id != user.id:
            return Response(
                {"detail": _("您只能发布自己创建的文章")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证文章是否已是发布状态
        if article.status == 'published':
            return Response(
                {"detail": _("文章已经是发布状态")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新文章状态为发布
        article.status = 'published'
        article.published_at = timezone.now()
        article.save(update_fields=['status', 'published_at'])
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='publish',
                entity_type='article',
                entity_id=article.id,
                details=f"发布文章: {article.title}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                tenant=article.tenant
            )
        except Exception as e:
            logger.error(f"记录文章发布操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _("文章已成功发布"),
                "id": article.id,
                "status": article.status,
                "published_at": article.published_at
            },
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="取消发布文章",
        description="""将文章状态从已发布改为草稿。
        
**权限要求**:
- 需要认证（登录）
- Member: 只能取消发布自己的文章
- Admin: 可以取消发布本租户所有文章
- Super Admin: 需通过X-Tenant-ID指定租户

**业务规则**:
- 文章当前状态必须是'published'
- 取消发布后状态变为'draft'（草稿）
- published_at时间戳保持不变
- 会记录操作日志

**使用场景**: Member发现文章有问题需要下线修改，可调用此接口将文章改为草稿
        """,
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="取消发布成功",
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'example': '文章已取消发布'},
                        'id': {'type': 'integer', 'example': 15},
                        'status': {'type': 'string', 'example': 'draft'}
                    }
                }
            ),
            400: OpenApiResponse(description="请求错误，例如文章不是发布状态"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        },
        examples=[
            OpenApiExample(
                'Unpublish Article Success',
                summary='取消发布成功示例',
                value={
                    'message': '文章已取消发布',
                    'id': 15,
                    'status': 'draft'
                },
                response_only=True,
            )
        ]
    )
    @action(detail=True, methods=['post'], url_path='unpublish')
    def unpublish(self, request, pk=None):
        """取消发布文章"""
        article = self.get_object()
        user = request.user
        
        # 权限检查：Member只能取消发布自己的文章
        if is_member(user) and article.author_id != user.id:
            return Response(
                {"detail": _("您只能取消发布自己创建的文章")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证文章是否为发布状态
        if article.status != 'published':
            return Response(
                {"detail": _("文章不是发布状态，无法取消发布")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新文章状态为草稿
        article.status = 'draft'
        article.save(update_fields=['status'])
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='unpublish',
                entity_type='article',
                entity_id=article.id,
                details=f"取消发布文章: {article.title}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                tenant=article.tenant
            )
        except Exception as e:
            logger.error(f"记录文章取消发布操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _("文章已取消发布"),
                "id": article.id,
                "status": article.status
            },
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="归档文章",
        description="""将文章状态改为归档。归档的文章不会在前台展示，但保留在数据库中。
        
**权限要求**:
- 需要认证（登录）
- Member: 只能归档自己的文章
- Admin: 可以归档本租户所有文章
- Super Admin: 需通过X-Tenant-ID指定租户

**业务规则**:
- 任何状态的文章都可以归档
- 归档后状态变为'archived'
- 归档的文章匿名用户无法访问
- 会记录操作日志

**使用场景**: Member想要隐藏过时或不再需要的文章，但又不想完全删除
        """,
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="归档成功",
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'example': '文章已归档'},
                        'id': {'type': 'integer', 'example': 15},
                        'status': {'type': 'string', 'example': 'archived'}
                    }
                }
            ),
            400: OpenApiResponse(description="请求错误，例如文章已经是归档状态"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="文章不存在"),
        },
        examples=[
            OpenApiExample(
                'Archive Article Success',
                summary='归档文章成功示例',
                value={
                    'message': '文章已归档',
                    'id': 15,
                    'status': 'archived'
                },
                response_only=True,
            )
        ]
    )
    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        """归档文章"""
        article = self.get_object()
        user = request.user
        
        # 权限检查：Member只能归档自己的文章
        if is_member(user) and article.author_id != user.id:
            return Response(
                {"detail": _("您只能归档自己创建的文章")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证文章是否已是归档状态
        if article.status == 'archived':
            return Response(
                {"detail": _("文章已经是归档状态")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新文章状态为归档
        article.status = 'archived'
        article.save(update_fields=['status'])
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='archive',
                entity_type='article',
                entity_id=article.id,
                details=f"归档文章: {article.title}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                tenant=article.tenant
            )
        except Exception as e:
            logger.error(f"记录文章归档操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _("文章已归档"),
                "id": article.id,
                "status": article.status
            },
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="批量删除文章",
        description="批量删除多篇文章",
        tags=["CMS-文章管理"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'article_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': '要删除的文章ID列表'
                    },
                    'force': {
                        'type': 'boolean',
                        'description': '是否强制删除，默认false'
                    }
                },
                'required': ['article_ids']
            }
        },
        responses={
            200: OpenApiResponse(description="批量删除成功"),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Batch Delete Articles Example',
                summary='批量删除文章示例',
                description='批量删除多篇文章',
                value={
                    'article_ids': [1, 2, 3],
                    'force': False
                },
                request_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='batch-delete')
    def batch_delete(self, request):
        """批量删除文章"""
        user = request.user
        tenant = user.tenant
        
        # 获取要删除的文章ID列表
        article_ids = request.data.get('article_ids', [])
        if not article_ids:
            return Response(
                {"detail": _("未提供要删除的文章ID")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文章ID列表格式
        try:
            article_ids = [int(article_id) for article_id in article_ids]
        except (ValueError, TypeError):
            return Response(
                {"detail": _("文章ID列表格式错误，必须是整数列表")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查是否强制删除
        force_delete = request.data.get('force', False)
        
        # 获取租户ID并验证
        tenant_id = getattr(request, 'tenant_id', None)
        if tenant_id:
            try:
                tenant_id = int(tenant_id)
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                raise TenantException(
                    error_code='INVALID_TENANT_ID',
                    detail=f'无效的租户ID格式: {tenant_id}',
                    tenant_id=tenant_id
                )
        
        # 根据权限获取可操作的文章
        if is_super_admin(user):
            articles = Article.objects.filter(id__in=article_ids)
        elif is_admin(user):
            articles = Article.objects.filter(id__in=article_ids, tenant_id=tenant_id)
        else:
            articles = Article.objects.filter(id__in=article_ids, tenant_id=tenant_id, author=user)
        
        # 统计找到的文章数量
        found_count = articles.count()
        if found_count == 0:
            return Response(
                {"detail": _("未找到可删除的文章")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 处理删除操作
        if force_delete:
            # 真实删除
            deleted_ids = list(articles.values_list('id', flat=True))
            deleted_titles = list(articles.values_list('title', flat=True))
            articles.delete()
        else:
            # 软删除
            deleted_ids = list(articles.values_list('id', flat=True))
            deleted_titles = list(articles.values_list('title', flat=True))
            articles.update(status='archived')
        
        # 记录操作日志
        for i, article_id in enumerate(deleted_ids):
            try:
                OperationLog.objects.create(
                    user=user,
                    action='delete',
                    entity_type='article',
                    entity_id=article_id,
                    details=f"批量删除文章: {deleted_titles[i]} (强制删除: {force_delete})",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    tenant=tenant
                )
            except Exception as e:
                logger.error(f"记录文章批量删除操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _("文章批量删除成功"),
                "requested_count": len(article_ids),
                "deleted_count": found_count,
                "deleted_ids": deleted_ids
            },
            status=status.HTTP_200_OK
        )

@extend_schema_view(
    list=extend_schema(
        summary="获取分类列表",
        description="获取文章分类列表，支持分页、过滤和搜索。默认按置顶、排序、名称排序。",
        tags=["CMS-分类管理"],
        parameters=[
            OpenApiParameter(name="parent", description="父分类ID", required=False, type=int),
            OpenApiParameter(name="is_active", description="是否激活", required=False, type=bool),
            OpenApiParameter(name="is_pinned", description="是否置顶", required=False, type=bool),
            OpenApiParameter(name="search", description="搜索关键词", required=False, type=str),
            OpenApiParameter(name="ordering", description="排序字段（可选：sort_order, name, created_at, is_pinned）", required=False, type=str),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CategorySerializer(many=True),
            403: OpenApiResponse(description="权限不足"),
        }
    ),
    retrieve=extend_schema(
        summary="获取分类详情",
        description="获取单个分类的详细信息",
        tags=["CMS-分类管理"],
        parameters=[
            OpenApiParameter(name="id", description="分类ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CategorySerializer,
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="分类不存在"),
        }
    ),
    create=extend_schema(
        summary="创建分类",
        description="创建新的文章分类",
        tags=["CMS-分类管理"],
        request=CategorySerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: CategorySerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Create Category Example',
                summary='创建分类示例',
                description='创建一个新的文章分类',
                value={
                    'name': '技术博客',
                    'slug': 'tech-blog',
                    'description': '技术相关的文章分类',
                    'parent': None,
                    'cover_image': 'https://example.com/images/tech.jpg',
                    'is_active': True,
                    'is_pinned': False,
                    'seo_title': '技术博客 - 分享技术知识',
                    'seo_description': '分享最新的技术知识和教程'
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        summary="更新分类",
        description="更新现有的文章分类",
        tags=["CMS-分类管理"],
        request=CategorySerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CategorySerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="分类不存在"),
        }
    ),
    partial_update=extend_schema(
        summary="部分更新分类",
        description="部分更新现有的文章分类",
        tags=["CMS-分类管理"],
        request=CategorySerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CategorySerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="分类不存在"),
        }
    ),
    destroy=extend_schema(
        summary="删除分类",
        description="删除指定的文章分类",
        tags=["CMS-分类管理"],
        parameters=[
            OpenApiParameter(name="id", description="分类ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="分类不存在"),
        }
    )
)
class CategoryViewSet(TenantModelViewSet):
    """
    分类视图集，提供增删改查API（支持多语言）
    
    - 普通用户: 只能查看分类
    - 租户管理员: 可以管理该租户下的所有分类
    - 超级管理员: 可以管理所有租户的分类
    """
    serializer_class = CategorySerializer
    permission_classes = [CategoryPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active', 'is_pinned']
    search_fields = ['translations__name', 'slug', 'translations__description']  # 搜索翻译字段
    ordering_fields = ['sort_order', 'created_at', 'is_pinned']  # 移除name（翻译字段不能直接排序）
    ordering = ['-is_pinned', 'sort_order', 'id']  # 使用id替代name
    pagination_class = None  # 禁用分页
    queryset = Category.objects.all().select_related('parent', 'tenant')  # 添加select_related优化查询
    
    def get_queryset(self):
        """
        获取分类查询集，根据用户角色和权限进行过滤
        
        - 匿名用户: 可以查看所有激活的分类
        - 已认证用户: 根据租户过滤
        """
        from common.utils.tenant_context import get_current_tenant
        
        queryset = super().get_queryset()
        
        # 匿名用户只能看到激活的分类
        user = self.request.user
        if not user.is_authenticated:
            # 从中间件设置的租户上下文获取租户
            current_tenant = get_current_tenant()
            if current_tenant:
                return queryset.filter(is_active=True, tenant=current_tenant)
            else:
                # 如果没有租户ID，返回空查询集
                return queryset.none()
        
        # 基于租户的过滤
        if not is_super_admin(user):
            queryset = queryset.filter(tenant=user.tenant)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        执行分类创建操作
        
        - 自动设置current租户
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 设置租户ID
        serializer.validated_data['tenant'] = tenant
        
        # 创建分类
        category = serializer.save()
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='create',
                entity_type='category',
                entity_id=category.id,
                details=f"创建分类: {category.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录分类创建操作日志失败: {str(e)}")
        
        return category
    
    def perform_update(self, serializer):
        """
        执行分类更新操作
        
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 更新分类
        category = serializer.save()
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='update',
                entity_type='category',
                entity_id=category.id,
                details=f"更新分类: {category.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录分类更新操作日志失败: {str(e)}")
        
        return category
    
    def perform_destroy(self, instance):
        """
        执行分类删除操作
        
        - 检查是否有文章关联到该分类
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 检查是否有文章关联到该分类
        has_articles = ArticleCategory.objects.filter(category=instance).exists()
        if has_articles:
            raise serializers.ValidationError(_("Cannot delete category with associated articles, please remove associated articles first"))
        
        # 检查是否有子分类
        has_children = Category.objects.filter(parent=instance).exists()
        if has_children:
            raise serializers.ValidationError(_("Cannot delete category with sub-categories, please delete all sub-categories first"))
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='delete',
                entity_type='category',
                entity_id=instance.id,
                details=f"删除分类: {instance.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录分类删除操作日志失败: {str(e)}")
        
        # 执行删除
        super().perform_destroy(instance)
    
    @extend_schema(
        summary="获取分类树",
        description="以树形结构获取current租户的所有分类",
        tags=["CMS-分类管理"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="分类树结构",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "description": "分类ID"},
                            "name": {"type": "string", "description": "分类名称"},
                            "slug": {"type": "string", "description": "分类别名"},
                            "description": {"type": "string", "description": "分类描述", "nullable": True},
                            "is_active": {"type": "boolean", "description": "是否激活"},
                            "sort_order": {"type": "integer", "description": "排序"},
                            "children": {
                                "type": "array",
                                "description": "子分类",
                                "items": {"$ref": "#/components/schemas/CategoryTree"}
                            }
                        }
                    }
                }
            ),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Category Tree Example',
                summary='分类树示例',
                description='获取current租户的分类树结构',
                value=[
                    {
                        'id': 1,
                        'name': '技术博客',
                        'slug': 'tech-blog',
                        'description': '技术相关文章',
                        'is_active': True,
                        'sort_order': 0,
                        'children': [
                            {
                                'id': 2,
                                'name': 'Python教程',
                                'slug': 'python-tutorial',
                                'description': 'Python编程教程',
                                'is_active': True,
                                'sort_order': 0,
                                'children': []
                            }
                        ]
                    }
                ]
            )
        ],
        operation_id="get_category_tree"
    )
    @action(detail=False, methods=['get'], url_path='tree')
    def get_category_tree(self, request):
        """获取分类树形结构"""
        from common.utils.tenant_context import get_current_tenant
        
        user = request.user
        
        # 获取所有顶级分类
        if not user.is_authenticated:
            # 匿名用户：使用中间件设置的租户上下文
            current_tenant = get_current_tenant()
            if current_tenant:
                root_categories = Category.objects.filter(
                    parent=None, 
                    is_active=True, 
                    tenant=current_tenant
                )
            else:
                # 如果没有租户ID，返回空列表
                return Response([])
        elif is_super_admin(user):
            root_categories = Category.objects.filter(parent=None)
        else:
            root_categories = Category.objects.filter(parent=None, tenant=user.tenant)
        
        def build_tree(category):
            """递归构建分类树"""
            if not user.is_authenticated:
                # 匿名用户：使用租户过滤子分类
                current_tenant = get_current_tenant()
                if current_tenant:
                    children = Category.objects.filter(
                        parent=category, 
                        is_active=True, 
                        tenant=current_tenant
                    )
                else:
                    children = Category.objects.none()
            else:
                children = Category.objects.filter(parent=category)
                
            return {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'is_active': category.is_active,
                'sort_order': category.sort_order,
                'children': [build_tree(child) for child in children]
            }
        
        # 构建完整的分类树
        tree = [build_tree(category) for category in root_categories]
        
        return Response(tree)

@extend_schema_view(
    list=extend_schema(
        summary="获取标签组列表",
        description="获取标签组列表，支持分页、过滤和搜索",
        tags=["CMS-标签管理"],
        parameters=[
            OpenApiParameter(name="is_active", description="是否激活", required=False, type=bool),
            OpenApiParameter(name="search", description="搜索关键词", required=False, type=str),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagGroupSerializer(many=True),
            403: OpenApiResponse(description="权限不足"),
        }
    ),
    retrieve=extend_schema(
        summary="获取标签组详情",
        description="获取单个标签组的详细信息",
        tags=["CMS-标签管理"],
        parameters=[
            OpenApiParameter(name="id", description="标签组ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagGroupSerializer,
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签组不存在"),
        }
    ),
    create=extend_schema(
        summary="创建标签组",
        description="创建新的标签组",
        tags=["CMS-标签管理"],
        request=TagGroupSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: TagGroupSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Create TagGroup Example',
                summary='创建标签组示例',
                description='创建一个新的标签组',
                value={
                    'name': '技术栈',
                    'slug': 'tech-stack',
                    'description': '文章使用的技术栈标签',
                    'is_active': True
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        summary="更新标签组",
        description="更新现有的标签组",
        tags=["CMS-标签管理"],
        request=TagGroupSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagGroupSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签组不存在"),
        }
    ),
    partial_update=extend_schema(
        summary="部分更新标签组",
        description="部分更新现有的标签组",
        tags=["CMS-标签管理"],
        request=TagGroupSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagGroupSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签组不存在"),
        }
    ),
    destroy=extend_schema(
        summary="删除标签组",
        description="删除指定的标签组",
        tags=["CMS-标签管理"],
        parameters=[
            OpenApiParameter(name="id", description="标签组ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签组不存在"),
        }
    ),
)
class TagGroupViewSet(TenantModelViewSet):
    """
    标签组视图集，提供增删改查API
    
    - 普通用户: 只能查看标签组
    - 租户管理员: 可以管理该租户下的所有标签组
    - 超级管理员: 可以管理所有租户的标签组
    """
    serializer_class = TagGroupSerializer
    permission_classes = [TagPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    queryset = TagGroup.objects.all().select_related('tenant')  # 添加select_related优化查询
    
    def get_queryset(self):
        """
        获取标签组查询集，根据用户角色和权限进行过滤
        
        - 匿名用户: 可以查看所有激活的标签组
        - 已认证用户: 根据租户过滤
        """
        from common.utils.tenant_context import get_current_tenant
        
        queryset = super().get_queryset()
        
        # 匿名用户只能看到激活的标签组
        user = self.request.user
        if not user.is_authenticated:
            # 从中间件设置的租户上下文获取租户
            current_tenant = get_current_tenant()
            if current_tenant:
                return queryset.filter(is_active=True, tenant=current_tenant)
            else:
                # 如果没有租户ID，返回空查询集
                return queryset.none()
        
        # 基于租户的过滤
        if not is_super_admin(user):
            queryset = queryset.filter(tenant=user.tenant)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        执行标签组创建操作
        
        - 自动设置current租户
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 设置租户ID
        serializer.validated_data['tenant'] = tenant
        
        # 创建标签组
        tag_group = serializer.save()
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='create',
                entity_type='tag_group',
                entity_id=tag_group.id,
                details=f"创建标签组: {tag_group.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录标签组创建操作日志失败: {str(e)}")
        
        return tag_group
    
    def perform_update(self, serializer):
        """
        执行标签组更新操作
        
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 更新标签组
        tag_group = serializer.save()
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='update',
                entity_type='tag_group',
                entity_id=tag_group.id,
                details=f"更新标签组: {tag_group.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录标签组更新操作日志失败: {str(e)}")
        
        return tag_group
    
    def perform_destroy(self, instance):
        """
        执行标签组删除操作
        
        - 检查是否有标签关联到该标签组
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 检查是否有标签关联到该标签组
        has_tags = Tag.objects.filter(group=instance).exists()
        if has_tags:
            raise serializers.ValidationError(_("Cannot delete tag group with associated tags, please remove associated tags first"))
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='delete',
                entity_type='tag_group',
                entity_id=instance.id,
                details=f"删除标签组: {instance.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录标签组删除操作日志失败: {str(e)}")
        
        # 执行删除
        super().perform_destroy(instance)


@extend_schema_view(
    list=extend_schema(
        summary="获取标签列表",
        description="获取标签列表，支持分页、过滤和搜索",
        tags=["CMS-标签管理"],
        parameters=[
            OpenApiParameter(name="group", description="标签组ID", required=False, type=int),
            OpenApiParameter(name="is_active", description="是否激活", required=False, type=bool),
            OpenApiParameter(name="search", description="搜索关键词", required=False, type=str),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagSerializer(many=True),
            403: OpenApiResponse(description="权限不足"),
        }
    ),
    retrieve=extend_schema(
        summary="获取标签详情",
        description="获取单个标签的详细信息",
        tags=["CMS-标签管理"],
        parameters=[
            OpenApiParameter(name="id", description="标签ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagSerializer,
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签不存在"),
        }
    ),
    create=extend_schema(
        summary="创建标签",
        description="创建新的标签",
        tags=["CMS-标签管理"],
        request=TagSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: TagSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Create Tag Example',
                summary='创建标签示例',
                description='创建一个新的标签',
                value={
                    'name': 'Python',
                    'slug': 'python',
                    'description': 'Python编程语言相关文章',
                    'group': 1,
                    'color': '#3776AB',
                    'is_active': True
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        summary="更新标签",
        description="更新现有的标签",
        tags=["CMS-标签管理"],
        request=TagSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签不存在"),
        }
    ),
    partial_update=extend_schema(
        summary="部分更新标签",
        description="部分更新现有的标签",
        tags=["CMS-标签管理"],
        request=TagSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: TagSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签不存在"),
        }
    ),
    destroy=extend_schema(
        summary="删除标签",
        description="删除指定的标签",
        tags=["CMS-标签管理"],
        parameters=[
            OpenApiParameter(name="id", description="标签ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="标签不存在"),
        }
    ),
)
class TagViewSet(TenantModelViewSet):
    """
    标签视图集，提供增删改查API
    
    - 普通用户: 只能查看标签
    - 租户管理员: 可以管理该租户下的所有标签
    - 超级管理员: 可以管理所有租户的标签
    """
    serializer_class = TagSerializer
    permission_classes = [TagPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group', 'is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    queryset = Tag.objects.all().select_related('group', 'tenant')  # 添加select_related优化查询
    
    def get_queryset(self):
        """
        获取标签查询集，根据用户角色和权限进行过滤
        
        - 匿名用户: 可以查看所有激活的标签
        - 已认证用户: 根据租户过滤
        """
        from common.utils.tenant_context import get_current_tenant
        
        queryset = super().get_queryset()
        
        # 匿名用户只能看到激活的标签
        user = self.request.user
        if not user.is_authenticated:
            # 从中间件设置的租户上下文获取租户
            current_tenant = get_current_tenant()
            if current_tenant:
                return queryset.filter(is_active=True, tenant=current_tenant)
            else:
                # 如果没有租户ID，返回空查询集
                return queryset.none()
        
        # 基于租户的过滤
        if not is_super_admin(user):
            queryset = queryset.filter(tenant=user.tenant)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        执行标签创建操作
        
        - 自动设置current租户
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 设置租户ID
        serializer.validated_data['tenant'] = tenant
        
        # 验证标签组是否属于current租户
        group = serializer.validated_data.get('group')
        if group and group.tenant != tenant:
            raise serializers.ValidationError(_("Tag group does not belong to current tenant"))
        
        # 创建标签
        tag = serializer.save()
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='create',
                entity_type='tag',
                entity_id=tag.id,
                details=f"创建标签: {tag.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录标签创建操作日志失败: {str(e)}")
        
        return tag
    
    def perform_update(self, serializer):
        """
        执行标签更新操作
        
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 验证标签组是否属于current租户
        group = serializer.validated_data.get('group')
        if group and group.tenant != tenant:
            raise serializers.ValidationError(_("Tag group does not belong to current tenant"))
        
        # 更新标签
        tag = serializer.save()
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='update',
                entity_type='tag',
                entity_id=tag.id,
                details=f"更新标签: {tag.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录标签更新操作日志失败: {str(e)}")
        
        return tag
    
    def perform_destroy(self, instance):
        """
        执行标签删除操作
        
        - 检查是否有文章关联到该标签
        - 记录操作日志
        """
        user = self.request.user
        tenant = user.tenant
        
        # 检查是否有文章关联到该标签
        has_articles = ArticleTag.objects.filter(tag=instance).exists()
        if has_articles:
            raise serializers.ValidationError(_("Cannot delete tag with associated articles, please remove associated articles first"))
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='delete',
                entity_type='tag',
                entity_id=instance.id,
                details=f"删除标签: {instance.name}",
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                tenant=tenant
            )
        except Exception as e:
            logger.error(f"记录标签删除操作日志失败: {str(e)}")
        
        # 执行删除
        super().perform_destroy(instance)
    
    @extend_schema(
        summary="获取标签使用统计",
        description="获取各个标签的使用统计信息",
        tags=["CMS-标签管理"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(description="标签使用统计"),
            403: OpenApiResponse(description="权限不足"),
        }
    )
    @action(detail=False, methods=['get'], url_path='usage-stats')
    def get_usage_stats(self, request):
        """获取标签使用统计"""
        from common.utils.tenant_context import get_current_tenant
        
        user = request.user
        
        # 获取标签及其使用次数
        if not user.is_authenticated:
            # 匿名用户：使用租户过滤
            current_tenant = get_current_tenant()
            if current_tenant:
                tags_with_count = Tag.objects.filter(
                    is_active=True, 
                    tenant=current_tenant
                ).annotate(
                    articles_count=Count('article_tags')
                ).values('id', 'name', 'slug', 'color', 'articles_count')
            else:
                # 如果没有租户ID，返回空列表
                return Response([])
        elif is_super_admin(user):
            tags_with_count = Tag.objects.annotate(
                articles_count=Count('article_tags')
            ).values('id', 'name', 'slug', 'color', 'articles_count')
        else:
            tags_with_count = Tag.objects.filter(tenant=user.tenant).annotate(
                articles_count=Count('article_tags')
            ).values('id', 'name', 'slug', 'color', 'articles_count')
        
        # 按使用次数降序排序
        tags_with_count = sorted(tags_with_count, key=lambda x: x['articles_count'], reverse=True)
        
        return Response(tags_with_count)

@extend_schema_view(
    list=extend_schema(
        summary="获取评论列表",
        description="获取评论列表，支持分页、过滤和搜索",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="article", description="文章ID过滤", required=False, type=int),
            OpenApiParameter(name="parent", description="父评论ID过滤(为空则获取顶级评论)", required=False, type=int),
            OpenApiParameter(name="user", description="用户ID过滤", required=False, type=int),
            OpenApiParameter(name="status", description="评论状态过滤", required=False, type=str, enum=["pending", "approved", "rejected", "spam"]),
            OpenApiParameter(name="is_pinned", description="是否置顶过滤", required=False, type=bool),
            OpenApiParameter(name="search", description="搜索关键词，在评论内容中匹配", required=False, type=str),
            OpenApiParameter(name="sort", description="排序字段", required=False, type=str, enum=["created_at", "likes_count"]),
            OpenApiParameter(name="sort_direction", description="排序方向", required=False, type=str, enum=["asc", "desc"]),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CommentSerializer(many=True),
            403: OpenApiResponse(description="权限不足"),
        }
    ),
    retrieve=extend_schema(
        summary="获取评论详情",
        description="获取单个评论的详细信息",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="id", description="评论ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CommentSerializer,
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    ),
    create=extend_schema(
        summary="创建评论",
        description="创建新的评论",
        tags=["CMS-评论管理"],
        request=CommentSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                'Create Comment Example',
                summary='创建评论示例',
                description='创建一条新评论',
                value={
                    'article': 1,
                    'parent': None,
                    'content': '这是一条评论内容',
                    'guest_name': '游客小明',  # 如果是游客评论
                    'guest_email': 'guest@example.com'  # 如果是游客评论
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        summary="更新评论",
        description="更新现有的评论",
        tags=["CMS-评论管理"],
        request=CommentSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CommentSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    ),
    partial_update=extend_schema(
        summary="部分更新评论",
        description="部分更新现有的评论",
        tags=["CMS-评论管理"],
        request=CommentSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CommentSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    ),
    destroy=extend_schema(
        summary="删除评论",
        description="删除指定的评论",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="id", description="评论ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    ),
)
class CommentViewSet(TenantModelViewSet):
    """
    评论视图集，提供增删改查API
    
    - 所有认证用户可以查看已批准的评论
    - 普通用户可以创建评论，但只能编辑/删除自己的评论
    - 文章作者可以管理其文章下的所有评论
    - 租户管理员可以管理该租户下的所有评论
    - 超级管理员可以管理所有评论
    """
    serializer_class = CommentSerializer
    permission_classes = [CommentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['article', 'user', 'status', 'is_pinned']  # 移除 parent，在 get_queryset 中手动处理
    search_fields = ['content', 'guest_name', 'guest_email']
    ordering_fields = ['created_at', 'updated_at', 'likes_count']
    ordering = ['-created_at']
    queryset = Comment.objects.all().select_related('user', 'article', 'parent', 'tenant')  # 添加select_related优化查询
    
    def get_queryset(self):
        """
        获取评论查询集，根据用户角色和权限进行过滤
        
        - 匿名用户: 只能查看已批准的评论
        - 已认证用户: 可以查看已批准的评论和自己的评论
        - 管理员: 可以查看所有评论
        """
        from common.utils.tenant_context import get_current_tenant
        
        queryset = super().get_queryset()
        
        # 匿名用户只能看到已批准的评论
        user = self.request.user
        if not user.is_authenticated:
            # 从中间件设置的租户上下文获取租户
            current_tenant = get_current_tenant()
            if current_tenant:
                return queryset.filter(status='approved', tenant=current_tenant)
            else:
                # 如果没有租户ID，返回空查询集
                return queryset.none()
        
        # 基于租户的过滤
        if not is_super_admin(user):
            queryset = queryset.filter(tenant=user.tenant)
        
        # 基于用户角色和权限的过滤
        if not (is_super_admin(user) or is_admin(user)):
            # 普通用户（包括Member）只能看到已批准的评论或自己的评论
            # 使用ID比较避免跨模型类型错误
            from users.models import Member
            if isinstance(user, Member):
                queryset = queryset.filter(
                    Q(status='approved') |  # 已批准的评论
                    Q(member_id=user.id)    # 自己的评论（Member）
                )
            else:
                queryset = queryset.filter(
                    Q(status='approved') |  # 已批准的评论
                    Q(user_id=user.id)      # 自己的评论（User）
                )
        
        # 处理特定的查询参数
        article_id = self.request.query_params.get('article')
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        
        parent_param = self.request.query_params.get('parent')
        if parent_param is not None:
            if parent_param == '' or parent_param.lower() == 'null':
                # 获取顶级评论
                queryset = queryset.filter(parent__isnull=True)
            else:
                # 获取指定父评论下的回复
                queryset = queryset.filter(parent_id=parent_param)
        
        # 支持 has_parent 参数（与文章API保持一致）
        has_parent = self.request.query_params.get('has_parent')
        if has_parent == 'true':
            queryset = queryset.filter(parent__isnull=False)
        elif has_parent == 'false':
            queryset = queryset.filter(parent__isnull=True)
        
        # 排序处理
        sort = self.request.query_params.get('sort')
        sort_direction = self.request.query_params.get('sort_direction', 'desc')
        if sort:
            direction = '-' if sort_direction == 'desc' else ''
            queryset = queryset.order_by(f'{direction}{sort}')
        
        return queryset
    
    def perform_create(self, serializer):
        """
        执行评论创建操作
        
        - 自动设置current用户和租户
        - 根据用户类型设置user或member字段
        - 设置初始状态（认证用户自动批准）
        - 记录IP和User-Agent
        - 记录操作日志
        """
        user = self.request.user
        
        # 获取租户（从中间件或用户）
        from common.utils.tenant_context import get_current_tenant
        tenant = get_current_tenant()
        if not tenant and user.is_authenticated:
            tenant = user.tenant
        
        # 设置租户ID
        serializer.validated_data['tenant'] = tenant
        
        # 根据用户类型设置对应的外键字段（如果未提供且不是游客评论）
        if not serializer.validated_data.get('guest_name'):
            from users.models import Member
            if isinstance(user, Member):
                serializer.validated_data['member'] = user
                serializer.validated_data['user'] = None
            else:
                serializer.validated_data['user'] = user
                serializer.validated_data['member'] = None
        
        # 验证文章权限
        article_id = serializer.validated_data.get('article').id
        try:
            article = Article.objects.get(id=article_id, tenant=tenant)
            if not article.allow_comment:
                raise serializers.ValidationError(_("This article does not allow comments"))
        except Article.DoesNotExist:
            raise serializers.ValidationError(_("Article does not exist or no permission to access"))
        
        # 设置初始状态：所有认证用户评论自动批准（TODO: 可通过配置控制）
        # 游客评论需要审核
        if serializer.validated_data.get('guest_name'):
            serializer.validated_data['status'] = 'pending'
        else:
            serializer.validated_data['status'] = 'approved'
        
        # 记录IP和User-Agent
        serializer.validated_data['ip_address'] = self.request.META.get('REMOTE_ADDR')
        serializer.validated_data['user_agent'] = self.request.META.get('HTTP_USER_AGENT')
        
        # 创建评论
        comment = serializer.save()
        
        # 更新文章评论数统计
        try:
            stats, created = ArticleStatistics.objects.get_or_create(
                article=comment.article,
                tenant=tenant
            )
            stats.comments_count = Comment.objects.filter(
                article=comment.article,
                status='approved'
            ).count()
            stats.save()
        except Exception as e:
            logger.error(f"更新文章评论统计失败: {str(e)}")
        
        # 记录操作日志（支持User和Member，游客不记录）
        if user.is_authenticated:
            try:
                from users.models import Member, User as AdminUser
                log_data = {
                    'action': 'create',
                    'entity_type': 'comment',
                    'entity_id': comment.id,
                    'details': f"创建评论: {comment.id}",
                    'ip_address': self.request.META.get('REMOTE_ADDR'),
                    'user_agent': self.request.META.get('HTTP_USER_AGENT'),
                    'tenant': tenant
                }
                
                if isinstance(user, Member):
                    log_data['member'] = user
                else:
                    log_data['user'] = user
                
                OperationLog.objects.create(**log_data)
            except Exception as e:
                logger.error(f"记录评论创建操作日志失败: {str(e)}")
        
        return comment
    
    def perform_update(self, serializer):
        """
        执行评论更新操作
        
        - 支持User和Member更新自己的评论
        - 记录操作日志
        - 状态变更时更新文章统计
        """
        user = self.request.user
        tenant = user.tenant
        instance = self.get_object()
        
        # 保存旧状态，用于检测状态变化
        old_status = instance.status
        
        # 更新评论
        comment = serializer.save()
        
        # 如果状态发生变化，更新文章评论统计
        if old_status != comment.status:
            try:
                stats, created = ArticleStatistics.objects.get_or_create(
                    article=comment.article,
                    tenant=tenant
                )
                stats.comments_count = Comment.objects.filter(
                    article=comment.article,
                    status='approved'
                ).count()
                stats.save()
            except Exception as e:
                logger.error(f"更新文章评论统计失败: {str(e)}")
        
        # 记录操作日志（支持User和Member）
        try:
            from users.models import Member, User as AdminUser
            log_data = {
                'action': 'update',
                'entity_type': 'comment',
                'entity_id': comment.id,
                'details': f"更新评论: {comment.id}",
                'ip_address': self.request.META.get('REMOTE_ADDR'),
                'user_agent': self.request.META.get('HTTP_USER_AGENT'),
                'tenant': tenant
            }
            
            if isinstance(user, Member):
                log_data['member'] = user
            else:
                log_data['user'] = user
            
            OperationLog.objects.create(**log_data)
        except Exception as e:
            logger.error(f"记录评论更新操作日志失败: {str(e)}")
        
        return comment
    
    def perform_destroy(self, instance):
        """
        执行评论删除操作
        
        - 支持User和Member删除自己的评论
        - Admin可以删除所有评论
        - 记录操作日志
        - 更新文章评论数统计
        """
        user = self.request.user
        tenant = user.tenant
        article = instance.article
        
        # 记录操作日志（支持User和Member）
        try:
            from users.models import Member, User as AdminUser
            log_data = {
                'action': 'delete',
                'entity_type': 'comment',
                'entity_id': instance.id,
                'details': f"删除评论: {instance.id}",
                'ip_address': self.request.META.get('REMOTE_ADDR'),
                'user_agent': self.request.META.get('HTTP_USER_AGENT'),
                'tenant': tenant
            }
            
            if isinstance(user, Member):
                log_data['member'] = user
            else:
                log_data['user'] = user
            
            OperationLog.objects.create(**log_data)
        except Exception as e:
            logger.error(f"记录评论删除操作日志失败: {str(e)}")
        
        # 执行删除
        super().perform_destroy(instance)
        
        # 更新文章评论统计
        try:
            stats, created = ArticleStatistics.objects.get_or_create(
                article=article,
                tenant=tenant
            )
            stats.comments_count = Comment.objects.filter(
                article=article,
                status='approved'
            ).count()
            stats.save()
        except Exception as e:
            logger.error(f"更新文章ID {article.id} 的评论统计失败: {str(e)}")
    
    @extend_schema(
        summary="获取评论回复",
        description="获取指定评论的所有回复",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="id", description="评论ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: CommentSerializer(many=True),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    )
    @action(detail=True, methods=['get'], url_path='replies')
    def replies(self, request, pk=None):
        """获取评论的回复"""
        from common.utils.tenant_context import get_current_tenant
        
        comment = self.get_object()
        replies = Comment.objects.filter(parent=comment)
        
        # 匿名用户只能看到已批准的评论
        user = request.user
        if not user.is_authenticated:
            # 从中间件设置的租户上下文获取租户
            current_tenant = get_current_tenant()
            if current_tenant:
                replies = replies.filter(status='approved', tenant=current_tenant)
            else:
                # 如果没有租户ID，返回空查询集
                replies = replies.none()
        # 非管理员且已认证用户只能看到已批准的评论或自己的评论
        elif not (is_super_admin(user) or is_admin(user) or user.id == comment.article.author_id):
            replies = replies.filter(
                Q(status='approved') |  # 已批准的评论
                Q(user=user)            # 自己的评论
            )
        
        # 排序
        replies = replies.order_by('-created_at')
        
        # 分页
        page = self.paginate_queryset(replies)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(replies, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="批准评论",
        description="将评论状态改为已批准",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="id", description="评论ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(description="批准成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """批准评论"""
        comment = self.get_object()
        user = request.user
        
        # Member 不能进行写操作
        if is_member(user):
            return Response(
                {"detail": _("普通成员没有权限进行此操作")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证权限（只有管理员和文章作者可以批准评论）
        if not can_moderate_comments(user, comment.article.author):
            return Response(
                {"detail": _("您没有权限批准此评论")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证评论是否已批准
        if comment.status == 'approved':
            return Response(
                {"detail": _("评论已经是批准状态")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新评论状态
        old_status = comment.status
        comment.status = 'approved'
        comment.save()
        
        # 更新文章评论数统计
        if old_status != 'approved':
            try:
                stats, created = ArticleStatistics.objects.get_or_create(
                    article=comment.article,
                    tenant=comment.tenant
                )
                stats.comments_count = Comment.objects.filter(
                    article=comment.article,
                    status='approved'
                ).count()
                stats.save()
            except Exception as e:
                logger.error(f"更新文章评论统计失败: {str(e)}")
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='approve',
                entity_type='comment',
                entity_id=comment.id,
                details=f"批准评论: {comment.id}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                tenant=comment.tenant
            )
        except Exception as e:
            logger.error(f"记录评论批准操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _("评论已批准"),
                "id": comment.id,
                "status": comment.status
            },
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="拒绝评论",
        description="将评论状态改为已拒绝",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="id", description="评论ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(description="拒绝成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """拒绝评论"""
        comment = self.get_object()
        user = request.user
        
        # Member 不能进行写操作
        if is_member(user):
            return Response(
                {"detail": _("普通成员没有权限进行此操作")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证权限（只有管理员和文章作者可以拒绝评论）
        if not can_moderate_comments(user, comment.article.author):
            return Response(
                {"detail": _("您没有权限拒绝此评论")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证评论是否已拒绝
        if comment.status == 'rejected':
            return Response(
                {"detail": _("评论已经是拒绝状态")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新评论状态
        old_status = comment.status
        comment.status = 'rejected'
        comment.save()
        
        # 如果之前是已批准状态，更新文章评论数统计
        if old_status == 'approved':
            try:
                stats, created = ArticleStatistics.objects.get_or_create(
                    article=comment.article,
                    tenant=comment.tenant
                )
                stats.comments_count = Comment.objects.filter(
                    article=comment.article,
                    status='approved'
                ).count()
                stats.save()
            except Exception as e:
                logger.error(f"更新文章评论统计失败: {str(e)}")
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='reject',
                entity_type='comment',
                entity_id=comment.id,
                details=f"拒绝评论: {comment.id}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                tenant=comment.tenant
            )
        except Exception as e:
            logger.error(f"记录评论拒绝操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _("评论已拒绝"),
                "id": comment.id,
                "status": comment.status
            },
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="标记为垃圾评论",
        description="将评论状态改为垃圾评论",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="id", description="评论ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(description="标记成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="评论不存在"),
        }
    )
    @action(detail=True, methods=['post'], url_path='mark-spam')
    def mark_as_spam(self, request, pk=None):
        """标记为垃圾评论"""
        comment = self.get_object()
        user = request.user
        
        # Member 不能进行写操作
        if is_member(user):
            return Response(
                {"detail": _("普通成员没有权限进行此操作")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证权限（只有管理员和文章作者可以标记垃圾评论）
        if not can_moderate_comments(user, comment.article.author):
            return Response(
                {"detail": _("您没有权限标记此评论为垃圾评论")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证评论是否已标记为垃圾
        if comment.status == 'spam':
            return Response(
                {"detail": _("评论已经被标记为垃圾评论")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新评论状态
        old_status = comment.status
        comment.status = 'spam'
        comment.save()
        
        # 如果之前是已批准状态，更新文章评论数统计
        if old_status == 'approved':
            try:
                stats, created = ArticleStatistics.objects.get_or_create(
                    article=comment.article,
                    tenant=comment.tenant
                )
                stats.comments_count = Comment.objects.filter(
                    article=comment.article,
                    status='approved'
                ).count()
                stats.save()
            except Exception as e:
                logger.error(f"更新文章评论统计失败: {str(e)}")
        
        # 记录操作日志
        try:
            OperationLog.objects.create(
                user=user,
                action='mark_spam',
                entity_type='comment',
                entity_id=comment.id,
                details=f"标记评论为垃圾评论: {comment.id}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                tenant=comment.tenant
            )
        except Exception as e:
            logger.error(f"记录评论标记为垃圾操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _("评论已被标记为垃圾评论"),
                "id": comment.id,
                "status": comment.status
            },
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="批量处理评论",
        description="批量审核、拒绝或删除多条评论",
        tags=["CMS-评论管理"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID", required=False, type=str, location=OpenApiParameter.HEADER),
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'comment_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': '要处理的评论ID列表'
                    },
                    'action': {
                        'type': 'string',
                        'enum': ['approve', 'reject', 'spam', 'delete'],
                        'description': '执行的操作'
                    }
                },
                'required': ['comment_ids', 'action']
            }
        },
        responses={
            200: OpenApiResponse(description="批量处理成功"),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        }
    )
    @action(detail=False, methods=['post'], url_path='batch')
    def batch_action(self, request):
        """批量处理评论"""
        user = request.user
        tenant = user.tenant
        
        # 获取评论ID列表和操作类型
        comment_ids = request.data.get('comment_ids', [])
        action = request.data.get('action')
        
        if not comment_ids:
            return Response(
                {"detail": _("未提供要处理的评论ID")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action not in ['approve', 'reject', 'spam', 'delete']:
            return Response(
                {"detail": _("不支持的操作类型")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 根据权限获取可操作的评论
        if is_super_admin(user):
            comments = Comment.objects.filter(id__in=comment_ids)
        elif is_admin(user):
            comments = Comment.objects.filter(id__in=comment_ids, tenant=tenant)
        else:
            # 普通用户只能操作自己的评论和自己文章下的评论
            authored_articles = Article.objects.filter(author=user).values_list('id', flat=True)
            comments = Comment.objects.filter(
                id__in=comment_ids,
                tenant=tenant
            ).filter(
                Q(user=user) |  # 自己的评论
                Q(article__id__in=authored_articles)  # 自己文章下的评论
            )
        
        # 统计找到的评论数量
        found_count = comments.count()
        if found_count == 0:
            return Response(
                {"detail": _("未找到可操作的评论")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 执行批量操作
        affected_article_ids = set(comments.values_list('article_id', flat=True))
        processed_ids = []
        
        if action == 'approve':
            # 批量批准评论
            processed_ids = list(comments.values_list('id', flat=True))
            comments.update(status='approved')
            action_desc = "批准"
        elif action == 'reject':
            # 批量拒绝评论
            processed_ids = list(comments.values_list('id', flat=True))
            comments.update(status='rejected')
            action_desc = "拒绝"
        elif action == 'spam':
            # 批量标记为垃圾评论
            processed_ids = list(comments.values_list('id', flat=True))
            comments.update(status='spam')
            action_desc = "标记为垃圾"
        elif action == 'delete':
            # 批量删除评论
            processed_ids = list(comments.values_list('id', flat=True))
            comments.delete()
            action_desc = "删除"
        
        # 更新受影响文章的评论统计
        for article_id in affected_article_ids:
            try:
                article = Article.objects.get(id=article_id)
                stats, created = ArticleStatistics.objects.get_or_create(
                    article=article,
                    tenant=tenant
                )
                stats.comments_count = Comment.objects.filter(
                    article=article,
                    status='approved'
                ).count()
                stats.save()
            except Exception as e:
                logger.error(f"更新文章ID {article_id} 的评论统计失败: {str(e)}")
        
        # 记录操作日志
        for comment_id in processed_ids:
            try:
                OperationLog.objects.create(
                    user=user,
                    action=f'batch_{action}',
                    entity_type='comment',
                    entity_id=comment_id,
                    details=f"批量{action_desc}评论: {comment_id}",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    tenant=tenant
                )
            except Exception as e:
                logger.error(f"记录评论批量处理操作日志失败: {str(e)}")
        
        return Response(
            {
                "message": _(f"评论批量{action_desc}成功"),
                "requested_count": len(comment_ids),
                "processed_count": found_count,
                "processed_ids": processed_ids
            },
            status=status.HTTP_200_OK
        )
