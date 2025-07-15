"""
订单历史记录视图
"""
import logging
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from common.permissions import IsAdmin
from orders.models import Order, OrderHistory
from orders.serializers import (
    OrderHistorySerializer, OrderHistoryDetailSerializer, 
    OrderCompareSerializer, OrderSerializer
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取订单历史记录列表",
        description="获取指定订单的所有历史记录",
        tags=["订单历史"],
        parameters=[
            # 路径参数已经在URL中定义，这里不需要重复定义
        ]
    ),
    retrieve=extend_schema(
        summary="获取订单历史记录详情",
        description="获取指定订单的特定版本历史记录详情",
        tags=["订单历史"],
        parameters=[
            # 路径参数已经在URL中定义，这里不需要重复定义
        ]
    ),
)
class OrderHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    订单历史记录视图集
    
    提供订单历史记录的查询、比较和还原功能
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['version', 'modified_at']
    ordering = ['-version']
    lookup_field = 'version'
    
    def get_queryset(self):
        """
        获取指定订单的历史记录
        """
        order_id = self.kwargs.get('order_id')
        return OrderHistory.objects.filter(order_id=order_id)
    
    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器
        """
        if self.action == 'retrieve':
            return OrderHistoryDetailSerializer
        elif self.action == 'compare':
            return OrderCompareSerializer
        return OrderHistorySerializer
    
    def get_serializer_context(self):
        """
        添加额外的上下文信息
        """
        context = super().get_serializer_context()
        context['order_id'] = self.kwargs.get('order_id')
        return context
    
    @extend_schema(
        summary="比较订单历史版本",
        description="比较指定订单的两个历史版本的差异",
        tags=["订单历史"],
        parameters=[
            # 路径参数已经在URL中定义，这里不需要重复定义
            OpenApiParameter(name="version1", description="第一个版本号", required=True, type=int),
            OpenApiParameter(name="version2", description="第二个版本号", required=True, type=int),
        ]
    )
    @action(detail=False, methods=['get'])
    def compare(self, request, order_id=None):
        """
        比较两个版本的订单数据
        """
        # 获取版本号
        version1 = request.query_params.get('version1')
        version2 = request.query_params.get('version2')
        
        if not version1 or not version2:
            return Response(
                {"error": "必须提供两个版本号"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            version1 = int(version1)
            version2 = int(version2)
        except ValueError:
            return Response(
                {"error": "版本号必须是整数"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取订单
        order = get_object_or_404(Order, id=order_id)
        
        # 获取历史记录
        history1 = get_object_or_404(OrderHistory, order=order, version=version1)
        history2 = get_object_or_404(OrderHistory, order=order, version=version2)
        
        # 比较差异
        differences = {}
        snapshot1 = history1.snapshot
        snapshot2 = history2.snapshot
        
        # 将JSON字符串解析为Python字典
        import json
        try:
            snapshot1 = json.loads(snapshot1)
            snapshot2 = json.loads(snapshot2)
        except (TypeError, json.JSONDecodeError) as e:
            return Response(
                {"error": f"无法解析历史记录快照: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 获取所有键的并集
        all_keys = set(snapshot1.keys()) | set(snapshot2.keys())
        
        # 比较每个键的值
        for key in all_keys:
            value1 = snapshot1.get(key)
            value2 = snapshot2.get(key)
            
            # 如果值不同，添加到差异中
            if value1 != value2:
                differences[key] = {
                    'version1': value1,
                    'version2': value2
                }
        
        # 构造响应数据
        result = {
            'order_id': order.id,
            'order_number': order.order_number,
            'version1': version1,
            'version2': version2,
            'differences': differences
        }
        
        return Response(result)
    
    @extend_schema(
        summary="还原到历史版本",
        description="将订单还原到指定的历史版本",
        tags=["订单历史"],
        request=None,
        responses={200: OrderSerializer}
    )
    @action(detail=True, methods=['post'])
    def restore(self, request, order_id=None, version=None):
        """
        将订单还原到特定历史版本
        """
        # 获取订单和历史记录
        order = get_object_or_404(Order, id=order_id)
        history = get_object_or_404(OrderHistory, order=order, version=version)
        
        # 获取快照数据
        snapshot = history.snapshot
        
        # 需要排除的字段
        exclude_fields = ['id', 'created_at', 'updated_at', 'tenant', 'is_deleted']
        
        # 更新订单字段
        update_data = {}
        for key, value in snapshot.items():
            if key not in exclude_fields:
                update_data[key] = value
        
        # 更新订单
        for key, value in update_data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        # 保存订单
        order.save()
        
        # 创建新的历史记录
        OrderHistory.create_history_record(
            order=order,
            user=request.user,
            change_details={
                'action': 'restore',
                'message': f'还原到版本 {version}',
                'restored_from_version': version
            }
        )
        
        # 序列化订单并返回
        serializer = OrderSerializer(order)
        return Response(serializer.data) 