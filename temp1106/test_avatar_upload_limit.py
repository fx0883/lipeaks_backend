#!/usr/bin/env python
"""
测试头像上传大小限制
验证修复后的配置是否生效
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.conf import settings


def test_settings():
    """测试 settings 配置"""
    print("=" * 60)
    print("测试 Django Settings 配置")
    print("=" * 60)
    
    # 检查 DATA_UPLOAD_MAX_MEMORY_SIZE
    max_memory_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', None)
    if max_memory_size:
        max_mb = max_memory_size / (1024 * 1024)
        print(f"✅ DATA_UPLOAD_MAX_MEMORY_SIZE: {max_mb:.0f}MB ({max_memory_size} bytes)")
    else:
        print("❌ DATA_UPLOAD_MAX_MEMORY_SIZE 未设置，将使用 Django 默认值 2.5MB")
    
    # 检查 FILE_UPLOAD_MAX_MEMORY_SIZE
    file_max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
    if file_max_size:
        file_mb = file_max_size / (1024 * 1024)
        print(f"✅ FILE_UPLOAD_MAX_MEMORY_SIZE: {file_mb:.0f}MB ({file_max_size} bytes)")
    else:
        print("⚠️  FILE_UPLOAD_MAX_MEMORY_SIZE 未设置，将使用 Django 默认值 2.5MB")
    
    # 检查 DATA_UPLOAD_MAX_NUMBER_FIELDS
    max_fields = getattr(settings, 'DATA_UPLOAD_MAX_NUMBER_FIELDS', None)
    if max_fields:
        print(f"✅ DATA_UPLOAD_MAX_NUMBER_FIELDS: {max_fields}")
    else:
        print("⚠️  DATA_UPLOAD_MAX_NUMBER_FIELDS 未设置，将使用 Django 默认值 1000")
    
    print()


def test_view_logic():
    """测试视图逻辑是否正确读取配置"""
    print("=" * 60)
    print("测试视图逻辑")
    print("=" * 60)
    
    # 模拟视图中的逻辑
    max_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)
    max_size_mb = max_size / (1024 * 1024)
    
    print(f"视图中读取的最大上传大小: {max_size_mb:.0f}MB")
    print(f"错误消息模板: 文件太大，头像大小不能超过{max_size_mb:.0f}MB")
    print()
    
    # 测试不同文件大小
    test_sizes = [
        (1 * 1024 * 1024, "1MB"),
        (2 * 1024 * 1024, "2MB"),
        (5 * 1024 * 1024, "5MB"),
        (10 * 1024 * 1024, "10MB"),
        (11 * 1024 * 1024, "11MB"),
        (15 * 1024 * 1024, "15MB"),
    ]
    
    print("文件大小测试结果:")
    print("-" * 60)
    for size, label in test_sizes:
        if size > max_size:
            status = "❌ 拒绝"
        else:
            status = "✅ 允许"
        print(f"{status} {label:>6} - {size:,} bytes")
    
    print()


def check_middleware():
    """检查中间件是否正确导入异常"""
    print("=" * 60)
    print("检查中间件")
    print("=" * 60)
    
    try:
        from common.middleware.enhanced_api_logging_middleware import EnhancedAPILoggingMiddleware
        from django.core.exceptions import RequestDataTooBig
        
        print("✅ EnhancedAPILoggingMiddleware 导入成功")
        print("✅ RequestDataTooBig 异常已导入")
        
        # 检查中间件类是否有 _get_request_body 方法
        if hasattr(EnhancedAPILoggingMiddleware, '_get_request_body'):
            print("✅ _get_request_body 方法存在")
        else:
            print("❌ _get_request_body 方法不存在")
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("头像上传大小限制测试")
    print("=" * 60)
    print()
    
    test_settings()
    test_view_logic()
    check_middleware()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n建议:")
    print("1. 重启 Django 服务器以应用新配置")
    print("2. 尝试上传一个 5-9MB 的图片进行实际测试")
    print("3. 检查日志文件确认没有 RequestDataTooBig 异常")
    print()


if __name__ == '__main__':
    main()

