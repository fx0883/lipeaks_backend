"""
客户订单视图
"""
import logging
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from common.permissions import IsAdminUser
from orders.models import Order
from orders.serializers import OrderListSerializer, OrderDetailSerializer
from customers.models import Customer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取客户订单列表",
        description="获取特定客户的所有订单，支持分页、排序和筛选",
        tags=["客户订单"],
        parameters=[
            # 路径参数已经在URL中定义，这里不需要重复定义
            OpenApiParameter(name="payment_status", description="按支付状态筛选订单", required=False, type=str),
            OpenApiParameter(name="service_type", description="按服务类型筛选订单", required=False, type=str),
            OpenApiParameter(name="order_date_from", description="按订单日期范围筛选（起始）", required=False, type=str),
            OpenApiParameter(name="order_date_to", description="按订单日期范围筛选（结束）", required=False, type=str),
            OpenApiParameter(name="start_date", description="按服务时间范围筛选（起始日期）", required=False, type=str),
            OpenApiParameter(name="end_date", description="按服务时间范围筛选（结束日期）", required=False, type=str),
            OpenApiParameter(name="search", description="搜索订单编号、译员等信息", required=False, type=str),
        ],
        examples=[
            OpenApiExample(
                name="客户订单列表响应示例",
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 15,
                            "customer_name": "上海环球公司",
                            "created_by_info": {"id": 1, "username": "admin", "display_name": "管理员"},
                            "customer_contact_info": {"id": 8, "username": "zhangsan", "display_name": "张三", "phone": "13800138000", "email": "zhangsan@example.com"},
                            "profit": 1000.00,
                            "profit_rate": 0.40,
                            "formatted_profit": "¥1000.00",
                            "formatted_profit_rate": "40.00%",
                            "created_at": "2025-07-15T08:30:45.123456Z",
                            "updated_at": "2025-07-15T08:30:45.123456Z",
                            "is_deleted": False,
                            "order_number": "PQ-202507-5678",
                            "service_type": "文档翻译",
                            "language": "中英",
                            "customer_count": "5000字",
                            "customer_total_amount": "2500.00",
                            "payment_status": "paid",
                            "payment_status_display": "已支付"
                        },
                        {
                            "id": 16,
                            "customer_name": "上海环球公司",
                            "created_by_info": {"id": 1, "username": "admin", "display_name": "管理员"},
                            "customer_contact_info": {"id": 8, "username": "zhangsan", "display_name": "张三", "phone": "13800138000", "email": "zhangsan@example.com"},
                            "profit": 800.00,
                            "profit_rate": 0.32,
                            "formatted_profit": "¥800.00",
                            "formatted_profit_rate": "32.00%",
                            "created_at": "2025-07-16T09:45:30.234567Z",
                            "updated_at": "2025-07-16T09:45:30.234567Z",
                            "is_deleted": False,
                            "order_number": "PQ-202507-9876",
                            "service_type": "口译服务",
                            "language": "中日",
                            "customer_count": "1天",
                            "customer_total_amount": "2500.00",
                            "payment_status": "unpaid",
                            "payment_status_display": "未支付"
                        }
                    ]
                },
                media_type="application/json",
                response_only=True,
                summary="客户订单列表响应示例"
            )
        ]
    ),
    retrieve=extend_schema(
        summary="获取客户订单详情",
        description="获取特定客户的指定订单详情",
        tags=["客户订单"],
        parameters=[
            # 路径参数已经在URL中定义，这里不需要重复定义
        ],
        examples=[
            OpenApiExample(
                name="客户订单详情响应示例",
                value={
                    "id": 15,
                    "customer": {
                        "id": 5,
                        "name": "上海环球公司",
                        "code": "SH001",
                        "contact_name": "张三",
                        "contact_phone": "13800138000",
                        "contact_email": "zhangsan@example.com"
                    },
                    "customer_contact": {
                        "id": 8,
                        "username": "zhangsan",
                        "display_name": "张三",
                        "phone": "13800138000",
                        "email": "zhangsan@example.com"
                    },
                    "history_count": 2,
                    "profit": 1000.00,
                    "profit_rate": 0.40,
                    "formatted_profit": "¥1000.00",
                    "formatted_profit_rate": "40.00%",
                    "created_at": "2025-07-15T08:30:45.123456Z",
                    "updated_at": "2025-07-15T08:30:45.123456Z",
                    "is_deleted": False,
                    "order_number": "PQ-202507-5678",
                    "source_platform": "官网",
                    "project_manager": "五组",
                    "customer_type": "老客户",
                    "order_date": "2025-07-15",
                    "service_type": "文档翻译",
                    "service_type_display": "文档翻译",
                    "language": "中英",
                    "customer_count": "5000字",
                    "translation_count": "5000字",
                    "service_time": "2025-07-20前交稿",
                    "project_location": "线上",
                    "translator": "张三",
                    "customer_price": "0.5元/字",
                    "customer_total_amount": "2500.00",
                    "translator_fee": "1250.00",
                    "translator_price": "0.25元/字",
                    "translator_payment_status": "已付款",
                    "translator_payment_method": "支付宝",
                    "project_fee": "250.00",
                    "project_details": "技术文档翻译，包含10个Word文档",
                    "cost_details": "版式调整费用250元",
                    "refund_amount": "0.00",
                    "refund_reason": None,
                    "payment_status": "paid",
                    "payment_status_display": "已支付",
                    "payment_date": "2025-07-15",
                    "payment_method": "银行转账",
                    "payment_remarks": "已确认收款",
                    "invoice_status": "issued",
                    "invoice_status_display": "已开具",
                    "invoice_info": "增值税专用发票已邮寄",
                    "contract_number": "HT-202507-001",
                    "contract_info": "合同已签署",
                    "contract_remarks": "客户要求提前交付",
                    "delivery_address": "上海市浦东新区xx路xx号",
                    "order_address": "上海市浦东新区xx路xx号",
                    "remarks": "客户要求保持原文格式",
                    "follow_up_record": "2025-07-16已电话回访，客户表示满意",
                    "tenant": 1
                },
                media_type="application/json",
                response_only=True,
                summary="客户订单详情响应示例"
            )
        ]
    ),
)
class CustomerOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    客户订单视图集
    
    提供获取特定客户的所有订单功能
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'service_type'] # 移除了status字段
    search_fields = ['order_number', 'translator', 'project_details', 'customer_contact__username', 'customer_contact__nick_name', 'customer_contact__first_name', 'customer_contact__last_name'] # 移除了description字段
    ordering_fields = ['created_at', 'order_date', 'customer_total_amount', 'payment_status'] # 更新了字段
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        获取特定客户的订单
        """
        customer_id = self.kwargs.get('customer_id')
        queryset = Order.objects.filter(customer_id=customer_id)
        
        # 按订单日期范围筛选
        order_date_from = self.request.query_params.get('order_date_from')
        order_date_to = self.request.query_params.get('order_date_to')
        if order_date_from:
            queryset = queryset.filter(order_date__gte=order_date_from)
        if order_date_to:
            queryset = queryset.filter(order_date__lte=order_date_to)
            
        # 按服务时间范围筛选
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(service_time__gte=parsed_date)
            except ValueError:
                # 如果解析失败，不进行筛选
                pass
                
        if end_date:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(service_time__lte=parsed_date)
            except ValueError:
                # 如果解析失败，不进行筛选
                pass
        
        return queryset
    
    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器
        """
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer 