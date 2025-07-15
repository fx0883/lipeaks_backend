"""
创建近一年约300条订单数据的脚本
专为租户ID为17的租户创建，数据包含各种订单类型和状态
"""
import os
import sys
import django
import random
from datetime import date, timedelta, datetime
from decimal import Decimal
import logging
from tqdm import tqdm

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order, OrderHistory
from customers.models import Customer, CustomerMemberRelation
from users.models import Member, User
from tenants.models import Tenant
from django.db import transaction
from django.utils import timezone


def get_tenant_customers_and_contacts(tenant_id):
    """
    获取指定租户ID下的客户和联系人
    
    Args:
        tenant_id: 租户ID
        
    Returns:
        tuple: (客户列表, 客户联系人关系字典)
    """
    logger.info(f"获取租户ID {tenant_id} 的客户和联系人数据...")
    
    # 获取指定租户ID的客户
    from customers.models import CustomerTenantRelation
    customer_relations = CustomerTenantRelation.objects.filter(tenant_id=tenant_id)
    customer_ids = [rel.customer_id for rel in customer_relations]
    customers = list(Customer.objects.filter(id__in=customer_ids, is_deleted=False))
    
    if not customers:
        raise ValueError(f"租户ID {tenant_id} 下没有找到客户数据，请先创建客户")
    
    logger.info(f"找到 {len(customers)} 个客户")
    
    # 获取客户的联系人关系
    customer_contacts = {}
    for customer in customers:
        relations = list(CustomerMemberRelation.objects.filter(customer=customer))
        if relations:
            customer_contacts[customer.id] = relations
        else:
            logger.warning(f"客户 {customer.name} 没有关联的联系人")
    
    if not customer_contacts:
        raise ValueError(f"租户ID {tenant_id} 下的客户没有联系人关系，请先创建联系人")
    
    return customers, customer_contacts


def generate_random_date_in_past_year():
    """
    生成过去一年内的随机日期
    
    Returns:
        随机日期对象
    """
    today = date.today()
    days_ago = random.randint(0, 364)  # 0到364天前（近一年）
    return today - timedelta(days=days_ago)


