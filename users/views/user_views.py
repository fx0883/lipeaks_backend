"""
用户相关视图

包含用户角色更新相关的视图
"""
import logging
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse

from common.permissions import IsSuperAdmin, IsAdmin
from common.utils.user_permissions import is_super_admin, is_admin
from common.exceptions import UserPermissionDeniedException
from users.models import User
from users.serializers import UserRoleUpdateSerializer

logger = logging.getLogger(__name__)

class UserRoleUpdateView(APIView):
    """
    更新用户角色视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    @extend_schema(
        summary="更新用户角色",
        description="更新指定用户的角色（管理员/普通成员）。超级管理员可以更新任何用户的角色；租户管理员只能更新同一租户内的普通用户角色。",
        request=UserRoleUpdateSerializer,
        responses={
            200: OpenApiResponse(
                description="角色更新成功",
                response=UserRoleUpdateSerializer
            ),
            400: OpenApiResponse(
                description="请求参数错误",
                response={
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string', 'example': '不能修改超级管理员的角色'},
                        'is_admin': {'type': 'array', 'items': {'type': 'string'}}
                    }
                }
            ),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="用户不存在")
        },
        tags=["用户管理"]
    )
    def post(self, request, pk):
        # 获取用户
        user = self.request.user
        target_user = get_object_or_404(User, pk=pk)
        
        # 管理员权限检查
        if not is_super_admin(user) and user.tenant != target_user.tenant:
            raise UserPermissionDeniedException(
                detail='无权限更改其他租户的用户角色',
                user_id=user.id,
                target_user_id=target_user.id,
                user_tenant_id=user.tenant.id if user.tenant else None,
                target_tenant_id=target_user.tenant.id if target_user.tenant else None
            )
        
        # 不能修改超级管理员的角色
        if is_super_admin(target_user):
            return Response(
                {"detail": "不能修改超级管理员的角色"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 序列化处理
        serializer = UserRoleUpdateSerializer(target_user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"用户 {user.username} 更新了用户 {target_user.username} 的角色")
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)