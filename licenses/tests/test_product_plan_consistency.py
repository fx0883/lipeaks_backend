"""
测试许可证产品-方案一致性验证
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from licenses.models import SoftwareProduct, LicensePlan, License
from tenants.models import Tenant

User = get_user_model()


class ProductPlanConsistencyModelTest(TestCase):
    """模型层一致性测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建租户
        self.tenant = Tenant.objects.create(
            name="测试租户",
            code="test_tenant"
        )
        
        # 创建产品
        self.product1 = SoftwareProduct.objects.create(
            name="产品A",
            code="PROD_A",
            public_key="test_key_1",
            private_key_hash="hash1"
        )
        
        self.product2 = SoftwareProduct.objects.create(
            name="产品B", 
            code="PROD_B",
            public_key="test_key_2",
            private_key_hash="hash2"
        )
        
        # 为产品A创建方案
        self.plan_a = LicensePlan.objects.create(
            product=self.product1,
            name="产品A专业版",
            code="PLAN_A_PRO",
            plan_type="professional",
            max_machines=5,
            validity_days=365,
            price=999.00
        )
        
        # 为产品B创建方案
        self.plan_b = LicensePlan.objects.create(
            product=self.product2,
            name="产品B基础版",
            code="PLAN_B_BASIC",
            plan_type="basic",
            max_machines=1,
            validity_days=365,
            price=299.00
        )
    
    def test_consistent_product_plan_creation(self):
        """测试一致的产品-方案创建许可证"""
        license_obj = License(
            product=self.product1,
            plan=self.plan_a,  # plan_a属于product1
            tenant=self.tenant,
            license_key="TEST-AAAA-BBBB-CCCC",
            customer_name="张三",
            customer_email="zhang@test.com",
            expires_at="2025-12-31 23:59:59"
        )
        
        # 应该不抛出异常
        try:
            license_obj.clean()
            license_obj.save()
            self.assertTrue(True, "一致的产品-方案应该能正常保存")
        except ValidationError:
            self.fail("一致的产品-方案不应该抛出验证错误")
    
    def test_inconsistent_product_plan_creation(self):
        """测试不一致的产品-方案创建许可证"""
        license_obj = License(
            product=self.product1,
            plan=self.plan_b,  # plan_b属于product2，与product1不一致
            tenant=self.tenant,
            license_key="TEST-AAAA-BBBB-DDDD",
            customer_name="李四",
            customer_email="li@test.com",
            expires_at="2025-12-31 23:59:59"
        )
        
        # 应该抛出验证错误
        with self.assertRaises(ValidationError) as context:
            license_obj.clean()
        
        # 检查错误信息
        errors = context.exception.message_dict
        self.assertIn('product', errors)
        self.assertIn('plan', errors)
        self.assertIn('不一致', str(errors['product'][0]))
    
    def test_auto_set_product_from_plan(self):
        """测试从plan自动设置product"""
        license_obj = License(
            # 不设置product
            plan=self.plan_a,  # plan_a属于product1
            tenant=self.tenant,
            license_key="TEST-AAAA-BBBB-EEEE",
            customer_name="王五",
            customer_email="wang@test.com",
            expires_at="2025-12-31 23:59:59"
        )
        
        # 调用clean应该自动设置product
        license_obj.clean()
        self.assertEqual(license_obj.product, self.product1)
        
        # 保存应该成功
        license_obj.save()
        self.assertEqual(license_obj.product, self.product1)


class ProductPlanConsistencyAPITest(APITestCase):
    """API层一致性测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建超级管理员用户
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_super_admin=True
        )
        
        # 创建租户
        self.tenant = Tenant.objects.create(
            name="测试租户",
            code="test_tenant"
        )
        
        # 创建产品
        self.product1 = SoftwareProduct.objects.create(
            name="产品A",
            code="PROD_A",
            public_key="test_key_1",
            private_key_hash="hash1"
        )
        
        self.product2 = SoftwareProduct.objects.create(
            name="产品B",
            code="PROD_B", 
            public_key="test_key_2",
            private_key_hash="hash2"
        )
        
        # 创建方案
        self.plan_a = LicensePlan.objects.create(
            product=self.product1,
            name="产品A专业版",
            code="PLAN_A_PRO",
            plan_type="professional",
            max_machines=5,
            validity_days=365,
            price=999.00
        )
        
        self.plan_b = LicensePlan.objects.create(
            product=self.product2,
            name="产品B基础版", 
            code="PLAN_B_BASIC",
            plan_type="basic",
            max_machines=1,
            validity_days=365,
            price=299.00
        )
        
        # 登录用户
        self.client.force_authenticate(user=self.user)
    
    def test_create_license_with_consistent_product_plan(self):
        """测试API创建一致的产品-方案许可证"""
        data = {
            'product': self.product1.id,
            'plan': self.plan_a.id,  # plan_a属于product1
            'tenant': self.tenant.id,
            'customer_info': {
                'name': '张三',
                'email': 'zhang@test.com'
            },
            'max_activations': 5,
            'validity_days': 365
        }
        
        response = self.client.post(
            '/api/v1/licenses/admin/licenses/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
    
    def test_create_license_with_inconsistent_product_plan(self):
        """测试API创建不一致的产品-方案许可证"""
        data = {
            'product': self.product1.id,
            'plan': self.plan_b.id,  # plan_b属于product2，与product1不一致
            'tenant': self.tenant.id,
            'customer_info': {
                'name': '李四',
                'email': 'li@test.com'
            },
            'max_activations': 5,
            'validity_days': 365
        }
        
        response = self.client.post(
            '/api/v1/licenses/admin/licenses/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('plan', response.data['data'])
        self.assertIn('不一致', response.data['data']['plan'][0])
    
    def test_create_license_with_plan_only(self):
        """测试只提供plan的情况，应该自动设置product"""
        data = {
            # 不提供product
            'plan': self.plan_a.id,
            'tenant': self.tenant.id,
            'customer_info': {
                'name': '王五',
                'email': 'wang@test.com'
            },
            'max_activations': 5,
            'validity_days': 365
        }
        
        response = self.client.post(
            '/api/v1/licenses/admin/licenses/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        # 验证product被自动设置为plan_a对应的product1
        self.assertEqual(response.data['data']['product'], self.product1.id)
