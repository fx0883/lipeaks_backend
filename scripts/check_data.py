"""
检查数据库中的数据情况
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order
from customers.models import Customer, CustomerMemberRelation
from users.models import Member, User
from tenants.models import Tenant

def check_data():
    """检查数据库中的数据情况"""
    print("====== 开始数据库数据统计 ======")
    
    # 客户数据
    customer_count = Customer.objects.filter(is_deleted=False).count()
    print(f"客户数量: {customer_count}")
    
    # 联系人数据
    member_count = Member.objects.filter(is_deleted=False).count()
    print(f"联系人数量: {member_count}")
    
    # 用户数据
    user_count = User.objects.filter(is_deleted=False).count()
    print(f"用户数量: {user_count}")
    
    # 订单数据
    order_count = Order.objects.filter(is_deleted=False).count()
    print(f"订单数量: {order_count}")
    
    # 租户数据
    tenant_count = Tenant.objects.count()
    print(f"租户数量: {tenant_count}")
    
    # 客户-联系人关系数据
    relation_count = CustomerMemberRelation.objects.count()
    print(f"客户-联系人关系数量: {relation_count}")
    
    # 显示最新创建的5个订单
    recent_orders = Order.objects.order_by('-created_at')[:5]
    print("\n最近创建的5个订单:")
    for order in recent_orders:
        print(f" - {order.order_number}: {order.customer.name} - 联系人: {order.customer_contact.username if order.customer_contact else '无'} - 状态: {order.status}")
    
    print("\n===== 数据统计完成 =====")

if __name__ == "__main__":
    check_data()
    # 确保所有输出都被刷新
    sys.stdout.flush() 