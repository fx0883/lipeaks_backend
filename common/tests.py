from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User
from common.models import Config
import json

class AdminRoutesAPITest(APITestCase):
    """
    管理员菜单路由API测试
    """
    
    def setUp(self):
        """
        测试前准备
        """
        # 创建超级管理员用户
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='password123',
            is_super_admin=True,
            is_admin=True,
            is_staff=True
        )
        
        # 创建普通用户
        self.normal_user = User.objects.create_user(
            username='normaluser',
            email='normaluser@example.com',
            password='password123'
        )
        
        # 创建超级管理员菜单配置
        self.menu_config = Config.objects.create(
            name='超级管理员菜单配置',
            key='super_admin_menu',
            type='menu',
            value=[
                {
                    "path": "/system",
                    "name": "System",
                    "component": "Layout",
                    "redirect": "/system/config",
                    "meta": {
                        "icon": "ep:setting",
                        "title": "系统设置",
                        "rank": 10,
                        "roles": ["admin"]
                    },
                    "children": [
                        {
                            "path": "config",
                            "name": "SystemConfig",
                            "component": "/src/views/system/config/index",
                            "meta": {
                                "title": "系统配置",
                                "roles": ["admin"]
                            }
                        }
                    ]
                }
            ],
            description='超级管理员的菜单配置，包含系统所有功能模块的菜单项'
        )
        
        # 创建API客户端
        self.client = APIClient()
    
    def test_super_admin_routes(self):
        """
        测试超级管理员获取菜单路由
        """
        # 登录超级管理员
        self.client.force_authenticate(user=self.super_admin)
        
        # 请求路由API
        url = reverse('common:admin-routes')
        response = self.client.get(url)
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查响应内容
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], 2000)
        self.assertEqual(response.data['message'], '获取路由成功')
        
        # 检查返回的菜单数据
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['path'], '/system')
        self.assertEqual(response.data['data'][0]['name'], 'System')
        self.assertEqual(len(response.data['data'][0]['children']), 1)
    
    def test_normal_user_routes(self):
        """
        测试普通用户获取菜单路由
        """
        # 登录普通用户
        self.client.force_authenticate(user=self.normal_user)
        
        # 请求路由API
        url = reverse('common:admin-routes')
        response = self.client.get(url)
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查响应内容
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], 2000)
        self.assertEqual(response.data['message'], '获取路由成功')
        
        # 检查返回的菜单数据（应为空数组）
        self.assertEqual(len(response.data['data']), 0)
    
    def test_unauthenticated_routes(self):
        """
        测试未认证用户获取菜单路由
        """
        # 不进行身份验证
        
        # 请求路由API
        url = reverse('common:admin-routes')
        response = self.client.get(url)
        
        # 检查响应状态码（应为401未授权）
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
