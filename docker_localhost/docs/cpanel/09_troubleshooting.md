# 常见问题排查

本文档提供了在cPanel环境中部署Django项目时可能遇到的常见问题及其解决方案。

## 应用程序启动问题

### 问题：应用程序无法启动，显示"500 Internal Server Error"

**可能原因**：
1. Passenger WSGI配置错误
2. Python路径或虚拟环境问题
3. Django设置模块未找到
4. 依赖项缺失或版本不兼容

**解决方案**：

1. 检查Passenger WSGI配置：

```bash
# 检查passenger_wsgi.py文件
cat ~/lipeaks_backend/passenger_wsgi.py
```

确保文件内容正确，特别是路径和环境变量设置。

2. 检查Python虚拟环境：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 验证Python版本
python --version

# 验证Django安装
python -c "import django; print(django.get_version())"
```

3. 创建调试版本的passenger_wsgi.py：

```bash
# 创建调试版本
cat > ~/lipeaks_backend/passenger_wsgi.py.debug << 'EOL'
import os
import sys
import traceback

# 获取当前脚本目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加项目目录到路径
sys.path.insert(0, CURRENT_DIR)

# 设置日志文件
LOG_FILE = os.path.join(os.path.dirname(CURRENT_DIR), 'logs/passenger_errors.log')

# 确保日志目录存在
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log_error(error_msg):
    """记录错误到日志文件"""
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{os.path.basename(__file__)}] {error_msg}\n")

try:
    # 设置Django设置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    # 尝试导入pymysql
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
        log_error("PyMySQL导入成功")
    except ImportError:
        log_error("警告：无法导入PyMySQL")
    
    # 尝试导入Django WSGI应用
    try:
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()
        log_error("Django WSGI应用导入成功")
    except Exception as e:
        log_error(f"Django WSGI应用导入失败: {str(e)}")
        log_error(traceback.format_exc())
        raise
    
