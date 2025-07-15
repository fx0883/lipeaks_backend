"""
创建测试订单数据的脚本
生成20个测试订单数据，包括相关的客户和客户联系人
"""
import os
import sys
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order
from customers.models import Customer, CustomerMemberRelation
from users.models import Member, User
from tenants.models import Tenant
from django.db import transaction


def create_test_orders(num_orders=20):
    """
    创建测试订单数据
    
    Args:
        num_orders: 要创建的订单数量
    """
    print(f"开始创建{num_orders}个测试订单...")

    # 获取现有数据
    try:
        customers = list(Customer.objects.filter(is_deleted=False))
        members = list(Member.objects.filter(is_deleted=False))
        users = list(User.objects.filter(is_deleted=False))
        tenant = Tenant.objects.first()  # 获取第一个租户作为示例
        
        print(f"可用客户数量: {len(customers)}")
        print(f"可用联系人数量: {len(members)}")
        print(f"可用用户数量: {len(users)}")
        print(f"选择租户: {tenant.name if tenant else 'None'}")
        
        if not customers:
            print("错误：没有找到可用的客户数据，请先创建客户")
            return
        
        if not members:
            print("错误：没有找到可用的联系人数据，请先创建联系人")
            return
            
        if not users:
            print("错误：没有找到可用的用户数据，请先创建用户")
            return
    except Exception as e:
        print(f"获取现有数据时出错: {e}")
        return

    # 服务类型和语言方向选项
    service_types = ['翻译服务', '本地化服务', '口译服务', '翻译审校', '排版服务', '术语管理', '文档转换']
    language_directions = ['英译中', '中译英', '日译中', '中译日', '德译中', '中译德', '法译中', '中译法', '西译中', '中译西']
    
    # 支付状态选项
    payment_statuses = ['unpaid', 'partially_paid', 'paid', 'refunded']
    
    # 发票状态选项
    invoice_statuses = ['not_required', 'pending', 'issued', 'invalid']
    
    # 支付方式选项
    payment_methods = ['银行转账', '支付宝', '微信支付', '现金', '信用卡']
    
    # 订单状态选项
    order_statuses = ['draft', 'pending', 'in_progress', 'completed', 'cancelled']
    
    # 价格单位选项
    price_units = ['元/千字', '元/小时', '元/页', '元/天', '元/项']
    
    # 创建订单数据
    created_orders = []
    
    with transaction.atomic():
        for i in range(num_orders):
            try:
                print(f"正在创建订单 #{i+1}...")
                # 随机选择客户
                customer = random.choice(customers)
                
                # 获取该客户已有的联系人关系
                customer_member_relations = list(CustomerMemberRelation.objects.filter(customer=customer))
                
                # 如果该客户没有联系人关系，随机创建一个
                if not customer_member_relations:
                    print(f"客户 {customer.name} 没有联系人，创建一个新联系人关系...")
                    member = random.choice(members)
                    relation = CustomerMemberRelation.objects.create(
                        customer=customer,
                        member=member,
                        role=random.choice(['决策者', '经理', '翻译协调人', '财务人员']),
                        is_primary=True
                    )
                    customer_member_relations = [relation]
                
                # 随机选择一个该客户的联系人
                contact_relation = random.choice(customer_member_relations)
                contact = contact_relation.member
                
                # 生成随机日期
                today = date.today()
                start_date = today - timedelta(days=random.randint(10, 100))
                due_date = start_date + timedelta(days=random.randint(5, 15))
                delivery_date = None
                if random.random() > 0.3:  # 70%的几率有交付日期
                    delivery_date = due_date - timedelta(days=random.randint(0, 5))
                
                # 生成随机价格和字数
                word_count = random.randint(1000, 10000)
                price_value = Decimal(str(random.uniform(80, 300))).quantize(Decimal('0.01'))
                price_unit = random.choice(price_units)
                price = f"{price_value} {price_unit}"
                
                # 基于旧的计算方式，仅用于生成测试数据
                total_amount = (price_value * word_count) / 1000
                translator_fee = total_amount * Decimal(str(random.uniform(0.4, 0.7))).quantize(Decimal('0.01'))
                other_costs = Decimal(str(random.uniform(0, 200))).quantize(Decimal('0.01'))
                project_fee = Decimal(str(random.uniform(100, 500))).quantize(Decimal('0.01'))
                project_details = f"项目明细 #{i+1} - 包含翻译、校对、排版等服务"
                
                # 随机选择状态
                status = random.choice(order_statuses)
                payment_status = random.choice(payment_statuses)
                
                # 根据状态设置支付日期
                payment_date = None
                if payment_status in ['paid', 'refunded']:
                    payment_date = delivery_date or due_date
                
                # 创建订单
                order = Order.objects.create(
                    customer=customer,
                    customer_contact=contact,
                    created_by=random.choice(users),
                    service_type=random.choice(service_types),
                    language_direction=random.choice(language_directions),
                    word_count=word_count,
                    description=f"测试订单 #{i+1} - {customer.name}的{random.choice(service_types)}项目",
                    translator=f"测试译员 #{random.randint(1, 10)}",
                    start_date=start_date,
                    due_date=due_date,
                    delivery_date=delivery_date,
                    price=price,
                    total_amount=total_amount,
                    translator_fee=translator_fee,
                    other_costs=other_costs,
                    project_fee=project_fee,
                    project_details=project_details,
                    status=status,
                    payment_status=payment_status,
                    payment_date=payment_date,
                    payment_method=random.choice(payment_methods) if payment_status != 'unpaid' else None,
                    invoice_status=random.choice(invoice_statuses),
                    invoice_info=f"发票信息：{customer.name}，统一社会信用代码：91000000000000000X",
                    contract_number=f"PQ-{today.year}{today.month:02d}-{random.randint(1000, 9999)}",
                    contract_info=f"{customer.name}与我司签订的翻译服务合同",
                    contract_remarks=f"合同备注：客户要求于{due_date}前完成交付",
                    remarks=f"这是一个自动生成的测试订单，客户: {customer.name}, 联系人: {contact.username}",
                    tags=f"测试,{random.choice(['紧急', '重要', '常规'])}",
                    follow_up_record=f"[{today}] 已与客户{contact.username}确认订单细节",
                    tenant=tenant
                )
                
                created_orders.append(order)
                print(f"成功创建订单 #{i+1}: {order.order_number} - {customer.name}")
                
            except Exception as e:
                print(f"创建订单 #{i+1} 时出错: {e}")
    
    print(f"成功创建 {len(created_orders)} 个测试订单")
    return created_orders


if __name__ == "__main__":
    # 可以通过命令行参数指定创建的订单数量
    num_orders = 20
    if len(sys.argv) > 1:
        try:
            num_orders = int(sys.argv[1])
        except ValueError:
            print("参数错误: 订单数量必须是整数")
            sys.exit(1)
    
    create_test_orders(num_orders) 