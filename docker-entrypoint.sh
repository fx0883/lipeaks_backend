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
        '${SUPERUSER_PASSWORD:-admin123456}'
    )
    print('超级管理员账号创建成功')
else:
    print('超级管理员账号已存在，跳过创建')
"
fi

# 启动Gunicorn服务器
echo "启动Web服务器..."
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 