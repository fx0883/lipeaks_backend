# 将Django项目部署到cPanel的指南

## 目录

- [简介](#简介)
- [前提条件](#前提条件)
- [部署步骤](#部署步骤)
  - [1. 准备cPanel环境](#1-准备cpanel环境)
  - [2. 上传项目代码](#2-上传项目代码)
  - [3. 配置Python环境](#3-配置python环境)
  - [4. 配置数据库](#4-配置数据库)
  - [5. MySQL驱动替换](#5-mysql驱动替换)
  - [6. 解决字符集问题](#6-解决字符集问题)
  - [7. 执行迁移和静态文件收集](#7-执行迁移和静态文件收集)
  - [8. 配置域名和应用重启](#8-配置域名和应用重启)
- [常见问题解决](#常见问题解决)
- [维护提示](#维护提示)

## 简介

本文档提供将多租户Django项目部署到cPanel服务器环境的详细指南。cPanel是一个流行的Web主机控制面板，提供了友好的界面来管理网站、邮件和FTP账户等。虽然它主要针对PHP应用，但通过适当的配置，也可以有效地部署Django应用。

## 前提条件

- 一个支持Python的cPanel主机账号（带有Python应用程序功能）
- Django项目源代码（本项目使用Git仓库：`https://github.com/fx0883/integrated_project.git`）
- cPanel登录凭据
- 基本的命令行和Git知识

## 部署步骤

### 1. 准备cPanel环境

1. 登录到您的cPanel控制面板
2. 在cPanel中创建MySQL数据库：
   - 找到"MySQL数据库"或"MySQL数据库向导"
   - 创建一个新数据库（如`your_username_multi_tenant_db`）
   - 创建一个新的数据库用户并设置密码
   - 将用户添加到数据库并授予所有权限

### 2. 上传项目代码

可以通过以下两种方式之一上传项目：

**通过Git**：
1. 在cPanel中找到"Git™版本控制"
2. 点击"创建"，然后输入：
   - 克隆URL: `https://github.com/fx0883/integrated_project.git`
   - 选择一个存储库路径（如`integrated_project`）

**通过File Manager**：
1. 在本地下载项目：`git clone https://github.com/fx0883/integrated_project.git`
2. 在cPanel中打开文件管理器
3. 导航到所需目录（通常是`public_html`）
4. 手动上传项目文件

### 3. 配置Python环境

1. 在cPanel中找到"设置Python版本"或"Python应用程序"
2. 点击"创建应用程序"并填写：
   - 应用路径：指向项目的后端目录
   - Python版本：选择3.9+（本项目使用3.12）
   - 应用入口点：`passenger_wsgi.py`
   - 应用入口函数：`application`

3. 创建完成后，cPanel会提供一个激活虚拟环境的命令。例如：
   ```bash
   source /home/username/virtualenv/integrated_project/backend/3.12/bin/activate && cd /home/username/integrated_project/backend
   ```

### 4. 配置数据库

创建一个`.env`文件，保存数据库连接和其他环境信息：

```bash
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=your_domain.com,www.your_domain.com,localhost
DB_NAME=your_cpanel_db_name
DB_USER=your_cpanel_db_user
DB_PASSWORD=your_cpanel_db_password
DB_HOST=localhost
DB_PORT=3306
```

### 5. MySQL驱动替换

cPanel环境通常缺少编译工具，无法安装`mysqlclient`，需要替换为纯Python实现的`PyMySQL`：

1. 编辑`core/settings.py`，在顶部添加：
   ```python
   import pymysql
   
   # 使用pymysql代替mysqlclient
   pymysql.install_as_MySQLdb()
   ```

2. 修改数据库配置：
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': os.getenv('DB_NAME', 'multi_tenant_db'),
           'USER': os.getenv('DB_USER', 'root'),
           'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
           'HOST': os.getenv('DB_HOST', 'localhost'),
           'PORT': os.getenv('DB_PORT', '3306'),
           'OPTIONS': {
               'charset': 'utf8mb4',
               'use_unicode': True,
               'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
               'autocommit': True,
           },
       }
   }
   ```

3. 更新`requirements.txt`，添加PyMySQL：
   ```
   pymysql==1.1.0
   ```

4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 6. 解决字符集问题

创建一个脚本`simple_fix_charset.py`来修复数据库和表的字符集：

```python
#!/usr/bin/env python
import os
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库连接参数
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'multi_tenant_db')
DB_PORT = int(os.getenv('DB_PORT', '3306'))

try:
    # 连接到MySQL服务器
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        # 设置数据库字符集
        cursor.execute(f"ALTER DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # 查询所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # 对每个表设置字符集
        for table in tables:
            table_name = table[0]
            cursor.execute(f"ALTER TABLE `{table_name}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    
    connection.commit()
    
except Exception as e:
    print(f"错误: {e}")
finally:
    if 'connection' in locals() and connection:
        connection.close()
```

运行此脚本：
```bash
python simple_fix_charset.py
```

### 7. 执行迁移和静态文件收集

```bash
# 执行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic --noinput
```

### 8. 配置域名和应用重启

1. 在cPanel中，找到"域名"或"子域名"部分
2. 添加域名或子域名，指向项目目录
3. 重启Python应用程序

## 常见问题解决

### MySQL字符集错误

如果遇到如下错误：
```
pymysql.err.DataError: (1366, "Incorrect string value: '\\xE6\\x97\\xA5\\xE5\\xBF\\x97' for column...")
```

这表示数据库未正确配置为支持UTF-8字符集，执行`simple_fix_charset.py`脚本或手动在phpMyAdmin中执行：
```sql
ALTER DATABASE `数据库名` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### SQL语法错误

如果遇到SQL语法错误，特别是在`init_command`中：
```
ProgrammingError: (1064, "You have an error in your SQL syntax...")
```

检查`init_command`格式，确保它与您的MySQL/MariaDB版本兼容。

### 无法安装mysqlclient

使用PyMySQL替代，它是纯Python实现，不需要编译。

### 静态文件无法加载

确保您已正确配置静态文件URL和目录：
1. 检查`STATIC_ROOT`和`MEDIA_ROOT`设置
2. 检查目录权限（通常需要755）
3. 创建符号链接或直接复制静态文件到公开可访问的目录

## 维护提示

1. **定期备份数据库**：
   ```bash
   mysqldump -u 用户名 -p 数据库名 > backup_$(date +%Y%m%d).sql
   ```

2. **监控日志文件**：定期检查`logs/`目录下的日志文件

3. **更新依赖**：定期更新Python依赖包以修复安全漏洞
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **设置HTTPS**：考虑在cPanel中为您的网站启用SSL证书，保护用户数据 