def create_orders_for_past_year(tenant_id, order_count=300):
    """
    为指定租户创建近一年约300条订单数据
    
    Args:
        tenant_id: 租户ID
        order_count: 要创建的订单数量
    """
    logger.info(f"开始为租户ID {tenant_id} 创建 {order_count} 条订单记录...")
    
    # 获取指定租户
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        logger.info(f"找到租户: {tenant.name}")
    except Tenant.DoesNotExist:
        logger.error(f"租户ID {tenant_id} 不存在")
        return
    
    # 获取客户和联系人
    try:
        customers, customer_contacts = get_tenant_customers_and_contacts(tenant_id)
    except ValueError as e:
        logger.error(str(e))
        return
    
    # 获取系统用户（用于记录历史）
    try:
        users = list(User.objects.filter(tenant_id=tenant_id, is_deleted=False))
        if not users:
            users = list(User.objects.filter(is_super_admin=True, is_deleted=False))
        
        if not users:
            logger.warning("没有找到适合的用户，将不会记录订单历史")
            user = None
        else:
            user = users[0]
    except Exception as e:
        logger.error(f"获取用户数据时出错: {e}")
        user = None
    
    # 服务类型和语种选项
    service_types = ['翻译', '本地化', '口译', '翻译审校', '排版', '术语管理', 'DTP', '创意翻译', '网站翻译', 
                     '视频翻译', '市场调研翻译', '法律翻译', '医疗翻译', '技术翻译', '金融翻译']
    
    languages = ['中英', '中日', '中韩', '中法', '中德', '中西', '中俄', '英日', '英法', '英德', '英西', 
                '中英德', '中英法', '中英日', '英法德', '多语种']
    
    # 订单和支付状态选项
    # 设置状态分布，使已完成订单占比较高
    order_statuses = ['draft', 'pending', 'in_progress', 'completed', 'cancelled']
    status_weights = [0.05, 0.10, 0.15, 0.65, 0.05]  # 权重调整为偏向已完成
    
    payment_statuses = ['unpaid', 'partially_paid', 'paid']
    payment_weights = [0.15, 0.15, 0.70]  # 权重调整为偏向已付款
    
    # 发票状态选项
    invoice_statuses = ['not_required', 'pending', 'issued']
    invoice_weights = [0.15, 0.25, 0.60]  # 权重调整为偏向已开票
    
    # 支付方式选项
    payment_methods = ['银行转账', '支付宝', '微信支付', '对公转账', '信用卡', '现金', '其他']
    
    # 项目负责人选项
    project_managers = ['一组', '二组', '三组', '四组', '五组', '六组', '七组', '八组', '九组', '十组']
    
    # 客户数量单位及对应的价格范围
    count_unit_configs = {
        '字': {'min': 100, 'max': 50000, 'price_min': 0.1, 'price_max': 1.0},
        '页': {'min': 1, 'max': 200, 'price_min': 50, 'price_max': 300},
        '份': {'min': 1, 'max': 50, 'price_min': 200, 'price_max': 2000},
        '天': {'min': 1, 'max': 10, 'price_min': 1000, 'price_max': 5000},
        '小时': {'min': 1, 'max': 24, 'price_min': 100, 'price_max': 800},
        '半天': {'min': 1, 'max': 20, 'price_min': 500, 'price_max': 2500},
    }
    
    # 客户来源平台
    source_platforms = ['官网', '小红书', '抖音', '微信', '介绍', '老客户推荐', '展会', '邮件咨询', 
                       '电话咨询', '合作伙伴', '广告', '搜索引擎', '线下活动']
    
    # 客户类型
    customer_types = ['新客户', '老客户', 'VIP客户', '重点客户', '潜在客户', '合作伙伴']
    
    # 创建订单数据
    created_orders = []
    
    # 按月份分布订单，使订单分布更加自然
    today = date.today()
    one_year_ago = today - timedelta(days=365)
    
    # 生成过去一年内的每个月的订单数分布，模拟业务季节性
    months = [one_year_ago + timedelta(days=30*i) for i in range(13)]
    
    # 季节性波动：假设Q4和Q1是旺季，Q2和Q3是淡季
    monthly_weights = [0.08, 0.09, 0.10, 0.07, 0.06, 0.06, 0.07, 0.08, 0.09, 0.10, 0.10, 0.10]
    monthly_orders = []
    
    for i, weight in enumerate(monthly_weights):
        monthly_orders.append(int(order_count * weight))
    
    # 确保总订单数为指定的order_count
    total_assigned = sum(monthly_orders)
    if total_assigned < order_count:
        monthly_orders[-1] += (order_count - total_assigned)
    
    # 将订单按月分配
    order_dates = []
    for i, month in enumerate(months[:-1]):  # 最后一个是当前月份的下一个月，不需要
        next_month = months[i + 1]
        days_in_month = (next_month - month).days
        month_orders = monthly_orders[i]
        
        for _ in range(month_orders):
            random_day = random.randint(0, days_in_month - 1)
            order_date = month + timedelta(days=random_day)
            order_dates.append(order_date)
    
    # 打乱顺序，使订单创建不按时间顺序
    random.shuffle(order_dates)
    
    # 使用tqdm显示进度条
    with transaction.atomic():
        for i, order_date in enumerate(tqdm(order_dates[:order_count], desc="创建订单")):
            try:
                # 随机选择客户
                customer = random.choice(customers)
                
                # 获取该客户已有的联系人关系
                if customer.id in customer_contacts:
                    contact_relations = customer_contacts[customer.id]
                    # 随机选择一个该客户的联系人
                    contact_relation = random.choice(contact_relations)
                    contact = contact_relation.member
                else:
                    contact = None
                
                # 随机选择服务类型和语种
                service_type = random.choice(service_types)
                language = random.choice(languages)
                
                # 服务时间应该在订单日期之后
                service_time_days = random.randint(3, 30)  # 3-30天的交付周期
                service_time = order_date + timedelta(days=service_time_days)
                
                # 随机生成客户数量和翻译数量
                count_unit = random.choice(list(count_unit_configs.keys()))
                config = count_unit_configs[count_unit]
                count_value = random.randint(config['min'], config['max'])
                customer_count = f"{count_value} {count_unit}"
                
                # 翻译数量稍有不同
                translation_count_value = int(count_value * random.uniform(0.9, 1.1))
                translation_count = f"{translation_count_value} {count_unit}"
                
                # 随机生成价格信息
                customer_price_value = Decimal(str(random.uniform(config['price_min'], config['price_max']))).quantize(Decimal('0.01'))
                customer_price = f"{customer_price_value} 元/{count_unit}"
                
                # 计算总价
                if count_unit == '字':
                    total_amount = (customer_price_value * Decimal(count_value)).quantize(Decimal('0.01'))
                else:
                    total_amount = (customer_price_value * Decimal(count_value)).quantize(Decimal('0.01'))
                
                # 译员费用（约为总价的40%-70%）
                translator_fee_percentage = Decimal(str(random.uniform(0.4, 0.7))).quantize(Decimal('0.01'))
                translator_fee = (total_amount * translator_fee_percentage).quantize(Decimal('0.01'))
                translator_price_value = (translator_fee / Decimal(count_value)).quantize(Decimal('0.01'))
                translator_price = f"{translator_price_value} 元/{count_unit}"
                
                # 项目费用（固定成本等）
                project_fee = Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.01'))
                
                # 随机生成状态信息，考虑到日期因素调整
                days_since_order = (today - order_date).days
                
                # 根据订单日期和服务时间决定状态
                if service_time > today:  # 尚未到服务时间
                    if random.random() < 0.7:  # 70%概率为进行中
                        status = 'in_progress'
                    else:
                        status = random.choices(['draft', 'pending'], weights=[0.3, 0.7], k=1)[0]
                else:  # 已过服务时间
                    if random.random() < 0.8:  # 80%概率已完成
                        status = 'completed'
                    else:
                        status = random.choices(['in_progress', 'cancelled'], weights=[0.8, 0.2], k=1)[0]
                
                # 根据状态决定支付状态
                if status == 'completed':
                    payment_status = random.choices(['paid', 'partially_paid'], weights=[0.9, 0.1], k=1)[0]
                elif status == 'in_progress':
                    payment_status = random.choices(['unpaid', 'partially_paid', 'paid'], weights=[0.3, 0.4, 0.3], k=1)[0]
                else:
                    payment_status = random.choices(['unpaid', 'partially_paid'], weights=[0.8, 0.2], k=1)[0]
                
                # 支付日期
                if payment_status == 'paid':
                    payment_date = service_time + timedelta(days=random.randint(0, 30))  # 在服务时间后0-30天付款
                    if payment_date > today:
                        payment_date = today - timedelta(days=random.randint(0, 5))  # 确保不超过今天
                elif payment_status == 'partially_paid':
                    payment_date = service_time - timedelta(days=random.randint(5, 15))  # 在服务时间前5-15天部分付款
                    if payment_date > today:
                        payment_date = None
                else:
                    payment_date = None
                
                payment_method = random.choice(payment_methods) if payment_status != 'unpaid' else None
                
                # 发票状态
                if payment_status == 'paid':
                    invoice_status = random.choices(invoice_statuses, weights=[0.1, 0.2, 0.7], k=1)[0]
                elif payment_status == 'partially_paid':
                    invoice_status = random.choices(invoice_statuses, weights=[0.2, 0.6, 0.2], k=1)[0]
                else:
                    invoice_status = random.choices(invoice_statuses, weights=[0.7, 0.3, 0.0], k=1)[0]
                
                # 创建订单
                order = Order.objects.create(
                    customer=customer,
                    source_platform=random.choice(source_platforms),
                    project_manager=random.choice(project_managers),
                    customer_type=random.choice(customer_types),
                    order_date=order_date,
                    
                    service_type=service_type,
                    language=language,
                    customer_count=customer_count,
                    translation_count=translation_count,
                    service_time=service_time,
                    project_location=random.choice(['线上', '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '天津']),
                    
                    customer_contact=contact,
                    translator=f"译员 {random.choice(['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴'])}{random.choice(['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'])}",
                    
                    customer_price=customer_price,
                    customer_total_amount=total_amount,
                    translator_fee=translator_fee,
                    translator_price=translator_price,
                    translator_payment_status=random.choice(['已付款', '未付款', '月结30天', '待确认']),
                    translator_payment_method=random.choice(['微信', '支付宝', '银行转账', '现金']),
                    project_fee=project_fee,
                    project_details=f"项目包括{service_type}服务，语种为{language}，共{customer_count}",
                    cost_details=f"译员费用: {translator_fee}元，项目费用: {project_fee}元",
                    
                    payment_status=payment_status,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    payment_remarks=f"{'已完成付款' if payment_status == 'paid' else '待付款' if payment_status == 'unpaid' else '部分付款已收到'}",
                    
                    invoice_status=invoice_status,
                    invoice_info=f"发票抬头：{customer.name}" if invoice_status != 'not_required' else None,
                    contract_number=f"CT-{order_date.strftime('%Y%m')}-{random.randint(1000, 9999)}",
                    contract_info=f"{customer.name}与公司签订的{service_type}服务合同，金额{total_amount}元" if random.random() > 0.3 else None,
                    
                    delivery_address=f"{random.choice(['北京市', '上海市', '广州市', '深圳市', '杭州市', '成都市', '武汉市'])}某区某街某号" if random.random() > 0.5 else None,
                    remarks=random.choice([
                        f"客户要求{service_time}前交付",
                        "请保持原文格式",
                        "需要翻译资质证明",
                        "客户要求保密处理",
                        f"项目负责人：{random.choice(['张三', '李四', '王五', '赵六'])}",
                        None
                    ]),
                    
                    tenant=tenant
                )
                
                created_orders.append(order)
                
                # 创建订单历史记录
                if user:
                    OrderHistory.create_history_record(
                        order=order,
                        user=user,
                        change_details={'action': 'create', 'message': '系统批量创建订单'}
                    )
                
            except Exception as e:
                logger.error(f"创建订单 #{i+1} 时出错: {e}", exc_info=True)
    
    logger.info(f"成功创建 {len(created_orders)} 个订单")
    return created_orders


if __name__ == "__main__":
    # 参数设置
    TENANT_ID = 17  # 指定租户ID
    ORDER_COUNT = 300  # 订单数量
    
    try:
        create_orders_for_past_year(TENANT_ID, ORDER_COUNT)
        print(f"成功为租户ID {TENANT_ID} 创建了 {ORDER_COUNT} 条近一年的订单数据。")
    except Exception as e:
        print(f"创建订单时出错: {e}")
        logger.error(f"创建订单时出错: {e}", exc_info=True) 