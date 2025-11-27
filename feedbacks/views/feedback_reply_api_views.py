"""
Feedback Reply APIView Implementation
将 FeedbackReplyViewSet 转换为 APIView，使用 Tenant-ID header 进行租户过滤
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from ..models import Feedback, FeedbackReply
from ..serializers import FeedbackReplySerializer, FeedbackReplyCreateSerializer
from ..permissions import FeedbackReplyPermission
from ..services import FeedbackService


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
    
    return None


class FeedbackReplyListView(APIView):
    """反馈回复列表和创建API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ GET不需要认证
    
    @extend_schema(
        tags=['Feedback System'],
        summary='List feedback replies',
        description='Get all replies for a specific feedback. Non-staff users do not see internal notes.',
        responses={200: FeedbackReplySerializer(many=True)}
    )
    def get(self, request, feedback_pk):
        """获取反馈回复列表"""
        tenant = get_tenant_from_request(request)
        
        # 检查反馈是否存在且属于当前租户
        try:
            feedback = Feedback.objects.get(pk=feedback_pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取回复列表
        queryset = FeedbackReply.objects.filter(
            feedback_id=feedback_pk,
            is_deleted=False
        )
        
        # 非管理员用户不显示内部备注
        if not request.user.is_staff:
            queryset = queryset.filter(is_internal_note=False)
        
        queryset = queryset.order_by('created_at')
        serializer = FeedbackReplySerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Create feedback reply',
        description='Add a reply to feedback. Can send email notification if configured.',
        request=FeedbackReplyCreateSerializer,
        responses={201: FeedbackReplySerializer}
    )
    def post(self, request, feedback_pk):
        """创建反馈回复"""
        tenant = get_tenant_from_request(request)
        
        # 检查反馈是否存在且属于当前租户
        try:
            feedback = Feedback.objects.get(pk=feedback_pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FeedbackReplyCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # 使用服务创建回复（处理邮件发送）
            reply = FeedbackService.add_reply(
                feedback=feedback,
                content=serializer.validated_data['content'],
                user=request.user,
                is_internal_note=serializer.validated_data.get('is_internal_note', False)
            )
            
            result_serializer = FeedbackReplySerializer(reply, context={'request': request})
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackReplyDetailView(APIView):
    """反馈回复详情API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ GET不需要认证
    
    def get_object(self, feedback_pk, pk, request):
        """获取回复对象并检查租户"""
        try:
            # 先检查反馈是否存在且属于当前租户
            tenant = get_tenant_from_request(request)
            feedback = Feedback.objects.get(pk=feedback_pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return None
            
            # 获取回复
            reply = FeedbackReply.objects.get(pk=pk, feedback_id=feedback_pk, is_deleted=False)
            
            # 非管理员用户不能访问内部备注
            if not request.user.is_staff and reply.is_internal_note:
                return None
            
            return reply
        except (Feedback.DoesNotExist, FeedbackReply.DoesNotExist):
            return None
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Get reply details',
        responses={200: FeedbackReplySerializer, 404: OpenApiResponse(description='Not found')}
    )
    def get(self, request, feedback_pk, pk):
        """获取回复详情"""
        reply = self.get_object(feedback_pk, pk, request)
        if not reply:
            return Response({'detail': 'Reply not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FeedbackReplySerializer(reply, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Update reply',
        request=FeedbackReplySerializer,
        responses={200: FeedbackReplySerializer}
    )
    def put(self, request, feedback_pk, pk):
        """完整更新回复"""
        return self._update(request, feedback_pk, pk, partial=False)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Partially update reply',
        request=FeedbackReplySerializer,
        responses={200: FeedbackReplySerializer}
    )
    def patch(self, request, feedback_pk, pk):
        """部分更新回复"""
        return self._update(request, feedback_pk, pk, partial=True)
    
    def _update(self, request, feedback_pk, pk, partial=False):
        """更新回复"""
        reply = self.get_object(feedback_pk, pk, request)
        if not reply:
            return Response({'detail': 'Reply not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FeedbackReplySerializer(reply, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Delete reply',
        responses={204: OpenApiResponse(description='Deleted successfully')}
    )
    def delete(self, request, feedback_pk, pk):
        """删除回复(软删除)"""
        reply = self.get_object(feedback_pk, pk, request)
        if not reply:
            return Response({'detail': 'Reply not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        reply.is_deleted = True
        reply.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)

