"""
通知系统管理端视图
"""
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from common.viewsets import TenantModelViewSet
from common.utils.tenant_context import get_current_tenant
from users.models import Member

from .models import Notification, NotificationRecipient


def get_tenant_from_request(request):
    """
    从 request 中获取租户
    
    优先级:
    1. request.tenant (中间件设置的租户对象)
    2. get_current_tenant() (线程本地存储)
    3. request.tenant_id (中间件设置的租户ID)
    4. request.user.tenant (用户关联的租户)
    """
    from tenants.models import Tenant
    
    # 1. 尝试从 request.tenant 属性获取
    tenant = getattr(request, 'tenant', None)
    if tenant:
        return tenant
    
    # 2. 尝试从线程本地存储获取
    tenant = get_current_tenant()
    if tenant:
        return tenant
    
    # 3. 尝试从 request.tenant_id 获取
    tenant_id = getattr(request, 'tenant_id', None)
    if tenant_id:
        try:
            tenant = Tenant.objects.get(id=int(tenant_id))
            return tenant
        except (Tenant.DoesNotExist, ValueError, TypeError):
            pass
    
    # 4. 尝试从用户关联的租户获取
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        tenant = getattr(user, 'tenant', None)
        if tenant:
            return tenant
    
    return None
from .serializers import (
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationCreateSerializer,
    NotificationUpdateSerializer,
    NotificationRecipientSerializer,
    NotificationStatisticsSerializer,
    RecipientAddSerializer,
    RecipientRemoveSerializer,
)
from .permissions import NotificationPermission


