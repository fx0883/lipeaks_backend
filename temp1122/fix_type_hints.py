#!/usr/bin/env python3
"""
修复licenses/serializers.py中的类型提示语法错误
"""
import re

file_path = '/Users/fengxuan/Documents/Github/lipeaks_backend/licenses/serializers.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复：serializers.XXX()() -> serializers.XXX()
content = re.sub(r'@extend_schema_field\(serializers\.(\w+)\((.*?)\)\(\)\)', 
                 r'@extend_schema_field(serializers.\1(\2))', 
                 content)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已修复类型提示语法错误")