except Exception as e:
    log_error(f"初始化失败: {str(e)}")
    log_error(traceback.format_exc())
    
    # 提供一个简单的应用程序，返回错误信息
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = b'应用程序初始化失败，请检查日志文件'
        response_headers = [('Content-type', 'text/plain'),
                           ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
EOL

# 备份原始文件
cp ~/lipeaks_backend/passenger_wsgi.py ~/lipeaks_backend/passenger_wsgi.py.bak

# 使用调试版本
cp ~/lipeaks_backend/passenger_wsgi.py.debug ~/lipeaks_backend/passenger_wsgi.py
```

4. 检查日志文件：

```bash
# 检查Passenger错误日志
tail -n 100 ~/logs/passenger_errors.log

# 检查Django错误日志
tail -n 100 ~/logs/error.log
```

### 问题：ModuleNotFoundError - 找不到模块

**可能原因**：
1. 依赖项未安装
2. Python路径配置错误
3. 虚拟环境未激活

**解决方案**：

1. 重新安装依赖项：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 重新安装依赖项
pip install -r ~/lipeaks_backend/requirements.txt
```

2. 检查Python路径：

```bash
# 检查Python路径
python -c "import sys; print(sys.path)"
```

3. 在passenger_wsgi.py中添加路径：

```python
# 添加虚拟环境路径
VIRTUALENV_PATH = '/home/username/virtualenv/lipeaks_backend/3.12/lib/python3.12/site-packages'
if VIRTUALENV_PATH not in sys.path:
    sys.path.insert(0, VIRTUALENV_PATH)
```

## 数据库问题

### 问题：数据库连接错误

**可能原因**：
1. 数据库凭据错误
2. 数据库服务器未运行
3. 数据库权限问题
4. 连接池配置错误

**解决方案**：

1. 验证数据库凭据：

```bash
# 使用MySQL客户端测试连接
mysql -u username -p -h localhost
```

2. 检查数据库设置：

```bash
# 检查.env文件中的数据库设置
grep -i "DB_" ~/lipeaks_backend/.env
```

3. 使用Django shell测试连接：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 使用Django shell测试数据库连接
python ~/lipeaks_backend/manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('数据库连接成功')"
```

### 问题：数据库迁移错误

**可能原因**：
1. 迁移文件冲突
2. 数据库架构与迁移不匹配
3. 权限问题

**解决方案**：

1. 重置迁移：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 标记所有迁移为已应用（不实际执行）
python ~/lipeaks_backend/manage.py migrate --fake
```

2. 手动修复数据库架构：

```bash
# 连接到数据库
mysql -u username -p database_name

# 在MySQL中执行必要的DDL语句
# 例如：ALTER TABLE table_name ADD COLUMN column_name VARCHAR(255);
```

3. 创建新的迁移：

```bash
# 创建新的迁移
python ~/lipeaks_backend/manage.py makemigrations

# 应用迁移
python ~/lipeaks_backend/manage.py migrate
```

## 静态文件和媒体文件问题

### 问题：静态文件无法加载（404错误）

**可能原因**：
1. 静态文件未收集
2. 静态文件URL配置错误
3. Web服务器配置问题
4. 文件权限问题

**解决方案**：

1. 重新收集静态文件：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 收集静态文件
python ~/lipeaks_backend/manage.py collectstatic --noinput
```

2. 检查静态文件目录：

```bash
# 检查静态文件目录内容
ls -la ~/public_html/static/
```

3. 检查.htaccess文件：

```bash
# 检查.htaccess文件
cat ~/public_html/.htaccess
```

确保.htaccess文件包含正确的静态文件处理规则。

4. 创建测试静态文件：

```bash
# 创建测试文件
echo "Static file test" > ~/public_html/static/test.txt
```

然后在浏览器中访问 `https://yourdomain.com/static/test.txt`。

### 问题：媒体文件上传失败

**可能原因**：
1. 媒体文件目录权限问题
2. 媒体文件URL配置错误
3. 磁盘空间不足

**解决方案**：

1. 检查媒体文件目录权限：

```bash
# 检查媒体文件目录权限
ls -la ~/public_html/media/

# 设置正确的权限
chmod -R 755 ~/public_html/media/
```

2. 检查磁盘空间：

```bash
# 检查磁盘空间
df -h
```

3. 测试媒体文件上传：

创建一个简单的上传测试视图，并尝试上传小文件。

## 性能问题

### 问题：网站加载缓慢

**可能原因**：
1. 数据库查询效率低
2. 缓存配置不当
3. 静态文件未优化
4. 服务器资源限制

**解决方案**：

1. 启用Django调试工具栏（仅在开发环境）：

```bash
# 安装Django调试工具栏
pip install django-debug-toolbar

# 在settings.py中配置
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']
```

2. 分析慢查询：

```bash
# 运行查询分析脚本
python ~/lipeaks_backend/analyze_queries.py
```

3. 优化数据库：

```bash
# 连接到MySQL
mysql -u username -p database_name

# 分析和优化表
mysql> ANALYZE TABLE table_name;
mysql> OPTIMIZE TABLE table_name;
```

4. 检查服务器资源使用情况：

```bash
# 检查CPU和内存使用情况
top

# 检查磁盘I/O
iostat -x 1 5
```

## 安全问题

### 问题：HTTPS配置错误

**可能原因**：
1. SSL证书未正确安装
2. Django HTTPS设置不正确
3. .htaccess重定向规则错误

**解决方案**：

1. 检查SSL证书状态：

在cPanel主界面，找到并点击**"SSL/TLS状态"**，确认证书状态正常。

2. 检查Django HTTPS设置：

```bash
# 检查settings.py中的HTTPS设置
grep -i "SECURE_" ~/lipeaks_backend/core/settings.py
```

确保以下设置已启用：

```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

3. 检查.htaccess重定向规则：

```bash
# 检查.htaccess文件中的HTTPS重定向规则
grep -i "RewriteRule" ~/public_html/.htaccess
```

确保包含以下规则：

```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

### 问题：敏感信息泄露

**可能原因**：
1. 敏感文件可公开访问
2. 错误页面显示详细信息
3. DEBUG模式启用

**解决方案**：

1. 运行安全检查脚本：

```bash
# 运行安全检查脚本
~/security_check.sh
```

2. 确保DEBUG模式已禁用：

```bash
# 检查DEBUG设置
grep -i "DEBUG" ~/lipeaks_backend/.env
```

确保设置为 `DEBUG=False`。

3. 检查错误页面：

确保已配置自定义错误页面，不显示详细的错误信息。

## 日志和监控问题

### 问题：无法找到日志文件

**可能原因**：
1. 日志目录不存在
2. 日志配置错误
3. 权限问题

**解决方案**：

1. 创建日志目录：

```bash
# 创建日志目录
mkdir -p ~/logs
chmod 700 ~/logs
```

2. 检查日志配置：

```bash
# 检查settings.py中的日志配置
grep -A 20 "LOGGING" ~/lipeaks_backend/core/settings.py
```

3. 创建测试日志：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 使用Django shell创建测试日志
python ~/lipeaks_backend/manage.py shell -c "import logging; logger = logging.getLogger('django'); logger.error('测试日志消息')"
```

4. 检查日志文件：

```bash
# 检查日志文件
ls -la ~/logs/
cat ~/logs/error.log
```

## 部署脚本问题

### 问题：cron作业未运行

**可能原因**：
1. cron配置错误
2. 脚本权限问题
3. 脚本路径错误

**解决方案**：

1. 检查cron配置：

```bash
# 查看当前cron作业
crontab -l
```

2. 检查脚本权限：

```bash
# 检查脚本权限
ls -la ~/health_check.sh
chmod +x ~/health_check.sh
```

3. 手动运行脚本测试：

```bash
# 手动运行脚本
~/health_check.sh
```

4. 检查cron日志：

```bash
# 检查cron日志
grep CRON /var/log/syslog
```

## 其他常见问题

### 问题：500错误但没有详细信息

**解决方案**：

1. 启用详细错误日志：

```bash
# 编辑.htaccess文件
cat >> ~/public_html/.htaccess << 'EOL'
# 启用PHP错误日志
php_flag display_errors off
php_flag log_errors on
php_value error_log /home/username/logs/php_errors.log
EOL
```

2. 检查Apache错误日志：

在cPanel主界面，找到并点击**"错误日志"**，查看最近的错误。

### 问题：应用程序在部署后工作一段时间后停止

**可能原因**：
1. 内存限制
2. 进程数限制
3. 连接池耗尽

**解决方案**：

1. 检查资源使用情况：

```bash
# 检查资源使用情况
top
free -m
```

2. 优化应用程序配置：

减少连接池大小，优化缓存设置，减少并发请求数。

3. 设置自动重启：

```bash
# 创建监控和重启脚本
cat > ~/monitor_and_restart.sh << 'EOL'
#!/bin/bash

# 检查应用程序是否响应
SITE_URL="https://yourdomain.com"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $SITE_URL)

if [ $HTTP_CODE -ne 200 ]; then
    echo "$(date): 网站返回错误码 HTTP $HTTP_CODE，尝试重启..." >> ~/restart.log
    touch ~/lipeaks_backend/passenger_wsgi.py
    echo "$(date): 重启完成" >> ~/restart.log
fi
EOL

# 设置执行权限
chmod +x ~/monitor_and_restart.sh

# 添加到cron
(crontab -l 2>/dev/null; echo "*/15 * * * * ~/monitor_and_restart.sh") | crontab -
```

## 下一步

解决常见问题后，您可以继续[维护与更新指南](10_maintenance.md)。 