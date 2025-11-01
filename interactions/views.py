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
from users.models import Member
from .models import ArticleFavorite, MemberLike, MemberFollow
from .serializers import (
    ArticleFavoriteSerializer, ArticleFavoriteCreateSerializer,
    MemberLikeSerializer, MemberLikeCreateSerializer,
    MemberFollowSerializer, MemberFollowCreateSerializer
)
from .permissions import ArticleFavoritePermission, MemberLikePermission, MemberFollowPermission

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


@extend_schema_view(
    list=extend_schema(
        summary="获取我点赞的用户列表",
        description="""获取当前Member用户点赞的其他用户列表。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以访问
- 仅返回当前用户点赞的记录

**返回内容**:
- 点赞记录ID和时间
- 被点赞用户的完整信息（用户名、昵称、头像等）
- 支持分页

**使用场景**: Member查看自己点赞过的用户列表
        """,
        tags=["用户互动-点赞"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
            OpenApiParameter(name="page", description="页码", required=False, type=int),
            OpenApiParameter(name="page_size", description="每页数量", required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(
                description="获取成功",
                response=MemberLikeSerializer(many=True)
            ),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（非Member用户）"),
        },
        examples=[
            OpenApiExample(
                'Member Likes List Success',
                summary='获取点赞列表成功示例',
                value={
                    'count': 10,
                    'next': 'http://api.example.com/api/v1/interactions/likes/?page=2',
                    'previous': None,
                    'results': [
                        {
                            'id': 15,
                            'from_member': 5,
                            'to_member': 8,
                            'from_member_info': {
                                'id': 5,
                                'username': 'member_user',
                                'nick_name': '普通用户',
                                'avatar': 'https://example.com/avatar1.jpg'
                            },
                            'to_member_info': {
                                'id': 8,
                                'username': 'another_member',
                                'nick_name': '另一个用户',
                                'avatar': 'https://example.com/avatar2.jpg'
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
        summary="点赞用户",
        description="""给指定Member用户点赞。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以点赞
- 只能点赞本租户内的用户
- 不能重复点赞同一用户
- 不能点赞自己

**业务规则**:
- 每个用户对每个用户只能点赞一次
- 点赞时自动记录租户和时间

**使用场景**: Member用户给其他用户点赞表示认可
        """,
        tags=["用户互动-点赞"],
        request=MemberLikeCreateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: OpenApiResponse(
                description="点赞成功",
                response=MemberLikeSerializer
            ),
            400: OpenApiResponse(description="请求错误（如用户不存在、已点赞、点赞自己等）"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（非Member用户或尝试点赞其他租户用户）"),
        },
        examples=[
            OpenApiExample(
                'Like Member Request',
                summary='点赞用户请求示例',
                value={
                    'to_member': 8
                },
                request_only=True,
            ),
            OpenApiExample(
                'Like Member Success',
                summary='点赞成功响应示例',
                value={
                    'id': 15,
                    'from_member': 5,
                    'to_member': 8,
                    'from_member_info': {
                        'id': 5,
                        'username': 'member_user',
                        'nick_name': '普通用户',
                        'avatar': 'https://example.com/avatar1.jpg'
                    },
                    'to_member_info': {
                        'id': 8,
                        'username': 'another_member',
                        'nick_name': '另一个用户',
                        'avatar': 'https://example.com/avatar2.jpg'
                    },
                    'tenant': 1,
                    'created_at': '2024-01-20T10:30:00Z'
                },
                response_only=True,
            )
        ]
    ),
    destroy=extend_schema(
        summary="取消点赞",
        description="""取消对指定用户的点赞。
        
**权限要求**:
- 需要认证（登录）
- 只能删除自己发起的点赞记录

**使用场景**: Member在点赞列表中取消对某用户的点赞
        """,
        tags=["用户互动-点赞"],
        parameters=[
            OpenApiParameter(name="id", description="点赞记录ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（尝试删除别人的点赞）"),
            404: OpenApiResponse(description="点赞记录不存在"),
        }
    )
)
class MemberLikeViewSet(viewsets.ModelViewSet):
    """
    用户点赞视图集
    
    提供Member用户之间点赞的增删查功能
    """
    serializer_class = MemberLikeSerializer
    permission_classes = [MemberLikePermission]
    authentication_classes = [JWTAuthentication]
    pagination_class = StandardResultsSetPagination
    queryset = MemberLike.objects.all().select_related('from_member', 'to_member', 'tenant')
    
    def get_queryset(self):
        """
        获取当前用户发起的点赞列表
        """
        member = self.request.user
        return self.queryset.filter(from_member=member, tenant=member.tenant)
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return MemberLikeCreateSerializer
        return MemberLikeSerializer
    
    def perform_create(self, serializer):
        """
        执行点赞创建操作
        
        - 自动设置当前用户和租户
        - 记录点赞时间
        """
        member = self.request.user
        serializer.save(from_member=member, tenant=member.tenant)
        logger.info(f"Member {member.username} liked member {serializer.instance.to_member_id}")
    
    @extend_schema(
        summary="获取收到的点赞列表",
        description="""获取其他用户给当前用户的点赞列表。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以访问

**返回内容**:
- 点赞记录ID和时间
- 点赞发起者的完整信息
- 支持分页

**使用场景**: Member查看有哪些用户给自己点赞了
        """,
        tags=["用户互动-点赞"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
            OpenApiParameter(name="page", description="页码", required=False, type=int),
            OpenApiParameter(name="page_size", description="每页数量", required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(
                description="获取成功",
                response=MemberLikeSerializer(many=True)
            ),
            401: OpenApiResponse(description="未认证"),
        },
        examples=[
            OpenApiExample(
                'Received Likes Success',
                summary='获取收到的点赞成功示例',
                value={
                    'count': 20,
                    'next': None,
                    'previous': None,
                    'results': [
                        {
                            'id': 25,
                            'from_member': 10,
                            'to_member': 5,
                            'from_member_info': {
                                'id': 10,
                                'username': 'fan_user',
                                'nick_name': '粉丝用户',
                                'avatar': 'https://example.com/avatar3.jpg'
                            },
                            'to_member_info': {
                                'id': 5,
                                'username': 'member_user',
                                'nick_name': '普通用户',
                                'avatar': 'https://example.com/avatar1.jpg'
                            },
                            'tenant': 1,
                            'created_at': '2024-01-21T15:30:00Z'
                        }
                    ]
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='received')
    def received_likes(self, request):
        """获取收到的点赞列表"""
        member = request.user
        
        queryset = MemberLike.objects.filter(
            to_member=member,
            tenant=member.tenant
        ).select_related('from_member', 'to_member', 'tenant')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="通过用户ID取消点赞",
        description="""根据被点赞用户ID取消点赞（便捷方法）。
        
**权限要求**:
- 需要认证（登录）

**业务规则**:
- 如果未点赞该用户，返回404

**使用场景**: Member在用户详情页点击取消点赞按钮（已知用户ID，不需要知道点赞记录ID）
        """,
        tags=["用户互动-点赞"],
        parameters=[
            OpenApiParameter(name="member_id", description="被点赞用户ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="取消点赞成功"),
            401: OpenApiResponse(description="未认证"),
            404: OpenApiResponse(description="点赞记录不存在"),
        },
        examples=[
            OpenApiExample(
                'Unlike By Member Success',
                summary='取消点赞成功',
                value={'message': '已取消点赞'},
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['delete'], url_path='by-member/(?P<member_id>[^/.]+)')
    def unlike_by_member(self, request, member_id=None):
        """根据用户ID取消点赞"""
        member = request.user
        
        # 查找点赞记录
        like = get_object_or_404(
            MemberLike,
            from_member=member,
            to_member_id=member_id,
            tenant=member.tenant
        )
        
        # 删除点赞
        like.delete()
        logger.info(f"Member {member.username} unliked member {member_id}")
        
        return Response(
            {'message': _('已取消点赞')},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @extend_schema(
        summary="检查是否已点赞用户",
        description="""检查当前用户是否已点赞指定用户。
        
**权限要求**:
- 需要认证（登录）

**返回内容**:
- is_liked: 是否已点赞
- like_id: 点赞记录ID（如已点赞）
- created_at: 点赞时间（如已点赞）

**使用场景**: 前端显示用户详情时，判断是否显示"已点赞"状态
        """,
        tags=["用户互动-点赞"],
        parameters=[
            OpenApiParameter(name="member_id", description="用户ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="查询成功",
                response={
                    'type': 'object',
                    'properties': {
                        'is_liked': {'type': 'boolean'},
                        'like_id': {'type': 'integer', 'nullable': True},
                        'created_at': {'type': 'string', 'format': 'date-time', 'nullable': True}
                    }
                }
            ),
            401: OpenApiResponse(description="未认证"),
            404: OpenApiResponse(description="用户不存在"),
        },
        examples=[
            OpenApiExample(
                'Member Is Liked',
                summary='用户已点赞',
                value={
                    'is_liked': True,
                    'like_id': 15,
                    'created_at': '2024-01-20T10:30:00Z'
                },
                response_only=True,
            ),
            OpenApiExample(
                'Member Not Liked',
                summary='用户未点赞',
                value={
                    'is_liked': False,
                    'like_id': None,
                    'created_at': None
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='check/(?P<member_id>[^/.]+)')
    def check_like(self, request, member_id=None):
        """检查是否已点赞某用户"""
        member = request.user
        
        # 验证用户存在
        target_member = get_object_or_404(Member, id=member_id, tenant=member.tenant)
        
        # 查找点赞记录
        like = MemberLike.objects.filter(
            from_member=member,
            to_member=target_member
        ).first()
        
        if like:
            return Response({
                'is_liked': True,
                'like_id': like.id,
                'created_at': like.created_at
            })
        else:
            return Response({
                'is_liked': False,
                'like_id': None,
                'created_at': None
            })


@extend_schema_view(
    list=extend_schema(
        summary="获取我的关注列表",
        description="""获取当前Member用户关注的其他用户列表。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以访问
- 仅返回当前用户的关注记录

**返回内容**:
- 关注记录ID和时间
- 被关注用户的完整信息
- 是否互相关注（is_mutual）
- 支持分页

**使用场景**: Member查看自己的关注列表
        """,
        tags=["用户互动-关注"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
            OpenApiParameter(name="page", description="页码", required=False, type=int),
            OpenApiParameter(name="page_size", description="每页数量", required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(
                description="获取成功",
                response=MemberFollowSerializer(many=True)
            ),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（非Member用户）"),
        },
        examples=[
            OpenApiExample(
                'Following List Success',
                summary='获取关注列表成功示例',
                value={
                    'count': 15,
                    'next': None,
                    'previous': None,
                    'results': [
                        {
                            'id': 30,
                            'follower': 5,
                            'following': 12,
                            'follower_info': {
                                'id': 5,
                                'username': 'member_user',
                                'nick_name': '普通用户',
                                'avatar': 'https://example.com/avatar1.jpg'
                            },
                            'following_info': {
                                'id': 12,
                                'username': 'followed_user',
                                'nick_name': '被关注用户',
                                'avatar': 'https://example.com/avatar4.jpg'
                            },
                            'is_mutual': True,
                            'tenant': 1,
                            'created_at': '2024-01-20T11:00:00Z'
                        }
                    ]
                },
                response_only=True,
            )
        ]
    ),
    create=extend_schema(
        summary="关注用户",
        description="""关注指定Member用户。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以关注
- 只能关注本租户内的用户
- 不能重复关注同一用户
- 不能关注自己

**业务规则**:
- 每个用户对每个用户只能关注一次
- 关注时自动记录租户和时间
- 关注后可能形成互相关注关系

**使用场景**: Member用户关注其他用户以接收其动态
        """,
        tags=["用户互动-关注"],
        request=MemberFollowCreateSerializer,
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            201: OpenApiResponse(
                description="关注成功",
                response=MemberFollowSerializer
            ),
            400: OpenApiResponse(description="请求错误（如用户不存在、已关注、关注自己等）"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（非Member用户或尝试关注其他租户用户）"),
        },
        examples=[
            OpenApiExample(
                'Follow Member Request',
                summary='关注用户请求示例',
                value={
                    'following': 12
                },
                request_only=True,
            ),
            OpenApiExample(
                'Follow Member Success',
                summary='关注成功响应示例',
                value={
                    'id': 30,
                    'follower': 5,
                    'following': 12,
                    'follower_info': {
                        'id': 5,
                        'username': 'member_user',
                        'nick_name': '普通用户',
                        'avatar': 'https://example.com/avatar1.jpg'
                    },
                    'following_info': {
                        'id': 12,
                        'username': 'followed_user',
                        'nick_name': '被关注用户',
                        'avatar': 'https://example.com/avatar4.jpg'
                    },
                    'is_mutual': False,
                    'tenant': 1,
                    'created_at': '2024-01-20T11:00:00Z'
                },
                response_only=True,
            )
        ]
    ),
    destroy=extend_schema(
        summary="取消关注",
        description="""取消对指定用户的关注。
        
**权限要求**:
- 需要认证（登录）
- 只能删除自己发起的关注记录

**使用场景**: Member在关注列表中取消对某用户的关注
        """,
        tags=["用户互动-关注"],
        parameters=[
            OpenApiParameter(name="id", description="关注记录ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足（尝试删除别人的关注）"),
            404: OpenApiResponse(description="关注记录不存在"),
        }
    )
)
class MemberFollowViewSet(viewsets.ModelViewSet):
    """
    用户关注视图集
    
    提供Member用户之间关注的增删查功能
    """
    serializer_class = MemberFollowSerializer
    permission_classes = [MemberFollowPermission]
    authentication_classes = [JWTAuthentication]
    pagination_class = StandardResultsSetPagination
    queryset = MemberFollow.objects.all().select_related('follower', 'following', 'tenant')
    
    def get_queryset(self):
        """
        获取当前用户发起的关注列表
        """
        member = self.request.user
        return self.queryset.filter(follower=member, tenant=member.tenant)
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return MemberFollowCreateSerializer
        return MemberFollowSerializer
    
    def perform_create(self, serializer):
        """
        执行关注创建操作
        
        - 自动设置当前用户和租户
        - 记录关注时间
        """
        member = self.request.user
        serializer.save(follower=member, tenant=member.tenant)
        logger.info(f"Member {member.username} followed member {serializer.instance.following_id}")
    
    @extend_schema(
        summary="获取粉丝列表",
        description="""获取关注当前用户的粉丝列表。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以访问

**返回内容**:
- 关注记录ID和时间
- 粉丝的完整信息
- 是否互相关注（is_mutual）
- 支持分页

**使用场景**: Member查看有哪些用户关注了自己
        """,
        tags=["用户互动-关注"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
            OpenApiParameter(name="page", description="页码", required=False, type=int),
            OpenApiParameter(name="page_size", description="每页数量", required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(
                description="获取成功",
                response=MemberFollowSerializer(many=True)
            ),
            401: OpenApiResponse(description="未认证"),
        },
        examples=[
            OpenApiExample(
                'Followers List Success',
                summary='获取粉丝列表成功示例',
                value={
                    'count': 25,
                    'next': None,
                    'previous': None,
                    'results': [
                        {
                            'id': 45,
                            'follower': 15,
                            'following': 5,
                            'follower_info': {
                                'id': 15,
                                'username': 'follower_user',
                                'nick_name': '粉丝用户',
                                'avatar': 'https://example.com/avatar5.jpg'
                            },
                            'following_info': {
                                'id': 5,
                                'username': 'member_user',
                                'nick_name': '普通用户',
                                'avatar': 'https://example.com/avatar1.jpg'
                            },
                            'is_mutual': True,
                            'tenant': 1,
                            'created_at': '2024-01-21T09:00:00Z'
                        }
                    ]
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='followers')
    def followers(self, request):
        """获取粉丝列表"""
        member = request.user
        
        queryset = MemberFollow.objects.filter(
            following=member,
            tenant=member.tenant
        ).select_related('follower', 'following', 'tenant')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="通过用户ID取消关注",
        description="""根据被关注用户ID取消关注（便捷方法）。
        
**权限要求**:
- 需要认证（登录）

**业务规则**:
- 如果未关注该用户，返回404

**使用场景**: Member在用户详情页点击取消关注按钮（已知用户ID，不需要知道关注记录ID）
        """,
        tags=["用户互动-关注"],
        parameters=[
            OpenApiParameter(name="member_id", description="被关注用户ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            204: OpenApiResponse(description="取消关注成功"),
            401: OpenApiResponse(description="未认证"),
            404: OpenApiResponse(description="关注记录不存在"),
        },
        examples=[
            OpenApiExample(
                'Unfollow By Member Success',
                summary='取消关注成功',
                value={'message': '已取消关注'},
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['delete'], url_path='by-member/(?P<member_id>[^/.]+)')
    def unfollow_by_member(self, request, member_id=None):
        """根据用户ID取消关注"""
        member = request.user
        
        # 查找关注记录
        follow = get_object_or_404(
            MemberFollow,
            follower=member,
            following_id=member_id,
            tenant=member.tenant
        )
        
        # 删除关注
        follow.delete()
        logger.info(f"Member {member.username} unfollowed member {member_id}")
        
        return Response(
            {'message': _('已取消关注')},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @extend_schema(
        summary="检查是否已关注用户",
        description="""检查当前用户是否已关注指定用户。
        
**权限要求**:
- 需要认证（登录）

**返回内容**:
- is_following: 是否已关注
- follow_id: 关注记录ID（如已关注）
- is_mutual: 是否互相关注
- created_at: 关注时间（如已关注）

**使用场景**: 前端显示用户详情时，判断是否显示"已关注"状态
        """,
        tags=["用户互动-关注"],
        parameters=[
            OpenApiParameter(name="member_id", description="用户ID", required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="查询成功",
                response={
                    'type': 'object',
                    'properties': {
                        'is_following': {'type': 'boolean'},
                        'follow_id': {'type': 'integer', 'nullable': True},
                        'is_mutual': {'type': 'boolean'},
                        'created_at': {'type': 'string', 'format': 'date-time', 'nullable': True}
                    }
                }
            ),
            401: OpenApiResponse(description="未认证"),
            404: OpenApiResponse(description="用户不存在"),
        },
        examples=[
            OpenApiExample(
                'Member Is Following',
                summary='用户已关注',
                value={
                    'is_following': True,
                    'follow_id': 30,
                    'is_mutual': True,
                    'created_at': '2024-01-20T11:00:00Z'
                },
                response_only=True,
            ),
            OpenApiExample(
                'Member Not Following',
                summary='用户未关注',
                value={
                    'is_following': False,
                    'follow_id': None,
                    'is_mutual': False,
                    'created_at': None
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='check/(?P<member_id>[^/.]+)')
    def check_follow(self, request, member_id=None):
        """检查是否已关注某用户"""
        member = request.user
        
        # 验证用户存在
        target_member = get_object_or_404(Member, id=member_id, tenant=member.tenant)
        
        # 查找关注记录
        follow = MemberFollow.objects.filter(
            follower=member,
            following=target_member
        ).first()
        
        if follow:
            # 检查是否互相关注
            is_mutual = MemberFollow.objects.filter(
                follower=target_member,
                following=member
            ).exists()
            
            return Response({
                'is_following': True,
                'follow_id': follow.id,
                'is_mutual': is_mutual,
                'created_at': follow.created_at
            })
        else:
            return Response({
                'is_following': False,
                'follow_id': None,
                'is_mutual': False,
                'created_at': None
            })
    
    @extend_schema(
        summary="获取互相关注列表",
        description="""获取与当前用户互相关注的用户列表。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以访问

**返回内容**:
- 互相关注的用户信息
- 关注时间
- 支持分页

**使用场景**: Member查看与自己互相关注（好友）的用户
        """,
        tags=["用户互动-关注"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
            OpenApiParameter(name="page", description="页码", required=False, type=int),
            OpenApiParameter(name="page_size", description="每页数量", required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(
                description="获取成功",
                response=MemberFollowSerializer(many=True)
            ),
            401: OpenApiResponse(description="未认证"),
        },
        examples=[
            OpenApiExample(
                'Mutual Follows Success',
                summary='获取互相关注列表成功示例',
                value={
                    'count': 10,
                    'next': None,
                    'previous': None,
                    'results': [
                        {
                            'id': 30,
                            'follower': 5,
                            'following': 12,
                            'follower_info': {
                                'id': 5,
                                'username': 'member_user',
                                'nick_name': '普通用户',
                                'avatar': 'https://example.com/avatar1.jpg'
                            },
                            'following_info': {
                                'id': 12,
                                'username': 'friend_user',
                                'nick_name': '好友用户',
                                'avatar': 'https://example.com/avatar4.jpg'
                            },
                            'is_mutual': True,
                            'tenant': 1,
                            'created_at': '2024-01-20T11:00:00Z'
                        }
                    ]
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='mutual')
    def mutual_follows(self, request):
        """获取互相关注列表"""
        member = request.user
        
        # 获取我关注的用户ID列表
        my_following_ids = MemberFollow.objects.filter(
            follower=member,
            tenant=member.tenant
        ).values_list('following_id', flat=True)
        
        # 获取关注我的用户中，我也关注的用户（互相关注）
        queryset = MemberFollow.objects.filter(
            follower=member,
            following_id__in=MemberFollow.objects.filter(
                following=member,
                tenant=member.tenant
            ).values_list('follower_id', flat=True),
            tenant=member.tenant
        ).select_related('follower', 'following', 'tenant')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取关注统计信息",
        description="""获取当前用户的关注统计数据。
        
**权限要求**:
- 需要认证（登录）
- 只有Member用户可以访问

**返回内容**:
- following_count: 关注数（我关注了多少人）
- followers_count: 粉丝数（多少人关注我）
- mutual_count: 互相关注数（好友数）

**使用场景**: 用户个人主页显示关注统计
        """,
        tags=["用户互动-关注"],
        parameters=[
            OpenApiParameter(name="X-Tenant-ID", description="租户ID（必须）", required=True, type=str, location=OpenApiParameter.HEADER),
        ],
        responses={
            200: OpenApiResponse(
                description="获取成功",
                response={
                    'type': 'object',
                    'properties': {
                        'following_count': {'type': 'integer'},
                        'followers_count': {'type': 'integer'},
                        'mutual_count': {'type': 'integer'}
                    }
                }
            ),
            401: OpenApiResponse(description="未认证"),
        },
        examples=[
            OpenApiExample(
                'Follow Stats Success',
                summary='获取关注统计成功示例',
                value={
                    'following_count': 15,
                    'followers_count': 25,
                    'mutual_count': 10
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """获取关注统计信息"""
        member = request.user
        
        # 关注数
        following_count = MemberFollow.objects.filter(
            follower=member,
            tenant=member.tenant
        ).count()
        
        # 粉丝数
        followers_count = MemberFollow.objects.filter(
            following=member,
            tenant=member.tenant
        ).count()
        
        # 互相关注数
        my_following_ids = MemberFollow.objects.filter(
            follower=member,
            tenant=member.tenant
        ).values_list('following_id', flat=True)
        
        mutual_count = MemberFollow.objects.filter(
            follower__in=my_following_ids,
            following=member,
            tenant=member.tenant
        ).count()
        
        return Response({
            'following_count': following_count,
            'followers_count': followers_count,
            'mutual_count': mutual_count
        })
