from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderHistory
from django.db import models
from common.admin import TenantAdminMixin
import datetime

class OrderHistoryInline(admin.TabularInline):
    model = OrderHistory
    extra = 0
    readonly_fields = ('version', 'modified_by', 'modified_at', 'view_change_details')
    fields = ('version', 'modified_by', 'modified_at', 'view_change_details')
    can_delete = False
    show_change_link = True
    verbose_name = _("历史记录")
    verbose_name_plural = _("历史记录")
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def view_change_details(self, obj):
        """提供一个链接到历史记录的详情页"""
        if obj.id:
            url = reverse('admin:orders_orderhistory_change', args=[obj.id])
            return format_html('<a href="{}">{}</a>', url, _("查看详情"))
        return "-"
    view_change_details.short_description = _("操作")

@admin.register(Order)
class OrderAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'order_number', 'customer', 'customer_contact', 'service_type', 'language',
        'customer_count', 'translation_count', 'customer_total_amount', 'translator_fee',
        'project_fee', 'get_profit', 'get_profit_rate_display', 'payment_status',
        'invoice_status', 'translator', 'order_date', 'service_time', 'created_at'
    )
    list_filter = ('payment_status', 'service_type', 'language', 'customer_type', 'invoice_status')
    search_fields = ('order_number', 'customer__name', 'project_details')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'get_profit', 'get_profit_rate_display')
    date_hierarchy = 'created_at'
    inlines = [OrderHistoryInline]
    
    def get_profit(self, obj):
        """获取毛利，并格式化为货币形式"""
        return f"¥{obj.calculate_profit():.2f}"
    get_profit.short_description = "毛利"
    
    def get_profit_rate_display(self, obj):
        """获取毛利率，并格式化为百分比形式"""
        return f"{obj.calculate_profit_rate():.2%}"
    get_profit_rate_display.short_description = "毛利率"
    
    def save_model(self, request, obj, form, change):
        """保存模型时记录历史"""
        # 判断是创建还是更新操作
        is_create = obj.pk is None
        
        # 如果是更新，先记录旧值
        old_data = {}
        if not is_create:
            try:
                old_obj = Order.objects.get(pk=obj.pk)
                for field in form.changed_data:
                    if hasattr(old_obj, field):
                        old_value = getattr(old_obj, field)
                        if isinstance(old_value, (models.Model,)):
                            old_data[field] = old_value.pk
                        elif isinstance(old_value, (datetime.date, datetime.datetime)):
                            old_data[field] = old_value.isoformat()
                        else:
                            old_data[field] = old_value
            except Order.DoesNotExist:
                pass
        
        # 保存模型
        super().save_model(request, obj, form, change)
        
        # 创建历史记录
        if is_create:
            OrderHistory.create_history_record(
                order=obj,
                user=request.user,
                change_details={'action': 'create', 'message': '管理界面创建订单'}
            )
        else:
            # 构建详细的变更记录
            changes = {}
            for field in form.changed_data:
                if field in old_data:
                    new_value = getattr(obj, field)
                    if isinstance(new_value, (models.Model,)):
                        new_value = new_value.pk
                    elif isinstance(new_value, (datetime.date, datetime.datetime)):
                        new_value = new_value.isoformat()
                    
                    changes[field] = {
                        'old': old_data[field],
                        'new': new_value
                    }
            
            if changes:
                OrderHistory.create_history_record(
                    order=obj,
                    user=request.user,
                    change_details={'action': 'update', 'changes': changes, 'message': '管理界面更新订单'}
                )
    
    def delete_model(self, request, obj):
        """删除模型时记录历史"""
        # 先记录历史
        OrderHistory.create_history_record(
            order=obj,
            user=request.user,
            change_details={'action': 'delete', 'message': '管理界面删除订单'}
        )
        # 执行删除
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """批量删除时记录历史"""
        for obj in queryset:
            OrderHistory.create_history_record(
                order=obj,
                user=request.user,
                change_details={'action': 'delete', 'message': '管理界面批量删除订单'}
            )
        super().delete_queryset(request, queryset)
    
    fieldsets = (
        (_('订单基本信息'), {
            'fields': ('order_number', 'customer', 'customer_type', 'source_platform', 'project_manager', 'order_date')
        }),
        (_('服务和语种信息'), {
            'fields': ('service_type', 'language', 'customer_count', 'translation_count', 'service_time', 'project_location')
        }),
        (_('人员信息'), {
            'fields': ('customer_contact', 'translator')
        }),
        (_('费用信息'), {
            'fields': ('customer_price', 'customer_total_amount', 'translator_fee', 'translator_price', 
                     'project_fee', 'project_details', 'cost_details', 'refund_amount', 'refund_reason',
                     'get_profit', 'get_profit_rate_display')
        }),
        (_('译员支付信息'), {
            'fields': ('translator_payment_status', 'translator_payment_method')
        }),
        (_('支付信息'), {
            'fields': ('payment_status', 'payment_date', 'payment_method', 'payment_remarks')
        }),
        (_('发票和合同信息'), {
            'fields': ('invoice_status', 'invoice_info', 'contract_number', 'contract_info', 'contract_remarks')
        }),
        (_('地址信息'), {
            'fields': ('delivery_address', 'order_address')
        }),
        (_('其他信息'), {
            'fields': ('remarks', 'follow_up_record')
        }),
        (_('系统信息'), {
            'fields': ('tenant', 'created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderHistory)
class OrderHistoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('order', 'version', 'modified_by', 'modified_at')
    list_filter = ('modified_at',)
    search_fields = ('order__order_number',)
    readonly_fields = ('order', 'version', 'modified_by', 'modified_at', 'change_details_formatted', 'snapshot_formatted')
    
    fieldsets = (
        (_('基本信息'), {
            'fields': ('order', 'version', 'modified_by', 'modified_at')
        }),
        (_('变更信息'), {
            'fields': ('change_details_formatted',)
        }),
        (_('快照信息'), {
            'fields': ('snapshot_formatted',)
        }),
    )
    
    def change_details_formatted(self, obj):
        """格式化显示变更详情"""
        import json
        try:
            if obj.change_details:
                details = json.loads(obj.change_details)
                html = "<pre>{}</pre>".format(json.dumps(details, indent=4, ensure_ascii=False))
                return format_html(html)
        except (TypeError, json.JSONDecodeError):
            pass
        return obj.change_details
    change_details_formatted.short_description = _("变更详情")
    
    def snapshot_formatted(self, obj):
        """格式化显示快照信息"""
        import json
        try:
            if obj.snapshot:
                snapshot = json.loads(obj.snapshot)
                html = "<pre>{}</pre>".format(json.dumps(snapshot, indent=4, ensure_ascii=False))
                return format_html(html)
        except (TypeError, json.JSONDecodeError):
            pass
        return obj.snapshot
    snapshot_formatted.short_description = _("快照信息")