@extend_schema_view(
    list=extend_schema(tags=['通知系统-管理端'], summary='获取通知列表'),
    retrieve=extend_schema(tags=['通知系统-管理端'], summary='获取通知详情'),
    create=extend_schema(tags=['通知系统-管理端'], summary='创建通知'),
    update=extend_schema(tags=['通知系统-管理端'], summary='更新通知'),
    partial_update=extend_schema(tags=['通知系统-管理端'], summary='部分更新通知'),
    destroy=extend_schema(tags=['通知系统-管理端'], summary='删除通知'),
)
class NotificationViewSet(TenantModelViewSet):
    """
    通知管理视图集
    
    管理端 API,用于租户管理员管理通知
    - GET 请求不需要认证,通过 X-Tenant-ID header 获取租户ID
    - POST/PATCH/DELETE 需要租户管理员权限
    """
    queryset = Notification.objects.all()
    permission_classes = [NotificationPermission]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'retrieve':
            return NotificationDetailSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NotificationUpdateSerializer
        elif self.action == 'recipients':
            return NotificationRecipientSerializer
        elif self.action == 'add_recipients':
            return RecipientAddSerializer
        elif self.action == 'remove_recipients':
            return RecipientRemoveSerializer
        elif self.action == 'statistics':
            return NotificationStatisticsSerializer
        return NotificationListSerializer
    
    def get_queryset(self):
        """
        获取查询集
        - 认证用户:基于用户的租户
        - 匿名用户:基于 X-Tenant-ID header
        """
        queryset = Notification.objects.filter(is_deleted=False)
        
        # 获取租户
        tenant = None
        if self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        
        if not tenant:
            tenant = get_tenant_from_request(self.request)
        
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        else:
            # 没有租户信息时返回空
            queryset = queryset.none()
        
        # 筛选条件
        application_id = self.request.query_params.get('application')
        scope = self.request.query_params.get('scope')
        notification_status = self.request.query_params.get('status')
        notification_type = self.request.query_params.get('type')
        priority = self.request.query_params.get('priority')
        
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        if scope:
            queryset = queryset.filter(scope=scope)
        if notification_status:
            queryset = queryset.filter(status=notification_status)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.select_related('application', 'created_by', 'tenant').order_by('-created_at')
    
    def perform_create(self, serializer):
        """创建时设置租户"""
        tenant = None
        if self.request.user.is_authenticated:
            tenant = getattr(self.request.user, 'tenant', None)
        
        if not tenant:
            tenant = get_tenant_from_request(self.request)
        
        serializer.save(tenant=tenant)
    
    @extend_schema(tags=['通知系统-管理端'], summary='获取通知的接收者列表')
    @action(detail=True, methods=['get'], url_path='recipients')
    def recipients(self, request, pk=None):
        """获取通知的接收者列表"""
        notification = self.get_object()
        recipients = NotificationRecipient.objects.filter(
            notification=notification,
            is_deleted=False
        ).select_related('member').order_by('-created_at')
        
        page = self.paginate_queryset(recipients)
        if page is not None:
            serializer = NotificationRecipientSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = NotificationRecipientSerializer(recipients, many=True)
        return Response(serializer.data)
    
    @extend_schema(tags=['通知系统-管理端'], summary='添加通知接收者')
    @action(detail=True, methods=['post'], url_path='add-recipients')
    def add_recipients(self, request, pk=None):
        """
        添加接收者(仅用于 scope=members 的通知)
        """
        notification = self.get_object()
        
        # 只有 scope=members 的通知可以手动添加接收者
        if notification.scope != 'members':
            return Response(
                {'detail': '只有"面向特定成员"的通知可以手动添加接收者'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RecipientAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member_ids = serializer.validated_data['member_ids']
        
        # 获取有效的成员(同租户)
        members = Member.objects.filter(
            id__in=member_ids,
            tenant=notification.tenant,
            is_active=True
        )
        
        added_count = 0
        for member in members:
            _, created = NotificationRecipient.objects.get_or_create(
                notification=notification,
                member=member,
                defaults={'tenant': notification.tenant}
            )
            if created:
                added_count += 1
        
        return Response({
            'detail': f'成功添加 {added_count} 个接收者',
            'added_count': added_count
        })
    
    @extend_schema(tags=['通知系统-管理端'], summary='移除通知接收者')
    @action(detail=True, methods=['post'], url_path='remove-recipients')
    def remove_recipients(self, request, pk=None):
        """移除接收者"""
        notification = self.get_object()
        
        serializer = RecipientRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member_ids = serializer.validated_data['member_ids']
        
        # 软删除接收者记录
        deleted_count = NotificationRecipient.objects.filter(
            notification=notification,
            member_id__in=member_ids,
            is_deleted=False
        ).update(is_deleted=True, deleted_at=timezone.now())
        
        return Response({
            'detail': f'成功移除 {deleted_count} 个接收者',
            'removed_count': deleted_count
        })
    
    @extend_schema(tags=['通知系统-管理端'], summary='发布通知')
    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """
        发布通知
        - 将状态从 draft 改为 published
        - 根据 scope 自动创建接收者记录
        - 如果 send_email=True,发送邮件
        """
        notification = self.get_object()
        
        if notification.status != 'draft':
            return Response(
                {'detail': '只有草稿状态的通知可以发布'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 根据 scope 创建接收者
        self._create_recipients_by_scope(notification)
        
        # 更新状态
        notification.status = 'published'
        notification.published_at = timezone.now()
        notification.save(update_fields=['status', 'published_at', 'updated_at'])
        
        # 发送邮件(异步)
        if notification.send_email:
            from .services import send_notification_email
            send_notification_email(notification.id)
        
        serializer = NotificationDetailSerializer(notification)
        return Response(serializer.data)
    
    def _create_recipients_by_scope(self, notification):
        """根据 scope 创建接收者记录"""
        if notification.scope == 'tenant':
            # 面向租户下所有成员
            members = Member.objects.filter(
                tenant=notification.tenant,
                is_active=True
            )
        elif notification.scope == 'application':
            # 面向应用下所有成员(这里假设所有租户成员都能看到应用的通知)
            # 如果有应用-成员关联,可以在这里筛选
            members = Member.objects.filter(
                tenant=notification.tenant,
                is_active=True
            )
        else:
            # scope=members,不自动创建,由管理员手动添加
            return
        
        # 批量创建接收者记录
        recipients_to_create = []
        existing_member_ids = set(
            NotificationRecipient.objects.filter(
                notification=notification
            ).values_list('member_id', flat=True)
        )
        
        for member in members:
            if member.id not in existing_member_ids:
                recipients_to_create.append(
                    NotificationRecipient(
                        notification=notification,
                        member=member,
                        tenant=notification.tenant
                    )
                )
        
        if recipients_to_create:
            NotificationRecipient.objects.bulk_create(recipients_to_create)
    
    @extend_schema(tags=['通知系统-管理端'], summary='归档通知')
    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        """归档通知"""
        notification = self.get_object()
        
        if notification.status == 'archived':
            return Response(
                {'detail': '通知已经是归档状态'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notification.status = 'archived'
        notification.save(update_fields=['status', 'updated_at'])
        
        serializer = NotificationDetailSerializer(notification)
        return Response(serializer.data)
    
    @extend_schema(tags=['通知系统-管理端'], summary='获取通知统计信息')
    @action(detail=True, methods=['get'], url_path='statistics')
    def statistics(self, request, pk=None):
        """获取通知统计信息"""
        notification = self.get_object()
        
        total = notification.get_recipient_count()
        read = notification.get_read_count()
        unread = notification.get_unread_count()
        read_rate = (read / total * 100) if total > 0 else 0
        
        data = {
            'total_recipients': total,
            'read_count': read,
            'unread_count': unread,
            'read_rate': round(read_rate, 2)
        }
        
        serializer = NotificationStatisticsSerializer(data)
        return Response(serializer.data)
