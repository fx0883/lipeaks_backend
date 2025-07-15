"""
用户菜单视图
"""
import logging
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse

from menus.models import Menu, UserMenu
from menus.serializers import MenuTreeSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取当前用户的菜单",
        description="获取当前登录用户能够访问的菜单列表，返回树形结构的菜单数据",
        tags=["用户菜单"],
        responses={
            200: OpenApiResponse(
                description="用户的菜单列表",
                examples=[
                    OpenApiExample(
                        name="成功响应",
                        value={
                            "menus": [
                                {
                                    "id": 1,
                                    "name": "用户管理",
                                    "code": "user_management",
                                    "icon": "user-group",
                                    "path": "/users",
                                    "component": "layout/users/index",
                                    "order": 1,
                                    "is_active": True,
                                    "children": [
                                        {
                                            "id": 2,
                                            "name": "用户列表",
                                            "code": "user_list",
                                            "icon": "list",
                                            "path": "/users/list",
                                            "component": "views/users/list",
                                            "order": 1,
                                            "is_active": True,
                                            "children": []
                                        }
                                    ]
                                },
                                {
                                    "id": 3,
                                    "name": "内容管理",
                                    "code": "content_management",
                                    "icon": "document",
                                    "path": "/content",
                                    "component": "layout/content/index",
                                    "order": 2,
                                    "is_active": True,
                                    "children": []
                                }
                            ]
                        }
                    )
                ]
            )
        }
    ),
)
class UserMenuViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    用户菜单视图集
    
    提供当前登录用户的菜单数据，包括：
    - 超级管理员：可访问所有激活的菜单
    - 管理员：可访问分配给自己的菜单
    - 普通用户：可访问分配给自己的菜单
    """
    serializer_class = MenuTreeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        获取当前用户的菜单
        """
        user = self.request.user
        
        if user.is_super_admin:
            # 超级管理员可以访问所有激活的菜单
            return Menu.objects.filter(is_active=True, parent__isnull=True)
        
        if user.is_admin:
            # 管理员只能访问分配给自己的激活菜单
            user_menu_ids = UserMenu.objects.filter(
                user=user,
                is_active=True
            ).values_list('menu_id', flat=True)
            
            return Menu.objects.filter(
                id__in=user_menu_ids,
                is_active=True,
                parent__isnull=True
            )
        
        # 普通用户也可以获取分配给自己的菜单
        user_menu_ids = UserMenu.objects.filter(
            user=user,
            is_active=True
        ).values_list('menu_id', flat=True)
        
        return Menu.objects.filter(
            id__in=user_menu_ids,
            is_active=True,
            parent__isnull=True
        )
    
    def list(self, request, *args, **kwargs):
        """
        获取当前用户的菜单
        """
        queryset = self.get_queryset()
        
        # 设置序列化上下文
        context = self.get_serializer_context()
        context['is_active'] = True
        
        serializer = self.get_serializer(queryset, many=True, context=context)
        return Response({"menus": serializer.data}) 