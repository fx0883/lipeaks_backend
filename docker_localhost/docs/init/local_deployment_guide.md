# 本地部署指南

本文档描述了如何在本地环境中部署和初始化本项目。

## 前提条件

- Python 3.8+
- MySQL 8.0+
- pip（Python包管理工具）

## 部署步骤

### 1. 创建数据库

首先，需要在MySQL中创建项目数据库：

```sql
CREATE DATABASE multi_tenant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 配置环境变量

在项目根目录创建`.env`文件，内容如下：

```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=multi_tenant_db
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

请根据您的MySQL配置修改用户名和密码。

### 3. 安装项目依赖

```bash
pip install -r requirements.txt
```

### 4. 创建数据库迁移文件

由于项目初始化需要重新生成迁移文件，请确保已删除所有旧的迁移文件（除了`__init__.py`）。然后创建新的迁移文件：

```bash
python manage.py makemigrations common tenants users rbac menus cms check_system charts customers orders
```

### 5. 应用迁移

执行迁移以创建数据库表结构：

```bash
python manage.py migrate
```

### 6. 导入初始化数据

项目需要导入初始化数据，使用以下方法之一：

#### 方法1: 使用MySQL命令行工具

```bash
mysql -u root -p multi_tenant_db < docs/init_sql/common_config.sql
```

#### 方法2: 使用MySQL Workbench或其他GUI工具

1. 打开MySQL Workbench并连接到数据库
2. 选择`multi_tenant_db`数据库
3. 选择"File" > "Open SQL Script"
4. 打开并执行`docs/init_sql/common_config.sql`文件

### 7. 创建超级用户

创建系统管理员账户：

```bash
python manage.py createsuperuser
```

按照提示输入用户名、电子邮件和密码。

### 8. 运行开发服务器

启动开发服务器：

```bash
python manage.py runserver
```

现在，您可以在浏览器中访问 http://localhost:8000/ 来使用应用。

## 常见问题

### 数据库连接问题

如果遇到数据库连接错误，请检查：
- MySQL服务是否正在运行
- `.env`文件中的数据库配置是否正确
- 数据库用户是否有足够权限

### 迁移错误

如果迁移过程中出现错误：
- 确保所有旧的迁移文件都已删除
- 检查模型定义是否有语法错误
- 尝试先删除数据库并重新创建

## 进阶配置

### 邮件设置

如果需要启用邮件功能（如密码重置），请在`.env`文件中添加以下配置：

```
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@example.com
``` 