#!/usr/bin/env python
"""
测试Application Retrieve API的错误
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from applications.models import Application
from applications.serializers import ApplicationDetailSerializer

# 获取应用实例
app = Application.objects.get(id=1)
print(f"Application: {app.name}")

try:
    # 测试序列化
    serializer = ApplicationDetailSerializer(app)
    print("序列化成功:")
    print(serializer.data)
except Exception as e:
    print(f"序列化失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# 测试各个统计方法
print("\n测试统计方法:")
try:
    print(f"License count: {app.get_license_count()}")
except Exception as e:
    print(f"get_license_count() 失败: {e}")

try:
    print(f"Active license count: {app.get_active_license_count()}")
except Exception as e:
    print(f"get_active_license_count() 失败: {e}")

try:
    print(f"Feedback count: {app.get_feedback_count()}")
except Exception as e:
    print(f"get_feedback_count() 失败: {e}")

try:
    print(f"Open feedback count: {app.get_open_feedback_count()}")
except Exception as e:
    print(f"get_open_feedback_count() 失败: {e}")

try:
    print(f"Article count: {app.get_article_count()}")
except Exception as e:
    print(f"get_article_count() 失败: {e}")
