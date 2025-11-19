#!/usr/bin/env python3
"""
修复外键类型不匹配的问题
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def get_column_type(table, column):
    """获取列的数据类型"""
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT DATA_TYPE, COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table}' 
            AND COLUMN_NAME = '{column}'
        """)
        result = cursor.fetchone()
        return result if result else None

def main():
    print("检查字段类型...")
    print("=" * 60)
    
    # 检查 user 表的 id 类型
    user_id_type = get_column_type('user', 'id')
    print(f"user.id 类型: {user_id_type}")
    
    # 检查 member 表的 id 类型
    member_id_type = get_column_type('member', 'id')
    print(f"member.id 类型: {member_id_type}")
    
    # 检查 cms_comment 的字段类型
    comment_user_id = get_column_type('cms_comment', 'user_id')
    comment_member_id = get_column_type('cms_comment', 'member_id')
    print(f"cms_comment.user_id 类型: {comment_user_id}")
    print(f"cms_comment.member_id 类型: {comment_member_id}")
    
    # 检查 cms_operation_log 的字段类型
    log_user_id = get_column_type('cms_operation_log', 'user_id')
    log_member_id = get_column_type('cms_operation_log', 'member_id')
    print(f"cms_operation_log.user_id 类型: {log_user_id}")
    print(f"cms_operation_log.member_id 类型: {log_member_id}")
    
    print("\n" + "=" * 60)
    print("开始修复...")
    
    with connection.cursor() as cursor:
        # 如果 member_id 需要改成 BIGINT
        if member_id_type and 'bigint' in member_id_type[1].lower():
            print("\n修复 cms_comment.member_id 为 BIGINT...")
            try:
                cursor.execute("""
                    ALTER TABLE cms_comment 
                    MODIFY COLUMN member_id BIGINT NULL
                """)
                print("✓ cms_comment.member_id 已修改为 BIGINT")
            except Exception as e:
                print(f"✗ 失败: {e}")
            
            print("\n添加外键约束...")
            try:
                cursor.execute("""
                    ALTER TABLE cms_comment 
                    ADD CONSTRAINT cms_comment_member_fk 
                    FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE
                """)
                print("✓ cms_comment 外键约束已添加")
            except Exception as e:
                print(f"✗ 失败: {e}")
            
            print("\n修复 cms_operation_log.member_id 为 BIGINT...")
            try:
                cursor.execute("""
                    ALTER TABLE cms_operation_log 
                    MODIFY COLUMN member_id BIGINT NULL
                """)
                print("✓ cms_operation_log.member_id 已修改为 BIGINT")
            except Exception as e:
                print(f"✗ 失败: {e}")
            
            print("\n添加外键约束...")
            try:
                cursor.execute("""
                    ALTER TABLE cms_operation_log 
                    ADD CONSTRAINT cms_operation_log_member_fk 
                    FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE
                """)
                print("✓ cms_operation_log 外键约束已添加")
            except Exception as e:
                print(f"✗ 失败: {e}")
        
        # 修改 user_id 允许 NULL（需要先删除外键）
        print("\n修复 cms_comment.user_id 允许 NULL...")
        try:
            # 删除旧外键
            cursor.execute("""
                ALTER TABLE cms_comment 
                DROP FOREIGN KEY cms_comment_user_id_9a882952_fk_user_id
            """)
            print("✓ 旧外键已删除")
        except Exception as e:
            print(f"  跳过删除外键: {e}")
        
        try:
            # 修改字段
            if user_id_type and 'bigint' in user_id_type[1].lower():
                cursor.execute("""
                    ALTER TABLE cms_comment 
                    MODIFY COLUMN user_id BIGINT NULL
                """)
            else:
                cursor.execute("""
                    ALTER TABLE cms_comment 
                    MODIFY COLUMN user_id INT NULL
                """)
            print("✓ user_id 已修改为允许 NULL")
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        try:
            # 重新添加外键
            cursor.execute("""
                ALTER TABLE cms_comment 
                ADD CONSTRAINT cms_comment_user_id_fk 
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            """)
            print("✓ 新外键已添加")
        except Exception as e:
            print(f"  跳过添加外键: {e}")
        
        print("\n修复 cms_operation_log.user_id 允许 NULL...")
        try:
            # 删除旧外键
            cursor.execute("""
                ALTER TABLE cms_operation_log 
                DROP FOREIGN KEY cms_operation_log_user_id_7630e408_fk_user_id
            """)
            print("✓ 旧外键已删除")
        except Exception as e:
            print(f"  跳过删除外键: {e}")
        
        try:
            # 修改字段
            if user_id_type and 'bigint' in user_id_type[1].lower():
                cursor.execute("""
                    ALTER TABLE cms_operation_log 
                    MODIFY COLUMN user_id BIGINT NULL
                """)
            else:
                cursor.execute("""
                    ALTER TABLE cms_operation_log 
                    MODIFY COLUMN user_id INT NULL
                """)
            print("✓ user_id 已修改为允许 NULL")
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        try:
            # 重新添加外键
            cursor.execute("""
                ALTER TABLE cms_operation_log 
                ADD CONSTRAINT cms_operation_log_user_id_fk 
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            """)
            print("✓ 新外键已添加")
        except Exception as e:
            print(f"  跳过添加外键: {e}")
    
    print("\n" + "=" * 60)
    print("修复完成！")

if __name__ == '__main__':
    main()
