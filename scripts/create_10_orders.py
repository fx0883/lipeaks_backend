"""
创建10条测试订单数据的脚本
使用当前数据库中已有的客户和联系人数据，或者在需要时创建新的客户和联系人
"""
import os
import sys
import django
import random
from datetime import date, timedelta
from decimal import Decimal
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order
from customers.models import Customer, CustomerMemberRelation
from users.models import Member, User
from tenants.models import Tenant
from django.db import transaction
from django.utils import timezone


def ensure_customers_and_contacts(min_customers=3):
    """
    确保数据库中有足够的客户和联系人数据
    
    Args:
        min_customers: 最少的客户数量
        
    Returns:
        tuple: (客户列表, 客户联系人列表)
    """
    logger.info("检查客户和联系人数据...")
    
    # 获取现有客户
    customers = list(Customer.objects.filter(is_deleted=False))
    
    # 如果客户数量不足，创建新客户
    if len(customers) < min_customers:
        logger.info(f"客户数量不足({len(customers)}个)，创建新客户...")
        
        # 客户类型和规模选项
        customer_types = ['enterprise', 'individual', 'government', 'education', 'nonprofit']
        company_sizes = ['micro', 'small', 'medium', 'large']
        
        # 创建新客户
        new_customers_count = min_customers - len(customers)
        for i in range(new_customers_count):
            customer = Customer.objects.create(
                name=f"测试客户_{timezone.now().strftime('%Y%m%d')}_{i+1}",
                type=random.choice(customer_types),
                status='active',
                company_size=random.choice(company_sizes),
                industry_type=random.choice(['IT', '教育', '医疗', '金融', '制造', '零售']),
                primary_contact_name=f"联系人_{i+1}",
                primary_contact_phone=f"1{random.randint(3, 9)}{''.join([str(random.randint(0, 9)) for _ in range(9)])}",
                primary_contact_email=f"contact_{i+1}@example.com",
                website=f"https://example{i+1}.com",
                notes="由测试脚本自动生成的客户",
                created_by="system"
            )
            customers.append(customer)
            logger.info(f"创建客户: {customer.name}")
    
    # 获取现有联系人
    members = list(Member.objects.filter(is_deleted=False))
    
    # 如果没有联系人，创建一些
    if not members:
        logger.info("没有找到联系人数据，创建新联系人...")
        
        # 尝试获取租户
        tenant = Tenant.objects.first()
        
        # 创建联系人
        for i in range(min_customers):
            username = f"contact_{timezone.now().strftime('%Y%m%d')}_{i+1}"
            member = Member.objects.create(
                username=username,
                email=f"{username}@example.com",
                phone=f"1{random.randint(3, 9)}{''.join([str(random.randint(0, 9)) for _ in range(9)])}",
                nick_name=f"测试联系人_{i+1}",
                tenant=tenant,
                is_active=True,
                status='active'
            )
            # 设置密码
            member.set_password("password123")
            member.save()
            
            members.append(member)
            logger.info(f"创建联系人: {member.username}")
    
    # 确保每个客户至少有一个联系人关系
    for customer in customers:
        relations = CustomerMemberRelation.objects.filter(customer=customer)
        if not relations.exists():
            # 为客户随机选择一个联系人
            member = random.choice(members)
            relation = CustomerMemberRelation.objects.create(
                customer=customer,
                member=member,
                role=random.choice(['决策者', '经理', '翻译协调人', '财务人员']),
                is_primary=True
            )
            logger.info(f"为客户 {customer.name} 创建联系人关系: {member.username}")
    
    return customers, members


def generate_random_date(start_days_ago=100, end_days_ago=1):
    """
    生成一个随机日期
    
    Args:
        start_days_ago: 开始日期距今天的天数
        end_days_ago: 结束日期距今天的天数
        
    Returns:
        随机日期对象
    """
    today = date.today()
    days_ago = random.randint(end_days_ago, start_days_ago)
    return today - timedelta(days=days_ago)


