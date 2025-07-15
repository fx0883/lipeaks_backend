"""
RBAC API测试
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from rbac.models import Permission, Role, RolePermission, UserRole
from users.models import User

class RBACPermissionAPITest(TestCase):
    """权限API测试"""
    
    def setUp(self):
        """测试准备"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username="test_admin",
            email="test@example.com",
            password="password123",
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.is_super_admin = True
        self.user.save()
        
        # 创建测试权限
        self.permission = Permission.objects.create(
            code="test:view",
            name="测试查看",
            description="测试权限描述",
            category="测试分类",
            is_system=True
        )
        
        # 创建API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_list_permissions(self):
        """测试获取权限列表"""
        url = reverse('rbac:permission-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], self.permission.code)
    
    def test_create_permission(self):
        """测试创建权限"""
        url = reverse('rbac:permission-list')
        data = {
            'code': 'test:create',
            'name': '测试创建',
            'description': '测试创建权限',
            'category': '测试分类'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Permission.objects.count(), 2)
        self.assertTrue(Permission.objects.filter(code='test:create').exists())
    
    def test_retrieve_permission(self):
        """测试获取权限详情"""
        url = reverse('rbac:permission-detail', args=[self.permission.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], self.permission.code)
    
    def test_update_permission(self):
        """测试更新权限"""
        url = reverse('rbac:permission-detail', args=[self.permission.id])
        data = {
            'code': 'test:view',
            'name': '测试查看(修改)',
            'description': '测试权限描述(修改)',
            'category': '测试分类'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.permission.refresh_from_db()
        self.assertEqual(self.permission.name, '测试查看(修改)')
        self.assertEqual(self.permission.description, '测试权限描述(修改)')
    
    def test_delete_permission(self):
        """测试删除权限"""
        # 创建一个非系统权限
        permission = Permission.objects.create(
            code="test:delete",
            name="测试删除",
            category="测试分类",
            is_system=False
        )
        
        url = reverse('rbac:permission-detail', args=[permission.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Permission.objects.filter(id=permission.id).exists())
    
    def test_cannot_delete_system_permission(self):
        """测试不能删除系统权限"""
        url = reverse('rbac:permission-detail', args=[self.permission.id])
        response = self.client.delete(url)
        
        # 应该返回禁止操作错误
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Permission.objects.filter(id=self.permission.id).exists())


class RBACRoleAPITest(TestCase):
    """角色API测试"""
    
    def setUp(self):
        """测试准备"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username="test_admin",
            email="test@example.com",
            password="password123",
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.is_super_admin = True
        self.user.save()
        
        # 创建测试权限
        self.permission = Permission.objects.create(
            code="test:view",
            name="测试查看",
            description="测试权限描述",
            category="测试分类",
            is_system=True
        )
        
        # 创建测试角色
        self.role = Role.objects.create(
            name="测试角色",
            code="test_role",
            description="测试角色描述",
            is_system=False
        )
        
        # 分配权限到角色
        RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )
        
        # 创建API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_list_roles(self):
        """测试获取角色列表"""
        url = reverse('rbac:role-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], self.role.code)
    
    def test_create_role(self):
        """测试创建角色"""
        url = reverse('rbac:role-list')
        data = {
            'name': '新测试角色',
            'code': 'new_test_role',
            'description': '新测试角色描述'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.count(), 2)
        self.assertTrue(Role.objects.filter(code='new_test_role').exists())
    
    def test_retrieve_role(self):
        """测试获取角色详情"""
        url = reverse('rbac:role-detail', args=[self.role.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], self.role.code)
        self.assertTrue('permissions' in response.data)
        self.assertEqual(len(response.data['permissions']), 1)
        self.assertEqual(response.data['permissions'][0]['code'], self.permission.code)
    
    def test_update_role(self):
        """测试更新角色"""
        url = reverse('rbac:role-detail', args=[self.role.id])
        data = {
            'name': '测试角色(修改)',
            'code': 'test_role',
            'description': '测试角色描述(修改)'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.role.refresh_from_db()
        self.assertEqual(self.role.name, '测试角色(修改)')
        self.assertEqual(self.role.description, '测试角色描述(修改)')
    
    def test_delete_role(self):
        """测试删除角色"""
        url = reverse('rbac:role-detail', args=[self.role.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Role.objects.filter(id=self.role.id).exists())
    
    def test_role_permissions(self):
        """测试角色权限API"""
        # 获取角色权限
        url = reverse('rbac:role-permissions', args=[self.role.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], self.permission.code)
        
        # 创建第二个测试权限
        permission2 = Permission.objects.create(
            code="test:edit",
            name="测试编辑",
            category="测试分类"
        )
        
        # 分配权限到角色
        url = reverse('rbac:role-add-permissions', args=[self.role.id])
        data = {'permission_ids': [permission2.id]}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.role.permissions.filter(id=permission2.id).exists())
        self.assertEqual(self.role.permissions.count(), 2)
        
        # 移除角色权限
        url = reverse('rbac:role-remove-permission', args=[self.role.id, permission2.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.role.permissions.filter(id=permission2.id).exists())
        self.assertEqual(self.role.permissions.count(), 1) 