"""
查看订单数据的脚本
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order
from customers.models import Customer


def view_orders():
    """
    查看订单数据的详细信息
    """
    orders = Order.objects.all()
    print(f"当前订单总数: {orders.count()}")
    
    # 显示前5个订单的详细信息
    print("\n前5个订单的详细信息:")
    for i, order in enumerate(orders[:5]):
        print(f"\n------ 订单 {i+1} ------")
        print(f"订单编号: {order.order_number}")
        print(f"客户: {order.customer.name}")
        print(f"客户联系人: {order.customer_contact.username if order.customer_contact else '无'}")
        print(f"订单日期: {order.order_date}")
        print(f"服务类型: {order.service_type}")
        print(f"语种: {order.language}")
        print(f"客户数量: {order.customer_count}")
        print(f"翻译数量: {order.translation_count}")
        print(f"服务时间: {order.service_time}")
        print(f"项目负责人: {order.project_manager}")
        print(f"客户总金额: {order.customer_total_amount}")
        print(f"译员费用: {order.translator_fee}")
        print(f"项目费用: {order.project_fee}")
        print(f"毛利: {order.calculate_profit()}")
        print(f"毛利率: {order.calculate_profit_rate():.2%}")
        print(f"支付状态: {order.payment_status}")
        print(f"发票状态: {order.invoice_status}")
        print(f"备注: {order.remarks[:50]}..." if order.remarks and len(order.remarks) > 50 else f"备注: {order.remarks}")


if __name__ == "__main__":
    view_orders() 