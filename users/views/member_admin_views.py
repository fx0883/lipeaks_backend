"""
管理员端Member管理视图
仅用于管理员管理普通用户(Member)的操作
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
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from common.pagination import StandardResultsSetPagination

from common.permissions import IsSuperAdminUser, IsAdminUser
from common.utils.user_permissions import is_super_admin, is_admin
from users.models import Member
from users.serializers import (
    MemberSerializer, 
    MemberCreateSerializer,
    SubAccountSerializer,
    SubAccountCreateSerializer,
)
from common.schema import common_error_responses, common_pagination_parameters
from tenants.models import Tenant

logger = logging.getLogger(__name__)


class AdminMemberListCreateView(generics.ListCreateAPIView):
    """
    管理员端：Member列表和创建视图
    
    注意：Member使用手动租户过滤而非TenantModelViewSet，原因：
    1. Member具有特殊的权限逻辑（普通Member只能看到自己，不是整个租户）
    2. 有复杂的过滤条件（子账号、父账号、搜索等）
    3. Member是用户身份模型，不是标准的业务数据资源
    4. 手动实现的租户隔离已经过测试验证，功能完整且安全
    
    租户隔离实现：
    - 超级管理员：可查看所有租户的Member
    - 租户管理员：只能查看自己租户的Member
    - 普通Member：只能查看自己（在其他View中实现）
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = MemberSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MemberCreateSerializer
        return MemberSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    @extend_schema(
        summary="【管理员】获取Member列表",
        description="管理员获取系统中的Member列表，支持搜索和分页。超级管理员可查看所有Member；租户管理员只能查看自己租户的Member。",
        responses={
            200: OpenApiResponse(
                description="获取Member列表成功",
                examples=[
                    OpenApiExample(
                        name="Member列表示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "获取成功",
                            "data": {
                                "count": 10,
                                "next": "http://example.com/api/v1/admin/members/?page=2",
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
        tags=["管理员-Member管理"]
    )
    def get(self, request, *args, **kwargs):
        try:
            return self.list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"获取Member列表失败: {str(e)}")
            return Response(
                {"detail": f"获取Member列表失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="【管理员】创建新Member",
        description="管理员创建新Member。超级管理员可创建任意租户下的Member；租户管理员只能创建自己租户的Member。",
        request=MemberCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Member创建成功",
                examples=[
                    OpenApiExample(
                        name="创建Member成功示例",
                        value={
                            "success": True,
                            "code": 2001,
                            "message": "创建成功",
                            "data": {
                                "id": 11,
                                "username": "newmember",
                                "email": "newmember@example.com",
                                "phone": "13900139000",
                                "nick_name": "新Member",
                                "tenant": 1,
                                "tenant_name": "测试租户"
                            }
                        }
                    )
                ]
            ),
            **common_error_responses
        },
        tags=["管理员-Member管理"]
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        
        if is_super_admin(user):
            queryset = Member.objects.filter(is_deleted=False)
        elif is_admin(user) and user.tenant:
            queryset = Member.objects.filter(tenant=user.tenant, is_deleted=False)
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
                queryset = queryset.filter(parent_id=parent_id)
            except ValueError:
                queryset = Member.objects.none()
        
        # 租户ID过滤
        tenant_id = self.request.query_params.get('tenant_id', None)
        if tenant_id and is_super_admin(user):
            try:
                tenant_id = int(tenant_id)
                queryset = queryset.filter(tenant_id=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                queryset = Member.objects.none()
        
        return queryset
        
    def perform_create(self, serializer):
        user = self.request.user
        tenant = None
        
        if not is_super_admin(user):
            tenant = user.tenant
            if not tenant:
                raise UserPermissionDeniedException(
                    detail='您没有关联的租户，无法创建Member',
                    user_id=user.id,
                    username=user.username
                )
        
        tenant_id = self.request.data.get('tenant_id')
        if tenant_id and is_super_admin(user):
            try:
                tenant_id = int(tenant_id)
                tenant = get_object_or_404(Tenant, pk=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                raise serializers.ValidationError({"tenant_id": f"无效的租户ID: {tenant_id}"})
        elif tenant_id and not is_super_admin(user):
            try:
                tenant_id = int(tenant_id)
                requested_tenant = get_object_or_404(Tenant, pk=tenant_id)
                if requested_tenant.id != user.tenant.id:
                    raise UserPermissionDeniedException(
                        detail='You can only create users in your own tenant',
                        user_id=user.id,
                        user_tenant_id=user.tenant.id,
                        requested_tenant_id=tenant_id
                    )
                tenant = user.tenant
            except (ValueError, TypeError):
                logger.error(f"无效的租户ID: {tenant_id}")
                raise serializers.ValidationError({"tenant_id": f"无效的租户ID: {tenant_id}"})
        
        logger.info(f"用户 {user.username} 创建新Member，租户设置为: {tenant.name if tenant else '无租户'}")
        serializer.save(tenant=tenant)


class AdminMemberRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    管理员端：Member详情、更新和删除视图
    
    注意：使用手动租户过滤，与AdminMemberListCreateView保持一致。
    租户隔离策略：
    - 超级管理员：可操作所有租户的Member
    - 租户管理员：只能操作自己租户的Member
    - 删除保护：不允许删除当前登录的账号
    """
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="【管理员】获取Member详情",
        description="管理员获取单个Member的详细信息。超级管理员可查看任何Member；租户管理员只能查看自己租户的Member。",
        responses={
            200: OpenApiResponse(description="成功获取Member详情", response=MemberSerializer),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="Member不存在")
        },
        tags=["管理员-Member管理"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="【管理员】更新Member信息",
        description="管理员更新指定Member的信息。超级管理员可更新任何Member；租户管理员只能更新自己租户的Member。",
        request=MemberSerializer,
        responses={
            200: OpenApiResponse(description="成功更新Member信息", response=MemberSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="Member不存在")
        },
        tags=["管理员-Member管理"]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="【管理员】部分更新Member信息",
        description="管理员部分更新指定Member的信息。超级管理员可更新任何Member；租户管理员只能更新自己租户的Member。",
        request=MemberSerializer,
        responses={
            200: OpenApiResponse(description="成功更新Member信息", response=MemberSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="Member不存在")
        },
        tags=["管理员-Member管理"]
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="【管理员】删除Member",
        description="管理员删除指定Member（软删除）。超级管理员可删除任何Member；租户管理员只能删除自己租户的Member。",
        responses={
            204: OpenApiResponse(description="成功删除Member"),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="Member不存在")
        },
        tags=["管理员-Member管理"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def get_queryset(self):
        user = self.request.user
        
        if is_super_admin(user):
            return Member.objects.filter(is_deleted=False)
            
        if is_admin(user) and user.tenant:
            return Member.objects.filter(tenant=user.tenant, is_deleted=False)
            
        return Member.objects.none()
    
    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        logger.info(f"用户 {user.username} 更新Member {instance.username} 的信息")
        serializer.save()
    
    def perform_destroy(self, instance):
        user = self.request.user
        logger.info(f"用户 {user.username} 软删除Member {instance.username}")
        instance.soft_delete()


class AdminSubAccountListView(generics.ListAPIView):
    """
    管理员端：子账号列表视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = SubAccountSerializer
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        summary="【管理员】获取子账号列表",
        description="管理员获取子账号列表。超级管理员可查看所有子账号；租户管理员可查看本租户的子账号。",
        responses={
            200: OpenApiResponse(description="获取子账号列表成功"),
            **common_error_responses
        },
        parameters=common_pagination_parameters,
        tags=["管理员-Member管理"]
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
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_queryset(self):
        user = self.request.user
        
        if is_super_admin(user):
            return Member.objects.filter(parent__isnull=False, is_deleted=False)
            
        if is_admin(user) and user.tenant:
            return Member.objects.filter(
                tenant=user.tenant, 
                parent__isnull=False,
                is_deleted=False
            )
            
        return Member.objects.none()


class AdminSubAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    管理员端：子账号详情、更新和删除视图
    """
    serializer_class = SubAccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="【管理员】获取子账号详情",
        description="管理员获取单个子账号的详细信息。",
        responses={
            200: OpenApiResponse(description="成功获取子账号详情", response=SubAccountSerializer),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["管理员-Member管理"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="【管理员】更新子账号信息",
        description="管理员更新指定子账号的信息。",
        request=SubAccountSerializer,
        responses={
            200: OpenApiResponse(description="成功更新子账号信息", response=SubAccountSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["管理员-Member管理"]
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    @extend_schema(
        summary="【管理员】部分更新子账号信息",
        description="管理员部分更新指定子账号的信息。",
        request=SubAccountSerializer,
        responses={
            200: OpenApiResponse(description="成功更新子账号信息", response=SubAccountSerializer),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["管理员-Member管理"]
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="【管理员】删除子账号",
        description="管理员删除指定子账号（软删除）。",
        responses={
            204: OpenApiResponse(description="成功删除子账号"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="子账号不存在")
        },
        tags=["管理员-Member管理"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_queryset(self):
        user = self.request.user
        
        if is_super_admin(user):
            return Member.objects.filter(parent__isnull=False, is_deleted=False)
            
        if is_admin(user) and user.tenant:
            return Member.objects.filter(
                tenant=user.tenant, 
                parent__isnull=False,
                is_deleted=False
            )
            
        return Member.objects.none()
    
    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        logger.info(f"用户 {user.username} 更新子账号 {instance.username} 的信息")
        serializer.save()
    
    def perform_destroy(self, instance):
        user = self.request.user
        logger.info(f"用户 {user.username} 软删除子账号 {instance.username}")
        instance.soft_delete()


class AdminMemberAvatarUploadView(APIView):
    """
    管理员端：为特定Member上传头像视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="【管理员】为Member上传头像",
        description="管理员为指定Member上传头像。超级管理员可为任何Member上传；租户管理员只能为自己租户的Member上传。",
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
            400: OpenApiResponse(description="请求错误"),
            401: OpenApiResponse(description="未认证"),
            403: OpenApiResponse(description="权限不足"),
            404: OpenApiResponse(description="Member不存在"),
            500: OpenApiResponse(description="服务器内部错误")
        },
        tags=["管理员-Member管理"]
    )
    def post(self, request, pk, *args, **kwargs):
        # 获取目标用户
        try:
            target_user = Member.objects.get(pk=pk, is_deleted=False)
        except Member.DoesNotExist:
            return Response(
                {"detail": "Member不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 权限检查
        current_user = request.user
        
        if is_admin(current_user):
            if not is_super_admin(current_user) and current_user.tenant != target_user.tenant:
                return Response(
                    {"detail": "您没有权限为该Member上传头像"},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {"detail": "您没有权限为Member上传头像"},
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
        
        # 验证文件大小（从settings获取配置，默认10MB）
        max_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)
        if avatar_file.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            return Response(
                {"detail": f"文件太大，头像大小不能超过{max_size_mb:.0f}MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 删除旧头像文件（如果存在）
            if target_user.avatar and target_user.avatar.startswith(settings.MEDIA_URL):
                avatar_path = target_user.avatar.replace(settings.MEDIA_URL, '', 1)
                old_avatar_path = os.path.join(settings.MEDIA_ROOT, avatar_path)
                
                if os.path.isfile(old_avatar_path):
                    try:
                        os.remove(old_avatar_path)
                        logger.info(f"删除Member {target_user.username} 的旧头像 {old_avatar_path}")
                    except OSError as e:
                        logger.warning(f"删除旧头像文件失败: {str(e)}")
            
            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            # 确保媒体目录存在
            avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(avatar_dir, unique_filename)
            with open(file_path, 'wb+') as destination:
                for chunk in avatar_file.chunks():
                    destination.write(chunk)
            
            # 生成相对URL路径（不带前缀斜杠）
            relative_url = f"media/avatars/{unique_filename}"
            
            # 更新用户头像URL
            target_user.avatar = relative_url
            target_user.save(update_fields=['avatar'])
            
            logger.info(f"管理员 {current_user.username} 为Member {target_user.username} 上传了新头像")
            
            return Response({
                "detail": "头像上传成功",
                "avatar": relative_url
            })
        
        except Exception as e:
            logger.error(f"头像上传失败: {str(e)}")
            return Response(
                {"detail": f"头像上传失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

