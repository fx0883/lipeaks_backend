"""
Feedback Notification Configuration API Views

反馈通知配置管理 API - 仅限租户管理员
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from feedbacks.models import (
    FeedbackNotificationConfig, 
    FeedbackNotificationRecipient
)
from feedbacks.serializers import (
    FeedbackNotificationConfigSerializer,
    FeedbackNotificationConfigCreateSerializer,
    FeedbackNotificationConfigUpdateSerializer,
    FeedbackNotificationRecipientSerializer,
    FeedbackNotificationRecipientCreateSerializer,
    NotificationTestSerializer
)
from feedbacks.permissions import IsTenantAdmin

logger = logging.getLogger(__name__)


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


@extend_schema_view(
    list=extend_schema(
        summary="获取通知配置列表",
        description="获取当前租户下所有应用的反馈通知配置"
    ),
    create=extend_schema(
        summary="创建通知配置",
        description="为指定应用创建反馈通知配置"
    ),
    retrieve=extend_schema(
        summary="获取通知配置详情",
        description="获取指定通知配置的详细信息，包含接收者列表"
    ),
    update=extend_schema(
        summary="更新通知配置",
        description="更新通知配置（如启用/禁用）"
    ),
    partial_update=extend_schema(
        summary="部分更新通知配置",
        description="部分更新通知配置字段"
    ),
    destroy=extend_schema(
        summary="删除通知配置",
        description="删除指定的通知配置及其所有接收者"
    ),
)
class FeedbackNotificationConfigViewSet(viewsets.ModelViewSet):
    """
    反馈通知配置管理 API
    
    仅限租户管理员访问，用于管理应用级别的反馈通知配置。
    """
    permission_classes = [IsTenantAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackNotificationConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FeedbackNotificationConfigUpdateSerializer
        elif self.action == 'add_recipient':
            return FeedbackNotificationRecipientCreateSerializer
        elif self.action == 'test':
            return NotificationTestSerializer
        return FeedbackNotificationConfigSerializer
    
    def get_queryset(self):
        """获取当前租户的通知配置"""
        tenant = get_tenant_from_request(self.request)
        if not tenant:
            return FeedbackNotificationConfig.objects.none()
        
        return FeedbackNotificationConfig.objects.filter(
            tenant=tenant,
            is_deleted=False
        ).select_related('application').prefetch_related('recipients')
    
    def perform_create(self, serializer):
        """创建时自动设置租户"""
        tenant = get_tenant_from_request(self.request)
        serializer.save(tenant=tenant)
        logger.info(
            f"Notification config created for application {serializer.instance.application.name} "
            f"by user {self.request.user.username}"
        )
    
    def perform_destroy(self, instance):
        """软删除"""
        instance.is_deleted = True
        instance.save()
        # 同时软删除所有接收者
        instance.recipients.update(is_deleted=True)
        logger.info(
            f"Notification config deleted for application {instance.application.name} "
            f"by user {self.request.user.username}"
        )
    
    # ==================== 接收者管理 ====================
    
    @extend_schema(
        summary="获取接收者列表",
        description="获取指定配置下的所有通知接收者",
        responses={200: FeedbackNotificationRecipientSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='recipients')
    def list_recipients(self, request, pk=None):
        """获取接收者列表"""
        config = self.get_object()
        recipients = config.recipients.filter(is_deleted=False)
        serializer = FeedbackNotificationRecipientSerializer(recipients, many=True)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })
    
    @extend_schema(
        summary="添加接收者",
        description="向指定配置添加新的通知接收者",
        request=FeedbackNotificationRecipientCreateSerializer,
        responses={201: FeedbackNotificationRecipientSerializer}
    )
    @action(detail=True, methods=['post'], url_path='recipients/add')
    def add_recipient(self, request, pk=None):
        """添加接收者"""
        config = self.get_object()
        serializer = FeedbackNotificationRecipientCreateSerializer(
            data=request.data,
            context={'request': request, 'config': config}
        )
        serializer.is_valid(raise_exception=True)
        
        tenant = get_tenant_from_request(self.request)
        recipient = FeedbackNotificationRecipient.objects.create(
            config=config,
            tenant=tenant,
            **serializer.validated_data
        )
        
        logger.info(
            f"Recipient {recipient.email} added to config {config.id} "
            f"by user {request.user.username}"
        )
        
        return Response({
            'code': 201,
            'message': _('接收者添加成功'),
            'data': FeedbackNotificationRecipientSerializer(recipient).data
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="删除接收者",
        description="从配置中删除指定的接收者",
        parameters=[
            OpenApiParameter(
                name='recipient_id',
                type=int,
                location=OpenApiParameter.PATH,
                description='接收者ID'
            )
        ]
    )
    @action(detail=True, methods=['delete'], url_path='recipients/(?P<recipient_id>[^/.]+)')
    def remove_recipient(self, request, pk=None, recipient_id=None):
        """删除接收者"""
        config = self.get_object()
        recipient = get_object_or_404(
            FeedbackNotificationRecipient,
            id=recipient_id,
            config=config,
            is_deleted=False
        )
        
        email = recipient.email
        recipient.is_deleted = True
        recipient.save()
        
        logger.info(
            f"Recipient {email} removed from config {config.id} "
            f"by user {request.user.username}"
        )
        
        return Response({
            'code': 200,
            'message': _('接收者已删除')
        })
    
    @extend_schema(
        summary="更新接收者",
        description="更新接收者信息（如启用/禁用、修改姓名）",
        parameters=[
            OpenApiParameter(
                name='recipient_id',
                type=int,
                location=OpenApiParameter.PATH,
                description='接收者ID'
            )
        ],
        request=FeedbackNotificationRecipientCreateSerializer,
        responses={200: FeedbackNotificationRecipientSerializer}
    )
    @action(detail=True, methods=['patch'], url_path='recipients/(?P<recipient_id>[^/.]+)/update')
    def update_recipient(self, request, pk=None, recipient_id=None):
        """更新接收者"""
        config = self.get_object()
        recipient = get_object_or_404(
            FeedbackNotificationRecipient,
            id=recipient_id,
            config=config,
            is_deleted=False
        )
        
        # 更新字段
        if 'email' in request.data:
            new_email = request.data['email']
            # 检查邮箱是否已被其他接收者使用
            if FeedbackNotificationRecipient.objects.filter(
                config=config,
                email=new_email,
                is_deleted=False
            ).exclude(id=recipient.id).exists():
                return Response({
                    'code': 400,
                    'message': _('该邮箱已存在于此配置中')
                }, status=status.HTTP_400_BAD_REQUEST)
            recipient.email = new_email
        if 'name' in request.data:
            recipient.name = request.data['name']
        if 'is_active' in request.data:
            recipient.is_active = request.data['is_active']
        recipient.save()
        
        logger.info(
            f"Recipient {recipient.email} updated in config {config.id} "
            f"by user {request.user.username}"
        )
        
        return Response({
            'code': 200,
            'message': _('接收者信息已更新'),
            'data': FeedbackNotificationRecipientSerializer(recipient).data
        })
    
    # ==================== 测试邮件 ====================
    
    @extend_schema(
        summary="发送测试邮件",
        description="发送测试通知邮件到指定邮箱，用于验证邮件配置是否正常",
        request=NotificationTestSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'message': {'type': 'string', 'example': '测试邮件已发送'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'status': {'type': 'string'},
                            'recipient': {'type': 'string'}
                        }
                    }
                }
            }
        }
    )
    @action(detail=True, methods=['post'], url_path='test')
    def test(self, request, pk=None):
        """发送测试邮件"""
        config = self.get_object()
        serializer = NotificationTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        test_email = serializer.validated_data['email']
        
        # 调用服务发送测试邮件
        from feedbacks.services import EmailService
        result = EmailService.send_test_notification(config, test_email)
        
        if result.get('status') == 'success':
            return Response({
                'code': 200,
                'message': _('测试邮件已发送'),
                'data': {
                    'status': 'sent',
                    'recipient': test_email
                }
            })
        else:
            return Response({
                'code': 500,
                'message': _('测试邮件发送失败'),
                'data': {
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error')
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ==================== 按应用查询 ====================
    
    @extend_schema(
        summary="按应用获取配置",
        description="根据应用ID获取其通知配置，如不存在则返回空",
        parameters=[
            OpenApiParameter(
                name='application_id',
                type=int,
                location=OpenApiParameter.PATH,
                description='应用ID'
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-application/(?P<application_id>[^/.]+)')
    def by_application(self, request, application_id=None):
        """按应用ID获取配置"""
        try:
            tenant = get_tenant_from_request(request)
            config = FeedbackNotificationConfig.objects.get(
                tenant=tenant,
                application_id=application_id,
                is_deleted=False
            )
            serializer = FeedbackNotificationConfigSerializer(config)
            return Response({
                'code': 200,
                'message': 'success',
                'data': serializer.data
            })
        except FeedbackNotificationConfig.DoesNotExist:
            return Response({
                'code': 404,
                'message': _('该应用暂未配置通知'),
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
