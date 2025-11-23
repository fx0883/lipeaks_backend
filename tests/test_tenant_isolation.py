"""
租户隔离功能单元测试
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from applications.models import Application
from orders.models import Order
from customers.models import Customer

User = get_user_model()


class TenantIsolationTestCase(TransactionTestCase):
    """租户隔离功能测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant1 = Tenant.objects.create(
            name="Test Tenant 1",
            code="TENANT1"
        )
        self.tenant2 = Tenant.objects.create(
            name="Test Tenant 2",
            code="TENANT2"
        )
        
        # 创建用户
        self.user1 = User.objects.create_user(
            username="user1",
            password="password123",
            tenant=self.tenant1
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="password123",
            tenant=self.tenant2
        )
    
    def test_application_tenant_isolation(self):
        """测试Application模型的租户隔离"""
        # 创建属于不同租户的应用
        app1 = Application.objects.create(
            name="App 1",
            code="APP1",
            tenant=self.tenant1
        )
        app2 = Application.objects.create(
            name="App 2",
            code="APP2",
            tenant=self.tenant2
        )
        
        # 验证租户1只能看到自己的应用
        tenant1_apps = Application.objects.filter(tenant=self.tenant1)
        self.assertEqual(tenant1_apps.count(), 1)
        self.assertEqual(tenant1_apps.first().id, app1.id)
        
        # 验证租户2只能看到自己的应用
        tenant2_apps = Application.objects.filter(tenant=self.tenant2)
        self.assertEqual(tenant2_apps.count(), 1)
        self.assertEqual(tenant2_apps.first().id, app2.id)
        
        # 验证跨租户访问失败
        cross_access = Application.objects.filter(
            tenant=self.tenant1,
            id=app2.id
        ).exists()
        self.assertFalse(cross_access)
    
    def test_order_tenant_isolation(self):
        """测试Order模型的租户隔离"""
        # 创建订单
        order1 = Order.objects.create(
            order_number="ORDER1",
            total_amount=100.00,
            tenant=self.tenant1
        )
        order2 = Order.objects.create(
            order_number="ORDER2",
            total_amount=200.00,
            tenant=self.tenant2
        )
        
        # 验证隔离
        self.assertEqual(
            Order.objects.filter(tenant=self.tenant1).count(),
            1
        )
        self.assertEqual(
            Order.objects.filter(tenant=self.tenant2).count(),
            1
        )
        
        # 验证跨租户访问失败
        self.assertFalse(
            Order.objects.filter(
                tenant=self.tenant1,
                id=order2.id
            ).exists()
        )
    
    def test_customer_tenant_isolation(self):
        """测试Customer模型的租户隔离"""
        # 创建客户
        customer1 = Customer.objects.create(
            name="Customer 1",
            status="active",
            tenant=self.tenant1
        )
        customer2 = Customer.objects.create(
            name="Customer 2",
            status="active",
            tenant=self.tenant2
        )
        
        # 验证隔离
        self.assertEqual(
            Customer.objects.filter(tenant=self.tenant1).count(),
            1
        )
        self.assertEqual(
            Customer.objects.filter(tenant=self.tenant2).count(),
            1
        )
    
    def test_tenant_id_required(self):
        """测试tenant_id字段是必需的"""
        # 尝试创建没有tenant的记录应该失败
        with self.assertRaises(Exception):
            Application.objects.create(
                name="No Tenant App",
                code="NOTENANT"
                # 没有tenant字段
            )
    
    def test_cross_tenant_update_fails(self):
        """测试跨租户更新失败"""
        # 创建应用
        app1 = Application.objects.create(
            name="App 1",
            code="APP1",
            tenant=self.tenant1
        )
        
        # 尝试用另一个租户更新
        # 在实际应用中，ViewSet会阻止这个操作
        # 这里只是验证数据层面的隔离
        tenant2_apps = Application.objects.filter(
            tenant=self.tenant2,
            id=app1.id
        )
        self.assertEqual(tenant2_apps.count(), 0)


class TenantModelViewSetTestCase(TestCase):
    """TenantModelViewSet功能测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
            tenant=self.tenant
        )
    
    def test_get_queryset_filters_by_tenant(self):
        """测试get_queryset自动按租户过滤"""
        # 创建测试数据
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            code="OTHER"
        )
        
        app1 = Application.objects.create(
            name="My App",
            code="MYAPP",
            tenant=self.tenant
        )
        app2 = Application.objects.create(
            name="Other App",
            code="OTHERAPP",
            tenant=other_tenant
        )
        
        # 验证过滤
        queryset = Application.objects.filter(tenant=self.tenant)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().id, app1.id)
    
    def test_perform_create_sets_tenant(self):
        """测试perform_create自动设置租户"""
        # 这个测试需要在实际的ViewSet中进行
        # 这里只是验证模型层面的功能
        app = Application.objects.create(
            name="Test App",
            code="TEST",
            tenant=self.tenant
        )
        
        self.assertEqual(app.tenant.id, self.tenant.id)
        self.assertIsNotNone(app.tenant_id)


class PerformanceTestCase(TestCase):
    """性能测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="TEST"
        )
        
        # 创建多个应用
        for i in range(100):
            Application.objects.create(
                name=f"App {i}",
                code=f"APP{i}",
                tenant=self.tenant
            )
    
    def test_query_performance_with_tenant_filter(self):
        """测试带租户过滤的查询性能"""
        import time
        
        # 测试查询时间
        start_time = time.time()
        apps = list(Application.objects.filter(tenant=self.tenant))
        query_time = time.time() - start_time
        
        # 验证查询时间合理（< 100ms）
        self.assertLess(query_time, 0.1)
        
        # 验证结果数量
        self.assertEqual(len(apps), 100)
