#!/usr/bin/env python3
"""
直接执行SQL迁移脚本
绕过Django的迁移系统和parler问题
"""
import os
import sys
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
import MySQLdb
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'passwd': os.getenv('DB_PASSWORD', 'password'),
    'db': os.getenv('DB_NAME', 'multi_tenant_db_dev'),
    'charset': 'utf8mb4'
}

def execute_migration():
    """执行迁移SQL"""
    print("=" * 60)
    print("开始执行Article模型迁移")
    print("=" * 60)
    print("")
    
    try:
        # 连接数据库
        print(f"连接数据库: {DB_CONFIG['db']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        conn = MySQLdb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 步骤1: 检查是否已经迁移
        print("\n步骤1: 检查当前表结构...")
        cursor.execute("SHOW COLUMNS FROM cms_article LIKE 'user_id'")
        if cursor.fetchone():
            print("⚠️  user_id字段已存在，可能已经迁移过")
            response = input("是否继续？(y/n): ")
            if response.lower() != 'y':
                print("迁移已取消")
                return
        
        # 步骤2: 添加新字段
        print("\n步骤2: 添加user_id和member_id字段...")
        try:
            cursor.execute("""
                ALTER TABLE cms_article 
                ADD COLUMN user_id INT NULL,
                ADD COLUMN member_id INT NULL
            """)
            print("✅ 新字段添加成功")
        except Exception as e:
            if 'Duplicate column name' in str(e):
                print("⚠️  字段已存在，跳过")
            else:
                raise
        
        # 步骤3: 添加外键约束
        print("\n步骤3: 添加外键约束...")
        try:
            cursor.execute("""
                ALTER TABLE cms_article
                ADD CONSTRAINT cms_article_user_fk 
                    FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE
            """)
            print("✅ user外键约束添加成功")
        except Exception as e:
            if 'Duplicate' in str(e) or 'already exists' in str(e):
                print("⚠️  user外键约束已存在")
            else:
                print(f"⚠️  user外键约束添加失败: {e}")
        
        try:
            cursor.execute("""
                ALTER TABLE cms_article
                ADD CONSTRAINT cms_article_member_fk 
                    FOREIGN KEY (member_id) REFERENCES users_member(id) ON DELETE CASCADE
            """)
            print("✅ member外键约束添加成功")
        except Exception as e:
            if 'Duplicate' in str(e) or 'already exists' in str(e):
                print("⚠️  member外键约束已存在")
            else:
                print(f"⚠️  member外键约束添加失败: {e}")
        
        conn.commit()
        
        # 步骤4: 迁移数据
        print("\n步骤4: 迁移数据...")
        
        # 获取ContentType ID
        cursor.execute("""
            SELECT id FROM django_content_type 
            WHERE app_label='users' AND model='user'
        """)
        user_ct = cursor.fetchone()
        
        cursor.execute("""
            SELECT id FROM django_content_type 
            WHERE app_label='users' AND model='member'
        """)
        member_ct = cursor.fetchone()
        
        if not user_ct or not member_ct:
            print("❌ ContentType未找到，无法迁移")
            return
        
        user_ct_id = user_ct[0]
        member_ct_id = member_ct[0]
        
        # 迁移User作者
        cursor.execute(f"""
            UPDATE cms_article 
            SET user_id = author_object_id 
            WHERE author_content_type_id = {user_ct_id} 
            AND author_object_id IS NOT NULL
            AND user_id IS NULL
        """)
        user_count = cursor.rowcount
        print(f"✅ 迁移了 {user_count} 篇User作者的文章")
        
        # 迁移Member作者
        cursor.execute(f"""
            UPDATE cms_article 
            SET member_id = author_object_id 
            WHERE author_content_type_id = {member_ct_id} 
            AND author_object_id IS NOT NULL
            AND member_id IS NULL
        """)
        member_count = cursor.rowcount
        print(f"✅ 迁移了 {member_count} 篇Member作者的文章")
        
        conn.commit()
        
        # 步骤5: 验证数据
        print("\n步骤5: 验证数据迁移...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) as user_articles,
                SUM(CASE WHEN member_id IS NOT NULL THEN 1 ELSE 0 END) as member_articles,
                SUM(CASE WHEN user_id IS NULL AND member_id IS NULL THEN 1 ELSE 0 END) as no_author,
                SUM(CASE WHEN user_id IS NOT NULL AND member_id IS NOT NULL THEN 1 ELSE 0 END) as both_authors
            FROM cms_article
        """)
        stats = cursor.fetchone()
        
        print(f"总文章数: {stats[0]}")
        print(f"User作者文章: {stats[1]}")
        print(f"Member作者文章: {stats[2]}")
        print(f"无作者文章: {stats[3]}")
        print(f"双作者文章（异常）: {stats[4]}")
        
        if stats[3] > 0 or stats[4] > 0:
            print("⚠️  发现异常数据，请检查！")
            return
        
        # 步骤6: 删除旧字段
        print("\n步骤6: 删除旧字段...")
        try:
            cursor.execute("ALTER TABLE cms_article DROP FOREIGN KEY cms_article_author_content_type_fk")
            print("✅ 删除旧外键约束")
        except Exception as e:
            print(f"⚠️  删除旧外键约束失败（可能不存在）: {e}")
        
        try:
            cursor.execute("""
                ALTER TABLE cms_article
                DROP COLUMN author_content_type_id,
                DROP COLUMN author_object_id
            """)
            print("✅ 删除旧字段")
        except Exception as e:
            print(f"⚠️  删除旧字段失败: {e}")
        
        conn.commit()
        
        # 步骤7: 添加索引
        print("\n步骤7: 添加索引...")
        indexes = [
            ("cms_article_user_idx", "user_id"),
            ("cms_article_member_idx", "member_id"),
            ("cms_article_tenant_user_idx", "tenant_id, user_id"),
            ("cms_article_tenant_member_idx", "tenant_id, member_id"),
        ]
        
        for idx_name, idx_fields in indexes:
            try:
                cursor.execute(f"CREATE INDEX {idx_name} ON cms_article({idx_fields})")
                print(f"✅ 创建索引: {idx_name}")
            except Exception as e:
                if 'Duplicate' in str(e) or 'already exists' in str(e):
                    print(f"⚠️  索引已存在: {idx_name}")
                else:
                    print(f"⚠️  创建索引失败 {idx_name}: {e}")
        
        conn.commit()
        
        # 步骤8: 添加约束
        print("\n步骤8: 添加CHECK约束...")
        try:
            cursor.execute("""
                ALTER TABLE cms_article
                ADD CONSTRAINT article_one_author_required 
                CHECK (
                    (user_id IS NOT NULL AND member_id IS NULL) OR 
                    (user_id IS NULL AND member_id IS NOT NULL)
                )
            """)
            print("✅ CHECK约束添加成功")
        except Exception as e:
            if 'Duplicate' in str(e) or 'already exists' in str(e):
                print("⚠️  约束已存在")
            else:
                print(f"⚠️  约束添加失败: {e}")
        
        conn.commit()
        
        # 步骤9: 标记迁移为已应用
        print("\n步骤9: 标记Django迁移为已应用...")
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('cms', '0008_replace_generic_fk_with_dual_fk', NOW())
        """)
        conn.commit()
        print("✅ Django迁移记录已添加")
        
        print("")
        print("=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
        print("")
        print(f"总计迁移: {user_count + member_count} 篇文章")
        print(f"  - User作者: {user_count} 篇")
        print(f"  - Member作者: {member_count} 篇")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("⚠️  警告: 此脚本将直接修改数据库！")
    print("请确保已经备份数据库！")
    print("")
    response = input("是否继续执行迁移？(yes/no): ")
    
    if response.lower() == 'yes':
        execute_migration()
    else:
        print("迁移已取消")

