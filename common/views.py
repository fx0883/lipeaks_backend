from django.shortcuts import render
import logging
from django.db.models import Q
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, inline_serializer
from common.permissions import IsSuperAdminUser, IsAdminUser
from common.models import APILog, Config
from common.serializers import APILogSerializer, APILogDetailSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.db import models
from django.utils.translation import gettext_lazy as _
from common.utils.tenant_manager import TenantManager
import os
import uuid
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser

logger = logging.getLogger(__name__)

class APILogListView(generics.ListAPIView):
    """
    API日志列表视图
    超级管理员可查看所有日志，租户管理员只能查看自己租户的日志
    """
    serializer_class = APILogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        parameters=[
            {
                'name': 'search',
                'type': 'string',
                'description': '搜索关键词(路径/用户名)'
            },
            {
                'name': 'start_date',
                'type': 'string',
                'format': 'date',
                'description': '开始日期 (YYYY-MM-DD)'
            },
            {
                'name': 'end_date',
                'type': 'string',
                'format': 'date',
                'description': '结束日期 (YYYY-MM-DD)'
            },
            {
                'name': 'status_type',
                'type': 'string',
                'description': '状态类型 (success/error)'
            },
            {
                'name': 'request_method',
                'type': 'string',
                'description': '请求方法 (GET/POST/PUT/DELETE)'
            },
            {
                'name': 'tenant_id',
                'type': 'integer',
                'description': '租户ID'
            }
        ],
        responses={200: APILogSerializer(many=True)},
        description="获取API日志列表，支持多种筛选条件",
        summary="获取API日志列表",
        tags=["系统", "日志"]
    )
    def get_queryset(self):
        """
        获取API日志查询集
        """
        user = self.request.user
        
        # 基础查询集
        if user.is_super_admin:
            # 超级管理员可查看所有日志
            queryset = APILog.objects.all()
        else:
            # 租户管理员只能查看自己租户的日志
            if user.tenant:
                queryset = APILog.objects.filter(tenant=user.tenant)
            else:
                # 如果用户没有关联租户，只能查看自己的日志
                queryset = APILog.objects.filter(user=user)
        
        # 应用过滤条件
        queryset = self._apply_filters(queryset)
        
        return queryset
    
    def _apply_filters(self, queryset):
        """
        应用过滤条件
        
        Args:
            queryset: 初始查询集
        
        Returns:
            过滤后的查询集
        """
        params = self.request.query_params
        
        # 搜索过滤
        search = params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(request_path__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        # 日期范围过滤
        start_date = params.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        
        end_date = params.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # 状态类型过滤
        status_type = params.get('status_type')
        if status_type:
            queryset = queryset.filter(status_type=status_type)
        
        # 请求方法过滤
        request_method = params.get('request_method')
        if request_method:
            queryset = queryset.filter(request_method=request_method)
        
        # 租户过滤 (仅超级管理员可用)
        if self.request.user.is_super_admin:
            tenant_id = params.get('tenant_id')
            if tenant_id:
                queryset = queryset.filter(tenant_id=tenant_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        重写列表方法，自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'code': 2000,
            'message': '获取成功',
            'data': {
                'count': queryset.count(),
                'results': serializer.data
            }
        })


