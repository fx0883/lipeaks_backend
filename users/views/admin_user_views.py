"""
管理员用户(User)相关视图
"""
import logging
import os
import uuid
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

from common.permissions import IsSuperAdmin, IsAdmin
from common.utils.user_permissions import is_super_admin, is_admin
from users.models import User
from users.serializers import (
    UserSerializer, 
    UserCreateSerializer, 
    ChangePasswordSerializer,
    SuperAdminCreateSerializer,
    UserRoleSerializer,
    UserUpdateSerializer
)
from common.schema import api_schema, common_search_parameter, user_status_parameter, user_admin_parameter, common_pagination_parameters, common_error_responses
from tenants.models import Tenant

logger = logging.getLogger(__name__)

class CurrentAdminUserView(APIView):
    """
    获取和更新current登录管理员用户信息
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    @extend_schema(
        summary="获取current管理员信息",
        description="获取current登录管理员用户的详细信息。需要管理员权限。",
        responses={
            200: OpenApiResponse(
                description="成功获取管理员信息",
                response=UserSerializer
            ),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足")
        },
        tags=["管理员用户"]
    )
    def get(self, request, *args, **kwargs):
        # 检查用户是否为管理员
        if not is_admin(request.user):
            return Response(
                {"detail": "该接口仅适用于管理员"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 使用自定义序列化器返回详细用户信息
        serializer = UserSerializer(request.user, context={'request': request})
        logger.info(f"管理员用户 {request.user.username} 获取了自己的信息")
        return Response(serializer.data)
    
    @extend_schema(
        summary="更新current管理员信息",
        description="更新current登录管理员用户的基本信息。需要管理员权限。",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                description="成功更新管理员信息",
                response=UserSerializer
            ),
            400: OpenApiResponse(description="请求参数错误"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足")
        },
        tags=["管理员用户"]
    )
    def put(self, request, *args, **kwargs):
        """
        更新current用户的基本信息
        """
        # 检查用户是否为管理员
        if not is_admin(request.user):
            return Response(
                {"detail": "该接口仅适用于管理员"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 不允许通过此接口修改某些字段
        protected_fields = ['username', 'email', 'is_active', 'is_admin', 'is_super_admin', 'tenant']
        for field in protected_fields:
            if field in request.data:
                return Response(
                    {"detail": f"不允许修改 {field} 字段"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"管理员用户 {request.user.username} 更新了自己的基本信息")
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserListCreateView(generics.ListCreateAPIView):
    """
    管理员用户列表和创建视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    
    def get_serializer_class(self):
        # 创建用户时使用创建序列化器
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def get_serializer_context(self):
        """
        添加请求到序列化器上下文
        """
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
        })
        return context
    
    @extend_schema(
        summary="获取管理员用户列表",
        description="获取系统中的管理员用户列表，支持搜索和分页。权限要求: 超级管理员可查看所有管理员；租户管理员只能查看自己租户的管理员。",
        responses={
            200: OpenApiResponse(
                description="获取管理员列表成功",
                examples=[
                    OpenApiExample(
                        name="管理员列表示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "获取成功",
                            "data": {
                                "count": 5,
                                "next": "http://example.com/api/v1/admin-users/?page=2",
                                "previous": None,
                                "results": [
                                    {
                                        "id": 1,
                                        "username": "admin",
                                        "email": "admin@example.com",
                                        "phone": "13800138000",
                                        "nick_name": "系统管理员",
                                        "tenant": None,
                                        "tenant_name": None,
                                        "is_admin": True,
                                        "is_member": False,
                                        "is_super_admin": True,
                                        "role": "超级管理员"
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
            **common_error_responses
        },
        parameters=[
            OpenApiParameter(
                name='search',
                description='搜索关键词，支持用户名、邮箱、昵称和手机号码搜索',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            ), 
            OpenApiParameter(
                name='status',
                description='用户状态筛选',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='is_super_admin',
                description='是否为超级管理员 (true/false)',
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='tenant_id',
                description='租户ID，用于筛选特定租户下的管理员',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY
            )
        ] + common_pagination_parameters,
        tags=["管理员用户"]
    )
    def get(self, request, *args, **kwargs):
        try:
            return self.list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"获取管理员列表失败: {str(e)}")
            return Response(
                {"detail": f"获取管理员列表失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="创建新管理员",
        description="创建新管理员用户。权限要求: 超级管理员可创建任意租户下的管理员；租户管理员只能创建自己租户的管理员，且无法指定其他租户。",
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="管理员创建成功",
                examples=[
                    OpenApiExample(
                        name="创建管理员成功示例",
                        value={
                            "success": True,
                            "code": 2001,
                            "message": "创建成功",
                            "data": {
                                "id": 10,
                                "username": "newadmin",
                                "email": "newadmin@example.com",
                                "phone": "13900139000",
                                "nick_name": "新管理员",
                                "tenant": 1,
                                "tenant_name": "测试租户",
                                "is_admin": True,
                                "is_member": False,
                                "is_super_admin": False,
                                "role": "租户管理员"
                            }
                        }
                    )
                ]
            ),
            **common_error_responses
        },
        tags=["管理员用户"]
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        获取查询集，支持过滤
        """
        user = self.request.user
        
        # 过滤仅显示管理员用户
        queryset = User.objects.filter(is_admin=True, is_deleted=False)
        
        # 超级管理员可以看到所有管理员
        if is_super_admin(user):
            pass # 保持查询集不变
        # 租户管理员只能看到自己租户的管理员
        elif is_admin(user) and user.tenant:
            queryset = queryset.filter(tenant=user.tenant)
        # 其他情况返回空查询集
        else:
            queryset = User.objects.none()
        
        # 搜索条件
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) | 
                Q(nick_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # 状态过滤
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 超级管理员过滤
        is_super_admin_param = self.request.query_params.get('is_super_admin', None)
        if is_super_admin_param is not None:
            is_super = is_super_admin_param.lower() == 'true'
            queryset = queryset.filter(is_super_admin=is_super)
        
        # 租户ID过滤
        tenant_id = self.request.query_params.get('tenant_id', None)
        if tenant_id and is_super_admin(user):  # 只有超级管理员可以按租户筛选
            try:
                tenant_id = int(tenant_id)
                queryset = queryset.filter(tenant_id=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                # 返回空查询集，因为无效的租户ID不应该匹配任何用户
                queryset = User.objects.none()
        
        return queryset
    
    def perform_create(self, serializer):
        """
        创建管理员用户，设置租户
        """
        user = self.request.user
        
        # 确保创建的是管理员用户
        if not serializer.validated_data.get('is_admin', False):
            serializer.validated_data['is_admin'] = True
            logger.info("强制设置创建用户为管理员")
        
        # 设置租户
        tenant = None
        if not is_super_admin(user):
            # 非超级管理员只能在自己租户创建用户
            tenant = user.tenant
            if not tenant:
                raise PermissionDenied("You have no associated tenant and cannot create an admin")
        
        # 如果传入了tenant_id参数并且是超级管理员
        tenant_id = self.request.data.get('tenant_id')
        if tenant_id and is_super_admin(user):
            try:
                tenant_id = int(tenant_id)
                tenant = get_object_or_404(Tenant, pk=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                raise serializers.ValidationError({"tenant_id": f"无效的租户ID: {tenant_id}"})
        elif tenant_id and not is_super_admin(user):
            # 非超级管理员尝试指定租户ID
            try:
                tenant_id = int(tenant_id)
                requested_tenant = get_object_or_404(Tenant, pk=tenant_id)
                if requested_tenant.id != user.tenant.id:
                    raise PermissionDenied("You can only create admins in your own tenant")
                tenant = user.tenant
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                raise serializers.ValidationError({"tenant_id": f"无效的租户ID: {tenant_id}"})
        
        logger.info(f"用户 {user.username} 创建新管理员，租户设置为: {tenant.name if tenant else '无租户'}")
        serializer.save(tenant=tenant)


class AdminUserRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    管理员用户详情、更新和删除视图
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    @extend_schema(
        summary="获取管理员详情",
        description="获取单个管理员用户的详细信息。权限要求：超级管理员可查看任何管理员；租户管理员只能查看自己租户的管理员。",
        responses={
            200: OpenApiResponse(description="成功获取管理员详情", response=UserSerializer),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="更新管理员信息",
        description="更新指定管理员的信息。权限要求：超级管理员可更新任何管理员；租户管理员只能更新自己租户的管理员。",
        request=UserUpdateSerializer,
        responses={
            200: OpenApiResponse(description="成功更新管理员信息", response=UserSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户"]
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    @extend_schema(
        summary="部分更新管理员信息",
        description="部分更新指定管理员的信息。权限要求：超级管理员可更新任何管理员；租户管理员只能更新自己租户的管理员。",
        request=UserUpdateSerializer,
        responses={
            200: OpenApiResponse(description="成功更新管理员信息", response=UserSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户"]
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="删除管理员",
        description="删除指定管理员（软删除）。权限要求：超级管理员可删除任何管理员（除自己外）；租户管理员只能删除自己租户的其他管理员。",
        responses={
            204: OpenApiResponse(description="成功删除管理员"),
            400: OpenApiResponse(description="请求参数错误，例如尝试删除current登录账号"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_serializer_context(self):
        """
        添加请求到序列化器上下文
        """
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
        })
        return context
    
    def get_queryset(self):
        """
        获取查询集
        """
        user = self.request.user
        
        # 只获取管理员用户
        queryset = User.objects.filter(is_admin=True, is_deleted=False)
        
        # 超级管理员可以操作所有管理员用户
        if is_super_admin(user):
            return queryset
            
        # 租户管理员只能操作自己租户的管理员
        if is_admin(user) and user.tenant:
            return queryset.filter(tenant=user.tenant)
            
        # 其他情况返回空查询集
        return User.objects.none()
    
    def perform_update(self, serializer):
        """
        执行更新操作
        """
        instance = serializer.instance
        user = self.request.user
        
        # 不允许非超级管理员修改 is_super_admin 字段
        if not is_super_admin(user) and 'is_super_admin' in serializer.validated_data:
            raise PermissionDenied("Only super admins can modify the super admin flag")
            
        # 确保用户仍然是管理员
        serializer.validated_data['is_admin'] = True
        
        # 日志记录
        logger.info(f"用户 {user.username} 更新管理员 {instance.username} 的信息")
        
        # 执行更新
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        执行删除操作（软删除）
        """
        user = self.request.user
        
        # 检查是否尝试删除超级管理员
        if is_super_admin(instance) and not is_super_admin(user):
            logger.warning(f"用户 {user.username} 尝试删除超级管理员 {instance.username}，操作被拒绝")
            raise PermissionDenied("Only super admins can delete other super admins")
        
        # 检查是否尝试删除current登录账号
        if instance.pk == user.pk:
            logger.warning(f"用户 {user.username} 尝试删除自己的账号，操作被拒绝")
            raise PermissionDenied("Cannot delete the currently logged-in account")
        
        # 日志记录
        logger.info(f"用户 {user.username} 软删除管理员 {instance.username}")
        
        # 执行软删除
        instance.soft_delete()


class SimpleResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="响应消息")


class GrantSuperAdminView(APIView):
    """
    授予超级管理员权限视图
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SimpleResponseSerializer  # 添加序列化器类
    
    @extend_schema(
        summary="授予超级管理员权限",
        description="将指定管理员提升为超级管理员。只有现有的超级管理员可以执行此操作。",
        responses={
            200: OpenApiResponse(
                description="授权成功",
                response=SimpleResponseSerializer
            ),
            400: OpenApiResponse(
                description="操作失败",
                response=SimpleResponseSerializer
            ),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户", "权限管理"]
    )
    def post(self, request, pk):
        try:
            # 获取目标用户
            target_user = get_object_or_404(User, pk=pk, is_deleted=False)
            
            # 检查目标用户是否已经是管理员
            if not is_admin(target_user):
                return Response(
                    {"detail": "只能为管理员授予超级管理员权限"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查用户是否已经是超级管理员
            if is_super_admin(target_user):
                return Response(
                    {"detail": f"用户 {target_user.username} 已经是超级管理员"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 授予超级管理员权限
            target_user.is_super_admin = True
            target_user.is_staff = True
            target_user.is_superuser = True
            target_user.tenant = None  # 超级管理员不属于任何租户
            target_user.save()
            
            logger.info(f"超级管理员 {request.user.username} 授予了 {target_user.username} 超级管理员权限")
            
            return Response(
                {"detail": f"已成功将 {target_user.username} 设为超级管理员"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"授予超级管理员权限时出错: {str(e)}")
            return Response(
                {"detail": f"操作失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RevokeSuperAdminView(APIView):
    """
    撤销超级管理员权限视图
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SimpleResponseSerializer  # 添加序列化器类
    
    @extend_schema(
        summary="撤销超级管理员权限",
        description="撤销指定超级管理员的权限，将其降为租户管理员。只有超级管理员可以执行此操作，并且不能撤销自己的权限。",
        responses={
            200: OpenApiResponse(
                description="撤销成功",
                response=SimpleResponseSerializer
            ),
            400: OpenApiResponse(
                description="操作失败",
                response=SimpleResponseSerializer
            ),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户", "权限管理"]
    )
    def post(self, request, pk):
        try:
            # 获取目标用户
            target_user = get_object_or_404(User, pk=pk, is_deleted=False)
            
            # 不能撤销自己的超级管理员权限
            if target_user.pk == request.user.pk:
                return Response(
                    {"detail": "不能撤销自己的超级管理员权限"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查用户是否是超级管理员
            if not is_super_admin(target_user):
                return Response(
                    {"detail": f"用户 {target_user.username} 不是超级管理员"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 撤销超级管理员权限
            target_user.is_super_admin = False
            target_user.is_staff = True  # 仍然保留管理员后台权限
            target_user.is_superuser = False
            
            # 需要为用户指定一个租户，因为超级管理员不属于任何租户
            tenant_id = request.data.get('tenant_id')
            if tenant_id:
                try:
                    tenant_id = int(tenant_id)
                    tenant = get_object_or_404(Tenant, pk=tenant_id)
                    target_user.tenant = tenant
                except (ValueError, TypeError, Tenant.DoesNotExist):
                    logger.error(f"无效的租户ID: {tenant_id}")
                    return Response(
                        {"detail": f"无效的租户ID: {tenant_id}，撤销超级管理员权限时必须指定有效的租户"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"detail": "撤销超级管理员权限时必须指定新的租户ID"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            target_user.save()
            
            logger.info(f"超级管理员 {request.user.username} 撤销了 {target_user.username} 的超级管理员权限，并将其分配给租户: {target_user.tenant.name}")
            
            return Response(
                {"detail": f"已成功撤销 {target_user.username} 的超级管理员权限，并将其设为租户 {target_user.tenant.name} 的管理员"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"撤销超级管理员权限时出错: {str(e)}")
            return Response(
                {"detail": f"操作失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminPasswordUpdateView(generics.UpdateAPIView):
    """
    管理员密码更新视图
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    def get_object(self):
        return self.request.user
    
    @extend_schema(
        summary="更新管理员密码",
        description="允许已认证的管理员修改自己的密码，需要提供旧密码和新密码",
        responses={
            200: OpenApiResponse(
                description="密码修改成功",
                examples=[
                    OpenApiExample(
                        name="密码修改成功示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "密码修改成功",
                            "data": {
                                "detail": "密码修改成功"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="请求参数错误"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足")
        },
        tags=["管理员用户"]
    )
    def update(self, request, *args, **kwargs):
        """
        更新用户密码
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # 检查旧密码
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": ["Incorrect old password"]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 设置新密码
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            logger.info(f"用户 {user.username} 成功修改了密码")
            
            return Response({
                "message": "密码修改成功",
                "detail": "密码修改成功"
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 覆盖这两个方法，确保它们调用update方法
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class SuperAdminCreateView(generics.CreateAPIView):
    """
    创建超级管理员账号视图
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SuperAdminCreateSerializer
    
    def perform_create(self, serializer):
        """
        设置为超级管理员
        """
        logger.info(f"超级管理员 {self.request.user.username} 创建了新的超级管理员账号")
        serializer.save()


class AdminUserAvatarUploadView(APIView):
    """
    管理员用户头像上传视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="上传current管理员头像",
        description="上传并更新current登录管理员用户的头像图片",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'avatar': {
                        'type': 'string',
                        'format': 'binary',
                        'description': '要上传的头像文件，支持JPG、PNG、GIF、WEBP或BMP格式',
                    },
                },
                'required': ['avatar']
            }
        },
        responses={
            200: OpenApiResponse(
                description="头像上传成功",
                response={
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string', 'example': '头像上传成功'},
                        'avatar': {'type': 'string', 'example': 'https://example.com/media/avatars/user-avatar.jpg'},
                    }
                }
            ),
            400: OpenApiResponse(
                description="请求错误",
                response={
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string', 'example': '未提供头像文件/不支持的文件类型/文件太大'},
                    }
                }
            ),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足"),
            500: OpenApiResponse(description="服务器内部错误")
        },
        tags=["管理员用户"]
    )
    def post(self, request, *args, **kwargs):
        """
        上传管理员用户头像
        """
        user = request.user
        
        # 检查用户是否为管理员
        if not is_admin(user):
            return Response(
                {"detail": "该接口仅适用于管理员"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        avatar_file = request.FILES.get('avatar')
        
        if not avatar_file:
            return Response(
                {"detail": "未提供头像文件"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件类型
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        ext = os.path.splitext(avatar_file.name)[1].lower()
        if ext not in valid_extensions:
            return Response(
                {"detail": "不支持的文件类型，请上传JPG、PNG、GIF、WEBP或BMP格式的图片"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件大小
        if avatar_file.size > 2 * 1024 * 1024:  # 2MB
            return Response(
                {"detail": "文件太大，头像大小不能超过2MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 删除旧头像文件（如果存在）
            if user.avatar and user.avatar.startswith(settings.MEDIA_URL):
                # 获取相对路径
                avatar_path = user.avatar.replace(settings.MEDIA_URL, '', 1)
                old_avatar_path = os.path.join(settings.MEDIA_ROOT, avatar_path)
                
                # 检查文件是否存在，如果存在则删除
                if os.path.isfile(old_avatar_path):
                    try:
                        os.remove(old_avatar_path)
                        logger.info(f"删除管理员用户 {user.username} 的旧头像 {old_avatar_path}")
                    except OSError as e:
                        logger.warning(f"删除旧头像文件失败: {str(e)}")
            
            # 生成唯一文件名，避免覆盖已有文件
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            # 确保媒体目录存在
            avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(avatar_dir, unique_filename)
            with open(file_path, 'wb+') as destination:
                for chunk in avatar_file.chunks():
                    destination.write(chunk)
            
            # 生成相对URL路径（保存到数据库）
            relative_url = f"{settings.MEDIA_URL}avatars/{unique_filename}"
            
            # 更新用户头像URL
            user.avatar = relative_url
            user.save(update_fields=['avatar'])
            
            logger.info(f"管理员用户 {user.username} 上传了新头像")
            
            return Response({
                "detail": "头像上传成功",
                "avatar": relative_url  # 返回给前端的是相对路径
            })
        
        except Exception as e:
            logger.error(f"头像上传失败: {str(e)}")
            return Response(
                {"detail": f"头像上传失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminUserSpecificAvatarUploadView(APIView):
    """
    为特定管理员用户上传头像视图
    
    允许超级管理员和租户管理员为其管理权限内的管理员用户上传头像
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="为特定管理员上传头像",
        description="允许超级管理员和租户管理员为特定管理员用户上传头像。租户管理员只能为其所属租户的管理员上传头像，超级管理员可以为任何管理员上传头像。",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'avatar': {
                        'type': 'string',
                        'format': 'binary',
                        'description': '要上传的头像文件，支持JPG、PNG、GIF、WEBP或BMP格式',
                    },
                },
                'required': ['avatar']
            }
        },
        responses={
            200: OpenApiResponse(
                description="头像上传成功",
                response={
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string', 'example': '头像上传成功'},
                        'avatar': {'type': 'string', 'example': 'https://example.com/media/avatars/user-avatar.jpg'},
                    }
                }
            ),
            400: OpenApiResponse(
                description="请求错误",
                response={
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string', 'example': '未提供头像文件/不支持的文件类型/文件太大'},
                    }
                }
            ),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在"),
            500: OpenApiResponse(description="服务器内部错误"),
        },
        tags=["管理员用户"]
    )
    def post(self, request, pk, *args, **kwargs):
        """
        为特定管理员用户上传头像
        """
        # 获取目标用户
        try:
            target_user = User.objects.get(pk=pk, is_admin=True, is_deleted=False)
        except User.DoesNotExist:
            return Response(
                {"detail": "管理员用户不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 权限检查：租户管理员只能为其租户内的管理员上传头像
        current_user = request.user
        if not is_super_admin(current_user) and (current_user.tenant != target_user.tenant or not is_admin(current_user)):
            return Response(
                {"detail": "您没有权限为该管理员上传头像"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        avatar_file = request.FILES.get('avatar')
        
        if not avatar_file:
            return Response(
                {"detail": "未提供头像文件"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件类型
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        ext = os.path.splitext(avatar_file.name)[1].lower()
        if ext not in valid_extensions:
            return Response(
                {"detail": "不支持的文件类型，请上传JPG、PNG、GIF、WEBP或BMP格式的图片"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件大小
        if avatar_file.size > 2 * 1024 * 1024:  # 2MB
            return Response(
                {"detail": "文件太大，头像大小不能超过2MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 删除旧头像文件（如果存在）
            if target_user.avatar and target_user.avatar.startswith(settings.MEDIA_URL):
                # 获取相对路径
                avatar_path = target_user.avatar.replace(settings.MEDIA_URL, '', 1)
                old_avatar_path = os.path.join(settings.MEDIA_ROOT, avatar_path)
                
                # 检查文件是否存在，如果存在则删除
                if os.path.isfile(old_avatar_path):
                    try:
                        os.remove(old_avatar_path)
                        logger.info(f"删除管理员用户 {target_user.username} 的旧头像 {old_avatar_path}")
                    except OSError as e:
                        logger.warning(f"删除旧头像文件失败: {str(e)}")
            
            # 生成唯一文件名，避免覆盖已有文件
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            # 确保媒体目录存在
            avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(avatar_dir, unique_filename)
            with open(file_path, 'wb+') as destination:
                for chunk in avatar_file.chunks():
                    destination.write(chunk)
            
            # 生成相对URL路径（保存到数据库）
            relative_url = f"{settings.MEDIA_URL}avatars/{unique_filename}"
            
            # 更新用户头像URL
            target_user.avatar = relative_url
            target_user.save(update_fields=['avatar'])
            
            logger.info(f"管理员用户 {current_user.username} 为管理员 {target_user.username} 上传了新头像")
            
            return Response({
                "detail": "头像上传成功",
                "avatar": relative_url  # 返回给前端的是相对路径
            })
        
        except Exception as e:
            logger.error(f"头像上传失败: {str(e)}")
            return Response(
                {"detail": f"头像上传失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeactivateAdminUserView(APIView):
    """
    停用管理员用户视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = SimpleResponseSerializer  # 使用简单响应序列化器
    
    @extend_schema(
        summary="停用管理员",
        description="停用指定管理员用户。权限要求：超级管理员可停用任何管理员（除自己外）；租户管理员只能停用自己租户的其他管理员。",
        responses={
            200: OpenApiResponse(
                description="停用成功",
                response=SimpleResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="停用成功示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "操作成功",
                            "data": {
                                "detail": "管理员已成功停用"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="请求参数错误，例如尝试停用current登录账号"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户"]
    )
    def post(self, request, pk):
        """
        停用指定管理员
        """
        try:
            # 获取要停用的用户
            user = get_object_or_404(User, pk=pk)
            
            # 不允许停用自己
            if user.id == request.user.id:
                return Response(
                    {"detail": "不能停用current登录的账号"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查权限：超级管理员可以停用任何管理员，租户管理员只能停用自己租户的管理员
            if not is_super_admin(request.user) and (is_super_admin(user) or user.tenant != request.user.tenant):
                return Response(
                    {"detail": "没有权限停用此管理员"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 执行停用操作
            user.is_active = False
            user.status = 'inactive'
            user.save(update_fields=['is_active', 'status'])
            
            logger.info(f"管理员 {request.user.username} 停用了管理员 {user.username}")
            
            return Response(
                {"detail": "管理员已成功停用"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"停用管理员失败: {str(e)}")
            return Response(
                {"detail": f"停用管理员失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActivateAdminUserView(APIView):
    """
    激活管理员用户视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = SimpleResponseSerializer  # 使用简单响应序列化器
    
    @extend_schema(
        summary="激活管理员",
        description="激活指定管理员用户。权限要求：超级管理员可激活任何管理员；租户管理员只能激活自己租户的管理员。",
        responses={
            200: OpenApiResponse(
                description="激活成功",
                response=SimpleResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="激活成功示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "操作成功",
                            "data": {
                                "detail": "管理员已成功激活"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="管理员不存在")
        },
        tags=["管理员用户"]
    )
    def post(self, request, pk):
        """
        激活指定管理员
        """
        try:
            # 获取要激活的用户
            user = get_object_or_404(User, pk=pk)
            
            # 检查权限：超级管理员可以激活任何管理员，租户管理员只能激活自己租户的管理员
            if not is_super_admin(request.user) and (is_super_admin(user) or user.tenant != request.user.tenant):
                return Response(
                    {"detail": "没有权限激活此管理员"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 执行激活操作
            user.is_active = True
            user.status = 'active'
            user.save(update_fields=['is_active', 'status'])
            
            logger.info(f"管理员 {request.user.username} 激活了管理员 {user.username}")
            
            return Response(
                {"detail": "管理员已成功激活"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"激活管理员失败: {str(e)}")
            return Response(
                {"detail": f"激活管理员失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 