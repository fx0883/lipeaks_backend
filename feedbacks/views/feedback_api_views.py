"""
Feedback APIView Implementation
将 FeedbackViewSet 转换为 APIView，使用 Tenant-ID header 进行租户过滤
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from common.pagination import StandardResultsSetPagination

from ..models import Feedback, FeedbackStatusHistory
from ..serializers import (
    FeedbackListSerializer,
    FeedbackDetailSerializer,
    FeedbackCreateSerializer,
    FeedbackUpdateSerializer,
)
from ..permissions import (
    FeedbackViewPermission,
    FeedbackCreatePermission,
    FeedbackUpdatePermission,
    FeedbackDeletePermission,
    FeedbackStatusChangePermission,
    is_tenant_admin,
    can_manage_feedback_app,
    filter_feedback_queryset_for_user,
)


def get_tenant_from_request(request):
    """
    从request中获取租户
    
    优先级：
    1. request.tenant (中间件设置)
    2. get_current_tenant() (线程本地存储)
    3. request.user.tenant (用户关联的租户)
    """
    # 1. 尝试从request属性获取
    tenant = getattr(request, 'tenant', None)
    if tenant:
        return tenant
    
    # 2. 尝试从线程本地存储获取
    from common.utils.tenant_context import get_current_tenant
    tenant = get_current_tenant()
    if tenant:
        return tenant
    
    # 3. 尝试从用户关联的租户获取
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        tenant = getattr(user, 'tenant', None)
        if tenant:
            return tenant
            
    # 4. 尝试从 X-Tenant-ID 请求头获取
    header_tid = request.headers.get('X-Tenant-ID') or request.GET.get('tenant_id')
    if header_tid:
        from tenants.models import Tenant
        tenant = Tenant.objects.filter(id=header_tid, is_deleted=False).first()
        if tenant:
            return tenant

    return None


class FeedbackListView(APIView):
    """反馈列表和创建API - GET和POST都不需要认证"""
    permission_classes = [AllowAny]  # ✅ 允许匿名访问和提交反馈
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Feedback System'],
        summary='List feedback',
        description='Get a list of feedback filtered by tenant. '
                   'Super admins see all tenant feedback, '
                   'tenant admins see all tenant feedback, regular users see only their own.',
        parameters=[
            OpenApiParameter('application', OpenApiTypes.INT, OpenApiParameter.QUERY, 
                           description='Filter by application ID'),
            OpenApiParameter('feedback_type', OpenApiTypes.STR, OpenApiParameter.QUERY, 
                           enum=['bug', 'feature', 'improvement', 'question', 'other']),
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY,
                           enum=['submitted', 'reviewing', 'confirmed', 'in_progress', 'resolved', 'closed', 'rejected', 'duplicate']),
            OpenApiParameter('priority', OpenApiTypes.STR, OpenApiParameter.QUERY, enum=['critical', 'high', 'medium', 'low']),
            OpenApiParameter('email_verified', OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter('search', OpenApiTypes.STR, OpenApiParameter.QUERY, description='Search in title, description'),
            OpenApiParameter('ordering', OpenApiTypes.STR, OpenApiParameter.QUERY, 
                           description='Order by: created_at, -created_at, vote_count, -vote_count, etc.'),
        ],
        responses={200: FeedbackListSerializer(many=True)}
    )
    def get(self, request):
        """获取反馈列表"""
        tenant = get_tenant_from_request(request)
        user = request.user
        
        # 基础查询集（预加载 application, user, tenant 消除 N+1）
        queryset = Feedback.objects.select_related('application', 'user', 'tenant').all()
        
        # 租户过滤
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        
        # 应用过滤 (可选)
        application_id = request.query_params.get('application')
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        
        # 权限与角色数据范围过滤（super_admin 不可见；tenant_owner 见全租户；app_admin 见管辖应用；普通用户见自己提交）
        queryset = filter_feedback_queryset_for_user(queryset, user)
        
        feedback_type = request.query_params.get('feedback_type')
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        
        feedback_status = request.query_params.get('status')
        if feedback_status:
            queryset = queryset.filter(status=feedback_status)
        
        priority = request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        email_verified = request.query_params.get('email_verified')
        if email_verified is not None:
            queryset = queryset.filter(email_verified=email_verified.lower() in ('true', '1'))
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(contact_email__icontains=search)
            )
        
        # 排序
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # 分页接入 (防 OOM)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = FeedbackListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
            
        serializer = FeedbackListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Submit feedback',
        description='Submit new feedback. Anyone can submit, anonymous users must provide email.',
        request=FeedbackCreateSerializer,
        responses={201: FeedbackDetailSerializer}
    )
    def post(self, request):
        """创建反馈"""
        import logging
        logger = logging.getLogger(__name__)
        
        tenant = get_tenant_from_request(request)
        
        try:
            serializer = FeedbackCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                # 设置租户
                logger.debug(f"Creating feedback with tenant: {tenant}")
                feedback = serializer.save(tenant=tenant if tenant else None)
                logger.debug(f"Feedback created successfully: {feedback.id}")

                # 触发新反馈邮件通知（异步处理，失败不影响反馈提交）
                try:
                    from ..services import EmailService
                    EmailService.send_new_feedback_notification(feedback)
                except Exception as notify_error:
                    logger.warning(f"Failed to trigger notification for feedback {feedback.id}: {notify_error}")

                detail_serializer = FeedbackDetailSerializer(feedback, context={'request': request})
                return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.warning(f"Feedback validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating feedback: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error creating feedback: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedbackDetailView(APIView):
    """反馈详情API - 仅限所属租户管理员/应用管理员或提交者访问"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, request):
        """获取反馈对象并检查租户与应用管辖权限"""
        try:
            feedback = Feedback.objects.select_related('application', 'user', 'tenant').get(pk=pk, is_deleted=False)
            tenant = get_tenant_from_request(request)
            if tenant and feedback.tenant != tenant:
                return None

            user = request.user
            if getattr(user, 'is_super_admin', False) or getattr(user, 'is_superuser', False):
                return None
            if is_tenant_admin(user):
                if not can_manage_feedback_app(user, feedback.application_id):
                    return None
                return feedback
            if feedback.user_id != user.id:
                return None
            return feedback
        except Feedback.DoesNotExist:
            return None
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Get feedback details',
        responses={200: FeedbackDetailSerializer, 404: OpenApiResponse(description='Not found')}
    )
    def get(self, request, pk):
        """获取反馈详情"""
        feedback = self.get_object(pk, request)
        if not feedback:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 增加浏览次数
        feedback.view_count += 1
        feedback.save(update_fields=['view_count'])
        
        serializer = FeedbackDetailSerializer(feedback, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Update feedback',
        request=FeedbackUpdateSerializer,
        responses={200: FeedbackDetailSerializer}
    )
    def put(self, request, pk):
        """完整更新反馈"""
        return self._update(request, pk, partial=False)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Partially update feedback',
        request=FeedbackUpdateSerializer,
        responses={200: FeedbackDetailSerializer}
    )
    def patch(self, request, pk):
        """部分更新反馈"""
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        """更新反馈"""
        feedback = self.get_object(pk, request)
        if not feedback:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)

        perm = FeedbackUpdatePermission()
        if not perm.has_object_permission(request, self, feedback):
            return Response({'detail': str(perm.message)}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = FeedbackUpdateSerializer(feedback, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            detail_serializer = FeedbackDetailSerializer(feedback, context={'request': request})
            return Response(detail_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Delete feedback',
        responses={204: OpenApiResponse(description='Deleted successfully')}
    )
    def delete(self, request, pk):
        """删除反馈(软删除)"""
        feedback = self.get_object(pk, request)
        if not feedback:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)

        perm = FeedbackDeletePermission()
        if not perm.has_object_permission(request, self, feedback):
            return Response({'detail': str(perm.message)}, status=status.HTTP_403_FORBIDDEN)
        
        feedback.is_deleted = True
        feedback.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeedbackChangeStatusView(APIView):
    """更改反馈状态API"""
    permission_classes = [FeedbackStatusChangePermission]
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Change feedback status',
        description='Change feedback status (tenant admin / app admin only). Creates status history record.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'enum': ['submitted', 'reviewing', 'confirmed', 'in_progress', 'resolved', 'closed', 'rejected', 'duplicate']},
                    'reason': {'type': 'string'}
                },
                'required': ['status']
            }
        },
        responses={200: FeedbackDetailSerializer}
    )
    def patch(self, request, pk):
        """更改反馈状态"""
        tenant = get_tenant_from_request(request)
        
        try:
            feedback = Feedback.objects.get(pk=pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, feedback)
        
        new_status = request.data.get('status')
        reason = request.data.get('reason') or request.data.get('comment', '')
        
        if not new_status:
            return Response({'detail': 'Status is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status == feedback.status:
            return Response({'detail': 'New status is same as current status.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建状态历史记录
        old_status = feedback.status
        feedback.status = new_status
        feedback.save(update_fields=['status'])
        
        FeedbackStatusHistory.objects.create(
            feedback=feedback,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            reason=reason,
            tenant=tenant
        )
        
        serializer = FeedbackDetailSerializer(feedback, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, pk):
        """兼容POST方式更新状态"""
        return self.patch(request, pk)


class FeedbackVerifyEmailView(APIView):
    """验证反馈邮箱API"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Verify feedback email',
        request={'application/json': {'type': 'object', 'properties': {'token': {'type': 'string'}}}},
        responses={200: OpenApiResponse(description='Email verified successfully')}
    )
    def post(self, request, pk):
        """验证反馈邮箱"""
        tenant = get_tenant_from_request(request)
        token = request.data.get('token')
        
        if not token:
            return Response({'detail': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            feedback = Feedback.objects.get(pk=pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if feedback.email_verified:
            return Response({'detail': 'Email already verified.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if feedback.email_verification_token != token:
            return Response({'detail': 'Invalid verification token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        feedback.email_verified = True
        feedback.email_verification_token = ''
        feedback.save(update_fields=['email_verified', 'email_verification_token'])
        
        return Response({'detail': 'Email verified successfully.'})


class FeedbackToggleNotificationsView(APIView):
    """切换反馈通知API"""
    permission_classes = [IsAuthenticated]
    serializer_class = FeedbackDetailSerializer  # For schema generation
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Toggle feedback notifications',
        request=None,  # No request body
        responses={200: FeedbackDetailSerializer}
    )
    def patch(self, request, pk):
        """切换反馈通知"""
        tenant = get_tenant_from_request(request)
        
        try:
            feedback = Feedback.objects.get(pk=pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 只有创建者可以切换通知
        if feedback.user != request.user:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        feedback.email_notification_enabled = not feedback.email_notification_enabled
        feedback.save(update_fields=['email_notification_enabled'])
        
        serializer = FeedbackDetailSerializer(feedback, context={'request': request})
        return Response(serializer.data)

