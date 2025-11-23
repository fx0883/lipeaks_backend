#!/usr/bin/env python3
"""
调试Schema生成问题
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 尝试生成schema
try:
    from drf_spectacular.generators import SchemaGenerator
    generator = SchemaGenerator()
    schema = generator.get_schema()
    print("✅ Schema生成成功!")
    print(f"API标题: {schema.get('info', {}).get('title')}")
    print(f"Paths数量: {len(schema.get('paths', {}))}")
except Exception as e:
    print(f"❌ Schema生成失败:")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    import traceback
    traceback.print_exc()
