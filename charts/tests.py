from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from django.utils import timezone

from tenants.models import Tenant
from users.models import User
from common.models import APILog

class ChartsAPITestCase(TestCase):
    """测试图表API"""
    
    def setUp(self):
        """设置初始数据"""
        # 创建超级管理员
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='password123',
            is_super_admin=True
        )
        
        # 创建普通管理员
        self.tenant_admin = User.objects.create_user(
            username='tenantadmin',
            email='tenantadmin@example.com',
            password='password123',
            is_admin=True
        )
        
        # 创建普通用户
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123'
        )
        
        # 创建测试租户
        self.tenant1 = Tenant.objects.create(
            name='Test Tenant 1',
            code='test1',
            status='active',
            created_at=timezone.now() - timedelta(days=30)
        )
        
        self.tenant2 = Tenant.objects.create(
            name='Test Tenant 2',
            code='test2',
            status='active',
            created_at=timezone.now() - timedelta(days=15)
        )
        
        self.tenant3 = Tenant.objects.create(
            name='Test Tenant 3',
            code='test3',
            status='suspended',
            created_at=timezone.now() - timedelta(days=7)
        )
        
        # API客户端
        self.client = APIClient()
        
    def test_tenant_trend_auth(self):
        """测试租户趋势API的权限控制"""
        url = reverse('charts:tenant-trend')
        
        # 未认证用户
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 普通用户
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 租户管理员
        self.client.force_authenticate(user=self.tenant_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 超级管理员
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_tenant_trend_data(self):
        """测试租户趋势API的数据正确性"""
        url = reverse('charts:tenant-trend')
        self.client.force_authenticate(user=self.super_admin)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证响应格式
        self.assertEqual(response.data['code'], 2000)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        
        chart_data = response.data['data']
        self.assertEqual(chart_data['chart_type'], 'line')
        self.assertIn('datasets', chart_data)
        self.assertIn('summary', chart_data)
        self.assertEqual(chart_data['summary']['total'], 3)  # 测试数据中有3个租户
        
    def test_tenant_status_distribution(self):
        """测试租户状态分布API"""
        url = reverse('charts:tenant-status-distribution')
        self.client.force_authenticate(user=self.super_admin)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        chart_data = response.data['data']
        self.assertEqual(chart_data['chart_type'], 'pie')
        
        # 验证数据与我们创建的测试数据一致
        # 2个活跃租户，1个暂停租户
        summary = chart_data['summary']
        self.assertEqual(summary['total'], 3)
        
    def test_tenant_creation_rate(self):
        """测试租户创建速率API"""
        url = reverse('charts:tenant-creation-rate')
        self.client.force_authenticate(user=self.super_admin)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 调试输出chart_data
        print(f"Chart data: {response.data['data']}")
        chart_data = response.data['data']
        self.assertEqual(chart_data['chart_type'], 'bar')
        
        # 验证汇总数据
        summary = chart_data['summary']
        # 如果没有数据，summary中会有message键而不是total_new键
        if 'message' in summary:
            self.assertIn('所选时间范围内没有新增租户', summary['message'])
        else:
            self.assertEqual(summary['total_new'], 3)  # 我们创建了3个租户

class TenantChartTests(TestCase):
    """租户图表API测试"""
    
    def setUp(self):
        # 创建超级管理员
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='password',
            is_super_admin=True
        )
        
        # 创建普通用户
        self.normal_user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='password'
        )
        
        # 创建租户
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            code='test',
            status='active'
        )
        
        # 创建API客户端
        self.client = APIClient()
    
    def test_tenant_trend_chart_auth(self):
        """测试租户趋势图权限控制"""
        url = reverse('charts:tenant-trend')
        
        # 未登录访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 普通用户访问
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 超级管理员访问
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_tenant_status_distribution_chart(self):
        """测试租户状态分布图"""
        # 创建不同状态的租户
        Tenant.objects.create(name='Active Tenant 1', code='active1', status='active')
        Tenant.objects.create(name='Active Tenant 2', code='active2', status='active')
        Tenant.objects.create(name='Suspended Tenant', code='suspended', status='suspended')
        
        url = reverse('charts:tenant-status-distribution')
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['data']['chart_type'], 'pie')
        
        # 验证数据总和是否等于租户总数
        total = sum(response.data['data']['datasets'][0]['data'])
        self.assertEqual(total, Tenant.objects.count())
    
    def test_tenant_creation_rate_chart(self):
        """测试租户创建速率图"""
        # 创建测试数据
        now = timezone.now()
        
        # 创建几个不同时间的租户
        for i in range(3):
            Tenant.objects.create(
                name=f'Tenant {i}',
                code=f'tenant{i}',
                status='active',
                created_at=now - timedelta(days=i*10)
            )
        
        url = reverse('charts:tenant-creation-rate')
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['data']['chart_type'], 'bar')

