"""
订单视图
"""
import logging
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField, Count
from django.http import HttpResponse
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
import io

from common.permissions import IsAdmin
from orders.models import Order
from orders.serializers import (
    OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer,
    OrderListSerializer, OrderDetailSerializer, OrderStatisticsSerializer
)
from customers.models import Customer
from users.models import Member
import django.db.models as models

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取订单列表",
        description="获取系统中的所有订单，支持分页、排序和筛选",
        tags=["订单管理"],
        parameters=[
            OpenApiParameter(name="payment_status", description="按支付状态筛选订单", required=False, type=str),
            OpenApiParameter(name="service_type", description="按服务类型筛选订单", required=False, type=str),
            OpenApiParameter(name="language", description="按语种筛选订单", required=False, type=str),
            OpenApiParameter(name="customer_id", description="按客户ID筛选订单", required=False, type=int),
            OpenApiParameter(name="customer_type", description="按客户类型筛选订单", required=False, type=str),
            OpenApiParameter(name="service_time", description="按服务时间筛选订单", required=False, type=str),
            OpenApiParameter(name="start_date", description="按服务时间范围筛选（起始日期）", required=False, type=str),
            OpenApiParameter(name="end_date", description="按服务时间范围筛选（结束日期）", required=False, type=str),
            OpenApiParameter(name="search", description="搜索订单编号、客户名称等信息", required=False, type=str),
        ]
    ),
    retrieve=extend_schema(
        summary="获取单个订单",
        description="获取指定ID的订单详情",
        tags=["订单管理"]
    ),
    create=extend_schema(
        summary="创建订单",
        description="创建新的订单记录",
        tags=["订单管理"],
        examples=[
            OpenApiExample(
                name="标准翻译订单示例",
                value={
                    "source_platform": "官网",
                    "project_manager": "五组",
                    "customer_type": "老客户",
                    "order_date": "2025-07-15",
                    "service_type": "文档翻译",
                    "language": "中英",
                    "customer_count": "5000字",
                    "translation_count": "5000字",
                    "service_time": "2025-07-20前交稿",
                    "project_location": "线上",
                    "translator": "张三",
                    "customer_price": "0.3元/字",
                    "customer_total_amount": "1500.00",
                    "translator_fee": "750.00",
                    "translator_price": "0.15元/字",
                    "translator_payment_status": "待付款",
                    "translator_payment_method": "支付宝",
                    "project_fee": "50.00",
                    "project_details": "技术文档翻译，包含5个Word文档",
                    "cost_details": "版式调整费用50元",
                    "refund_amount": "0.00",
                    "refund_reason": None,
                    "payment_status": "paid",
                    "payment_date": "2025-07-15",
                    "payment_method": "微信支付",
                    "invoice_status": "pending",
                    "invoice_info": "需要开具增值税专用发票",
                    "remarks": "客户要求保持原文格式",
                    "customer": 1,
                    "customer_contact": 5
                },
                media_type="application/json",
                summary="创建标准翻译订单示例"
            ),
            OpenApiExample(
                name="口译服务订单示例",
                value={
                    "source_platform": "电话咨询",
                    "project_manager": "三组",
                    "customer_type": "VIP客户",
                    "order_date": "2025-07-16",
                    "service_type": "口译服务",
                    "language": "中日",
                    "customer_count": "1天",
                    "translation_count": "1天",
                    "service_time": "2025-07-25 9:00-17:00",
                    "project_location": "上海市浦东新区xx大厦",
                    "translator": "李四",
                    "customer_price": "3000元/天",
                    "customer_total_amount": "3000.00",
                    "translator_fee": "1800.00",
                    "translator_price": "1800元/天",
                    "translator_payment_status": "未付款",
                    "translator_payment_method": "对公转账",
                    "project_fee": "200.00",
                    "project_details": "商务会议交替传译",
                    "cost_details": "交通费200元",
                    "payment_status": "unpaid",
                    "invoice_status": "not_required",
                    "remarks": "译员需提前30分钟到场",
                    "customer": 2,
                    "customer_contact": 8
                },
                media_type="application/json",
                summary="创建口译服务订单示例"
            ),
            OpenApiExample(
                name="校对服务订单示例",
                value={
                    "source_platform": "邮件咨询",
                    "project_manager": "八组",
                    "customer_type": "新客户",
                    "order_date": "2025-07-17",
                    "service_type": "校对服务",
                    "language": "中英",
                    "customer_count": "3000字",
                    "translation_count": "3000字",
                    "service_time": "2025-07-18前交稿",
                    "project_location": "线上",
                    "translator": "王五",
                    "customer_price": "0.1元/字",
                    "customer_total_amount": "300.00",
                    "translator_fee": "150.00",
                    "translator_price": "0.05元/字",
                    "translator_payment_status": "待付款",
                    "translator_payment_method": "微信",
                    "project_fee": "0.00",
                    "project_details": "英文论文校对",
                    "payment_status": "paid",
                    "payment_date": "2025-07-17",
                    "payment_method": "支付宝",
                    "invoice_status": "issued",
                    "invoice_info": "已开具电子发票",
                    "remarks": "客户要求重点检查专业术语",
                    "customer": 3,
                    "customer_contact": 12
                },
                media_type="application/json",
                summary="创建校对服务订单示例"
            )
        ]
    ),
    update=extend_schema(
        summary="更新订单",
        description="更新指定ID的订单信息，应传入订单的所有字段",
        tags=["订单管理"],
        examples=[
            OpenApiExample(
                name="更新订单完整示例",
                value={
                    "source_platform": "官网",
                    "project_manager": "五组",
                    "customer_type": "老客户",
                    "order_date": "2025-07-15",
                    "service_type": "文档翻译",
                    "language": "中英",
                    "customer_count": "5000字",
                    "translation_count": "5000字",
                    "service_time": "2025-07-20前交稿",
                    "project_location": "线上",
                    "translator": "张三",
                    "customer_price": "0.3元/字",
                    "customer_total_amount": "1500.00",
                    "translator_fee": "750.00",
                    "translator_price": "0.15元/字",
                    "translator_payment_status": "待付款",
                    "translator_payment_method": "支付宝",
                    "project_fee": "50.00",
                    "project_details": "技术文档翻译，包含5个Word文档",
                    "cost_details": "版式调整费用50元",
                    "refund_amount": "0.00",
                    "refund_reason": None,
                    "payment_status": "paid",
                    "payment_date": "2025-07-15",
                    "payment_method": "微信支付",
                    "payment_remarks": "已确认收款",
                    "invoice_status": "pending",
                    "invoice_info": "需要开具增值税专用发票",
                    "contract_number": "",
                    "contract_info": "",
                    "contract_remarks": "",
                    "delivery_address": "",
                    "order_address": "",
                    "remarks": "客户要求保持原文格式",
                    "follow_up_record": "",
                    "customer": 1,
                    "customer_contact": 5
                },
                media_type="application/json",
                summary="更新订单的完整示例 - 包含所有字段"
            ),
            OpenApiExample(
                name="更新订单状态示例",
                value={
                    "payment_status": "paid",
                    "payment_date": "2025-07-18",
                    "payment_method": "银行转账",
                    "payment_remarks": "已确认收款"
                },
                media_type="application/json",
                summary="更新订单支付状态（部分更新，实际应传入完整对象）"
            ),
            OpenApiExample(
                name="更新译员信息示例",
                value={
                    "translator": "赵六",
                    "translator_fee": "800.00",
                    "translator_price": "0.16元/字",
                    "translator_payment_status": "已付款",
                    "translator_payment_method": "微信转账",
                    "project_fee": "100.00",
                    "project_details": "文档翻译含排版服务"
                },
                media_type="application/json",
                summary="更新译员和费用信息（部分更新，实际应传入完整对象）"
            ),
            OpenApiExample(
                name="更新发票状态示例",
                value={
                    "invoice_status": "issued",
                    "invoice_info": "增值税专用发票已邮寄，单号：SF1234567890",
                    "remarks": "客户已确认收到发票"
                },
                media_type="application/json",
                summary="更新发票状态信息（部分更新，实际应传入完整对象）"
            )
        ]
    ),
    partial_update=extend_schema(
        summary="部分更新订单",
        description="部分更新指定ID的订单信息，允许只传入需要更新的字段",
        tags=["订单管理"],
        examples=[
            OpenApiExample(
                name="部分更新示例",
                value={
                    "remarks": "客户要求加急处理，将于明天完成",
                    "follow_up_record": "2025-07-18已电话告知客户进度"
                },
                media_type="application/json",
                summary="部分更新订单备注和回访记录"
            ),
            OpenApiExample(
                name="部分更新支付状态示例",
                value={
                    "payment_status": "paid",
                    "payment_date": "2025-07-18",
                    "payment_method": "银行转账",
                    "payment_remarks": "已确认收款"
                },
                media_type="application/json",
                summary="部分更新订单支付状态"
            )
        ]
    ),
    destroy=extend_schema(
        summary="删除订单",
        description="删除指定ID的订单（软删除）",
        tags=["订单管理"]
    ),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    订单管理视图集
    
    提供订单的增删改查、搜索、筛选、导出等功能
    
    HTTP方法说明:
    - PUT (update): 需要传入订单的完整对象，包含所有字段
    - PATCH (partial_update): 允许只传入需要更新的字段
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'service_type', 'language', 'customer', 'customer_type']
    search_fields = ['order_number', 'customer__name', 'translator', 'project_details', 'customer_contact__username', 'customer_contact__nick_name', 'customer_contact__first_name', 'customer_contact__last_name']
    ordering_fields = ['created_at', 'order_date', 'customer_total_amount', 'payment_status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器
        """
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'statistics':
            return OrderStatisticsSerializer
        return OrderSerializer
    
    def get_queryset(self):
        """
        获取订单查询集，默认不返回已删除的订单
        """
        queryset = Order.objects.all()
        
        # 默认不显示已删除订单，除非明确要求
        show_deleted = self.request.query_params.get('show_deleted', 'false').lower() == 'true'
        if not show_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        # 筛选参数处理
        payment_status = self.request.query_params.get('payment_status')
        service_type = self.request.query_params.get('service_type')
        language = self.request.query_params.get('language')
        customer_id = self.request.query_params.get('customer_id')
        customer_type = self.request.query_params.get('customer_type')
        service_time = self.request.query_params.get('service_time')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        if language:
            queryset = queryset.filter(language=language)
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)
        
        if service_time:
            try:
                # 尝试解析为日期格式
                from datetime import datetime
                parsed_date = datetime.strptime(service_time, '%Y-%m-%d').date()
                queryset = queryset.filter(service_time=parsed_date)
            except ValueError:
                # 如果解析失败，不进行筛选
                pass
        
        # 处理服务时间范围查询
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
    
    def perform_destroy(self, instance):
        """
        执行软删除并记录历史
        """
        # 获取current用户
        user = self.request.user
        
        # 先记录历史
        from orders.models import OrderHistory
        OrderHistory.create_history_record(
            order=instance,
            user=user,
            change_details={'action': 'delete', 'message': '删除订单（API操作）'}
        )
        
        # 执行软删除
        instance.soft_delete()
    
    def perform_update(self, serializer):
        """
        执行更新操作，记录日志
        
        注意：历史记录的创建已经在OrderUpdateSerializer的update方法中处理，
        这里只是添加额外的日志记录
        """
        logger.info(f"执行订单更新操作: ID={serializer.instance.id}, 订单号={serializer.instance.order_number}")
        
        # 调用父类方法执行实际更新
        # OrderUpdateSerializer中已经处理了历史记录创建，不需要在这里重复
        super().perform_update(serializer)
        
        logger.info(f"订单更新完成: ID={serializer.instance.id}, 订单号={serializer.instance.order_number}")
    
    @extend_schema(
        summary="导出订单数据",
        description="导出订单数据为Excel文件，可选择按订单ID列表进行筛选",
        tags=["订单管理"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'order_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': '要导出的订单ID列表，如果不提供则导出所有订单'
                    },
                    'format': {
                        'type': 'string',
                        'enum': ['xlsx', 'csv'],
                        'default': 'xlsx',
                        'description': '导出格式，支持xlsx和csv'
                    }
                }
            }
        },
        responses={
            200: {
                'description': 'Excel或CSV文件下载',
                'content': {
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {},
                    'text/csv': {}
                }
            }
        },
        examples=[
            OpenApiExample(
                name="导出指定订单",
                value={
                    "order_ids": [1, 2, 3, 4, 5],
                    "format": "xlsx"
                },
                media_type="application/json",
                summary="导出指定ID的订单"
            ),
            OpenApiExample(
                name="导出所有订单为CSV",
                value={
                    "format": "csv"
                },
                media_type="application/json",
                summary="导出所有订单为CSV格式"
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def export(self, request):
        """
        导出订单数据（POST方法）
        
        可以通过JSON请求体传递order_ids数组来指定要导出的订单ID列表
        如果不提供order_ids，则导出current租户下所有订单
        """
        logger.info(f"开始处理订单导出请求，请求数据: {request.data}")
        
        # 获取基础查询集
        queryset = self.get_queryset()
        logger.info(f"初始查询集数量: {queryset.count()}")
        
        # 从请求体获取参数
        order_ids = request.data.get('order_ids')
        export_format = request.data.get('format', 'xlsx').lower()
        
        logger.info(f"导出参数 - order_ids: {order_ids}, format: {export_format}")
        
        # 处理order_ids参数，如果提供了，则按ID列表筛选
        if order_ids and isinstance(order_ids, list) and order_ids:
            try:
                queryset = queryset.filter(id__in=order_ids)
                logger.info(f"按ID列表筛选订单: {order_ids}")
            except Exception as e:
                logger.error(f"处理order_ids参数出错: {str(e)}")
                return Response(
                    {"error": f"处理订单ID列表出错: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 应用其他过滤条件
        queryset = self.filter_queryset(queryset)
        
        # 准备导出数据
        data = []
        for order in queryset:
            data.append({
                '订单编号': order.order_number,
                '客户': order.customer.name,
                '客户类型': order.customer_type or '',
                '来源平台': order.source_platform or '',
                '项目负责人': order.project_manager or '',
                '下单日期': order.order_date,
                '服务类型': order.service_type,
                '语种': order.language,
                '客户数量': order.customer_count or '',
                '翻译数量': order.translation_count or '',
                '服务时间': order.service_time.strftime('%Y-%m-%d') if order.service_time else '',
                '项目地点': order.project_location or '',
                '客户联系人': order.customer_contact.display_name if order.customer_contact else '',
                '客户联系人昵称': order.customer_contact.nick_name if order.customer_contact and order.customer_contact.nick_name else '',
                '客户联系人手机': order.customer_contact.phone if order.customer_contact and order.customer_contact.phone else '',
                '客户联系人微信': order.customer_contact.wechat_id if order.customer_contact and order.customer_contact.wechat_id else '',
                '客户单价': order.customer_price or '',
                '客户总价': float(order.customer_total_amount),
                '译员': order.translator or '',
                '译员费用': float(order.translator_fee),
                '翻译单价': order.translator_price or '',
                '译费支付状态': order.translator_payment_status or '',
                '译费支付方式': order.translator_payment_method or '',
                '项目费用': float(order.project_fee),
                '项目明细': order.project_details or '',
                '费用明细': order.cost_details or '',
                '项目退款': float(order.refund_amount),
                '退款原因': order.refund_reason or '',
                '毛利': float(order.calculate_profit()),
                '毛利率': f"{order.calculate_profit_rate():.2%}",
                '支付状态': order.payment_status,
                '支付日期': order.payment_date,
                '支付方式': order.payment_method or '',
                '支付备注': order.payment_remarks or '',
                '发票状态': order.invoice_status,
                '发票信息': order.invoice_info or '',
                '合同编号': order.contract_number or '',
                '合同信息': order.contract_info or '',
                '合同备注': order.contract_remarks or '',
                '收件地址': order.delivery_address or '',
                '下单地址': order.order_address or '',
                '备注': order.remarks or '',
                '回访记录': order.follow_up_record or '',
                '创建时间': order.created_at.replace(tzinfo=None) if order.created_at else None,
                '更新时间': order.updated_at.replace(tzinfo=None) if order.updated_at else None,
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)

        # 特别处理日期字段 - 确保date类型字段正确导出
        for col in df.columns:
            # 检查是否为日期或日期时间列
            if col in ['下单日期', '支付日期', '创建时间', '更新时间']:
                # 安全地转换日期时间对象
                def convert_datetime(x):
                    if pd.isna(x) or x is None:
                        return None
                    try:
                        if hasattr(x, 'to_pydatetime'):
                            return x.to_pydatetime().replace(tzinfo=None)
                        elif hasattr(x, 'tzinfo'):
                            return x.replace(tzinfo=None)
                        elif isinstance(x, str) and (x.count('-') == 2 or x.count('/') == 2):
                            # 尝试解析字符串为日期
                            return pd.to_datetime(x).to_pydatetime().replace(tzinfo=None)
                        return x
                    except Exception as e:
                        logger.warning(f"转换{col}列的值({x})时出错: {str(e)}")
                        return x
                
                df[col] = df[col].apply(convert_datetime)
                logger.info(f"完成处理日期时间列: {col}, 示例值: {df[col].iloc[0] if not df[col].empty else None}")
        
        # 生成包含时间戳的文件名
        import time
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # 如果指定了订单ID，在文件名中包含数量信息
        if order_ids and isinstance(order_ids, list):
            count_info = f"{len(order_ids)}orders"
            id_info = f"_{min(order_ids)}-{max(order_ids)}" if len(order_ids) > 1 else f"_{order_ids[0]}"
        else:
            count_info = "all_orders"
            id_info = ""
        
        try:
            # 导出文件
            if export_format == 'csv':
                filename = f"orders_{count_info}{id_info}_{timestamp}.csv"
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                df.to_csv(response, index=False, encoding='utf-8-sig')
            else:  # xlsx 或其他格式默认为 xlsx
                filename = f"orders_{count_info}{id_info}_{timestamp}.xlsx"
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                df.to_excel(response, index=False, engine='openpyxl')
            
            logger.info(f"成功导出订单数据: {filename}, 共 {len(data)} 条记录")
            return response
        except Exception as e:
            # 记录详细错误信息
            logger.error(f"导出订单数据失败: {str(e)}", exc_info=True)
            return Response(
                {"error": f"导出失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="导入订单数据",
        description="从Excel文件导入订单数据",
        tags=["订单管理"],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'update_existing': {'type': 'boolean', 'default': False}
                },
                'required': ['file']
            }
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string'},
                'total_records': {'type': 'integer'},
                'created': {'type': 'integer'},
                'updated': {'type': 'integer'},
                'failed': {'type': 'integer'},
                'errors': {'type': 'array', 'items': {'type': 'string'}}
            }
        }},
        examples=[
            OpenApiExample(
                name="导入订单响应示例",
                value={
                    "status": "success",
                    "total_records": 10,
                    "created": 8,
                    "updated": 0,
                    "failed": 2,
                    "errors": [
                        "行5: 客户ID不存在",
                        "行8: 金额格式不正确"
                    ]
                },
                media_type="application/json",
                response_only=True,
                summary="导入订单响应示例"
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """
        导入订单数据
        """
        # 检查是否上传了文件
        if 'file' not in request.FILES:
            return Response(
                {"error": "未提供文件"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        update_existing = request.data.get('update_existing', 'false').lower() == 'true'
        
        # 检查文件类型
        if not file.name.endswith(('.xlsx', '.xls')):
            return Response(
                {"error": "仅支持Excel文件(.xlsx, .xls)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file)
            
            # 添加日志记录
            logger.info(f"成功读取Excel文件，共有{len(df)}行数据")
            logger.info(f"Excel列名: {list(df.columns)}")
            
            # 统计结果
            total_records = len(df)
            created_count = 0
            updated_count = 0
            failed_count = 0
            errors = []
            
            # 处理每一行数据
            for index, row in df.iterrows():
                try:
                    # 获取订单编号，用于判断是更新还是创建
                    order_number = str(row.get('订单编号', '')).strip()
                    
                    # 查找客户信息
                    customer_name = str(row.get('客户', '')).strip()
                    customer = None
                    if customer_name:
                        try:
                            # 使用filter而不是get，避免多个结果的错误
                            customers = Customer.objects.filter(name=customer_name)
                            if customers.count() > 1:
                                # 如果有多个同名客户，记录警告并使用第一个
                                logger.warning(f"第{index+1}行: 发现多个同名客户 '{customer_name}'，使用第一个")
                                customer = customers.first()
                            elif customers.count() == 1:
                                customer = customers.first()
                            else:
                                raise Customer.DoesNotExist()
                        except Customer.DoesNotExist:
                            errors.append(f"第{index+1}行: 客户 '{customer_name}' 不存在")
                            failed_count += 1
                            continue
                    else:
                        errors.append(f"第{index+1}行: 缺少客户信息")
                        failed_count += 1
                        continue
                    
                    # 查找客户联系人信息
                    contact_name = str(row.get('客户联系人', '')).strip()
                    customer_contact = None
                    if contact_name:
                        try:
                            # 尝试根据display_name查找联系人
                            customer_contact = Member.objects.filter(
                                tenant=customer.tenant,
                                is_deleted=False
                            ).filter(
                                models.Q(nick_name=contact_name) | 
                                models.Q(username=contact_name) |
                                models.Q(first_name__contains=contact_name) |
                                models.Q(last_name__contains=contact_name)
                            ).first()
                        except Exception as e:
                            logger.warning(f"查找联系人 '{contact_name}' 时出错: {str(e)}")
                    
                    # 准备订单数据
                    order_data = {
                        'customer': customer,
                        'order_number': order_number if order_number else None,
                        'source_platform': row.get('来源平台'),
                        'project_manager': row.get('项目负责人'),
                        'customer_type': row.get('客户类型'),
                        'order_date': row.get('下单日期'),
                        'service_type': row.get('服务类型'),
                        'language': row.get('语种'),
                        'customer_count': row.get('客户数量'),
                        'translation_count': row.get('翻译数量'),
                        'service_time': row.get('服务时间'),
                        'project_location': row.get('项目地点'),
                        'customer_contact': customer_contact,
                        'translator': row.get('译员'),
                        'customer_price': row.get('客户单价'),
                        'customer_total_amount': row.get('客户总价'),
                        'translator_fee': row.get('译员费用'),
                        'translator_price': row.get('翻译单价'),
                        'translator_payment_status': row.get('译费支付状态'),
                        'translator_payment_method': row.get('译费支付方式'),
                        'project_fee': row.get('项目费用'),
                        'project_details': row.get('项目明细'),
                        'cost_details': row.get('费用明细'),
                        'refund_amount': row.get('项目退款', 0),
                        'refund_reason': row.get('退款原因'),
                        'payment_status': row.get('支付状态', 'unpaid'),
                        'payment_date': row.get('支付日期'),
                        'payment_method': row.get('支付方式'),
                        'payment_remarks': row.get('支付备注'),
                        'invoice_status': row.get('发票状态', 'not_required'),
                        'invoice_info': row.get('发票信息'),
                        'contract_number': row.get('合同编号'),
                        'contract_info': row.get('合同信息'),
                        'contract_remarks': row.get('合同备注'),
                        'delivery_address': row.get('收件地址'),
                        'order_address': row.get('下单地址'),
                        'remarks': row.get('备注'),
                        'follow_up_record': row.get('回访记录')
                    }
                    
                    # 检查必填字段
                    if not all([order_data['customer'], order_data['service_type'], 
                              order_data['language'], order_data['customer_count']]):
                        errors.append(f"第{index+1}行: 缺少必填字段")
                        failed_count += 1
                        continue
                    
                    # 处理数值字段，确保非空
                    for field in ['customer_total_amount', 'translator_fee', 'project_fee', 'refund_amount']:
                        if field in order_data and (pd.isna(order_data[field]) or order_data[field] == ''):
                            order_data[field] = 0
                    
                    # 处理所有可能的日期时间字段
                    date_fields = ['order_date', 'payment_date', 'service_time', 'created_at', 'updated_at']
                    
                    # 记录原始数据用于调试
                    logger.debug(f"第{index+1}行原始数据: {row}")
                    
                    # 检查并处理所有日期字段
                    for field in date_fields:
                        if field in order_data:
                            # 检查是否为NaT
                            if pd.isna(order_data[field]) or order_data[field] is pd.NaT:
                                logger.info(f"第{index+1}行: {field}字段为NaT或空值，设置为None")
                                order_data[field] = None
                            # 检查是否为pandas Timestamp
                            elif hasattr(order_data[field], 'to_pydatetime'):
                                try:
                                    # 转换为不带时区的日期对象
                                    if field in ['order_date', 'payment_date']:
                                        order_data[field] = order_data[field].date()
                                    else:
                                        order_data[field] = order_data[field].replace(tzinfo=None)
                                    logger.info(f"第{index+1}行: 成功转换{field}字段: {order_data[field]}")
                                except Exception as e:
                                    logger.warning(f"第{index+1}行: 转换{field}字段时出错: {str(e)}")
                                    order_data[field] = None
                            # 检查是否为字符串
                            elif isinstance(order_data[field], str) and order_data[field].strip():
                                try:
                                    from datetime import datetime
                                    date_obj = datetime.strptime(order_data[field].strip(), '%Y-%m-%d').date()
                                    order_data[field] = date_obj
                                    logger.info(f"第{index+1}行: 从字符串转换{field}字段: {order_data[field]}")
                                except ValueError:
                                    logger.warning(f"第{index+1}行: {field}字段日期格式错误: {order_data[field]}")
                                    order_data[field] = None
                            # 其他情况
                            elif order_data[field] == '' or order_data[field] is None:
                                order_data[field] = None
                    
                    # 检查是否有订单编号（用于更新）
                    if order_number and update_existing:
                        # 尝试更新现有订单
                        try:
                            order = Order.objects.get(order_number=order_number)
                            
                            # 记录旧值用于历史记录
                            changes = {}
                            
                            # 更新订单字段
                            for key, value in order_data.items():
                                if key == 'order_number':  # 不更新订单编号
                                    continue
                                
                                if hasattr(order, key) and pd.notna(value):
                                    old_value = getattr(order, key)
                                    if old_value != value:
                                        changes[key] = {'old': old_value, 'new': value}
                                        setattr(order, key, value)
                            
                            if changes:
                                order.save()
                                # 记录历史
                                from orders.models import OrderHistory
                                OrderHistory.create_history_record(
                                    order=order,
                                    user=request.user,
                                    change_details={'changes': changes, 'source': 'import_data'}
                                )
                                updated_count += 1
                                logger.info(f"成功更新订单: {order.order_number}")
                            else:
                                logger.info(f"订单 {order.order_number} 无需更新")
                                
                        except Order.DoesNotExist:
                            # 如果订单不存在，但有订单编号，使用该编号创建新订单
                            try:
                                # 移除order_number字段，让模型自动生成
                                if not update_existing:
                                    order_data.pop('order_number', None)
                                
                                # 移除可能导致问题的字段
                                for field in ['created_at', 'updated_at']:
                                    if field in order_data:
                                        order_data.pop(field, None)
                                
                                # 确保所有日期字段都是正确的格式
                                for field, value in list(order_data.items()):
                                    # 如果值是NaT或者None，从字典中移除该字段
                                    if pd.isna(value) or value is None or value == '':
                                        order_data.pop(field, None)
                                
                                # 记录最终的订单数据
                                logger.info(f"第{index+1}行最终订单数据: {order_data}")
                                
                                # 直接创建订单对象
                                order = Order(**order_data)
                                order.created_by = request.user
                                order.updated_by = request.user
                                order.save()
                                
                                created_count += 1
                                logger.info(f"成功创建订单: {order.order_number}")
                            except Exception as e:
                                errors.append(f"第{index+1}行: 创建订单失败 - {str(e)}")
                                failed_count += 1
                                logger.error(f"创建订单失败: {str(e)}", exc_info=True)
                    else:
                        # 创建新订单
                        try:
                            # 移除order_number字段，让模型自动生成
                            order_data.pop('order_number', None)
                            
                            # 移除可能导致问题的字段
                            for field in ['created_at', 'updated_at']:
                                if field in order_data:
                                    order_data.pop(field, None)
                            
                            # 确保所有日期字段都是正确的格式
                            for field, value in list(order_data.items()):
                                # 如果值是NaT或者None，从字典中移除该字段
                                if pd.isna(value) or value is None or value == '':
                                    order_data.pop(field, None)
                            
                            # 记录最终的订单数据
                            logger.info(f"第{index+1}行最终订单数据: {order_data}")
                            
                            # 直接创建订单对象
                            order = Order(**order_data)
                            order.created_by = request.user
                            order.updated_by = request.user
                            order.save()
                            
                            created_count += 1
                            logger.info(f"成功创建订单: {order.order_number}")
                        except Exception as e:
                            errors.append(f"第{index+1}行: 创建订单失败 - {str(e)}")
                            failed_count += 1
                            logger.error(f"创建订单失败: {str(e)}", exc_info=True)
                
                except Exception as e:
                    errors.append(f"第{index+1}行: {str(e)}")
                    failed_count += 1
            
            # 返回导入结果
            return Response({
                'status': 'success',
                'total_records': total_records,
                'created': created_count,
                'updated': updated_count,
                'failed': failed_count,
                'errors': errors
            })
        
        except Exception as e:
            return Response(
                {"error": f"导入失败: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="获取订单统计数据",
        description="获取订单的统计数据，包括总数、总金额、平均金额等。所有日期筛选和周期统计都基于服务时间(service_time)。",
        tags=["订单管理"],
        parameters=[
            OpenApiParameter(name="period", description="统计周期，可选值: daily, weekly, monthly, yearly", required=False, type=str, default="monthly"),
            OpenApiParameter(name="start_date", description="服务时间范围起始日期", required=False, type=str),
            OpenApiParameter(name="end_date", description="服务时间范围结束日期", required=False, type=str),
            OpenApiParameter(name="customer", description="客户ID", required=False, type=int),
            OpenApiParameter(name="service_type", description="服务类型", required=False, type=str),
        ]
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        获取订单统计数据
        """
        # 获取过滤后的查询集
        queryset = self.filter_queryset(self.get_queryset())
        
        # 获取查询参数
        period = request.query_params.get('period', 'monthly')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # 如果没有提供日期范围，默认为最近一年
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 按日期范围筛选 - 改为筛选服务时间，与get_queryset保持一致
        # 注意：此处不需要额外筛选，因为已经在get_queryset中处理了start_date和end_date参数
        
        # 计算基本统计数据
        total_count = queryset.count()
        
        # 如果没有订单，返回空统计数据
        if total_count == 0:
            return Response({
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
                'total_orders': 0,
                'customer_total_amount': 0,
                'total_profit': 0,
                'average_profit_rate': 0,
                'by_period': [],
                'by_service_type': [],
                'by_payment_status': []
            })
        
        # 计算总金额和毛利
        amount_stats = queryset.aggregate(
            total_amount=Sum('customer_total_amount'),
            total_translator_fee=Sum('translator_fee'),
            total_project_fee=Sum('project_fee')
        )
        
        total_amount = amount_stats['total_amount'] or 0
        total_translator_fee = amount_stats['total_translator_fee'] or 0
        total_project_fee = amount_stats['total_project_fee'] or 0
        total_profit = total_amount - total_translator_fee - total_project_fee
        
        # 计算平均毛利率
        average_profit_rate = total_profit / total_amount if total_amount > 0 else 0
        
        # 按支付状态统计
        payment_status_stats = queryset.values('payment_status').annotate(
            count=Count('id'),
            amount=Sum('customer_total_amount')
        )
        by_payment_status = [
            {
                'payment_status': item['payment_status'],
                'orders': item['count'],
                'amount': float(item['amount'] or 0)
            } for item in payment_status_stats
        ]
        
        # 按服务类型统计
        service_type_stats = queryset.values('service_type').annotate(
            count=Count('id'),
            amount=Sum('customer_total_amount')
        )
        by_service_type = [
            {
                'service_type': item['service_type'],
                'orders': item['count'],
                'amount': float(item['amount'] or 0)
            } for item in service_type_stats
        ]
        
        # 按周期统计 - 所有统计都基于服务时间(service_time)
        by_period = []
        if period == 'daily':
            # 按日统计 - 使用service_time而不是created_at
            date_stats = queryset.extra(
                select={'date': "DATE(service_time)"}
            ).values('date').annotate(
                count=Count('id'),
                amount=Sum('customer_total_amount'),
                profit=Sum('customer_total_amount') - Sum('translator_fee') - Sum('project_fee')
            ).order_by('date')
            
            by_period = [
                {
                    'period': item['date'].strftime('%Y-%m-%d') if item['date'] else 'unknown',
                    'orders': item['count'],
                    'amount': float(item['amount'] or 0),
                    'profit': float(item['profit'] or 0)
                } for item in date_stats
            ]
        elif period == 'weekly':
            # 按周统计 - 使用service_time而不是created_at
            date_stats = queryset.extra(
                select={'week': "CONCAT(YEAR(service_time), '-', WEEK(service_time))"}
            ).values('week').annotate(
                count=Count('id'),
                amount=Sum('customer_total_amount'),
                profit=Sum('customer_total_amount') - Sum('translator_fee') - Sum('project_fee')
            ).order_by('week')
            
            by_period = [
                {
                    'period': item['week'] if item['week'] else 'unknown',
                    'orders': item['count'],
                    'amount': float(item['amount'] or 0),
                    'profit': float(item['profit'] or 0)
                } for item in date_stats
            ]
        elif period == 'monthly':
            # 按月统计 - 使用service_time而不是created_at
            from django.db.models.functions import ExtractYear, ExtractMonth, Cast
            from django.db.models import F, Value, CharField, Case, When
            from django.db.models.functions import Concat

            # 使用Extract提取年和月，然后用Concat组合成YYYY-MM格式
            date_stats = queryset.annotate(
                year=ExtractYear('service_time'),
                month=ExtractMonth('service_time'),
                month_str=Concat(
                    F('year'), 
                    Value('-'),
                    Case(
                        When(month__lt=10, then=Concat(Value('0'), F('month'), output_field=CharField())),
                        default=Cast('month', output_field=CharField()),
                    ),
                    output_field=CharField()
                )
            ).values('month_str').annotate(
                count=Count('id'),
                amount=Sum('customer_total_amount'),
                profit=Sum('customer_total_amount') - Sum('translator_fee') - Sum('project_fee')
            ).order_by('month_str')
            
            by_period = [
                {
                    'period': item['month_str'] if item['month_str'] else 'unknown',
                    'orders': item['count'],
                    'amount': float(item['amount'] or 0),
                    'profit': float(item['profit'] or 0)
                } for item in date_stats
            ]
        elif period == 'yearly':
            # 按年统计 - 使用service_time而不是created_at
            date_stats = queryset.extra(
                select={'year': "YEAR(service_time)"}
            ).values('year').annotate(
                count=Count('id'),
                amount=Sum('customer_total_amount'),
                profit=Sum('customer_total_amount') - Sum('translator_fee') - Sum('project_fee')
            ).order_by('year')
            
            by_period = [
                {
                    'period': str(item['year']) if item['year'] else 'unknown',
                    'orders': item['count'],
                    'amount': float(item['amount'] or 0),
                    'profit': float(item['profit'] or 0)
                } for item in date_stats
            ]
        
        # 返回统计数据
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_orders': total_count,
            'customer_total_amount': float(total_amount),
            'total_profit': float(total_profit),
            'average_profit_rate': float(average_profit_rate),
            'by_period': by_period,
            'by_service_type': by_service_type,
            'by_payment_status': by_payment_status
        })
    
    @extend_schema(
        summary="获取订单提醒",
        description="获取未来N天内需要交付的订单提醒",
        tags=["订单管理"],
        parameters=[
            OpenApiParameter(name="days", description="未来天数范围", required=False, type=int, default=7),
            OpenApiParameter(name="keyword", description="关键字筛选", required=False, type=str),
        ]
    )
    @action(detail=False, methods=['get'])
    def reminders(self, request):
        """
        获取订单提醒，基于服务交付日期(service_time)分析未来N天内需要交付的订单
        """
        # 获取查询参数
        days = int(request.query_params.get('days', 7))
        keyword = request.query_params.get('keyword', '')
        
        # 计算日期范围
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        
        # 初始化查询集，筛选未删除订单
        queryset = Order.objects.filter(is_deleted=False)
        
        # 处理筛选逻辑
        if keyword:
            # 如果提供了关键字，按关键字筛选
            queryset = queryset.filter(
                Q(order_number__icontains=keyword) |
                Q(project_details__icontains=keyword) |
                Q(remarks__icontains=keyword) |
                Q(customer__name__icontains=keyword) |
                Q(translator__icontains=keyword) |
                Q(customer_contact__username__icontains=keyword) |
                Q(customer_contact__nick_name__icontains=keyword) |
                Q(customer_contact__first_name__icontains=keyword) |
                Q(customer_contact__last_name__icontains=keyword)
            )
        else:
            # 如果没有关键字，根据服务时间筛选
            # 筛选未来days天内需要交付的订单
            queryset = queryset.filter(
                # 服务时间不为空
                ~Q(service_time=None) &
                # 服务时间在今天及以后
                Q(service_time__gte=today) & 
                # 服务时间在指定范围内
                Q(service_time__lte=end_date)
            )
        
        # 确保至少返回一些数据
        if not queryset.exists():
            # 如果没有匹配的订单，返回最近的几条有服务时间的订单
            queryset = Order.objects.filter(
                is_deleted=False
            ).exclude(
                service_time=None
            ).order_by('service_time')[:10]
            
            # 如果仍然没有，则返回最近创建的订单
            if not queryset.exists():
                queryset = Order.objects.filter(
                    is_deleted=False
                ).order_by('-created_at')[:10]
        
        reminders = []
        
        # 处理结果
        for order in queryset:
            reminders.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer': {
                    'id': order.customer.id,
                    'name': order.customer.name
                },
                'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else None,
                'service_time': order.service_time.strftime('%Y-%m-%d') if order.service_time else None,
                'service_type': order.service_type,
                'language': order.language,
                'customer_count': order.customer_count,
                'project_location': order.project_location,
                'payment_status': order.payment_status
            })
        
        return Response({
            'count': len(reminders),
            'reminders': reminders
        })
    
    @extend_schema(
        summary="批量操作订单",
        description="批量更新或删除订单",
        tags=["订单管理"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'order_ids': {'type': 'array', 'items': {'type': 'integer'}},
                    'action': {'type': 'string', 'enum': ['update', 'delete']},
                    'data': {'type': 'object'}
                },
                'required': ['order_ids', 'action']
            }
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string'},
                'message': {'type': 'string'},
                'updated_count': {'type': 'integer'},
                'errors': {'type': 'array', 'items': {'type': 'string'}}
            }
        }},
        examples=[
            OpenApiExample(
                name="批量更新支付状态",
                value={
                    "order_ids": [1, 2, 3],
                    "action": "update",
                    "data": {
                        "payment_status": "paid",
                        "payment_date": "2025-07-18",
                        "payment_method": "银行转账"
                    }
                },
                media_type="application/json",
                summary="批量更新订单支付状态"
            ),
            OpenApiExample(
                name="批量删除订单",
                value={
                    "order_ids": [4, 5, 6],
                    "action": "delete"
                },
                media_type="application/json",
                summary="批量删除多个订单"
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """
        批量操作订单
        """
        # 获取参数
        order_ids = request.data.get('order_ids', [])
        action = request.data.get('action')
        data = request.data.get('data', {})
        
        if not order_ids or not action:
            return Response(
                {"error": "缺少必要参数：order_ids 或 action"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取订单列表
        queryset = Order.objects.filter(id__in=order_ids, is_deleted=False)
        if not queryset.exists():
            return Response(
                {"error": "未找到有效订单"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 执行批量操作
        user = request.user
        if action == 'delete':
            # 批量软删除
            from orders.models import OrderHistory
            OrderHistory.create_bulk_history_records(
                orders=queryset,
                user=user,
                action='delete',
                message='批量删除订单'
            )
            
            # 执行软删除
            updated_count = 0
            errors = []
            for order in queryset:
                try:
                    order.soft_delete()
                    updated_count += 1
                except Exception as e:
                    errors.append(f"订单 {order.order_number} 删除失败: {str(e)}")
            
            return Response({
                'status': 'success',
                'message': f'成功删除 {updated_count} 个订单',
                'updated_count': updated_count,
                'errors': errors
            })
            
        elif action == 'update':
            # 批量更新
            if not data:
                return Response(
                    {"error": "更新操作需要提供 data 字段"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 处理日期字段，将字符串转换为日期对象
            date_fields = ['payment_date', 'order_date', 'service_time']
            for field in date_fields:
                if field in data:
                    # 如果是空值，直接移除该字段，不更新
                    if data[field] is None or data[field] == '':
                        data.pop(field)
                                        # 如果是非空字符串，尝试转换为日期对象
                    elif isinstance(data[field], str) and data[field].strip():
                        try:
                            from datetime import datetime
                            # 转换字符串为日期对象
                            data[field] = datetime.strptime(data[field], '%Y-%m-%d').date()
                        except ValueError:
                            return Response(
                                {"error": f"日期格式错误: {field}={data[field]}，应为YYYY-MM-DD格式"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
            
            # 执行批量更新
            updated_count = 0
            errors = []
            updated_orders = []
            
            for order in queryset:
                try:
                    # 记录旧值
                    changes = {}
                    for field, value in data.items():
                        if hasattr(order, field):
                            old_value = getattr(order, field)
                            if old_value != value:
                                # 对于外键字段需要特殊处理
                                if field.endswith('_id') and field[:-3] in order._meta.get_fields():
                                    changes[field[:-3]] = {'old': old_value, 'new': value}
                                else:
                                    changes[field] = {'old': old_value, 'new': value}
                                setattr(order, field, value)
                    
                    if changes:
                        order.save()
                        updated_orders.append(order)
                        updated_count += 1
                except Exception as e:
                    errors.append(f"订单 {order.order_number} 更新失败: {str(e)}")
            
            # 记录批量更新历史
            if updated_orders:
                from orders.models import OrderHistory
                OrderHistory.create_bulk_history_records(
                    orders=updated_orders,
                    user=user,
                    action='update',
                    message=f'批量更新订单字段: {", ".join(data.keys())}'
                )
            
            return Response({
                'status': 'success',
                'message': f'成功更新 {updated_count} 个订单',
                'updated_count': updated_count,
                'errors': errors
            })
            
        else:
            return Response(
                {"error": f"不支持的操作类型: {action}"},
                status=status.HTTP_400_BAD_REQUEST
            ) 