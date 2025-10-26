# feedbacks/views/email_api_views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import OpenApiTypes
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from ..models import EmailTemplate, FeedbackEmailLog
from ..serializers import EmailTemplateSerializer, FeedbackEmailLogSerializer
from ..permissions import EmailTemplatePermission, is_tenant_admin


class EmailTemplateListView(APIView):
    """
    邮件模板列表视图
    GET: 获取所有邮件模板（不需要认证）
    POST: 创建新邮件模板（仅限租户管理员）
    """
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    @extend_schema(
        tags=['Email Templates'],
        summary='获取邮件模板列表',
        description='获取当前租户的所有邮件模板',
        parameters=[
            OpenApiParameter(
                name='template_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按模板类型筛选',
                enum=['reply', 'status_change', 'verification', 'welcome']
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='筛选激活状态'
            ),
        ],
        responses={
            200: EmailTemplateSerializer(many=True),
            401: OpenApiResponse(description='未授权')
        }
    )
    def get(self, request):
        # 获取当前租户的模板
        queryset = EmailTemplate.objects.filter(is_deleted=False)
        
        # 过滤租户
        if hasattr(request, 'tenant') and request.tenant:
            queryset = queryset.filter(tenant=request.tenant)
        
        # 筛选条件
        template_type = request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
            
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active_bool)
        
        # 排序
        queryset = queryset.order_by('template_type', 'name')
        
        serializer = EmailTemplateSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Email Templates'],
        summary='创建邮件模板',
        description='创建新的邮件模板（仅限租户管理员）',
        request=EmailTemplateSerializer,
        responses={
            201: EmailTemplateSerializer,
            400: OpenApiResponse(description='请求参数错误'),
            403: OpenApiResponse(description='权限不足'),
            401: OpenApiResponse(description='未授权')
        }
    )
    def post(self, request):
        # 权限检查：只有租户管理员可以创建
        if not is_tenant_admin(request.user):
            return Response(
                {
                    'success': False,
                    'code': 4003,
                    'message': _('Only tenant administrators can manage email templates.'),
                    'data': None,
                    'error_code': 'AUTH_PERMISSION_DENIED'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EmailTemplateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # 自动设置租户
            tenant = getattr(request, 'tenant', None)
            template = serializer.save(tenant=tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(
            {
                'success': False,
                'code': 4000,
                'message': _('请求参数错误'),
                'data': serializer.errors,
                'error_code': 'VALIDATION_ERROR'
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class EmailTemplateDetailView(APIView):
    """
    邮件模板详情视图
    GET: 获取单个邮件模板（不需要认证）
    PUT: 完全更新邮件模板（仅限租户管理员）
    PATCH: 部分更新邮件模板（仅限租户管理员）
    DELETE: 删除邮件模板（仅限租户管理员）
    """
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    def get_object(self, pk, request):
        """获取邮件模板对象"""
        try:
            queryset = EmailTemplate.objects.filter(pk=pk, is_deleted=False)
            if hasattr(request, 'tenant') and request.tenant:
                queryset = queryset.filter(tenant=request.tenant)
            return queryset.get()
        except EmailTemplate.DoesNotExist:
            return None
    
    @extend_schema(
        tags=['Email Templates'],
        summary='获取邮件模板详情',
        description='获取指定ID的邮件模板详细信息',
        responses={
            200: EmailTemplateSerializer,
            404: OpenApiResponse(description='邮件模板不存在'),
            401: OpenApiResponse(description='未授权')
        }
    )
    def get(self, request, pk):
        template = self.get_object(pk, request)
        if not template:
            return Response(
                {
                    'success': False,
                    'code': 4004,
                    'message': _('邮件模板不存在'),
                    'data': None,
                    'error_code': 'NOT_FOUND'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EmailTemplateSerializer(template, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Email Templates'],
        summary='完全更新邮件模板',
        description='完全更新邮件模板信息（仅限租户管理员）',
        request=EmailTemplateSerializer,
        responses={
            200: EmailTemplateSerializer,
            400: OpenApiResponse(description='请求参数错误'),
            403: OpenApiResponse(description='权限不足'),
            404: OpenApiResponse(description='邮件模板不存在'),
            401: OpenApiResponse(description='未授权')
        }
    )
    def put(self, request, pk):
        return self._update(request, pk, partial=False)
    
    @extend_schema(
        tags=['Email Templates'],
        summary='部分更新邮件模板',
        description='部分更新邮件模板信息（仅限租户管理员）',
        request=EmailTemplateSerializer,
        responses={
            200: EmailTemplateSerializer,
            400: OpenApiResponse(description='请求参数错误'),
            403: OpenApiResponse(description='权限不足'),
            404: OpenApiResponse(description='邮件模板不存在'),
            401: OpenApiResponse(description='未授权')
        }
    )
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        # 权限检查：只有租户管理员可以更新
        if not is_tenant_admin(request.user):
            return Response(
                {
                    'success': False,
                    'code': 4003,
                    'message': _('Only tenant administrators can manage email templates.'),
                    'data': None,
                    'error_code': 'AUTH_PERMISSION_DENIED'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        template = self.get_object(pk, request)
        if not template:
            return Response(
                {
                    'success': False,
                    'code': 4004,
                    'message': _('邮件模板不存在'),
                    'data': None,
                    'error_code': 'NOT_FOUND'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EmailTemplateSerializer(
            template, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(
            {
                'success': False,
                'code': 4000,
                'message': _('请求参数错误'),
                'data': serializer.errors,
                'error_code': 'VALIDATION_ERROR'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        tags=['Email Templates'],
        summary='删除邮件模板',
        description='删除邮件模板（仅限租户管理员）',
        responses={
            204: OpenApiResponse(description='删除成功'),
            403: OpenApiResponse(description='权限不足'),
            404: OpenApiResponse(description='邮件模板不存在'),
            401: OpenApiResponse(description='未授权')
        }
    )
    def delete(self, request, pk):
        # 权限检查：只有租户管理员可以删除
        if not is_tenant_admin(request.user):
            return Response(
                {
                    'success': False,
                    'code': 4003,
                    'message': _('Only tenant administrators can manage email templates.'),
                    'data': None,
                    'error_code': 'AUTH_PERMISSION_DENIED'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        template = self.get_object(pk, request)
        if not template:
            return Response(
                {
                    'success': False,
                    'code': 4004,
                    'message': _('邮件模板不存在'),
                    'data': None,
                    'error_code': 'NOT_FOUND'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 软删除
        template.is_deleted = True
        template.save(update_fields=['is_deleted'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailLogListView(APIView):
    """
    邮件日志列表视图（只读）
    GET: 获取邮件发送日志（不需要认证）
    """
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    @extend_schema(
        tags=['Email Logs'],
        summary='获取邮件日志列表',
        description='获取邮件发送历史记录',
        parameters=[
            OpenApiParameter(
                name='feedback',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='按反馈ID筛选'
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按邮件状态筛选',
                enum=['pending', 'sending', 'sent', 'failed', 'bounced']
            ),
            OpenApiParameter(
                name='email_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按邮件类型筛选',
                enum=['reply', 'status_change', 'verification', 'summary']
            ),
            OpenApiParameter(
                name='recipient',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按收件人筛选'
            ),
        ],
        responses={
            200: FeedbackEmailLogSerializer(many=True),
            401: OpenApiResponse(description='未授权')
        }
    )
    def get(self, request):
        # 获取当前租户的邮件日志
        queryset = FeedbackEmailLog.objects.filter(is_deleted=False)
        
        # 过滤租户
        if hasattr(request, 'tenant') and request.tenant:
            queryset = queryset.filter(tenant=request.tenant)
        
        # 筛选条件
        feedback_id = request.query_params.get('feedback')
        if feedback_id:
            queryset = queryset.filter(feedback_id=feedback_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        email_type = request.query_params.get('email_type')
        if email_type:
            queryset = queryset.filter(email_type=email_type)
            
        recipient = request.query_params.get('recipient')
        if recipient:
            queryset = queryset.filter(recipient__icontains=recipient)
        
        # 排序
        queryset = queryset.order_by('-created_at')
        
        # 分页 (简单限制前100条)
        queryset = queryset[:100]
        
        serializer = FeedbackEmailLogSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class EmailLogDetailView(APIView):
    """
    邮件日志详情视图（只读）
    GET: 获取单个邮件日志详情（不需要认证）
    """
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    def get_object(self, pk, request):
        """获取邮件日志对象"""
        try:
            queryset = FeedbackEmailLog.objects.filter(pk=pk, is_deleted=False)
            if hasattr(request, 'tenant') and request.tenant:
                queryset = queryset.filter(tenant=request.tenant)
            return queryset.get()
        except FeedbackEmailLog.DoesNotExist:
            return None
    
    @extend_schema(
        tags=['Email Logs'],
        summary='获取邮件日志详情',
        description='获取指定ID的邮件日志详细信息',
        responses={
            200: FeedbackEmailLogSerializer,
            404: OpenApiResponse(description='邮件日志不存在'),
            401: OpenApiResponse(description='未授权')
        }
    )
    def get(self, request, pk):
        email_log = self.get_object(pk, request)
        if not email_log:
            return Response(
                {
                    'success': False,
                    'code': 4004,
                    'message': _('邮件日志不存在'),
                    'data': None,
                    'error_code': 'NOT_FOUND'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = FeedbackEmailLogSerializer(email_log, context={'request': request})
        return Response(serializer.data)
