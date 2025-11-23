#!/usr/bin/env python3
"""
执行SQL migrations脚本
绕过django-parler的兼容性问题
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def execute_sql_file(filename):
    """执行SQL文件"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    print(f"\n{'='*60}")
    print(f"执行: {filename}")
    print('='*60)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    with connection.cursor() as cursor:
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
                
            try:
                print(f"\n[{i}/{len(statements)}] 执行SQL...")
                # 打印SQL的前100个字符
                preview = statement[:100].replace('\n', ' ')
                print(f"   {preview}...")
                
                cursor.execute(statement)
                
                # 如果是SELECT语句，打印结果
                if statement.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    for row in result:
                        print(f"   ✅ {row}")
                else:
                    print(f"   ✅ 成功")
                    
            except Exception as e:
                # 忽略"列已存在"和"索引已存在"的错误
                error_msg = str(e).lower()
                if 'duplicate column' in error_msg or 'already exists' in error_msg:
                    print(f"   ⚠️  跳过（已存在）: {e}")
                else:
                    print(f"   ❌ 失败: {e}")
                    return False
    
    return True

def main():
    print("\n" + "="*60)
    print("BaseModel字段SQL Migration执行脚本")
    print("="*60)
    
    # 执行CMS SQL
    success_cms = execute_sql_file('cms_add_basemodel_fields.sql')
    
    # 执行Common SQL
    success_common = execute_sql_file('common_add_basemodel_fields.sql')
    
    print("\n" + "="*60)
    if success_cms and success_common:
        print("✅ 所有SQL执行成功！")
        print("="*60)
        print("\n下一步：标记migrations为已执行")
        print("python3 manage.py migrate --fake cms")
        print("python3 manage.py migrate --fake common")
        return 0
    else:
        print("❌ 部分SQL执行失败")
        print("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
