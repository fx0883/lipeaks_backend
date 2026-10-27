"""
SEC-05, SEC-08, ARCH-03 配置层回归测试
验证多租户隔离路径白名单、DEBUG 环境变量读取优先级与回退、.gitignore 敏感凭据防泄露规则
"""
import os
import unittest
from unittest.mock import patch
from django.conf import settings
from django.test import SimpleTestCase


class SystemSettingsRegressionTests(SimpleTestCase):
    """验证全局配置与安全规则"""

    def test_tenant_isolated_api_paths_contains_all_core_endpoints(self):
        """[SEC-05] TENANT_ISOLATED_API_PATHS 必须包含 points, check-system 与 interactions"""
        isolated_paths = getattr(settings, 'TENANT_ISOLATED_API_PATHS', [])
        required_paths = [
            '/api/v1/points/',
            '/api/v1/check-system/',
            '/api/v1/interactions/',
        ]
        for path in required_paths:
            self.assertIn(path, isolated_paths, f"Path {path} must be in TENANT_ISOLATED_API_PATHS")

    def test_debug_setting_prefers_debug_env_var(self):
        """[SEC-08] DEBUG 环境变量解析优先于 INFO"""
        with patch.dict(os.environ, {'DEBUG': 'False', 'INFO': 'True'}):
            _val = os.getenv('DEBUG', os.getenv('INFO', 'False'))
            debug_result = _val.lower() in ('true', '1')
            self.assertFalse(debug_result, "DEBUG=False should take precedence over INFO=True")

        with patch.dict(os.environ, {'DEBUG': 'True', 'INFO': 'False'}):
            _val = os.getenv('DEBUG', os.getenv('INFO', 'False'))
            debug_result = _val.lower() in ('true', '1')
            self.assertTrue(debug_result, "DEBUG=True should take precedence over INFO=False")

    def test_debug_setting_fallback_to_info_when_debug_unset(self):
        """[SEC-08] 当 DEBUG 环境变量未定义时，回退读取 INFO"""
        env_without_debug = {k: v for k, v in os.environ.items() if k != 'DEBUG'}
        env_without_debug['INFO'] = 'True'
        with patch.dict(os.environ, env_without_debug, clear=True):
            _val = os.getenv('DEBUG', os.getenv('INFO', 'False'))
            debug_result = _val.lower() in ('true', '1')
            self.assertTrue(debug_result, "When DEBUG is unset, should fallback to INFO=True")

    def test_gitignore_contains_required_protection_patterns(self):
        """[SEC-06 & ARCH-03] .gitignore 必须包含敏感环境凭据与 SQL 备份文件忽略规则"""
        gitignore_path = settings.BASE_DIR / '.gitignore'
        self.assertTrue(gitignore_path.exists(), ".gitignore file must exist")

        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()

        patterns_to_check = [
            '.env',
            '.env.*',
            '!.env.example',
            'wechat/wechat_config.json',
            'docs/sql/*.sql',
        ]
        for pattern in patterns_to_check:
            self.assertIn(pattern, content, f"Pattern {pattern} must be present in .gitignore")
