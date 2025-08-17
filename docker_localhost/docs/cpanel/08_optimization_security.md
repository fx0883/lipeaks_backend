# 性能优化与安全配置

本文档将指导您对cPanel环境中的Django应用程序进行性能优化和安全配置，以提高应用程序的响应速度和安全性。

## 性能优化

### 1. 数据库优化

#### 添加索引

为经常查询的字段添加索引可以显著提高查询性能：

1. 检查现有索引：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 使用Django shell检查索引
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SHOW INDEX FROM your_table_name'); print([row for row in cursor.fetchall()])"
```

2. 创建迁移文件来添加索引：

```python
# 示例迁移文件
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('your_app', '前一个迁移文件'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='yourmodel',
            index=models.Index(fields=['frequently_searched_field'], name='idx_frequently_searched_field'),
        ),
    ]
```

#### 优化查询

1. 创建查询分析脚本：

```bash
# 创建查询分析脚本
cat > ~/lipeaks_backend/analyze_queries.py << 'EOL'
#!/usr/bin/env python
import os
import re
import time
from collections import defaultdict
from django.db import connection
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def analyze_queries():
    """分析慢查询并提供优化建议"""
    # 连接到数据库
    with connection.cursor() as cursor:
        # 检查是否启用了慢查询日志
        cursor.execute("SHOW VARIABLES LIKE 'slow_query_log'")
        slow_log_enabled = cursor.fetchone()[1]
        
        if slow_log_enabled != 'ON':
            print("慢查询日志未启用。请联系您的主机提供商启用慢查询日志。")
            return
        
        # 获取慢查询日志文件位置
        cursor.execute("SHOW VARIABLES LIKE 'slow_query_log_file'")
        slow_log_file = cursor.fetchone()[1]
        print(f"慢查询日志文件: {slow_log_file}")
        
        # 获取慢查询阈值
        cursor.execute("SHOW VARIABLES LIKE 'long_query_time'")
        long_query_time = cursor.fetchone()[1]
        print(f"慢查询阈值: {long_query_time}秒")
        
        # 分析表结构
        print("\n分析表结构...")
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            print(f"\n表 '{table}':")
            
            # 检查表大小
            cursor.execute(f"SELECT TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES WHERE TABLE_NAME = '{table}'")
            rows, data_size, index_size = cursor.fetchone()
            print(f"  行数: {rows or 0}")
            print(f"  数据大小: {data_size/1024/1024:.2f}MB")
            print(f"  索引大小: {index_size/1024/1024:.2f}MB")
            
            # 检查索引
            cursor.execute(f"SHOW INDEX FROM {table}")
            indices = cursor.fetchall()
            print(f"  索引数量: {len(indices)}")
            
            # 检查是否有TEXT或BLOB列没有索引
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            for col in columns:
                col_name, col_type = col[0], col[1]
                if 'text' in col_type.lower() or 'blob' in col_type.lower():
                    index_exists = any(idx[4] == col_name for idx in indices)
                    if not index_exists:
                        print(f"  警告: 列 '{col_name}' 是 {col_type} 类型但没有索引")
        
        # 提供优化建议
        print("\n优化建议:")
        print("1. 为经常在WHERE子句中使用的列添加索引")
        print("2. 避免在查询中使用SELECT *，只选择需要的列")
        print("3. 使用适当的字段类型（例如，对于枚举值使用ENUM而不是VARCHAR）")
        print("4. 考虑对大表进行分区")
        print("5. 定期优化和分析表: OPTIMIZE TABLE table_name; ANALYZE TABLE table_name;")

if __name__ == "__main__":
    analyze_queries()
EOL

# 设置执行权限
chmod +x ~/lipeaks_backend/analyze_queries.py
```

2. 执行查询分析：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 运行查询分析脚本
python ~/lipeaks_backend/analyze_queries.py
```

### 2. 缓存配置

在cPanel环境中配置Django缓存：

#### 使用文件缓存

1. 在`settings.py`中配置文件缓存：

```python
# 缓存设置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(os.path.dirname(BASE_DIR), 'cache'),
        'TIMEOUT': 60 * 60 * 24,  # 24小时
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
```

