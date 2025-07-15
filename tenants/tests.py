from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from tenants.models import Tenant, TenantQuota

class TenantPermissionTestCase(TestCase):
    """
    租户API权限测试
    """
    def setUp(self):
        """
        测试准备
        """
        # 创建超级管理员
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='password123',
            is_super_admin=True
        )
        
        # 创建租户
        self.tenant = Tenant.objects.create(
            name='测试租户',
            code='test',
            status='active',
            contact_name='测试联系人',
            contact_email='contact@example.com'
        )
        
        # 创建租户管理员
        self.tenant_admin = User.objects.create_user(
            username='tenantadmin',
            email='tenantadmin@example.com',
            password='password123',
            is_admin=True,
            tenant=self.tenant
        )
        
        # 创建普通用户
        self.normal_user = User.objects.create_user(
            username='normaluser',
            email='normaluser@example.com',
            password='password123',
            is_admin=False,
            tenant=self.tenant
        )
        
        # 创建API客户端
        self.client = APIClient()
    
    def test_tenant_list_permissions(self):
        """
        测试租户列表API权限
        """
        url = reverse('tenants:tenant-list-create')
        
        # 未登录用户 - 应该返回401
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 普通用户 - 应该返回403
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 租户管理员 - 应该返回403
        self.client.force_authenticate(user=self.tenant_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 超级管理员 - 应该返回200
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_tenant_create_permissions(self):
        """
        测试创建租户API权限
        """
        url = reverse('tenants:tenant-list-create')
        data = {
            'name': '新租户',
            'code': 'new',
            'contact_name': '联系人',
            'contact_email': 'new@example.com',
            'contact_phone': '13800138000',
            'status': 'active'
        }
        
        # 未登录用户 - 应该返回401
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 普通用户 - 应该返回403
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 租户管理员 - 应该返回403
        self.client.force_authenticate(user=self.tenant_admin)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 超级管理员 - 应该返回201
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_tenant_quota_usage_permissions(self):
        """
        测试租户配额使用情况API权限
        """
        url = reverse('tenants:tenant-quota-usage', args=[self.tenant.id])
        
        # 未登录用户 - 应该返回401
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 普通用户 - 应该返回403
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 租户管理员 - 应该返回200（只能访问自己的租户）
        self.client.force_authenticate(user=self.tenant_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 创建另一个租户
        other_tenant = Tenant.objects.create(
            name='其他租户',
            code='other',
            status='active',
            contact_name='其他联系人',
            contact_email='other@example.com'
        )
        
        # 租户管理员访问其他租户 - 应该返回403
        other_url = reverse('tenants:tenant-quota-usage', args=[other_tenant.id])
        self.client.force_authenticate(user=self.tenant_admin)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 超级管理员访问任何租户 - 应该返回200
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
