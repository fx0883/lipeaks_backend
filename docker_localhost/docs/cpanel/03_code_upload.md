# 上传和配置项目代码

本文档将指导您如何将Django项目代码上传到cPanel服务器，并进行必要的配置调整。

## 上传项目代码的方法

有几种方法可以将项目代码上传到cPanel服务器，下面介绍最常用的三种方法：

### 方法1：使用Git克隆（推荐）

如果您的项目代码存储在Git仓库中，并且cPanel支持Git功能，这是最推荐的方法：

1. 在cPanel主界面，找到并点击**"Git™版本控制"**
2. 点击**"创建"**按钮
3. 填写以下信息：
   - **克隆URL**：您的Git仓库URL（例如 `https://github.com/yourusername/lipeaks_backend.git`）
   - **存储库路径**：指定存储库在服务器上的位置（例如 `lipeaks_backend`）
   - **存储库名称**：为存储库指定一个名称（例如 `lipeaks_backend`）
4. 如果是私有仓库，还需要提供Git凭据
5. 点击**"创建"**按钮开始克隆过程
6. 克隆完成后，您可以在指定的路径找到项目文件

#### 使用SSH更新Git仓库（如果可用）

如果您有SSH访问权限，可以使用以下命令更新仓库：

```bash
cd ~/lipeaks_backend
git pull origin main  # 或您的主分支名称
```

### 方法2：使用文件管理器上传

如果您没有Git仓库或cPanel不支持Git功能，可以使用文件管理器上传项目：

1. 在本地计算机上，将项目文件打包成ZIP文件
2. 在cPanel主界面，点击**"文件管理器"**
3. 导航到您计划存放项目的目录（例如 `/home/username/lipeaks_backend`）
4. 点击**"上传"**按钮
5. 选择并上传ZIP文件
6. 上传完成后，选择ZIP文件并点击**"提取"**
7. 指定提取路径，然后点击**"提取文件"**按钮
8. 提取完成后，可以删除ZIP文件

### 方法3：使用FTP/SFTP上传

如果您有大量文件或网络连接不稳定，FTP/SFTP可能是更好的选择：

1. 在cPanel主界面，找到并点击**"FTP账户"**
2. 记下您的FTP凭据，或创建一个新的FTP账户
3. 使用FileZilla、WinSCP等FTP客户端连接到服务器
4. 导航到目标目录
5. 上传项目文件

## 配置项目设置

上传代码后，需要调整项目设置以适应cPanel环境：

### 创建和配置.env文件

为了安全地管理敏感配置，创建一个`.env`文件：

1. 使用文件管理器或SSH，导航到项目根目录
2. 创建一个新文件`.env`
3. 添加以下环境变量（根据您的实际情况修改）：

```
# Django设置
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost

# 数据库设置
DB_NAME=username_multi_tenant_db
DB_USER=username_django_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306

# 邮件设置
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@example.com

# 前端URL
FRONTEND_URL=https://yourdomain.com
```

### 修改settings.py

检查并调整`core/settings.py`文件中的设置：

1. 确保项目正确加载`.env`文件中的环境变量
2. 调整静态文件和媒体文件路径
3. 配置日志目录

以下是一些关键设置的示例修改：

#### 静态文件和媒体文件路径

```python
# 静态文件设置
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'public_html/static')

# 媒体文件设置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'public_html/media')
```

#### 日志设置

```python
# 日志目录
LOGS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
```

### 修改passenger_wsgi.py

检查并确认`passenger_wsgi.py`文件配置正确：

```python
import os
import sys
import pymysql

# 获取当前脚本目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加项目目录到路径
sys.path.insert(0, CURRENT_DIR)

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 设置pymysql选项
pymysql.connect_timeout = 30
pymysql.install_as_MySQLdb()

# 应用程序对象
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 创建.htaccess文件

在项目根目录创建`.htaccess`文件，配置Apache服务器：

```apache
# 启用Python应用程序
AddHandler wsgi-script .py
Options +ExecCGI

# 设置索引文件
DirectoryIndex passenger_wsgi.py

# 重写规则
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ passenger_wsgi.py/$1 [QSA,L]

# 静态文件缓存
<FilesMatch "\.(jpg|jpeg|png|gif|ico|css|js)$">
    Header set Cache-Control "max-age=2592000, public"
</FilesMatch>

# 安全设置
<Files ~ "^\.">
    Order allow,deny
    Deny from all
</Files>

# 禁止访问敏感文件
<FilesMatch "^(\.env|manage\.py)$">
    Order allow,deny
    Deny from all
</FilesMatch>
```

## 设置文件权限

设置适当的文件权限以确保安全性和功能性：

1. 使用文件管理器或SSH，导航到项目根目录
2. 设置以下权限：
   - Python文件（.py）：`644`（用户可读写，组和其他只读）
   - 配置文件（.env, settings.py等）：`600`（仅用户可读写）
   - 目录：`755`（用户可读写执行，组和其他可读执行）
   - 日志目录：`700`（仅用户可读写执行）

使用SSH可以批量设置权限：

```bash
# 设置所有Python文件权限
find ~/lipeaks_backend -type f -name "*.py" -exec chmod 644 {} \;

# 设置所有目录权限
find ~/lipeaks_backend -type d -exec chmod 755 {} \;

# 设置配置文件权限
chmod 600 ~/lipeaks_backend/.env
chmod 600 ~/lipeaks_backend/core/settings.py

# 设置日志目录权限
chmod 700 ~/logs
```

## 创建符号链接（如果需要）

如果您的项目目录不在公共可访问目录中，需要为静态文件和媒体文件创建符号链接：

```bash
# 创建静态文件目录（如果不存在）
mkdir -p ~/public_html/static
mkdir -p ~/public_html/media

# 创建符号链接
ln -sf ~/lipeaks_backend/staticfiles/* ~/public_html/static/
ln -sf ~/lipeaks_backend/media/* ~/public_html/media/
```

## 下一步

完成代码上传和配置后，您可以继续[配置Python环境](04_python_setup.md)。 