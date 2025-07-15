"""
订单管理系统模型
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json
import uuid
from common.models import BaseModel
from customers.models import Customer
from users.models import Member, User


class Order(BaseModel):
    """
    订单模型，包含订单基本信息、服务信息、费用信息等
    """
    # 订单状态选项
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    


    
    # 1. 订单基本信息
    order_number = models.CharField(_("订单编号"), max_length=100, unique=True, editable=False)
    customer = models.ForeignKey(
        Customer, 
        verbose_name=_("客户"), 
        on_delete=models.PROTECT,
        related_name="orders"
    )
    source_platform = models.CharField(_("来源平台"), max_length=100, blank=True, null=True, 
                                       help_text=_("如：淘宝、小红书店铺、抖音私信等"))
    project_manager = models.CharField(_("项目负责人"), max_length=100, blank=True, null=True,
                                       help_text=_("如：三组、六组、九组等"))
    customer_type = models.CharField(_("客户类型"), max_length=100, blank=True, null=True,
                                     help_text=_("如：老客户、新客户、VIP客户等"))
    order_date = models.DateField(_("下单日期"), null=True, blank=True)
    
    # 2. 服务和语种信息
    service_type = models.CharField(_("服务类型"), max_length=200, default="翻译")
    language = models.CharField(_("语种"), max_length=100, default="中英")  # 原 语种
    customer_count = models.CharField(_("客户数量"), max_length=100, blank=True, null=True,
                                      help_text=_("如：份、字、天、半天、小时、页"))
    translation_count = models.CharField(_("翻译数量"), max_length=100, blank=True, null=True,
                                       help_text=_("与客户数量单位相同但单独计算"))
    service_time = models.DateField(_("服务时间"), blank=True, null=True,
                             help_text=_("服务交付日期"))
    project_location = models.CharField(_("项目地点"), max_length=100, blank=True, null=True,
                                      help_text=_("如：城市、线上"))
    
    # 3. 人员信息
    customer_contact = models.ForeignKey(
        Member,
        verbose_name=_("客户联系人"),
        on_delete=models.PROTECT,
        related_name="customer_contact_orders",
        null=True,
        blank=True
    )
    # 由客户自己填写，改为CharField
    translator = models.CharField(_("译员"), max_length=100, blank=True, null=True)


    
    # 4. 费用信息
    customer_price = models.CharField(_("客户单价"), max_length=100, blank=True, null=True,
                             help_text=_("如：元/份、元/字、元/天、元/半天、元/小时、元/页"))
    customer_total_amount = models.DecimalField(_("客户总价"), max_digits=10, decimal_places=2, default=0)  # 原 客户总价
    translator_fee = models.DecimalField(_("译员费用"), max_digits=10, decimal_places=2, default=0)
    translator_price = models.CharField(_("翻译单价"), max_length=100, blank=True, null=True,
                                      help_text=_("如：元/份、元/字、元/天、元/半天、元/小时、元/页"))
    translator_payment_status = models.CharField(_("译费支付状态"), max_length=100, blank=True, null=True,
                                              help_text=_("如：已付款、未付款、月结30天"))
    translator_payment_method = models.CharField(_("译费支付方式"), max_length=100, blank=True, null=True,
                                              help_text=_("如：对公转账、微信转账、支付宝转账"))
    project_fee = models.DecimalField(_("项目费用"), max_digits=10, decimal_places=2, default=0)
    project_details = models.TextField(_("项目明细"), blank=True, null=True)  # 原 项目明细
    cost_details = models.TextField(_("费用明细"), blank=True, null=True)
    refund_amount = models.DecimalField(_("项目退款"), max_digits=10, decimal_places=2, default=0)
    refund_reason = models.CharField(_("退款原因"), max_length=200, blank=True, null=True)
    
    # 5. 支付信息
    payment_status = models.CharField(_("支付状态"), max_length=50, default='unpaid')
    payment_date = models.DateField(_("支付日期"), null=True, blank=True)
    payment_method = models.CharField(_("支付方式"), max_length=50, blank=True, null=True)
    payment_remarks = models.TextField(_("支付备注"), blank=True, null=True)
    
    # 6. 发票和合同信息
    invoice_status = models.CharField(_("发票状态"), max_length=50, default='not_required')
    invoice_info = models.TextField(_("发票信息"), blank=True, null=True)
    contract_number = models.CharField(_("合同编号"), max_length=100, blank=True, null=True)
    contract_info = models.TextField(_("合同信息"), blank=True, null=True)
    contract_remarks = models.TextField(_("合同备注"), blank=True, null=True)
    
    # 7. 其他信息
    delivery_address = models.CharField(_("收件地址"), max_length=200, blank=True, null=True)
    order_address = models.CharField(_("订单地址"), max_length=200, blank=True, null=True)
    remarks = models.TextField(_("备注"), blank=True, null=True)
    follow_up_record = models.TextField(_("回访记录"), blank=True, null=True)
    
    class Meta:
        verbose_name = _('订单')
        verbose_name_plural = _('订单')
        db_table = 'order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # 如果是新订单，生成订单编号
        if not self.order_number:
            self.order_number = self._generate_order_number()
        
        super().save(*args, **kwargs)
    
    def _generate_order_number(self):
        """
        生成唯一的订单编号，格式：PQ-{年份}{月份}-{4位随机数}
        例如：PQ-202507-1234
        """
        now = timezone.now()
        prefix = f"PQ-{now.year}{now.month:02d}-"
        random_suffix = str(uuid.uuid4().int)[:4]
        return f"{prefix}{random_suffix}"
    
    def calculate_profit(self):
        """
        计算订单毛利
        公式：客户总价 - 译员费用 - 项目费用
        """
        return self.customer_total_amount - self.translator_fee - self.project_fee
    
    def calculate_profit_rate(self):
        """
        计算订单毛利率
        公式：(客户总价 - 译员费用 - 项目费用) / 客户总价
        """
        if self.customer_total_amount == 0:
            return 0
        
        profit = self.calculate_profit()
        return profit / self.customer_total_amount


class OrderHistory(models.Model):
    """
    订单历史记录，记录订单的变更历史
    """
    order = models.ForeignKey(
        Order,
        verbose_name=_("订单"),
        on_delete=models.CASCADE,
        related_name="history_records"
    )
    version = models.PositiveIntegerField(_("版本号"))
    modified_by = models.ForeignKey(
        User,
        verbose_name=_("修改人"),
        on_delete=models.PROTECT,
        related_name="order_modifications"
    )
    modified_at = models.DateTimeField(_("修改时间"), auto_now_add=True)
    change_details = models.TextField(_("变更详情"), default="{}")
    snapshot = models.TextField(_("快照"), default="{}")
    
    class Meta:
        verbose_name = _('订单历史')
        verbose_name_plural = _('订单历史')
        db_table = 'order_history'
        ordering = ['-modified_at']
        unique_together = [['order', 'version']]
    
    def __str__(self):
        return f"{self.order.order_number} - 版本 {self.version}"
    
    @staticmethod
    def create_history_record(order, user, change_details=None):
        """
        创建订单历史记录
        
        Args:
            order: 订单对象
            user: 修改用户
            change_details: 变更详情，默认为None
        
        Returns:
            OrderHistory: 创建的历史记录对象
        """
        # 获取当前订单的最大版本号
        last_version = OrderHistory.objects.filter(order=order).order_by('-version').first()
        new_version = 1 if not last_version else last_version.version + 1
        
        # 创建订单快照
        snapshot = {
            'id': order.id,
            'order_number': order.order_number,
            'customer_id': order.customer_id,
            'customer_name': order.customer.name,
            'source_platform': order.source_platform,
            'project_manager': order.project_manager,
            'customer_type': order.customer_type,
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'service_type': order.service_type,
            'language': order.language,
            'customer_count': order.customer_count,
            'translation_count': order.translation_count,
            'service_time': order.service_time.isoformat() if order.service_time else None,
            'project_location': order.project_location,
            'customer_contact_id': order.customer_contact_id,
            'customer_contact_name': order.customer_contact.display_name if order.customer_contact else None,
            'translator': order.translator,
            'customer_price': order.customer_price,
            'customer_total_amount': float(order.customer_total_amount),
            'translator_fee': float(order.translator_fee),
            'translator_price': order.translator_price,
            'translator_payment_status': order.translator_payment_status,
            'translator_payment_method': order.translator_payment_method,
            'project_fee': float(order.project_fee),
            'project_details': order.project_details,
            'cost_details': order.cost_details,
            'refund_amount': float(order.refund_amount),
            'refund_reason': order.refund_reason,
            'payment_status': order.payment_status,
            'payment_date': order.payment_date.isoformat() if order.payment_date and hasattr(order.payment_date, 'isoformat') else order.payment_date,
            'payment_method': order.payment_method,
            'payment_remarks': order.payment_remarks,
            'invoice_status': order.invoice_status,
            'invoice_info': order.invoice_info,
            'contract_number': order.contract_number,
            'contract_info': order.contract_info,
            'contract_remarks': order.contract_remarks,
            'delivery_address': order.delivery_address,
            'order_address': order.order_address,
            'remarks': order.remarks,
            'follow_up_record': order.follow_up_record,
            'tenant_id': order.tenant_id if order.tenant_id else None,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'is_deleted': order.is_deleted,
            # 记录当前执行更新的用户信息
            'modified_by_id': user.id,
            'modified_by_username': user.username,
            'modified_by_display_name': user.display_name if hasattr(user, 'display_name') else user.username,
            'modified_at': timezone.now().isoformat(),
        }
        
        # 将字典转换为JSON字符串
        snapshot_json = json.dumps(snapshot)
        change_details_json = json.dumps(change_details or {})
        
        # 创建历史记录
        return OrderHistory.objects.create(
            order=order,
            version=new_version,
            modified_by=user,
            change_details=change_details_json,
            snapshot=snapshot_json
        )
        
    @staticmethod
    def create_bulk_history_records(orders, user, action, message=None):
        """
        批量创建订单历史记录
        
        Args:
            orders: 订单对象列表
            user: 修改用户
            action: 操作类型，如'create', 'update', 'delete'
            message: 操作描述，默认为None
            
        Returns:
            int: 创建的历史记录数量
        """
        history_records = []
        now = timezone.now()
        
        for order in orders:
            # 获取版本号
            last_version = OrderHistory.objects.filter(order=order).order_by('-version').first()
            new_version = 1 if not last_version else last_version.version + 1
            
            # 创建订单快照
            snapshot = {
                'id': order.id,
                'order_number': order.order_number,
                'customer_id': order.customer_id,
                'customer_name': order.customer.name,
                'source_platform': order.source_platform,
                'project_manager': order.project_manager,
                'customer_type': order.customer_type,
                'order_date': order.order_date.isoformat() if order.order_date else None,
                'service_type': order.service_type,
                'language': order.language,
                'customer_count': order.customer_count,
                'translation_count': order.translation_count,
                'service_time': order.service_time.isoformat() if order.service_time else None,
                'project_location': order.project_location,
                'customer_contact_id': order.customer_contact_id,
                'customer_contact_name': order.customer_contact.display_name if order.customer_contact else None,
                'translator': order.translator,
                'customer_price': order.customer_price,
                'customer_total_amount': float(order.customer_total_amount),
                'translator_fee': float(order.translator_fee),
                'translator_price': order.translator_price,
                'translator_payment_status': order.translator_payment_status,
                'translator_payment_method': order.translator_payment_method,
                'project_fee': float(order.project_fee),
                'project_details': order.project_details,
                'cost_details': order.cost_details,
                'refund_amount': float(order.refund_amount),
                'refund_reason': order.refund_reason,
                'payment_status': order.payment_status,
                'payment_date': order.payment_date.isoformat() if order.payment_date and hasattr(order.payment_date, 'isoformat') else order.payment_date,
                'payment_method': order.payment_method,
                'payment_remarks': order.payment_remarks,
                'invoice_status': order.invoice_status,
                'invoice_info': order.invoice_info,
                'contract_number': order.contract_number,
                'contract_info': order.contract_info,
                'contract_remarks': order.contract_remarks,
                'delivery_address': order.delivery_address,
                'order_address': order.order_address,
                'remarks': order.remarks,
                'follow_up_record': order.follow_up_record,
                'tenant_id': order.tenant_id if order.tenant_id else None,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'is_deleted': order.is_deleted,
                # 记录当前执行更新的用户信息
                'modified_by_id': user.id,
                'modified_by_username': user.username,
                'modified_by_display_name': user.display_name if hasattr(user, 'display_name') else user.username,
                'modified_at': now.isoformat(),
            }
            
            # 创建变更详情
            change_details = {
                'action': action,
                'message': message or f'批量{action}操作'
            }
            
            # 将字典转换为JSON字符串
            snapshot_json = json.dumps(snapshot)
            change_details_json = json.dumps(change_details)
            
            # 准备历史记录
            history_records.append(OrderHistory(
                order=order,
                version=new_version,
                modified_by=user,
                modified_at=now,
                change_details=change_details_json,
                snapshot=snapshot_json
            ))
        
        # 批量创建
        if history_records:
            created = OrderHistory.objects.bulk_create(history_records)
            return len(created)
        return 0
