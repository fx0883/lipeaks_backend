"""
Feedback Attachment APIView Implementation
将 FeedbackAttachmentViewSet 转换为 APIView，使用 Tenant-ID header 进行租户过滤
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import Feedback, FeedbackAttachment
from ..serializers import FeedbackAttachmentSerializer
from ..permissions import FeedbackReplyPermission  # 使用回复权限，附件上传需要相同权限


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


class FeedbackAttachmentListView(APIView):
    """反馈附件列表和上传API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ GET不需要认证
    parser_classes = (MultiPartParser, FormParser)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='List feedback attachments',
        description='Get all attachments for a specific feedback.',
        responses={200: FeedbackAttachmentSerializer(many=True)}
    )
    def get(self, request, feedback_pk):
        """获取反馈附件列表"""
        tenant = get_tenant_from_request(request)
        
        # 检查反馈是否存在且属于当前租户
        try:
            feedback = Feedback.objects.get(pk=feedback_pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取附件列表
        queryset = FeedbackAttachment.objects.filter(
            feedback_id=feedback_pk,
            is_deleted=False
        ).order_by('created_at')
        
        serializer = FeedbackAttachmentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Upload attachment',
        description='Upload a file attachment for feedback. Supports images, documents, and archives.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'description': {'type': 'string'}
                }
            }
        },
        responses={
            201: FeedbackAttachmentSerializer,
            400: OpenApiResponse(description='Invalid file'),
            413: OpenApiResponse(description='File too large'),
            415: OpenApiResponse(description='Unsupported file type')
        }
    )
    def post(self, request, feedback_pk):
        """上传反馈附件"""
        tenant = get_tenant_from_request(request)
        
        # 检查反馈是否存在且属于当前租户
        try:
            feedback = Feedback.objects.get(pk=feedback_pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 创建附件数据
        data = request.data.copy()
        data['feedback'] = feedback_pk
        
        serializer = FeedbackAttachmentSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            attachment = serializer.save(
                feedback=feedback,
                uploaded_by=request.user if request.user.is_authenticated else None,
                tenant=tenant
            )
            result_serializer = FeedbackAttachmentSerializer(attachment, context={'request': request})
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackAttachmentDetailView(APIView):
    """反馈附件详情API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ GET不需要认证
    
    def get_object(self, feedback_pk, pk, request):
        """获取附件对象并检查租户"""
        try:
            # 先检查反馈是否存在且属于当前租户
            tenant = get_tenant_from_request(request)
            feedback = Feedback.objects.get(pk=feedback_pk, is_deleted=False)
            if tenant and feedback.tenant != tenant:
                return None
            
            # 获取附件
            attachment = FeedbackAttachment.objects.get(pk=pk, feedback_id=feedback_pk, is_deleted=False)
            return attachment
        except (Feedback.DoesNotExist, FeedbackAttachment.DoesNotExist):
            return None
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Get attachment details',
        responses={200: FeedbackAttachmentSerializer, 404: OpenApiResponse(description='Not found')}
    )
    def get(self, request, feedback_pk, pk):
        """获取附件详情"""
        attachment = self.get_object(feedback_pk, pk, request)
        if not attachment:
            return Response({'detail': 'Attachment not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FeedbackAttachmentSerializer(attachment, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Delete attachment',
        responses={204: OpenApiResponse(description='Deleted successfully')}
    )
    def delete(self, request, feedback_pk, pk):
        """删除附件(软删除)"""
        attachment = self.get_object(feedback_pk, pk, request)
        if not attachment:
            return Response({'detail': 'Attachment not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        attachment.is_deleted = True
        attachment.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)