class APILogDetailView(generics.RetrieveAPIView):
    """
    API日志详情视图
    """
    serializer_class = APILogDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'pk'
    
    @extend_schema(
        responses={200: APILogDetailSerializer()},
        description="获取API日志详情",
        summary="获取API日志详情",
        tags=["系统", "日志"]
    )
    def get_queryset(self):
        """
        获取API日志查询集
        """
        user = self.request.user
        
        # 基础查询集
        if user.is_super_admin:
            # 超级管理员可查看所有日志
            return APILog.objects.all()
        
        # 租户管理员只能查看自己租户的日志
        if user.tenant:
            return APILog.objects.filter(tenant=user.tenant)
        
        # 如果用户没有关联租户，只能查看自己的日志
        return APILog.objects.filter(user=user)
    
    def retrieve(self, request, *args, **kwargs):
        """
        重写查询方法，自定义响应格式
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'code': 2000,
            'message': '获取成功',
            'data': serializer.data
        })

# 定义测试用序列化器
class TestStandardResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="测试消息")
    test_field = serializers.CharField(help_text="测试字段")
    items = serializers.ListField(child=serializers.IntegerField(), help_text="测试列表")

class TestErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="错误详情")
    fields = serializers.DictField(child=serializers.CharField(), help_text="字段错误信息")

class TestAuthErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="认证错误详情")

class PaginationInfoSerializer(serializers.Serializer):
    count = serializers.IntegerField(help_text="总数")
    next = serializers.CharField(help_text="下一页链接", allow_null=True)
    previous = serializers.CharField(help_text="上一页链接", allow_null=True)
    page_size = serializers.IntegerField(help_text="每页大小")
    current_page = serializers.IntegerField(help_text="当前页码")
    total_pages = serializers.IntegerField(help_text="总页数")

class ResultItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="项目ID")
    name = serializers.CharField(help_text="项目名称")

class TestPaginationResponseSerializer(serializers.Serializer):
    pagination = PaginationInfoSerializer(help_text="分页信息")
    results = serializers.ListField(child=ResultItemSerializer(), help_text="结果列表")

# 将函数视图转换为基于类的视图
class TestStandardResponseView(APIView):
    """
    测试成功响应的统一格式
    """
    permission_classes = [AllowAny]
    serializer_class = TestStandardResponseSerializer  # 添加序列化器类
    
    @extend_schema(
        description="测试统一响应格式的API",
        summary="测试成功响应",
        responses={
            200: TestStandardResponseSerializer
        },
        tags=["测试"]
    )
    def get(self, request):
        """
        测试成功响应
        """
        data = {
            'message': '这是一个测试消息',
            'test_field': '这是一个测试字段',
            'items': [1, 2, 3, 4, 5]
        }
        
        return Response({
            'success': True,
            'code': 2000,
            'message': '操作成功',
            'data': data
        })


class TestErrorResponseView(APIView):
    """
    测试错误响应的统一格式
    """
    permission_classes = [AllowAny]
    serializer_class = TestErrorResponseSerializer  # 添加序列化器类
    
    @extend_schema(
        description="测试错误响应的统一格式",
        summary="测试错误响应",
        responses={
            400: TestErrorResponseSerializer
        },
        tags=["测试"]
    )
    def get(self, request):
        """
        测试错误响应
        """
        error_data = {
            'detail': '请求参数错误',
            'fields': {
                'name': '名称不能为空',
                'email': '邮箱格式不正确'
            }
        }
        
        return Response({
            'success': False,
            'code': 4000,
            'message': '请求参数错误',
            'data': error_data
        }, status=status.HTTP_400_BAD_REQUEST)


class TestAuthErrorResponseView(APIView):
    """
    测试认证失败响应的统一格式
    """
    permission_classes = [AllowAny]
    serializer_class = TestAuthErrorResponseSerializer  # 添加序列化器类
    
    @extend_schema(
        description="测试认证失败响应的统一格式",
        summary="测试认证失败响应",
        responses={
            401: TestAuthErrorResponseSerializer
        },
        tags=["测试"]
    )
    def get(self, request):
        """
        测试认证失败响应
        """
        return Response({
            'success': False,
            'code': 4001,
            'message': '认证失败',
            'data': {
                'detail': '身份验证凭据未提供或已过期'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)


class TestPaginationResponseView(APIView):
    """
    测试分页响应的统一格式
    """
    permission_classes = [AllowAny]
    serializer_class = TestPaginationResponseSerializer  # 添加序列化器类
    
    @extend_schema(
        description="测试分页响应的统一格式",
        summary="测试分页响应",
        responses={
            200: TestPaginationResponseSerializer
        },
        tags=["测试"]
    )
    def get(self, request):
        """
        测试分页响应
        """
        # 模拟分页数据
        pagination_data = {
            'count': 100,
            'next': 'http://example.com/api/items?page=3',
            'previous': 'http://example.com/api/items?page=1',
            'page_size': 10,
            'current_page': 2,
            'total_pages': 10
        }
        
        # 模拟结果数据
        results = [
            {'id': i, 'name': f'Item {i}'} for i in range(10, 20)
        ]
        
        return Response({
            'success': True,
            'code': 2000,
            'message': '获取成功',
            'data': {
                'pagination': pagination_data,
                'results': results
            }
        })


# 函数视图示例
@extend_schema(
    responses={
        200: TestStandardResponseSerializer,
    },
    tags=["测试接口"],
    summary="测试标准响应格式",
    description="测试API成功响应的标准格式",
)
@api_view(['GET'])
@permission_classes([AllowAny])
def test_standard_response(request):
    """
    测试标准响应格式
    """
    data = {
        'message': '这是一个测试消息',
        'test_field': '这是一个测试字段',
        'items': [1, 2, 3, 4, 5]
    }
    
    return Response({
        'success': True,
        'code': 2000,
        'message': '操作成功',
        'data': data
    })


@extend_schema(
    responses={
        400: TestErrorResponseSerializer,
    },
    tags=["测试接口"],
    summary="测试错误响应格式",
    description="测试API错误响应的标准格式",
)
@api_view(['GET'])
@permission_classes([AllowAny])
def test_error_response(request):
    """
    测试错误响应格式
    """
    error_data = {
        'detail': '请求参数错误',
        'fields': {
            'name': '名称不能为空',
            'email': '邮箱格式不正确'
        }
    }
    
    return Response({
        'success': False,
        'code': 4000,
        'message': '请求参数错误',
        'data': error_data
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={
        401: TestAuthErrorResponseSerializer,
    },
    tags=["测试接口"],
    summary="测试认证错误响应格式",
    description="测试API认证错误响应的标准格式",
)
@api_view(['GET'])
@permission_classes([AllowAny])
def test_auth_error_response(request):
    """
    测试认证错误响应格式
    """
    return Response({
        'success': False,
        'code': 4001,
        'message': '认证失败',
        'data': {
            'detail': '身份验证凭据未提供或已过期'
        }
    }, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    responses={
        200: TestPaginationResponseSerializer,
    },
    tags=["测试接口"],
    summary="测试分页响应格式",
    description="测试API分页响应的标准格式",
)
@api_view(['GET'])
@permission_classes([AllowAny])
def test_pagination_response(request):
    """
    测试分页响应格式
    """
    # 模拟分页数据
    pagination_data = {
        'count': 100,
        'next': 'http://example.com/api/items?page=3',
        'previous': 'http://example.com/api/items?page=1',
        'page_size': 10,
        'current_page': 2,
        'total_pages': 10
    }
    
    # 模拟结果数据
    results = [
        {'id': i, 'name': f'Item {i}'} for i in range(10, 20)
    ]
    
    # 返回标准化的分页响应
    paginated_data = {
        'pagination': pagination_data,
        'results': results
    }
    
    return Response({
        'success': True,
        'code': 2000,
        'message': '获取成功',
        'data': paginated_data
    })

class FileUploadView(APIView):
    """
    通用文件上传视图
    
    允许已登录用户上传图片文件，并返回可访问的URL
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="上传图片文件",
        description="上传图片文件并返回访问URL，仅支持已登录用户。\n\n"
                   "- 对于普通租户用户：默认上传到'租户ID/'目录，指定folder参数则上传到'租户ID/{folder}/'目录\n"
                   "- 对于超级管理员：默认上传到'super_admin/'目录，指定folder参数则上传到'super_admin/{folder}/'目录",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': '要上传的图片文件，支持JPG、PNG、GIF、WEBP或BMP格式',
                    },
                    'folder': {
                        'type': 'string',
                        'description': '可选的存储子文件夹名称',
                    }
                },
                'required': ['file']
            }
        },
        responses={
            200: OpenApiResponse(
                description="文件上传成功",
                response={
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean', 'example': True},
                        'code': {'type': 'integer', 'example': 2000},
                        'message': {'type': 'string', 'example': '文件上传成功'},
                        'data': {
                            'type': 'object',
                            'properties': {
                                'url': {'type': 'string', 'example': 'https://example.com/media/uploads/image.jpg'},
                                'filename': {'type': 'string', 'example': 'image.jpg'},
                                'size': {'type': 'integer', 'example': 1024},
                            }
                        }
                    }
                }
            ),
            400: OpenApiResponse(
                description="请求错误",
                response={
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean', 'example': False},
                        'code': {'type': 'integer', 'example': 4000},
                        'message': {'type': 'string', 'example': '请求参数错误'},
                        'data': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string', 'example': '未提供文件/不支持的文件类型/文件太大'},
                            }
                        }
                    }
                }
            ),
            401: OpenApiResponse(description="未认证"),
            500: OpenApiResponse(description="服务器内部错误")
        },
        tags=["通用功能"]
    )
    def post(self, request, *args, **kwargs):
        """
        上传图片文件
        """
        user = request.user
        
        # 获取上传的文件
        upload_file = request.FILES.get('file')
        
        if not upload_file:
            return Response({
                'success': False,
                'code': 4000,
                'message': '请求参数错误',
                'data': {
                    'detail': '未提供文件'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件类型
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        ext = os.path.splitext(upload_file.name)[1].lower()
        if ext not in valid_extensions:
            return Response({
                'success': False,
                'code': 4000,
                'message': '请求参数错误',
                'data': {
                    'detail': '不支持的文件类型，请上传JPG、PNG、GIF、WEBP或BMP格式的图片'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件大小
        max_size = 5 * 1024 * 1024  # 5MB
        if upload_file.size > max_size:
            return Response({
                'success': False,
                'code': 4000,
                'message': '请求参数错误',
                'data': {
                    'detail': f'文件太大，图片大小不能超过5MB'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取存储子文件夹（如果提供）
            folder = request.data.get('folder', '')
            
            # 安全处理文件夹名称，避免路径遍历
            folder = folder.replace('..', '').replace('/', '').replace('\\', '')
            
            # 根据用户类型确定基础目录
            if user.is_super_admin:
                # 超级管理员：默认super_admin目录，有folder则为super_admin/{folder}
                base_dir = 'super_admin'
                if folder:
                    upload_dir_name = f"{base_dir}/{folder}"
                else:
                    upload_dir_name = base_dir
            else:
                # 普通租户用户：默认租户ID目录，有folder则为租户ID/{folder}
                if user.tenant:
                    base_dir = str(user.tenant.id)
                    if folder:
                        upload_dir_name = f"{base_dir}/{folder}"
                    else:
                        upload_dir_name = base_dir
                else:
                    # 如果用户没有关联租户，使用用户ID作为目录
                    base_dir = f"user_{user.id}"
                    if folder:
                        upload_dir_name = f"{base_dir}/{folder}"
                    else:
                        upload_dir_name = base_dir
            
            # 生成唯一文件名，避免覆盖已有文件
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            # 确保媒体目录存在
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', upload_dir_name)
            os.makedirs(upload_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, 'wb+') as destination:
                for chunk in upload_file.chunks():
                    destination.write(chunk)
            
            # 生成相对URL路径
            relative_url = f"{settings.MEDIA_URL}uploads/{upload_dir_name}/{unique_filename}"
            
            # 为响应生成完整URL
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            full_url = f"{protocol}://{domain}{relative_url}"
            
            logger.info(f"用户 {user.username} 上传了图片 {unique_filename} 到目录 {upload_dir_name}")
            
            return Response({
                'success': True,
                'code': 2000,
                'message': '文件上传成功',
                'data': {
                    'url': full_url,
                    'filename': unique_filename,
                    'size': upload_file.size
                }
            })
        
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return Response({
                'success': False,
                'code': 5000,
                'message': '服务器内部错误',
                'data': {
                    'detail': f'文件上传失败: {str(e)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
