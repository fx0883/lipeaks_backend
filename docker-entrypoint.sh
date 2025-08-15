#!/bin/bash

# 等待数据库准备就绪
echo "等待数据库..."
# 增加重试次数和超时时间
max_retries=30
count=0
while ! nc -z db 3306; do
  sleep 3
  count=$((count+1))
  echo "等待数据库连接... $count/$max_retries"
  if [ $count -ge $max_retries ]; then
    echo "等待数据库超时，请检查数据库服务是否正常启动"
    exit 1
  fi
done
echo "数据库已准备就绪!"

# 设置环境变量
export DJANGO_SETTINGS_MODULE=core.settings_docker

# 等待数据库完全初始化
echo "等待数据库完全初始化..."
sleep 10

# 数据库状态检测函数
check_database_initialized() {
    echo "检查数据库是否已初始化..."
    python -c "
import os
import django
import pymysql
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_docker')
django.setup()
from django.conf import settings

try:
    # 连接数据库
    conn = pymysql.connect(
        host=settings.DATABASES['default']['HOST'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        db=settings.DATABASES['default']['NAME'],
        port=int(settings.DATABASES['default'].get('PORT', 3306)),
        charset='utf8mb4'
    )
    
    with conn.cursor() as cursor:
        # 检查关键表是否存在
        cursor.execute(\"\"\"
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = '%s' 
            AND table_name IN ('django_migrations', 'auth_user', 'tenant', 'user')
        \"\"\" % settings.DATABASES['default']['NAME'])
        
        table_count = cursor.fetchone()[0]
        
        if table_count >= 4:
            # 检查是否有基础数据
            cursor.execute('SELECT COUNT(*) FROM auth_user')
            user_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM tenant')
            tenant_count = cursor.fetchone()[0]
            
            if user_count > 0 and tenant_count > 0:
                print('√ 数据库已初始化，包含基础数据')
                exit(0)  # 成功
            else:
                print('× 数据库表存在但缺少基础数据')
                exit(1)  # 失败
        else:
            print('× 数据库未初始化，缺少关键表')
            exit(1)  # 失败
            
except Exception as e:
    print(f'× 数据库检查失败: {str(e)}')
    exit(1)  # 失败
finally:
    if 'conn' in locals():
        conn.close()
"
    return $?
}

# SQL快照导入函数
import_database_snapshot() {
    echo "检查是否需要导入数据库快照..."
    
    # 检查环境变量
    if [ "${IMPORT_DB_SNAPSHOT}" != "true" ]; then
        echo "IMPORT_DB_SNAPSHOT 不为 true，跳过数据库快照导入"
        return 0
    fi
    
    # 检查数据库是否已初始化
    if check_database_initialized; then
        echo "数据库已初始化，跳过SQL快照导入"
        return 0
    fi
    
    # 检查SQL文件是否存在
    sql_file="/app/docs/init_sql/multi_tenant_db_dev.sql"
    if [ ! -f "$sql_file" ]; then
        echo "警告: SQL快照文件不存在: $sql_file"
        echo "跳过数据库快照导入"
        return 0
    fi
    
    echo "开始导入数据库快照: $sql_file"
    
    python -c "
import os
import django
import pymysql
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_docker')
django.setup()
from django.conf import settings

sql_file = '/app/docs/init_sql/multi_tenant_db_dev.sql'

try:
    # 读取SQL文件内容
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f'SQL文件大小: {len(sql_content)} 字符')
    
    # 连接数据库
    conn = pymysql.connect(
        host=settings.DATABASES['default']['HOST'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
        port=int(settings.DATABASES['default'].get('PORT', 3306)),
        charset='utf8mb4',
        # 关键参数：允许执行多条SQL语句
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
    )
    
    with conn.cursor() as cursor:
        print('执行SQL快照导入...')
        # 执行整个SQL脚本
        cursor.execute(sql_content)
        
        # 处理所有结果集
        while cursor.nextset():
            pass
        
    # 提交事务
    conn.commit()
    print('√ SQL快照导入成功')
    
except Exception as e:
    print(f'× SQL快照导入失败: {str(e)}')
    if 'conn' in locals():
        conn.rollback()
    exit(1)
finally:
    if 'conn' in locals():
        conn.close()
"
    
    if [ $? -eq 0 ]; then
        echo "数据库快照导入完成"
        return 0
    else
        echo "数据库快照导入失败"
        return 1
    fi
}

# 执行数据库快照导入
import_database_snapshot

# 检查数据库状态并决定是否执行迁移
if check_database_initialized; then
    echo "数据库已初始化，跳过迁移步骤"
else
    echo "数据库未初始化，执行迁移步骤"
    
    # 创建迁移文件
    echo "创建迁移文件..."
    python manage.py makemigrations common tenants users rbac menus cms check_system charts customers orders

    # 应用所有迁移（包括Django自带的迁移）
    echo "应用所有迁移..."
    python manage.py migrate

    # 单独确认Django auth迁移
    echo "确认auth迁移..."
    python manage.py migrate auth
    python manage.py migrate admin
    python manage.py migrate sessions
    python manage.py migrate contenttypes

    # 单独确认应用迁移 - 特别是可能包含user_menu表的应用
    echo "确认menus应用迁移..."
    python manage.py migrate menus --fake-initial

    echo "确认users应用迁移..."
    python manage.py migrate users --fake-initial

    echo "确认rbac应用迁移..."
    python manage.py migrate rbac --fake-initial
fi

# 检查user_menu表是否存在
echo "检查user_menu表是否存在..."
python -c "
import os
import django
import pymysql
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_docker')
django.setup()
from django.conf import settings

# 连接数据库
conn = pymysql.connect(
    host=settings.DATABASES['default']['HOST'],
    user=settings.DATABASES['default']['USER'],
    password=settings.DATABASES['default']['PASSWORD'],
    db=settings.DATABASES['default']['NAME']
)

try:
    with conn.cursor() as cursor:
        cursor.execute(\"\"\"
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = '%s' 
            AND table_name = 'user_menu'
        \"\"\" % settings.DATABASES['default']['NAME'])
        if cursor.fetchone()[0] == 0:
            print('警告: user_menu 表不存在!')
            print('尝试手动创建user_menu表...')
            cursor.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS `user_menu` (
                  `id` bigint NOT NULL AUTO_INCREMENT,
                  `user_id` bigint NOT NULL,
                  `menu_id` bigint NOT NULL,
                  PRIMARY KEY (`id`),
                  UNIQUE KEY `user_menu_user_id_menu_id_d8c3a1e1_uniq` (`user_id`,`menu_id`),
                  KEY `user_menu_menu_id_75a7e331_fk_menu_id` (`menu_id`),
                  CONSTRAINT `user_menu_menu_id_75a7e331_fk_menu_id` FOREIGN KEY (`menu_id`) REFERENCES `menu` (`id`),
                  CONSTRAINT `user_menu_user_id_7718ce7f_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
            \"\"\")
            print('user_menu表已手动创建')
        else:
            print('√ user_menu 表已存在')
finally:
    conn.close()
"

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput --clear

# 复制admin静态文件 (额外保证)
echo "确保admin静态文件可用..."
if [ ! -d /app/staticfiles/admin ]; then
  mkdir -p /app/staticfiles/admin
  cp -r /usr/local/lib/python3.13/site-packages/django/contrib/admin/static/admin/* /app/staticfiles/admin/
fi

# 修改权限
echo "设置文件权限..."
chmod -R 755 /app/staticfiles
chmod -R 755 /app/media

# 创建超级管理员账号
echo "检查是否需要创建超级管理员..."
if [ "${CREATE_SUPERUSER}" = "true" ]; then
  echo "创建超级管理员账号..."
  python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_docker')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${SUPERUSER_USERNAME:-admin}').exists():
    User.objects.create_superuser(
        '${SUPERUSER_USERNAME:-admin}',
        '${SUPERUSER_EMAIL:-admin@example.com}',
        '${SUPERUSER_PASSWORD:-admin_main}'
    )
    print('超级管理员账号创建成功')
else:
    print('超级管理员账号已存在，跳过创建')
"
fi

# 执行SQL配置脚本
echo "执行common_config.sql脚本..."
python manage.py run_config_sql

# 启动Gunicorn服务器
echo "启动Web服务器..."
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 