2. 创建缓存目录：

```bash
# 创建缓存目录
mkdir -p ~/cache
chmod 700 ~/cache
```

#### 使用内存缓存（如果可用）

如果您的cPanel主机支持Memcached或Redis，可以配置更高效的缓存：

```python
# Memcached配置示例
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# Redis配置示例
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. 静态文件优化

#### 压缩CSS和JavaScript文件

1. 安装Django Compressor：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 安装Django Compressor
pip install django-compressor
```

2. 在`settings.py`中配置Compressor：

```python
# 添加到INSTALLED_APPS
INSTALLED_APPS = [
    # ... 其他应用 ...
    'compressor',
]

# 添加到STATICFILES_FINDERS
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

# Compressor设置
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
```

3. 在模板中使用Compressor：

```html
{% load compress %}

{% compress css %}
<link rel="stylesheet" href="{% static 'css/style.css' %}">
<link rel="stylesheet" href="{% static 'css/responsive.css' %}">
{% endcompress %}

{% compress js %}
<script src="{% static 'js/main.js' %}"></script>
<script src="{% static 'js/utils.js' %}"></script>
{% endcompress %}
```

### 4. 应用程序优化

#### 使用数据库连接池

1. 安装django-db-connection-pool：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 安装连接池
pip install django-db-connection-pool
```

2. 在`settings.py`中配置连接池：

```python
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 10,
            'RECYCLE': 300,  # 5分钟
        }
    }
}
```

#### 优化模板加载

在`settings.py`中启用模板缓存：

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # ... 其他处理器 ...
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
```

## 安全配置

### 1. 设置安全中间件

在`settings.py`中配置安全中间件：

```python
# 安全中间件设置
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ... 其他中间件 ...
]

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1年
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 2. 配置密码策略

在`settings.py`中配置强密码策略：

```python
# 密码验证设置
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 密码重置超时（秒）
PASSWORD_RESET_TIMEOUT = 86400  # 24小时
```

### 3. 防止暴力攻击

安装并配置django-axes来防止暴力攻击：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 安装django-axes
pip install django-axes
```

在`settings.py`中配置django-axes：

```python
# 添加到INSTALLED_APPS
INSTALLED_APPS = [
    # ... 其他应用 ...
    'axes',
]

# 添加到MIDDLEWARE（放在AuthenticationMiddleware之后）
MIDDLEWARE = [
    # ... 其他中间件 ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    # ... 其他中间件 ...
]

# Axes配置
AXES_FAILURE_LIMIT = 5  # 5次失败尝试后锁定
AXES_COOLOFF_TIME = 1  # 1小时后解锁
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # 同时锁定用户和IP
```

### 4. 配置内容安全策略（CSP）

在`settings.py`中配置CSP：

```python
# 安装django-csp
# pip install django-csp

# 添加到MIDDLEWARE（放在第一位）
MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    # ... 其他中间件 ...
]

# CSP配置
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "data:")
```

### 5. 保护敏感文件

创建一个脚本来检查和保护敏感文件：

