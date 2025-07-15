"""
用户菜单管理视图
"""
import logging
from django.db import transaction
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse

from common.permissions import IsAdmin
from menus.models import UserMenu, Menu
from menus.serializers import (
    UserMenuDetailSerializer,
    UserMenusSerializer
)
from users.models import User

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取用户的菜单列表",
        description="获取指定用户的菜单列表，仅限超级管理员访问",
        tags=["用户菜单管理"],
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="管理员用户ID",
                location=OpenApiParameter.PATH,
                required=True,
                type=int
            )
        ],
        responses={
            200: OpenApiResponse(
                description="用户的菜单列表",
                examples=[
                    OpenApiExample(
                        name="成功响应",
                        value={
                            "user_id": 101,
                            "username": "admin123",
                            "menus": [
                                {
                                    "id": 1,
                                    "name": "用户管理",
                                    "code": "user_management",
                                    "is_active": True
                                },
                                {
                                    "id": 2,
                                    "name": "内容管理",
                                    "code": "content_management",
                                    "is_active": True
                                }
                            ]
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="用户不存在")
        }
    ),
    create=extend_schema(
        summary="分配菜单给用户",
        description="为指定用户分配菜单，仅限超级管理员操作",
        tags=["用户菜单管理"],
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="管理员用户ID",
                location=OpenApiParameter.PATH,
                required=True,
                type=int
            )
        ],
        request=UserMenusSerializer,
        responses={
            201: OpenApiResponse(
                description="菜单分配成功",
                examples=[
                    OpenApiExample(
                        name="成功响应",
                        value={
                            "assigned_menus": [
                                {
                                    "id": 1,
                                    "name": "用户管理"
                                },
                                {
                                    "id": 2,
                                    "name": "内容管理"
                                }
                            ]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="请求数据无效或目标用户不是管理员"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="用户不存在")
        }
    ),
    destroy=extend_schema(
        summary="移除用户的菜单",
        description="移除用户的特定菜单，仅限超级管理员操作",
        tags=["用户菜单管理"],
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="管理员用户ID",
                location=OpenApiParameter.PATH,
                required=True,
                type=int
            ),
            OpenApiParameter(
                name="pk",
                description="菜单ID",
                location=OpenApiParameter.PATH,
                required=True,
                type=int
            )
        ],
        responses={
            204: OpenApiResponse(description="菜单移除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="用户菜单关联不存在")
        }
    ),
)
class AdminMenuViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """
    管理员菜单管理视图集，用于超级管理员分配菜单给其他管理员用户
    """
    permission_classes = [IsAdmin]
    serializer_class = UserMenuDetailSerializer
    
    def get_queryset(self):
        """
        获取用户菜单关联
        """
        user_id = self.kwargs.get('user_id')
        current_user = self.request.user
        
        # 验证访问权限
        if not current_user.is_super_admin:
            return UserMenu.objects.none()
        
        return UserMenu.objects.filter(user_id=user_id, is_active=True)
    
    def list(self, request, *args, **kwargs):
        """
        获取用户的菜单列表
        """
        user_id = kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "用户不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            "user_id": user.id,
            "username": user.username,
            "menus": serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """
        为用户分配菜单
        """
        if not request.user.is_super_admin:
            return Response(
                {"detail": "只有超级管理员才能分配菜单给用户"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "用户不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查目标用户是否是管理员
        if not user.is_admin and not user.is_super_admin:
            return Response(
                {"detail": "只能为管理员用户分配菜单"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = UserMenusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        menu_ids = serializer.validated_data['menu_ids']
        menus = Menu.objects.filter(id__in=menu_ids)
        
        if len(menus) != len(menu_ids):
            return Response(
                {"detail": "包含无效的菜单ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assigned_menus = []
        with transaction.atomic():
            # 首先禁用不在当前列表中的所有菜单
            UserMenu.objects.filter(user=user).exclude(menu_id__in=menu_ids).update(is_active=False)
            
            # 然后添加或激活请求中的菜单
            for menu in menus:
                user_menu, created = UserMenu.objects.get_or_create(
                    user=user,
                    menu=menu,
                    defaults={'is_active': True}
                )
                if not created and not user_menu.is_active:
                    user_menu.is_active = True
                    user_menu.save()
                
                assigned_menus.append({
                    "id": menu.id,
                    "name": menu.name
                })
        
        logger.info(f"用户 '{user.username}' 分配了 {len(assigned_menus)} 个菜单，操作者: {request.user.username}")
        
        return Response({
            "assigned_menus": assigned_menus
        }, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """
        移除用户的特定菜单
        """
        if not request.user.is_super_admin:
            return Response(
                {"detail": "只有超级管理员才能移除用户的菜单"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = kwargs.get('user_id')
        menu_id = kwargs.get('pk')
        
        try:
            user_menu = UserMenu.objects.get(user_id=user_id, menu_id=menu_id)
        except UserMenu.DoesNotExist:
            return Response(
                {"detail": "用户菜单关联不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        username = user_menu.user.username
        menu_name = user_menu.menu.name
        
        user_menu.delete()
        logger.info(f"移除用户 '{username}' 的菜单 '{menu_name}'，操作者: {request.user.username}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary="批量移除用户菜单",
        description="批量移除用户的菜单，仅限超级管理员操作",
        tags=["用户菜单管理"],
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="管理员用户ID",
                location=OpenApiParameter.PATH,
                required=True,
                type=int
            )
        ],
        request=UserMenusSerializer,
        responses={
            204: OpenApiResponse(description="菜单批量移除成功"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="用户不存在")
        }
    )
    @action(detail=False, methods=['delete'], url_path='batch')
    def batch_remove(self, request, user_id=None):
        """
        批量移除用户菜单
        """
        if not request.user.is_super_admin:
            return Response(
                {"detail": "只有超级管理员才能批量移除用户的菜单"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "用户不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserMenusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        menu_ids = serializer.validated_data['menu_ids']
        removed_count = UserMenu.objects.filter(
            user_id=user_id,
            menu_id__in=menu_ids
        ).delete()[0]
        
        logger.info(f"批量移除用户 '{user.username}' 的 {removed_count} 个菜单，操作者: {request.user.username}")
        
        return Response(status=status.HTTP_204_NO_CONTENT) 