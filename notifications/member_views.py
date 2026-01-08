"""
通知系统成员端视图
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from common.permissions import IsMemberUser

from .models import NotificationRecipient
from .serializers import (
    MemberNotificationListSerializer,
    MemberNotificationDetailSerializer,
    UnreadCountSerializer,
)


class MemberNotificationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    成员端通知视图集
    
    成员端API，用于成员查看和管理自己的通知
    - 所有请求都需要成员认证
    """
    permission_classes = [IsMemberUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MemberNotificationListSerializer
        elif self.action == 'retrieve':
            return MemberNotificationDetailSerializer
        elif self.action == 'unread_count':
            return UnreadCountSerializer
        return MemberNotificationListSerializer
    
    def get_queryset(self):
        """获取当前成员的通知列表"""
        # 获取当前成员
        member = getattr(self.request.user, 'member_profile', None)
        if not member:
            return NotificationRecipient.objects.none()
        
        queryset = NotificationRecipient.objects.filter(
            member=member,
            is_deleted=False,
            notification__status='published',
            notification__is_deleted=False
        ).select_related(
            'notification',
            'notification__application'
        ).order_by('-notification__published_at')
        
        # 筛选条件
        application_id = self.request.query_params.get('application')
        is_read = self.request.query_params.get('is_read')
        notification_type = self.request.query_params.get('type')
        priority = self.request.query_params.get('priority')
        
        if application_id:
            queryset = queryset.filter(notification__application_id=application_id)
        if is_read is not None:
            is_read_bool = is_read.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_read=is_read_bool)
        if notification_type:
            queryset = queryset.filter(notification__notification_type=notification_type)
        if priority:
            queryset = queryset.filter(notification__priority=priority)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """获取通知详情并自动标记为已读"""
        instance = self.get_object()
        
        # 自动标记为已读
        if not instance.is_read:
            instance.is_read = True
            instance.read_at = timezone.now()
            instance.save(update_fields=['is_read', 'read_at', 'updated_at'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """标记单条通知为已读"""
        instance = self.get_object()
        
        if not instance.is_read:
            instance.is_read = True
            instance.read_at = timezone.now()
            instance.save(update_fields=['is_read', 'read_at', 'updated_at'])
        
        serializer = MemberNotificationDetailSerializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        """标记所有通知为已读"""
        member = getattr(request.user, 'member_profile', None)
        if not member:
            return Response(
                {'detail': '未找到成员信息'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新所有未读通知
        updated_count = NotificationRecipient.objects.filter(
            member=member,
            is_read=False,
            is_deleted=False,
            notification__status='published',
            notification__is_deleted=False
        ).update(
            is_read=True,
            read_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        return Response({
            'detail': f'已将 {updated_count} 条通知标记为已读',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """获取未读通知数量"""
        member = getattr(request.user, 'member_profile', None)
        if not member:
            return Response({'unread_count': 0})
        
        count = NotificationRecipient.objects.filter(
            member=member,
            is_read=False,
            is_deleted=False,
            notification__status='published',
            notification__is_deleted=False
        ).count()
        
        serializer = UnreadCountSerializer({'unread_count': count})
        return Response(serializer.data)