def create_10_orders():
    """
    创建10条订单记录
    """
    logger.info("开始创建10条订单记录...")
    
    # 确保有足够的客户和联系人数据
    customers, members = ensure_customers_and_contacts(min_customers=3)
    
    # 获取系统用户（用于记录历史）
    try:
        users = list(User.objects.filter(is_deleted=False))
        if not users:
            logger.warning("没有找到系统用户，将不会记录订单历史")
            user = None
        else:
            user = users[0]
    except Exception as e:
        logger.error(f"获取用户数据时出错: {e}")
        user = None
    
    # 获取租户
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            logger.warning("没有找到租户数据")
    except Exception as e:
        logger.error(f"获取租户数据时出错: {e}")
        tenant = None
    
    # 服务类型和语种选项
    service_types = ['翻译', '本地化', '口译', '翻译审校', '排版', '术语管理', 'DTP']
    languages = ['中英', '中日', '中韩', '中法', '中德', '中西', '中俄', '英日', '英法']
    
    # 支付状态选项
    payment_statuses = ['unpaid', 'partially_paid', 'paid']
    
    # 发票状态选项
    invoice_statuses = ['not_required', 'pending', 'issued']
    
    # 支付方式选项
    payment_methods = ['银行转账', '支付宝', '微信支付', '对公转账', '信用卡']
    
    # 订单状态选项
    order_statuses = ['draft', 'pending', 'in_progress', 'completed', 'cancelled']
    
    # 项目负责人选项
    project_managers = ['一组', '二组', '三组', '四组', '五组', '六组']
    
    # 客户数量单位
    customer_count_units = ['字', '份', '页', '天', '小时', '半天']
    
    # 创建订单数据
    created_orders = []
    
    with transaction.atomic():
        for i in range(10):
            try:
                logger.info(f"正在创建订单 #{i+1}...")
                # 随机选择客户
                customer = random.choice(customers)
                
                # 获取该客户已有的联系人关系
                customer_member_relations = list(CustomerMemberRelation.objects.filter(customer=customer))
                
                # 随机选择一个该客户的联系人
                contact_relation = random.choice(customer_member_relations)
                contact = contact_relation.member
                
                # 生成随机日期
                order_date = generate_random_date(100, 10)
                service_time = order_date + timedelta(days=random.randint(5, 20))
                
                # 随机选择服务类型和语种
                service_type = random.choice(service_types)
                language = random.choice(languages)
                
                # 随机生成客户数量和翻译数量
                count_unit = random.choice(customer_count_units)
                count_value = random.randint(100, 10000) if count_unit == '字' else random.randint(1, 50)
                customer_count = f"{count_value} {count_unit}"
                translation_count = f"{int(count_value * random.uniform(0.9, 1.1))} {count_unit}"
                
                # 随机生成价格信息
                customer_price_value = Decimal(str(random.uniform(0.1, 1.0))).quantize(Decimal('0.01')) if count_unit == '字' else Decimal(str(random.uniform(100, 2000))).quantize(Decimal('0.01'))
                customer_price = f"{customer_price_value} 元/{count_unit}"
                
                # 计算总价（简化计算）
                if count_unit == '字':
                    total_amount = customer_price_value * Decimal(count_value)
                else:
                    total_amount = customer_price_value * Decimal(count_value) / Decimal('10')
                
                # 译员费用（约为总价的40%-70%）
                translator_fee_percentage = Decimal(str(random.uniform(0.4, 0.7))).quantize(Decimal('0.01'))
                translator_fee = (total_amount * translator_fee_percentage).quantize(Decimal('0.01'))
                translator_price = f"{(translator_fee / Decimal(count_value)).quantize(Decimal('0.01'))} 元/{count_unit}" if count_unit == '字' else f"{translator_fee / Decimal(count_value) * Decimal('10')} 元/{count_unit}"
                
                # 项目费用（固定成本等）
                project_fee = Decimal(str(random.uniform(50, 200))).quantize(Decimal('0.01'))
                
                # 随机生成其他信息
                status = random.choice(order_statuses)
                payment_status = 'paid' if status == 'completed' else random.choice(payment_statuses)
                payment_date = service_time if payment_status == 'paid' else None
                payment_method = random.choice(payment_methods) if payment_status != 'unpaid' else None
                
                # 创建订单
                order = Order.objects.create(
                    customer=customer,
                    source_platform=random.choice(['官网', '小红书', '抖音', '微信', '介绍']),
                    project_manager=random.choice(project_managers),
                    customer_type=random.choice(['新客户', '老客户', 'VIP客户']),
                    order_date=order_date,
                    
                    service_type=service_type,
                    language=language,
                    customer_count=customer_count,
                    translation_count=translation_count,
                    service_time=service_time,
                    project_location=random.choice(['线上', '北京', '上海', '广州', '深圳']),
                    
                    customer_contact=contact,
                    translator=f"测试译员 #{random.randint(1, 10)}",
                    
                    customer_price=customer_price,
                    customer_total_amount=total_amount,
                    translator_fee=translator_fee,
                    translator_price=translator_price,
                    translator_payment_status=random.choice(['已付款', '未付款', '月结30天']),
                    translator_payment_method=random.choice(['微信', '支付宝', '银行转账']),
                    project_fee=project_fee,
                    project_details=f"项目包括{service_type}服务，语种为{language}",
                    cost_details=f"译员费用: {translator_fee}元，项目费用: {project_fee}元",
                    
                    payment_status=payment_status,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    payment_remarks=f"{'已完成付款' if payment_status == 'paid' else '待付款'}",
                    
                    invoice_status=random.choice(invoice_statuses),
                    invoice_info=f"发票抬头：{customer.name}" if random.random() > 0.3 else None,
                    contract_number=f"CT-{order_date.strftime('%Y%m')}-{random.randint(1000, 9999)}",
                    contract_info=f"{customer.name}与公司签订的{service_type}服务合同",
                    
                    delivery_address=f"{random.choice(['北京市', '上海市', '广州市', '深圳市'])}某区某街某号",
                    remarks=f"这是一个测试订单，客户: {customer.name}, 联系人: {contact.username}",
                    
                    tenant=tenant
                )
                
                created_orders.append(order)
                
                # 创建订单历史记录
                if user:
                    from orders.models import OrderHistory
                    OrderHistory.create_history_record(
                        order=order,
                        user=user,
                        change_details={'action': 'create', 'message': '通过脚本创建订单'}
                    )
                
                logger.info(f"成功创建订单 #{i+1}: {order.order_number} - {customer.name}")
                
            except Exception as e:
                logger.error(f"创建订单 #{i+1} 时出错: {e}", exc_info=True)
    
    logger.info(f"成功创建 {len(created_orders)} 个订单")
    return created_orders


if __name__ == "__main__":
    create_10_orders() 