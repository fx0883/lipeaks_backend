#!/usr/bin/env python3
"""
添加外键约束
"""
import os
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
import MySQLdb
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'passwd': os.getenv('DB_PASSWORD', 'password'),
    'db': os.getenv('DB_NAME', 'multi_tenant_db_dev'),
    'charset': 'utf8mb4'
}

print("连接数据库...")
conn = MySQLdb.connect(**DB_CONFIG)
cursor = conn.cursor()

print("添加外键约束...")

# 添加user外键
try:
    cursor.execute("""
        ALTER TABLE cms_article
        ADD CONSTRAINT cms_article_user_fk 
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
    """)
    print("✅ user外键约束添加成功")
except Exception as e:
    print(f"⚠️  user外键: {e}")

# 添加member外键
try:
    cursor.execute("""
        ALTER TABLE cms_article
        ADD CONSTRAINT cms_article_member_fk 
            FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE
    """)
    print("✅ member外键约束添加成功")
except Exception as e:
    print(f"⚠️  member外键: {e}")

conn.commit()
cursor.close()
conn.close()

print("✅ 外键约束添加完成！")

