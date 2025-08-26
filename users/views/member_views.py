"""
普通用户(Member)相关视图
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
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from common.pagination import StandardResultsSetPagination

from common.permissions import IsAdmin, IsSuperAdmin
from users.models import Member
from users.serializers import (
    MemberSerializer, 
    MemberCreateSerializer,
    SubAccountSerializer,
    SubAccountCreateSerializer,
    UserPasswordUpdateSerializer
)
from common.schema import api_schema, common_search_parameter, user_status_parameter, common_pagination_parameters, common_error_responses
from tenants.models import Tenant

logger = logging.getLogger(__name__)

class MemberListCreateView(generics.ListCreateAPIView):
    """
    普通用户列表和创建视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = MemberSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        # 创建用户时使用创建序列化器
        if self.request.method == 'POST':
            return MemberCreateSerializer
        return MemberSerializer
    
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
        summary="获取普通用户列表",
        description="获取系统中的普通用户列表，支持搜索和分页。权限要求: 超级管理员可查看所有普通用户；租户管理员只能查看自己租户的普通用户。",
        responses={
            200: OpenApiResponse(
                description="获取普通用户列表成功",
                examples=[
                    OpenApiExample(
                        name="普通用户列表示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "获取成功",
                            "data": {
                                "count": 10,
                                "next": "http://example.com/api/v1/members/?page=2",
                                "previous": None,
                                "results": [
                                    {
                                        "id": 10,
                                        "username": "member1",
                                        "email": "member1@example.com",
                                        "phone": "13800138000",
                                        "nick_name": "普通用户1",
                                        "tenant": 1,
                                        "tenant_name": "测试租户",
                                        "is_sub_account": False,
                                        "parent": None,
                                        "parent_username": None
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
                name='is_sub_account',
                description='是否为子账号 (true/false)',
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='parent',
                description='父账号ID，用于筛选特定父账号下的子账号',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='tenant_id',
                description='租户ID，用于筛选特定租户下的普通用户',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY
            )
        ] + common_pagination_parameters,
        tags=["普通用户管理"]
    )
    def get(self, request, *args, **kwargs):
        try:
            return self.list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"获取普通用户列表失败: {str(e)}")
            return Response(
                {"detail": f"获取普通用户列表失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="创建新普通用户",
        description="创建新普通用户。权限要求: 超级管理员可创建任意租户下的普通用户；租户管理员只能创建自己租户的普通用户，且无法指定其他租户。",
        request=MemberCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="普通用户创建成功示例",
                examples=[
                    OpenApiExample(
                        name="创建普通用户成功示例",
                        value={
                            "success": True,
                            "code": 2001,
                            "message": "创建成功",
                            "data": {
                                "id": 11,
                                "username": "newmember",
                                "email": "newmember@example.com",
                                "phone": "13900139000",
                                "nick_name": "新普通用户",
                                "tenant": 1,
                                "tenant_name": "测试租户",
                                "is_sub_account": False,
                                "parent": None,
                                "parent_username": None
                            }
                        }
                    )
                ]
            ),
            **common_error_responses
        },
        tags=["普通用户管理"]
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        获取查询集，支持过滤
        """
        user = self.request.user
        
        # 超级管理员可以看到所有普通用户
        if user.is_super_admin:
            queryset = Member.objects.filter(is_deleted=False)
        # 租户管理员只能看到自己租户的普通用户
        elif hasattr(user, 'is_admin') and user.is_admin and user.tenant:
            queryset = Member.objects.filter(tenant=user.tenant, is_deleted=False)
        # 其他情况返回空查询集
        else:
            queryset = Member.objects.none()
        
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
        
        # 子账号过滤
        is_sub_account = self.request.query_params.get('is_sub_account', None)
        if is_sub_account is not None:
            is_sub = is_sub_account.lower() == 'true'
            if is_sub:
                queryset = queryset.filter(parent__isnull=False)
            else:
                queryset = queryset.filter(parent__isnull=True)
        
        # 父账号过滤
        parent_id = self.request.query_params.get('parent', None)
        if parent_id:
            try:
                parent_id = int(parent_id)
                # 查询指定父账号下的子账号
                queryset = queryset.filter(parent_id=parent_id)
            except ValueError:
                queryset = Member.objects.none()
        
        # 租户ID过滤
        tenant_id = self.request.query_params.get('tenant_id', None)
        if tenant_id and user.is_super_admin:  # 只有超级管理员可以按租户筛选
            try:
                tenant_id = int(tenant_id)
                queryset = queryset.filter(tenant_id=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                # 返回空查询集，因为无效的租户ID不应该匹配任何用户
                queryset = Member.objects.none()
        
        return queryset
        
    def perform_create(self, serializer):
        """
        创建普通用户，设置租户
        """
        user = self.request.user
        
        # 设置租户
        tenant = None
        if not user.is_super_admin:
            # 非超级管理员只能在自己租户创建用户
            tenant = user.tenant
            if not tenant:
                raise PermissionDenied("您没有关联的租户，无法创建普通用户")
        
        # 如果传入了tenant_id参数并且是超级管理员
        tenant_id = self.request.data.get('tenant_id')
        if tenant_id and user.is_super_admin:
            try:
                tenant_id = int(tenant_id)
                tenant = get_object_or_404(Tenant, pk=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                raise serializers.ValidationError({"tenant_id": f"无效的租户ID: {tenant_id}"})
        elif tenant_id and not user.is_super_admin:
            # 非超级管理员尝试指定租户ID
            try:
                tenant_id = int(tenant_id)
                requested_tenant = get_object_or_404(Tenant, pk=tenant_id)
                if requested_tenant.id != user.tenant.id:
                    raise PermissionDenied("您只能在自己的租户下创建用户")
                tenant = user.tenant
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                raise serializers.ValidationError({"tenant_id": f"无效的租户ID: {tenant_id}"})
        
        logger.info(f"用户 {user.username} 创建新普通用户，租户设置为: {tenant.name if tenant else '无租户'}")
        serializer.save(tenant=tenant)


class MemberRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    普通用户详情、更新和删除视图
    """
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="获取普通用户详情",
        description="获取单个普通用户的详细信息。权限要求：超级管理员可查看任何普通用户；租户管理员只能查看自己租户的普通用户；普通用户只能查看自己。",
        responses={
            200: OpenApiResponse(description="成功获取普通用户详情", response=MemberSerializer),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="普通用户不存在")
        },
        tags=["普通用户管理"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="更新普通用户信息",
        description="更新指定普通用户的信息。权限要求：超级管理员可更新任何普通用户；租户管理员只能更新自己租户的普通用户；普通用户只能更新自己。",
        request=MemberSerializer,
        responses={
            200: OpenApiResponse(description="成功更新普通用户信息", response=MemberSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="普通用户不存在")
        },
        tags=["普通用户管理"]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="部分更新普通用户信息",
        description="部分更新指定普通用户的信息。权限要求：超级管理员可更新任何普通用户；租户管理员只能更新自己租户的普通用户；普通用户只能更新自己。",
        request=MemberSerializer,
        responses={
            200: OpenApiResponse(description="成功更新普通用户信息", response=MemberSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="普通用户不存在")
        },
        tags=["普通用户管理"]
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="删除普通用户",
        description="删除指定普通用户（软删除）。权限要求：超级管理员可删除任何普通用户；租户管理员只能删除自己租户的普通用户。不能删除当前登录的用户账号。",
        responses={
            204: OpenApiResponse(description="成功删除普通用户"),
            400: OpenApiResponse(description="请求参数错误，例如尝试删除当前登录账号"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="普通用户不存在")
        },
        tags=["普通用户管理"]
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
        
        # 如果用户是Member类型，只能查看自己
        if isinstance(user, Member):
            return Member.objects.filter(pk=user.pk, is_deleted=False)
            
        # 超级管理员可以操作所有普通用户
        if user.is_super_admin:
            return Member.objects.filter(is_deleted=False)
            
        # 租户管理员只能操作自己租户的普通用户
        if hasattr(user, 'is_admin') and user.is_admin and user.tenant:
            return Member.objects.filter(tenant=user.tenant, is_deleted=False)
            
        # 其他情况返回空查询集
        return Member.objects.none()
    
    def perform_update(self, serializer):
        """
        执行更新操作
        """
        instance = serializer.instance
        user = self.request.user
        
        # 日志记录
        logger.info(f"用户 {user.username} 更新普通用户 {instance.username} 的信息")
        
        # 执行更新
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        执行删除操作（软删除）
        """
        user = self.request.user
        
        # 检查是否尝试删除当前登录账号
        # 只有当用户是Member类型且ID相同时才拒绝操作
        if isinstance(user, Member) and instance.pk == user.pk:
            logger.warning(f"用户 {user.username} 尝试删除自己的账号，操作被拒绝")
            raise PermissionDenied("不能删除当前登录的账号")
        
        # 日志记录
        logger.info(f"用户 {user.username} 软删除普通用户 {instance.username}")
        
        # 执行软删除
        instance.soft_delete()


class CurrentMemberView(APIView):
    """
    获取和更新当前登录普通用户信息
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        """
        添加请求到序列化器上下文
        """
        return {'request': self.request}
    
    @extend_schema(
        summary="获取当前登录普通用户信息",
        description="获取当前登录普通用户的详细信息。",
        responses={
            200: OpenApiResponse(description="成功获取当前用户信息", response=MemberSerializer),
            403: OpenApiResponse(description="权限不足")
        },
        tags=["普通用户管理"]
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # 检查当前用户是否为普通用户
        if not isinstance(user, Member):
            logger.warning(f"非普通用户 {user.username} 尝试访问普通用户专属API")
            return Response(
                {"detail": "此接口仅适用于普通用户，请使用对应的管理员用户接口"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MemberSerializer(user, context=self.get_serializer_context())
        return api_schema.success(data=serializer.data)
    
    @extend_schema(
        summary="更新当前登录普通用户信息",
        description="更新当前登录普通用户的基本信息。",
        request=MemberSerializer,
        responses={
            200: OpenApiResponse(description="成功更新当前用户信息", response=MemberSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足")
        },
        tags=["普通用户管理"]
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        
        # 检查当前用户是否为普通用户
        if not isinstance(user, Member):
            logger.warning(f"非普通用户 {user.username} 尝试访问普通用户专属API")
            return Response(
                {"detail": "此接口仅适用于普通用户，请使用对应的管理员用户接口"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 不允许通过此接口修改用户名和邮箱，其他字段允许，交由序列化器校验
        protected_fields = ['username', 'email']
        for field in protected_fields:
            if field in request.data:
                return Response(
                    {"detail": f"不允许修改 {field} 字段"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 验证并保存
        serializer = MemberSerializer(user, data=request.data, partial=True, context=self.get_serializer_context())
        if serializer.is_valid():
            serializer.save()
            return api_schema.success("更新成功", serializer.data)
        else:
            logger.warning(f"用户 {user.username} 更新个人信息失败: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemberPasswordUpdateView(APIView):
    """
    普通用户密码更新视图
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="更新普通用户密码",
        description="普通用户更新自己的密码。需要提供旧密码进行验证。",
        request=UserPasswordUpdateSerializer,
        responses={
            200: OpenApiResponse(
                description="密码更新成功",
                examples=[
                    OpenApiExample(
                        name="密码更新成功示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "密码更新成功",
                            "data": None
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足")
        },
        tags=["普通用户管理"]
    )
    def post(self, request):
        user = request.user
        
        # 检查当前用户是否为普通用户
        if not isinstance(user, Member):
            logger.warning(f"非普通用户 {user.username} 尝试访问普通用户专属API")
            return Response(
                {"detail": "此接口仅适用于普通用户，请使用对应的管理员用户接口"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserPasswordUpdateSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新密码
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        logger.info(f"用户 {user.username} 成功更新了密码")
        return api_schema.success("密码更新成功")


class SubAccountListCreateView(generics.ListCreateAPIView):
    """
    子账号列表和创建视图
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubAccountCreateSerializer
        return SubAccountSerializer
    
    def get_serializer_context(self):
        """
        添加请求到序列化器上下文
        """
        return {'request': self.request}
    
    @extend_schema(
        summary="获取子账号列表",
        description="获取当前用户的子账号列表。普通用户只能查看自己的子账号；管理员可根据权限查看系统中的子账号。",
        responses={
            200: OpenApiResponse(
                description="获取子账号列表成功",
                examples=[
                    OpenApiExample(
                        name="子账号列表示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "获取成功",
                            "data": {
                                "count": 5,
                                "next": None,
                                "previous": None,
                                "results": [
                                    {
                                        "id": 20,
                                        "username": "subaccount1",
                                        "email": "sub1@example.com",
                                        "phone": "13900001111",
                                        "nick_name": "子账号1",
                                        "tenant": 1,
                                        "tenant_name": "测试租户",
                                        "is_sub_account": True,
                                        "parent": 10,
                                        "parent_username": "parentuser"
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
            **common_error_responses
        },
        parameters=common_pagination_parameters,
        tags=["子账号管理"]
    )
    def get(self, request, *args, **kwargs):
        try:
            return self.list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"获取子账号列表失败: {str(e)}")
            return Response(
                {"detail": f"获取子账号列表失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="创建新子账号",
        description="创建一个与当前用户关联的新子账号。子账号默认不能登录，仅用于数据关联。",
        request=SubAccountCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="子账号创建成功",
                examples=[
                    OpenApiExample(
                        name="创建子账号成功示例",
                        value={
                            "success": True,
                            "code": 2001,
                            "message": "创建成功",
                            "data": {
                                "id": 21,
                                "username": "newsubaccount",
                                "email": "newsub@example.com",
                                "phone": "13900002222",
                                "nick_name": "新子账号",
                                "tenant": 1,
                                "tenant_name": "测试租户",
                                "is_sub_account": True,
                                "parent": 10,
                                "parent_username": "parentuser"
                            }
                        }
                    )
                ]
            ),
            **common_error_responses
        },
        tags=["子账号管理"]
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        获取查询集
        """
        user = self.request.user
        
        # 子账号不应该查看子账号
        if isinstance(user, Member) and user.is_sub_account:
            return Member.objects.none()
        
        # 如果是普通用户，只能查看自己的子账号
        if isinstance(user, Member):
            return Member.objects.filter(parent=user, is_deleted=False)
        
        # 如果是超级管理员
        if user.is_super_admin:
            return Member.objects.filter(parent__isnull=False, is_deleted=False)
            
        # 如果是租户管理员，可以查看本租户内的子账号
        if hasattr(user, 'is_admin') and user.is_admin and user.tenant:
            return Member.objects.filter(
                tenant=user.tenant, 
                parent__isnull=False,
                is_deleted=False
            )
            
        # 其他情况返回空查询集
        return Member.objects.none()
    
    def list(self, request, *args, **kwargs):
        """
        重写列表方法，使用api_schema格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return api_schema.success(data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        重写创建方法，使用api_schema格式
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return api_schema.created(data=serializer.data, headers=headers)


class SubAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    子账号详情、更新和删除视图
    """
    serializer_class = SubAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        """
        添加请求到序列化器上下文
        """
        return {'request': self.request}
    
    @extend_schema(
        summary="获取子账号详情",
        description="获取单个子账号的详细信息。普通用户只能查看自己的子账号；管理员可根据权限查看系统中的子账号。",
        responses={
            200: OpenApiResponse(description="成功获取子账号详情", response=SubAccountSerializer),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["子账号管理"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="更新子账号信息",
        description="更新指定子账号的信息。普通用户只能更新自己的子账号；管理员可根据权限更新系统中的子账号。",
        request=SubAccountSerializer,
        responses={
            200: OpenApiResponse(description="成功更新子账号信息", response=SubAccountSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["子账号管理"]
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    @extend_schema(
        summary="部分更新子账号信息",
        description="部分更新指定子账号的信息。普通用户只能更新自己的子账号；管理员可根据权限更新系统中的子账号。",
        request=SubAccountSerializer,
        responses={
            200: OpenApiResponse(description="成功更新子账号信息", response=SubAccountSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["子账号管理"]
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="删除子账号",
        description="删除指定子账号（软删除）。普通用户只能删除自己的子账号；管理员可根据权限删除系统中的子账号。",
        responses={
            204: OpenApiResponse(description="成功删除子账号"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["子账号管理"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        获取查询集
        """
        user = self.request.user
        
        # 子账号不应该查看子账号
        if isinstance(user, Member) and user.is_sub_account:
            return Member.objects.none()
        
        # 如果是普通用户，只能操作自己的子账号
        if isinstance(user, Member):
            return Member.objects.filter(parent=user, is_deleted=False)
        
        # 如果是超级管理员
        if user.is_super_admin:
            return Member.objects.filter(parent__isnull=False, is_deleted=False)
            
        # 如果是租户管理员，可以操作本租户内的子账号
        if hasattr(user, 'is_admin') and user.is_admin and user.tenant:
            return Member.objects.filter(
                tenant=user.tenant, 
                parent__isnull=False,
                is_deleted=False
            )
            
        # 其他情况返回空查询集
        return Member.objects.none()
    
    def perform_update(self, serializer):
        """
        执行更新操作
        """
        instance = serializer.instance
        user = self.request.user
        
        # 日志记录
        logger.info(f"用户 {user.username} 更新子账号 {instance.username} 的信息")
        
        # 执行更新
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        执行删除操作（软删除）
        """
        user = self.request.user
        
        # 日志记录
        logger.info(f"用户 {user.username} 软删除子账号 {instance.username}")
        
        # 执行软删除
        instance.soft_delete()


class MemberAvatarUploadView(APIView):
    """
    普通用户头像上传视图
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="上传当前普通用户头像",
        description="上传并更新当前登录普通用户的头像图片",
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
        tags=["普通用户管理"]
    )
    def post(self, request, *args, **kwargs):
        """
        上传普通用户头像
        """
        user = request.user
        
        # 检查用户是否为Member类型
        if not isinstance(user, Member):
            return Response(
                {"detail": "该接口仅适用于普通用户"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # 检查用户是否为子账号（子账号不允许操作）
        if user.is_sub_account:
            return Response(
                {"detail": "子账号不允许更改头像"},
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
                        logger.info(f"删除普通用户 {user.username} 的旧头像 {old_avatar_path}")
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
            
            logger.info(f"普通用户 {user.username} 上传了新头像")
            
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


class MemberSpecificAvatarUploadView(APIView):
    """
    为特定普通用户上传头像视图
    
    允许管理员和普通用户为其下属子账号上传头像
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="为特定普通用户上传头像",
        description="允许管理员和普通用户为特定普通用户上传头像。租户管理员只能为其所属租户的普通用户上传头像，超级管理员可以为任何普通用户上传头像，普通用户只能为自己的子账号上传头像。",
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
            404: OpenApiResponse(description="普通用户不存在"),
            500: OpenApiResponse(description="服务器内部错误"),
        },
        tags=["普通用户管理"]
    )
    def post(self, request, pk, *args, **kwargs):
        """
        为特定普通用户上传头像
        """
        # 获取目标用户
        try:
            target_user = Member.objects.get(pk=pk, is_deleted=False)
        except Member.DoesNotExist:
            return Response(
                {"detail": "普通用户不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 权限检查
        current_user = request.user
        
        # 如果当前用户是Member类型
        if isinstance(current_user, Member):
            # 只能为自己的子账号上传头像
            if target_user.parent != current_user:
                return Response(
                    {"detail": "您只能为自己的子账号上传头像"},
                    status=status.HTTP_403_FORBIDDEN
                )
        # 如果当前用户是管理员
        elif hasattr(current_user, 'is_admin') and current_user.is_admin:
            # 超级管理员可以为任何普通用户上传头像
            if not current_user.is_super_admin and current_user.tenant != target_user.tenant:
                return Response(
                    {"detail": "您没有权限为该普通用户上传头像"},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {"detail": "您没有权限为普通用户上传头像"},
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
                        logger.info(f"删除普通用户 {target_user.username} 的旧头像 {old_avatar_path}")
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
            
            # 根据当前用户类型记录日志
            if isinstance(current_user, Member):
                logger.info(f"普通用户 {current_user.username} 为其子账号 {target_user.username} 上传了新头像")
            else:
                logger.info(f"管理员 {current_user.username} 为普通用户 {target_user.username} 上传了新头像")
            
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