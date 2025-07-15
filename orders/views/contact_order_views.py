"""
联系人订单视图
"""
import logging
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from common.permissions import IsAdmin
from orders.models import Order
from orders.serializers import OrderListSerializer, OrderDetailSerializer
from users.models import Member

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取联系人订单列表",
        description="获取特定联系人的所有订单，支持分页、排序和筛选",
        tags=["联系人订单"],
        parameters=[
            # 移除了contact_id查询参数
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
                name="联系人订单列表响应示例",
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 18,
                            "customer_name": "北京科技有限公司",
                            "created_by_info": {"id": 1, "username": "admin", "display_name": "管理员"},
                            "customer_contact_info": {"id": 12, "username": "lisi", "display_name": "李四", "phone": "13900139000", "email": "lisi@example.com"},
                            "profit": 600.00,
                            "profit_rate": 0.30,
                            "formatted_profit": "¥600.00",
                            "formatted_profit_rate": "30.00%",
                            "created_at": "2025-07-10T11:22:33.123456Z",
                            "updated_at": "2025-07-10T11:22:33.123456Z",
                            "is_deleted": False,
                            "order_number": "PQ-202507-1234",
                            "service_type": "校对服务",
                            "language": "中英",
                            "customer_count": "3000字",
                            "customer_total_amount": "2000.00",
                            "payment_status": "paid",
                            "payment_status_display": "已支付"
                        },
                        {
                            "id": 19,
                            "customer_name": "北京科技有限公司",
                            "created_by_info": {"id": 1, "username": "admin", "display_name": "管理员"},
                            "customer_contact_info": {"id": 12, "username": "lisi", "display_name": "李四", "phone": "13900139000", "email": "lisi@example.com"},
                            "profit": 800.00,
                            "profit_rate": 0.40,
                            "formatted_profit": "¥800.00",
                            "formatted_profit_rate": "40.00%",
                            "created_at": "2025-07-12T14:25:36.234567Z",
                            "updated_at": "2025-07-12T14:25:36.234567Z",
                            "is_deleted": False,
                            "order_number": "PQ-202507-5432",
                            "service_type": "文档翻译",
                            "language": "中英",
                            "customer_count": "2000字",
                            "customer_total_amount": "2000.00",
                            "payment_status": "unpaid",
                            "payment_status_display": "未支付"
                        }
                    ]
                },
                media_type="application/json",
                response_only=True,
                summary="联系人订单列表响应示例"
            )
        ]
    ),
    retrieve=extend_schema(
        summary="获取联系人订单详情",
        description="获取特定联系人的指定订单详情",
        tags=["联系人订单"],
        parameters=[
            # 路径参数已经在URL中定义，这里不需要重复定义
        ],
        examples=[
            OpenApiExample(
                name="联系人订单详情响应示例",
                value={
                    "id": 18,
                    "customer": {
                        "id": 3,
                        "name": "北京科技有限公司",
                        "code": "BJ001",
                        "contact_name": "李四",
                        "contact_phone": "13900139000",
                        "contact_email": "lisi@example.com"
                    },
                    "customer_contact": {
                        "id": 12,
                        "username": "lisi",
                        "display_name": "李四",
                        "phone": "13900139000",
                        "email": "lisi@example.com"
                    },
                    "history_count": 1,
                    "profit": 600.00,
                    "profit_rate": 0.30,
                    "formatted_profit": "¥600.00",
                    "formatted_profit_rate": "30.00%",
                    "created_at": "2025-07-10T11:22:33.123456Z",
                    "updated_at": "2025-07-10T11:22:33.123456Z",
                    "is_deleted": False,
                    "order_number": "PQ-202507-1234",
                    "source_platform": "邮件咨询",
                    "project_manager": "八组",
                    "customer_type": "新客户",
                    "order_date": "2025-07-10",
                    "service_type": "校对服务",
                    "service_type_display": "校对服务",
                    "language": "中英",
                    "customer_count": "3000字",
                    "translation_count": "3000字",
                    "service_time": "2025-07-12前交稿",
                    "project_location": "线上",
                    "translator": "王五",
                    "customer_price": "0.67元/字",
                    "customer_total_amount": "2000.00",
                    "translator_fee": "1200.00",
                    "translator_price": "0.4元/字",
                    "translator_payment_status": "已付款",
                    "translator_payment_method": "微信",
                    "project_fee": "200.00",
                    "project_details": "英文论文校对",
                    "cost_details": "术语表制作费用200元",
                    "refund_amount": "0.00",
                    "refund_reason": None,
                    "payment_status": "paid",
                    "payment_status_display": "已支付",
                    "payment_date": "2025-07-10",
                    "payment_method": "支付宝",
                    "payment_remarks": "已确认收款",
                    "invoice_status": "issued",
                    "invoice_status_display": "已开具",
                    "invoice_info": "已开具电子发票",
                    "contract_number": None,
                    "contract_info": None,
                    "contract_remarks": None,
                    "delivery_address": None,
                    "order_address": "北京市海淀区xx路xx号",
                    "remarks": "客户要求重点检查专业术语",
                    "follow_up_record": "2025-07-11已电话回访，客户表示满意",
                    "tenant": 1
                },
                media_type="application/json",
                response_only=True,
                summary="联系人订单详情响应示例"
            )
        ]
    ),
)
class ContactOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    联系人订单视图集
    
    提供获取特定联系人的所有订单功能
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'service_type'] # 移除了status字段
    search_fields = ['order_number', 'translator', 'project_details', 'customer_contact__username', 'customer_contact__nick_name', 'customer_contact__first_name', 'customer_contact__last_name'] # 移除了description字段
    ordering_fields = ['created_at', 'order_date', 'customer_total_amount', 'payment_status'] # 更新了字段
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        获取特定联系人的订单
        """
        contact_id = self.kwargs.get('contact_id')
        queryset = Order.objects.filter(customer_contact_id=contact_id, is_deleted=False)
        
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