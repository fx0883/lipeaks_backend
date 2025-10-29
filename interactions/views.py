"""
用户互动视图
"""
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse, OpenApiTypes
import logging

from common.authentication.jwt_auth import JWTAuthentication
from common.pagination import StandardResultsSetPagination
from cms.models import Article
from .models import ArticleFavorite
from .serializers import ArticleFavoriteSerializer, ArticleFavoriteCreateSerializer
from .permissions import ArticleFavoritePermission

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取我的收藏列表",
        description="""获取当前用户收藏的文章列表。
        
**权限要求**:
- 需要认证（登录）
- 仅返回当前用户的收藏

**返回内容**:
- 收藏记录ID和时间
- 文章完整信息（标题、封面、作者等）
- 支持分页

**使用场景**: Member查看自己收藏的文章列表
        """,
        tags=["用户互动-收藏"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
            OpenApiParameter(name="page", description="页码", required=False, type=int),
            OpenApiParameter(name="page_size", description="每页数量", required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(
                description="获取成功",
                response=ArticleFavoriteSerializer(many=True)
            ),
            401: OpenApiResponse(description="未认证"),
        },
        examples=[
            OpenApiExample(
                'Favorites List Success',
                summary='获取收藏列表成功示例',
                value={
                    'count': 15,
                    'next': 'http://api.example.com/api/v1/interactions/favorites/?page=2',
                    'previous': None,
                    'results': [
                        {
                            'id': 23,
                            'user': 5,
                            'article': 42,
                            'article_detail': {
                                'id': 42,
                                'title': '深入理解Python装饰器',
                                'slug': 'python-decorators',
                                'excerpt': '本文详细介绍Python装饰器的原理和应用...',
                                'cover_image': 'https://example.com/python.jpg',
                                'author_info': {'id': 3, 'username': 'author'},
                                'status': 'published',
                                'views_count': 1250,
                                'likes_count': 42
                            },
                            'user_info': {
                                'id': 5,
                                'username': 'member_user'
                            },
                            'tenant': 1,
                            'created_at': '2024-01-20T10:30:00Z'
                        }
                    ]
                },
                response_only=True,
            )
        ]
    ),
    create=extend_schema(
        summary="收藏文章",
        description="""将文章添加到收藏列表。
        
**权限要求**:
- 需要认证（登录）
- 只能收藏本租户内的文章
- 不能重复收藏同一文章

**业务规则**:
- 每个用户对每篇文章只能收藏一次
- 收藏时自动记录租户和时间
- 文章的收藏计数会相应增加（如有实现）

**使用场景**: Member浏览文章时点击收藏按钮
        """,
        tags=["用户互动-收藏"],
        request=ArticleFavoriteCreateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: OpenApiResponse(
                description="收藏成功",
                response=ArticleFavoriteSerializer
            ),
            400: OpenApiResponse(description="请求错误（如文章不存在、已收藏等）"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（如尝试收藏其他租户的文章）"),
        },
        examples=[
            OpenApiExample(
                'Favorite Article Request',
                summary='收藏文章请求示例',
                value={
                    'article': 42
                },
                request_only=True,
            ),
            OpenApiExample(
                'Favorite Article Success',
                summary='收藏成功响应示例',
                value={
                    'id': 23,
                    'user': 5,
                    'article': 42,
                    'article_detail': {
                        'id': 42,
                        'title': '深入理解Python装饰器',
                        'slug': 'python-decorators',
                        'excerpt': '本文详细介绍Python装饰器的原理和应用...',
                        'cover_image': 'https://example.com/python.jpg'
                    },
                    'user_info': {
                        'id': 5,
                        'username': 'member_user'
                    },
                    'tenant': 1,
                    'created_at': '2024-01-20T10:30:00Z'
                },
                response_only=True,
            )
        ]
    ),
    destroy=extend_schema(
        summary="取消收藏",
        description="""从收藏列表中移除文章。
        
**权限要求**:
- 需要认证（登录）
- 只能删除自己的收藏记录

**业务规则**:
- 删除后文章的收藏计数会相应减少（如有实现）
- 操作是幂等的（重复删除不会报错）

**使用场景**: Member在收藏列表中点击取消收藏
        """,
        tags=["用户互动-收藏"],
        parameters=[
            OpenApiParameter(name="id", description="收藏记录ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（尝试删除别人的收藏）"),
            404: OpenApiResponse(description="收藏记录不存在"),
        }
    )
)
class ArticleFavoriteViewSet(viewsets.ModelViewSet):
    """
    文章收藏视图集
    
    提供文章收藏的增删查功能
    """
    serializer_class = ArticleFavoriteSerializer
    permission_classes = [ArticleFavoritePermission]
    authentication_classes = [JWTAuthentication]
    pagination_class = StandardResultsSetPagination
    queryset = ArticleFavorite.objects.all().select_related('user', 'article', 'tenant')
    
    def get_queryset(self):
        """
        获取当前用户的收藏列表
        """
        user = self.request.user
        return self.queryset.filter(user=user, tenant=user.tenant)
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return ArticleFavoriteCreateSerializer
        return ArticleFavoriteSerializer
    
    def perform_create(self, serializer):
        """
        执行收藏创建操作
        
        - 自动设置当前用户和租户
        - 记录收藏时间
        """
        user = self.request.user
        serializer.save(user=user, tenant=user.tenant)
        logger.info(f"User {user.username} favorited article {serializer.instance.article_id}")
    
    @extend_schema(
        summary="通过文章ID取消收藏",
        description="""根据文章ID取消收藏（便捷方法）。
        
**权限要求**:
- 需要认证（登录）

**业务规则**:
- 如果该文章未被收藏，返回404
- 只能取消收藏自己的记录

**使用场景**: Member在文章详情页点击取消收藏按钮（已知文章ID，不需要知道收藏记录ID）
        """,
        tags=["用户互动-收藏"],
        parameters=[
            OpenApiParameter(name="article_id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="取消收藏成功"),
            401: OpenApiResponse(description="未认证"),
            404: OpenApiResponse(description="收藏记录不存在或文章不存在"),
        },
        examples=[
            OpenApiExample(
                'Unfavorite By Article ID Success',
                summary='取消收藏成功',
                value={'message': '已取消收藏'},
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['delete'], url_path='by-article/(?P<article_id>[^/.]+)')
    def unfavorite_by_article(self, request, article_id=None):
        """根据文章ID取消收藏"""
        user = request.user
        
        # 查找收藏记录
        favorite = get_object_or_404(
            ArticleFavorite,
            user=user,
            article_id=article_id,
            tenant=user.tenant
        )
        
        # 删除收藏
        favorite.delete()
        logger.info(f"User {user.username} unfavorited article {article_id}")
        
        return Response(
            {'message': _('已取消收藏')},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @extend_schema(
        summary="检查文章是否已收藏",
        description="""检查当前用户是否已收藏指定文章。
        
**权限要求**:
- 需要认证（登录）

**返回内容**:
- is_favorited: 是否已收藏
- favorite_id: 收藏记录ID（如已收藏）
- created_at: 收藏时间（如已收藏）

**使用场景**: 前端显示文章详情时，判断是否显示"已收藏"状态
        """,
        tags=["用户互动-收藏"],
        parameters=[
            OpenApiParameter(name="article_id", description="文章ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="查询成功",
                response={
                    'type': 'object',
                    'properties': {
                        'is_favorited': {'type': 'boolean'},
                        'favorite_id': {'type': 'integer', 'nullable': True},
                        'created_at': {'type': 'string', 'format': 'date-time', 'nullable': True}
                    }
                }
            ),
            401: OpenApiResponse(description="未认证"),
            404: OpenApiResponse(description="文章不存在"),
        },
        examples=[
            OpenApiExample(
                'Article Is Favorited',
                summary='文章已收藏',
                value={
                    'is_favorited': True,
                    'favorite_id': 23,
                    'created_at': '2024-01-20T10:30:00Z'
                },
                response_only=True,
            ),
            OpenApiExample(
                'Article Not Favorited',
                summary='文章未收藏',
                value={
                    'is_favorited': False,
                    'favorite_id': None,
                    'created_at': None
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='check/(?P<article_id>[^/.]+)')
    def check_favorite(self, request, article_id=None):
        """检查文章是否已收藏"""
        user = request.user
        
        # 验证文章存在
        article = get_object_or_404(Article, id=article_id, tenant=user.tenant)
        
        # 查找收藏记录
        favorite = ArticleFavorite.objects.filter(
            user=user,
            article=article
        ).first()
        
        if favorite:
            return Response({
                'is_favorited': True,
                'favorite_id': favorite.id,
                'created_at': favorite.created_at
            })
        else:
            return Response({
                'is_favorited': False,
                'favorite_id': None,
                'created_at': None
            })
