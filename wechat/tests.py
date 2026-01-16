"""
微信小程序登录测试
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from wechat.models import WechatUser
from wechat.serializers import WechatLoginSerializer
from users.models import Member
from tenants.models import Tenant


class WechatUserModelTest(TestCase):
    """微信用户模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="test_tenant"
        )
        self.member = Member.objects.create(
            username="test_member",
            email="test@example.com",
            tenant=self.tenant
        )
    
    def test_create_wechat_user(self):
        """测试创建微信用户"""
        wechat_user = WechatUser.objects.create(
            member=self.member,
            openid="test_openid_12345678",
            unionid="test_unionid_12345678",
            session_key="test_session_key"
        )
        
        self.assertEqual(wechat_user.member, self.member)
        self.assertEqual(wechat_user.openid, "test_openid_12345678")
        self.assertIsNotNone(wechat_user.created_at)
    
    def test_wechat_user_str(self):
        """测试微信用户字符串表示"""
        wechat_user = WechatUser.objects.create(
            member=self.member,
            openid="test_openid_12345678",
            nickname="测试用户"
        )
        
        self.assertIn("测试用户", str(wechat_user))
    
    def test_update_session_key(self):
        """测试更新会话密钥"""
        wechat_user = WechatUser.objects.create(
            member=self.member,
            openid="test_openid_12345678",
            session_key="old_key"
        )
        
        wechat_user.update_session_key("new_key")
        wechat_user.refresh_from_db()
        
        self.assertEqual(wechat_user.session_key, "new_key")


class WechatLoginSerializerTest(TestCase):
    """微信登录序列化器测试"""
    
    def test_missing_code(self):
        """测试缺少 code 参数"""
        serializer = WechatLoginSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)
    
    def test_invalid_code_format(self):
        """测试无效的 code 格式"""
        serializer = WechatLoginSerializer(data={'code': 'abc'})
        self.assertFalse(serializer.is_valid())
    
    @patch('wechat.serializers.requests.get')
    def test_call_code2session_success(self, mock_get):
        """测试 code2Session API 调用成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'openid': 'test_openid_12345678',
            'session_key': 'test_session_key',
            'unionid': 'test_unionid'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with patch('wechat.serializers.settings') as mock_settings:
            mock_settings.WECHAT_APPID = 'test_appid'
            mock_settings.WECHAT_SECRET = 'test_secret'
            
            serializer = WechatLoginSerializer(data={'code': 'valid_code_12345'})
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['openid'], 'test_openid_12345678')
    
    @patch('wechat.serializers.requests.get')
    def test_call_code2session_invalid_code(self, mock_get):
        """测试 code2Session API 返回错误码"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'errcode': 40029,
            'errmsg': 'invalid code'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with patch('wechat.serializers.settings') as mock_settings:
            mock_settings.WECHAT_APPID = 'test_appid'
            mock_settings.WECHAT_SECRET = 'test_secret'
            
            serializer = WechatLoginSerializer(data={'code': 'invalid_code_12345'})
            self.assertFalse(serializer.is_valid())


class WechatLoginViewTest(APITestCase):
    """微信登录视图测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="test_tenant"
        )
        self.login_url = reverse('wechat:wechat-login')
    
    def test_missing_code(self):
        """测试缺少 code 参数返回 400"""
        response = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('wechat.serializers.requests.get')
    def test_new_user_login(self, mock_get):
        """测试新用户首次登录自动创建账号"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'openid': 'new_user_openid_123',
            'session_key': 'test_session_key',
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with patch('wechat.serializers.settings') as mock_settings:
            mock_settings.WECHAT_APPID = 'test_appid'
            mock_settings.WECHAT_SECRET = 'test_secret'
            
            response = self.client.post(
                self.login_url,
                {'code': 'valid_code_12345', 'tenant_id': self.tenant.id},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['is_new_user'])
        self.assertIn('token', response.data['data'])
        
        # 验证创建了 WechatUser 和 Member
        wechat_user = WechatUser.objects.filter(openid='new_user_openid_123').first()
        self.assertIsNotNone(wechat_user)
        self.assertIsNotNone(wechat_user.member)
    
    @patch('wechat.serializers.requests.get')
    def test_existing_user_login(self, mock_get):
        """测试已绑定用户登录"""
        # 先创建已绑定的用户
        member = Member.objects.create(
            username="existing_member",
            email="existing@example.com",
            tenant=self.tenant
        )
        WechatUser.objects.create(
            member=member,
            openid='existing_user_openid',
            session_key='old_session_key'
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'openid': 'existing_user_openid',
            'session_key': 'new_session_key',
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with patch('wechat.serializers.settings') as mock_settings:
            mock_settings.WECHAT_APPID = 'test_appid'
            mock_settings.WECHAT_SECRET = 'test_secret'
            
            response = self.client.post(
                self.login_url,
                {'code': 'valid_code_12345'},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(response.data['data']['is_new_user'])
        
        # 验证 session_key 已更新
        wechat_user = WechatUser.objects.get(openid='existing_user_openid')
        self.assertEqual(wechat_user.session_key, 'new_session_key')
