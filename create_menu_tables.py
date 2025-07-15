import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def run_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        print(f"执行SQL: {sql[:60]}...")

# 创建menu表
menu_sql = '''
CREATE TABLE IF NOT EXISTS `menu` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, 
    `name` varchar(100) NOT NULL UNIQUE, 
    `code` varchar(100) NOT NULL UNIQUE, 
    `path` varchar(200) NOT NULL, 
    `component` varchar(200) NULL, 
    `redirect` varchar(200) NULL, 
    `title` varchar(100) NOT NULL, 
    `icon` varchar(100) NULL, 
    `extra_icon` varchar(100) NULL, 
    `rank` integer NOT NULL, 
    `show_link` bool NOT NULL, 
    `show_parent` bool NOT NULL, 
    `roles` json NULL, 
    `auths` json NULL, 
    `keep_alive` bool NOT NULL, 
    `frame_src` varchar(255) NULL, 
    `frame_loading` bool NOT NULL, 
    `hidden_tag` bool NOT NULL, 
    `dynamic_level` integer NULL, 
    `active_path` varchar(200) NULL, 
    `transition_name` varchar(100) NULL, 
    `enter_transition` varchar(100) NULL, 
    `leave_transition` varchar(100) NULL, 
    `is_active` bool NOT NULL, 
    `remarks` longtext NULL, 
    `created_at` datetime(6) NOT NULL, 
    `updated_at` datetime(6) NOT NULL, 
    `parent_id` bigint NULL
)'''
run_sql(menu_sql)

# 创建user_menu表
user_menu_sql = '''
CREATE TABLE IF NOT EXISTS `user_menu` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, 
    `is_active` bool NOT NULL, 
    `created_at` datetime(6) NOT NULL, 
    `updated_at` datetime(6) NOT NULL, 
    `menu_id` bigint NOT NULL, 
    `user_id` bigint NOT NULL
)'''
run_sql(user_menu_sql)

# 添加约束
constraints = [
    "ALTER TABLE `menu` ADD CONSTRAINT `menu_parent_id_7f4b2723_fk_menu_id` FOREIGN KEY (`parent_id`) REFERENCES `menu` (`id`)",
    "ALTER TABLE `user_menu` ADD CONSTRAINT `user_menu_user_id_menu_id_ac2250fa_uniq` UNIQUE (`user_id`, `menu_id`)",
    "ALTER TABLE `user_menu` ADD CONSTRAINT `user_menu_menu_id_55893c45_fk_menu_id` FOREIGN KEY (`menu_id`) REFERENCES `menu` (`id`)",
    "ALTER TABLE `user_menu` ADD CONSTRAINT `user_menu_user_id_0c169855_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)"
]

for constraint in constraints:
    try:
        run_sql(constraint)
    except Exception as e:
        print(f"添加约束失败，可能已存在: {str(e)}")

# 添加迁移记录
migration_sql = '''
INSERT INTO django_migrations (app, name, applied) 
VALUES ('menus', '0001_initial', NOW())
'''

try:
    run_sql(migration_sql)
except Exception as e:
    print(f"添加迁移记录失败: {str(e)}")

print("表创建和迁移完成") 