```bash
# 创建安全检查脚本
cat > ~/security_check.sh << 'EOL'
#!/bin/bash

# 设置变量
PROJECT_DIR=~/lipeaks_backend
PUBLIC_DIR=~/public_html

# 检查敏感文件权限
check_permissions() {
    echo "检查敏感文件权限..."
    
    # 检查.env文件
    if [ -f "$PROJECT_DIR/.env" ]; then
        PERM=$(stat -c "%a" "$PROJECT_DIR/.env")
        if [ "$PERM" != "600" ]; then
            echo "警告: .env文件权限不安全 ($PERM)，应该是600"
            chmod 600 "$PROJECT_DIR/.env"
            echo "已修复: 设置.env文件权限为600"
        else
            echo "正常: .env文件权限为600"
        fi
    fi
    
    # 检查settings.py文件
    if [ -f "$PROJECT_DIR/core/settings.py" ]; then
        PERM=$(stat -c "%a" "$PROJECT_DIR/core/settings.py")
        if [ "$PERM" != "644" ] && [ "$PERM" != "640" ]; then
            echo "警告: settings.py文件权限不安全 ($PERM)，应该是644或640"
            chmod 644 "$PROJECT_DIR/core/settings.py"
            echo "已修复: 设置settings.py文件权限为644"
        else
            echo "正常: settings.py文件权限为$PERM"
        fi
    fi
    
    # 检查日志目录
    if [ -d "$PROJECT_DIR/logs" ]; then
        PERM=$(stat -c "%a" "$PROJECT_DIR/logs")
        if [ "$PERM" != "700" ] && [ "$PERM" != "750" ]; then
            echo "警告: logs目录权限不安全 ($PERM)，应该是700或750"
            chmod 700 "$PROJECT_DIR/logs"
            echo "已修复: 设置logs目录权限为700"
        else
            echo "正常: logs目录权限为$PERM"
        fi
    fi
}

# 检查敏感文件是否可公开访问
check_public_access() {
    echo -e "\n检查敏感文件是否可公开访问..."
    
    # 检查.env文件
    if [ -f "$PUBLIC_DIR/.env" ]; then
        echo "严重警告: .env文件在公开目录中!"
        rm -i "$PUBLIC_DIR/.env"
    else
        echo "正常: 公开目录中没有.env文件"
    fi
    
    # 检查settings.py文件
    if [ -f "$PUBLIC_DIR/settings.py" ] || [ -f "$PUBLIC_DIR/core/settings.py" ]; then
        echo "严重警告: settings.py文件在公开目录中!"
    else
        echo "正常: 公开目录中没有settings.py文件"
    fi
    
    # 检查.git目录
    if [ -d "$PUBLIC_DIR/.git" ]; then
        echo "严重警告: .git目录在公开目录中!"
    else
        echo "正常: 公开目录中没有.git目录"
    fi
    
    # 检查.htaccess文件是否正确保护Python文件
    if [ -f "$PUBLIC_DIR/.htaccess" ]; then
        if ! grep -q "FilesMatch.*\.py" "$PUBLIC_DIR/.htaccess"; then
            echo "警告: .htaccess文件可能没有正确保护Python文件"
        else
            echo "正常: .htaccess文件包含Python文件保护规则"
        fi
    else
        echo "警告: 公开目录中没有.htaccess文件"
    fi
}

# 运行检查
check_permissions
check_public_access

echo -e "\n安全检查完成!"
EOL

# 设置执行权限
chmod +x ~/security_check.sh
```

### 6. 配置防火墙（如果可用）

如果cPanel提供防火墙配置选项：

1. 在cPanel主界面，找到并点击**"ConfigServer Security & Firewall"**或类似选项
2. 配置以下规则：
   - 限制SSH访问到特定IP地址
   - 阻止常见攻击端口
   - 启用登录失败保护

### 7. 设置自动安全更新

创建一个脚本来定期更新依赖：

```bash
# 创建更新脚本
cat > ~/update_dependencies.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/dependency_updates.log

# 记录开始时间
echo "$(date): 开始依赖更新" >> $LOG_FILE

# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 切换到项目目录
cd ~/lipeaks_backend

# 备份当前requirements.txt
cp requirements.txt requirements.txt.bak

# 检查安全漏洞
echo "检查安全漏洞..." >> $LOG_FILE
pip list --outdated | grep -i "django\|pillow\|requests\|cryptography\|pyjwt" >> $LOG_FILE

# 更新关键安全依赖
echo "更新关键安全依赖..." >> $LOG_FILE
pip install --upgrade django pillow requests cryptography pyjwt

# 重启应用程序
touch ~/lipeaks_backend/passenger_wsgi.py

echo "$(date): 依赖更新完成" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/update_dependencies.sh
```

设置每月自动更新：

```bash
# 在cPanel中设置cron作业，每月第一天凌晨3点执行更新
(crontab -l 2>/dev/null; echo "0 3 1 * * ~/update_dependencies.sh") | crontab -
```

## 下一步

完成性能优化与安全配置后，您可以继续[常见问题排查](09_troubleshooting.md)。 