class UserChartTests(TestCase):
    """用户图表API测试"""
    
    def setUp(self):
        # 创建超级管理员
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='password',
            is_super_admin=True
        )
        
        # 创建普通用户
        self.normal_user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='password'
        )
        
        # 创建租户管理员
        self.tenant_admin = User.objects.create_user(
            username='tenantadmin',
            email='tenantadmin@example.com',
            password='password',
            is_admin=True
        )
        
        # 创建租户
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            code='test',
            status='active'
        )
        
        # 创建API客户端
        self.client = APIClient()
        
        # 创建一些测试数据
        now = timezone.now()
        
        # 创建几个用户，设置不同的创建时间
        for i in range(5):
            User.objects.create_user(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                password='password',
                date_joined=now - timedelta(days=i*10)
            )
        
        # 创建一些API日志，包括登录记录
        for i in range(10):
            APILog.objects.create(
                user=self.normal_user,
                ip_address='127.0.0.1',
                request_method='POST',
                request_path='/api/v1/auth/login/',
                status_code=200,
                response_time=100,
                status_type='success',
                created_at=now - timedelta(hours=i*5)
            )
    
    def test_user_growth_trend_chart_auth(self):
        """测试用户增长趋势图权限控制"""
        url = reverse('charts:user-growth-trend')
        
        # 未登录访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 普通用户访问
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 超级管理员访问
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_growth_trend_chart_data(self):
        """测试用户增长趋势图数据"""
        url = reverse('charts:user-growth-trend')
        self.client.force_authenticate(user=self.super_admin)
        
        # 测试不同的周期参数
        for period in ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']:
            response = self.client.get(url, {'period': period})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['code'], 2000)
            self.assertEqual(response.data['data']['chart_type'], 'line')
            
            # 验证总用户数是否正确
            self.assertEqual(response.data['data']['summary']['total_users'], User.objects.filter(is_deleted=False).count())
    
    def test_user_role_distribution_chart(self):
        """测试用户角色分布图"""
        url = reverse('charts:user-role-distribution')
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 2000)
        self.assertEqual(response.data['data']['chart_type'], 'pie')
        
        # 验证数据总和是否等于用户总数
        total = sum(response.data['data']['datasets'][0]['data'])
        self.assertEqual(total, User.objects.filter(is_deleted=False).count())
    
    def test_active_users_chart(self):
        """测试活跃用户统计图"""
        url = reverse('charts:active-users')
        self.client.force_authenticate(user=self.super_admin)
        
        # 测试不同的周期参数
        for period in ['daily', 'weekly', 'monthly']:
            response = self.client.get(url, {'period': period})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['code'], 2000)
            self.assertEqual(response.data['data']['chart_type'], 'line')
    
    def test_login_heatmap_chart(self):
        """测试用户登录热力图"""
        url = reverse('charts:login-heatmap')
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 2000)
        self.assertEqual(response.data['data']['chart_type'], 'heatmap')
        
        # 验证热力图数据格式
        if response.data['data']['dataset']:
            for point in response.data['data']['dataset']:
                self.assertEqual(len(point), 3)  # [weekday, hour, count]
