"""
订单应用的序列化器
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderHistory
from customers.serializers import CustomerListSerializer
from users.serializers import UserMinimalSerializer, MemberMinimalSerializer
from users.models import User, Member
import logging

logger = logging.getLogger(__name__)


class OrderSerializer(serializers.ModelSerializer):
    """
    订单基本序列化器
    """
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    invoice_status_display = serializers.CharField(source='get_invoice_status_display', read_only=True)
    profit = serializers.SerializerMethodField()
    profit_rate = serializers.SerializerMethodField()
    formatted_profit = serializers.SerializerMethodField()
    formatted_profit_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_deleted', 'order_number', 'tenant')
    
    def to_internal_value(self, data):
        """
        重写to_internal_value方法，处理payment_date为null或空字符串的情况
        """
        # 检查payment_date是否为空值（null或空字符串）
        if 'payment_date' in data and (data['payment_date'] is None or data['payment_date'] == ''):
            # 从数据中移除payment_date，这样就不会更新此字段
            data = data.copy()  # 创建一个副本以避免修改原始数据
            data.pop('payment_date')
        
        # 调用父类方法继续处理
        return super().to_internal_value(data)
    
    def get_profit(self, obj):
        """
        获取订单毛利
        """
        return obj.calculate_profit()
    
    def get_formatted_profit(self, obj):
        """
        获取格式化的订单毛利（带货币符号）
        """
        return f"¥{obj.calculate_profit():.2f}"
    
    def get_profit_rate(self, obj):
        """
        获取订单毛利率
        """
        return obj.calculate_profit_rate()
    
    def get_formatted_profit_rate(self, obj):
        """
        获取格式化的订单毛利率（百分比形式）
        """
        return f"{obj.calculate_profit_rate():.2%}"


class OrderCreateSerializer(OrderSerializer):
    """
    创建订单序列化器
    """
    def validate(self, data):
        """
        验证订单创建数据
        """
        # 对于总金额为0的情况，客户数量不应为空
        if 'customer_total_amount' not in data or data.get('customer_total_amount', 0) == 0:
            customer_count = data.get('customer_count')
            if not customer_count:
                raise serializers.ValidationError({'customer_count': _('Customer count cannot be empty')})
        
        return data
    
    def create(self, validated_data):
        """
        创建订单并记录历史
        """
        # 从请求中获取用户
        user = self.context['request'].user
        
        # 设置租户
        if hasattr(user, 'tenant') and user.tenant:
            validated_data['tenant'] = user.tenant
        
        # 创建订单
        order = super().create(validated_data)
        
        # 创建历史记录
        OrderHistory.create_history_record(
            order=order,
            user=user,
            change_details={'action': 'create', 'message': '创建订单'}
        )
        
        return order


class OrderUpdateSerializer(OrderSerializer):
    """
    更新订单序列化器
    """
    def update(self, instance, validated_data):
        """
        更新订单并记录变更历史
        """
        # 从请求中获取用户
        user = self.context['request'].user
        
        # 记录开始更新的日志
        logger.info(f"开始更新订单: ID={instance.id}, 订单号={instance.order_number}, 用户={user.username}")
        
        # 记录变更详情
        change_details = {'action': 'update', 'changes': {}}
        for field, value in validated_data.items():
            if hasattr(instance, field):
                old_value = getattr(instance, field)
                if old_value != value:
                    # 对于简单类型，直接记录旧值和新值
                    if isinstance(old_value, (int, float, str, bool)) or old_value is None:
                        change_details['changes'][field] = {
                            'old': old_value,
                            'new': value
                        }
                        logger.debug(f"订单字段变更: {field}, 旧值: {old_value}, 新值: {value}")
                    # 对于外键字段，尝试记录更多有用信息
                    elif field.endswith('_id') or field in ['customer', 'customer_contact']:
                        # 记录外键对象的ID和标识信息
                        old_id = getattr(old_value, 'id', None) if old_value else None
                        old_name = getattr(old_value, 'name', None) or getattr(old_value, 'display_name', None) if old_value else None
                        
                        new_id = getattr(value, 'id', None) if value else None
                        new_name = getattr(value, 'name', None) or getattr(value, 'display_name', None) if value else None
                        
                        change_details['changes'][field] = {
                            'old': {'id': old_id, 'name': old_name} if old_value else None,
                            'new': {'id': new_id, 'name': new_name} if value else None
                        }
                        logger.debug(f"订单外键字段变更: {field}, 旧值: {old_id}/{old_name}, 新值: {new_id}/{new_name}")
                    # 对于其他复杂类型，记录基本变更信息
                    else:
                        change_details['changes'][field] = {
                            'old_type': type(old_value).__name__ if old_value else 'None',
                            'new_type': type(value).__name__ if value else 'None',
                            'changed': True
                        }
                        logger.debug(f"订单复杂类型字段变更: {field}, 类型从 {type(old_value).__name__} 变为 {type(value).__name__}")
        
        # 更新订单
        order = super().update(instance, validated_data)
        
        # 如果有变更，创建历史记录
        if change_details['changes']:
            change_details['message'] = f'更新订单字段: {", ".join(change_details["changes"].keys())}'
            
            # 创建历史记录
            history = OrderHistory.create_history_record(
                order=order,
                user=user,
                change_details=change_details
            )
            
            logger.info(f"订单更新完成并创建历史记录: ID={order.id}, 订单号={order.order_number}, 历史版本={history.version}")
        else:
            logger.info(f"订单无实际变更，未创建历史记录: ID={order.id}, 订单号={order.order_number}")
        
        return order


class OrderHistorySerializer(serializers.ModelSerializer):
    """
    订单历史记录序列化器
    """
    modified_by_name = serializers.SerializerMethodField()
    change_details_data = serializers.SerializerMethodField()
    snapshot_data = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderHistory
        fields = ['id', 'order', 'version', 'modified_by', 'modified_by_name', 'modified_at', 
                 'change_details', 'change_details_data', 'snapshot', 'snapshot_data']
        read_only_fields = ('order', 'version', 'modified_by', 'modified_at', 'change_details', 'snapshot')
    
    def get_modified_by_name(self, obj):
        """
        获取修改人姓名
        """
        if obj.modified_by:
            return obj.modified_by.username
        return None
    
    def get_change_details_data(self, obj):
        """
        将变更详情JSON字符串转换为Python对象
        """
        import json
        try:
            if obj.change_details:
                return json.loads(obj.change_details)
        except (TypeError, json.JSONDecodeError):
            pass
        return {}
    
    def get_snapshot_data(self, obj):
        """
        将快照JSON字符串转换为Python对象
        """
        import json
        try:
            if obj.snapshot:
                snapshot_data = json.loads(obj.snapshot)
                
                # 确保存在customer_contact_name字段
                # 如果snapshot_data中没有这个字段但有customer_contact_id，尝试从Member获取
                if 'customer_contact_name' not in snapshot_data and 'customer_contact_id' in snapshot_data and snapshot_data['customer_contact_id']:
                    from users.models import Member
                    try:
                        member = Member.objects.get(id=snapshot_data['customer_contact_id'])
                        snapshot_data['customer_contact_name'] = member.display_name
                    except (Member.DoesNotExist, Exception):
                        # 如果找不到用户或出现其他错误，设置为None
                        snapshot_data['customer_contact_name'] = None
                
                return snapshot_data
        except (TypeError, json.JSONDecodeError):
            pass
        return {}


class OrderHistoryDetailSerializer(OrderHistorySerializer):
    """
    订单历史记录详情序列化器，包含完整快照
    """
    modified_by = UserMinimalSerializer(read_only=True)
    
    class Meta(OrderHistorySerializer.Meta):
        depth = 1  # 增加序列化深度，展开关联对象


class OrderCompareSerializer(serializers.Serializer):
    """
    订单版本比较序列化器
    """
    order_id = serializers.IntegerField(read_only=True)
    order_number = serializers.CharField(read_only=True)
    version1 = serializers.IntegerField(required=True)
    version2 = serializers.IntegerField(required=True)
    differences = serializers.JSONField(read_only=True)
    
    def validate(self, data):
        """
        验证版本比较数据
        """
        version1 = data.get('version1')
        version2 = data.get('version2')
        
        if version1 == version2:
            raise serializers.ValidationError({'version2': _('Cannot be the same as version1')})
        
        # 检查是否存在对应的历史记录
        order_id = self.context.get('order_id')
        if order_id:
            if not OrderHistory.objects.filter(order_id=order_id, version=version1).exists():
                raise serializers.ValidationError({'version1': _(f'订单{order_id}不存在版本{version1}')})
            if not OrderHistory.objects.filter(order_id=order_id, version=version2).exists():
                raise serializers.ValidationError({'version2': _(f'订单{order_id}不存在版本{version2}')})
        
        return data


class OrderListSerializer(serializers.ModelSerializer):
    """
    订单列表序列化器（包含所有字段，与OrderSerializer保持一致）
    """
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    invoice_status_display = serializers.CharField(source='get_invoice_status_display', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    customer_contact_info = serializers.SerializerMethodField()
    profit = serializers.SerializerMethodField()
    profit_rate = serializers.SerializerMethodField()
    formatted_profit = serializers.SerializerMethodField()
    formatted_profit_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'  # 修改为包含所有字段
        read_only_fields = ('created_at', 'updated_at', 'is_deleted', 'order_number', 'tenant')
    
    def get_profit(self, obj):
        """
        获取订单毛利
        """
        return obj.calculate_profit()
    
    def get_profit_rate(self, obj):
        """
        获取订单毛利率
        """
        return obj.calculate_profit_rate()
    
    def get_formatted_profit(self, obj):
        """
        获取格式化的订单毛利（带货币符号）
        """
        return f"¥{obj.calculate_profit():.2f}"
    
    def get_formatted_profit_rate(self, obj):
        """
        获取格式化的订单毛利率（百分比形式）
        """
        return f"{obj.calculate_profit_rate():.2%}"
    
    def get_created_by_info(self, obj):
        """
        获取创建人信息
        """
        user = None
        if hasattr(obj, 'created_by_id') and obj.created_by_id:
            try:
                user = User.objects.get(id=obj.created_by_id)
            except User.DoesNotExist:
                pass
        
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'display_name': user.display_name if hasattr(user, 'display_name') else user.username
            }
        return None
    
    def get_customer_contact_info(self, obj):
        """
        获取客户联系人信息
        """
        member = None
        if obj.customer_contact_id:
            try:
                member = Member.objects.get(id=obj.customer_contact_id)
            except Member.DoesNotExist:
                pass
        
        if member:
            return {
                'id': member.id,
                'username': member.username,
                'display_name': member.display_name,
                'phone': member.phone,
                'email': member.email,
                'wechat_id': member.wechat_id
            }
        return None


class OrderDetailSerializer(OrderSerializer):
    """
    订单详情序列化器（包含关联数据）
    """
    customer = CustomerListSerializer(read_only=True)
    customer_contact = MemberMinimalSerializer(read_only=True)
    history_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_deleted', 'order_number', 'tenant')
    
    def get_history_count(self, obj):
        """
        获取历史记录数量
        """
        return OrderHistory.objects.filter(order=obj).count()


class OrderStatisticsSerializer(serializers.Serializer):
    """
    订单统计数据序列化器
    """
    period = serializers.CharField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    total_orders = serializers.IntegerField(read_only=True)
    customer_total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    average_profit_rate = serializers.FloatField(read_only=True)
    by_period = serializers.ListField(child=serializers.JSONField(), read_only=True)
    by_service_type = serializers.ListField(child=serializers.JSONField(), read_only=True)
    by_payment_status = serializers.ListField(child=serializers.JSONField(), read_only=True)