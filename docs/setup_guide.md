# 多租户用户管理系统 - 安装与运行指南

本文档提供详细的项目环境设置和运行指南，包括虚拟环境配置、依赖安装、数据库迁移以及服务启动等步骤。

## 1. 环境准备

### 1.1 Python 环境要求
- Python 3.10 或更高版本
- pip 包管理工具

### 1.2 数据库要求
- MySQL 8.0 或更高版本

## 2. 克隆项目

```bash
# 通过 Git 克隆项目
git clone https://github.com/yourusername/integrated_project.git
cd integrated_project
```

## 3. 虚拟环境设置

### Windows 环境

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 验证激活成功
# 命令提示符前应出现 (venv)
```

### Linux/Mac 环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证激活成功
# 命令提示符前应出现 (venv)
```

## 4. 安装依赖

```bash
# 确保已激活虚拟环境
pip install -r requirements.txt

# 如果没有 requirements.txt 文件，可以手动安装核心依赖
pip install django==5.2
pip install djangorestframework
pip install mysqlclient
pip install python-dotenv
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install drf-spectacular
```

## 5. 环境变量配置

在项目根目录创建 `.env` 文件并配置以下环境变量：

```
# 调试模式
DEBUG=True

# 密钥（生产环境中应使用复杂的随机字符串）
SECRET_KEY=your_secret_key_here

# 数据库配置
DB_NAME=integrated_project
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

# 允许的主机
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS设置（如需跨域访问）
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 6. 数据库准备

### 6.1 创建数据库

在 MySQL 中创建数据库：

```sql
CREATE DATABASE integrated_project CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6.2 数据库迁移

```bash
# 确保已激活虚拟环境

# 创建迁移文件
python manage.py makemigrations --skip-checks

# 应用迁移
python manage.py migrate

# 创建超级管理员用户
python manage.py createsuperuser
```

## 7. 运行开发服务器

```bash
# 确保已激活虚拟环境
python manage.py runserver 0.0.0.0:8000
```

服务器将在 http://127.0.0.1:8000 上启动。

## 8. API 文档访问

API 文档可通过以下 URL 访问：

- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- OpenAPI Schema: http://127.0.0.1:8000/api/schema/

## 9. 常见问题与解决方案

### 9.1 数据库连接问题

如果遇到数据库连接问题，请检查：
- MySQL 服务是否运行
- .env 文件中的数据库配置是否正确
- 数据库用户是否有足够权限

### 9.2 依赖安装问题

如果安装依赖时出现问题：

```bash
# 尝试更新 pip
pip install --upgrade pip

# 逐个安装依赖，查看具体错误
```

### 9.3 迁移问题

如果遇到迁移问题，可尝试：

```bash
# 使用 --skip-checks 参数跳过检查
python manage.py makemigrations --skip-checks

# 如有循环导入问题，请检查模型定义
```

## 10. 生产环境部署

对于生产环境，建议：

1. 设置 `DEBUG=False`
2. 使用 Nginx + Gunicorn 作为服务器
3. 配置 HTTPS
4. 使用环境变量管理敏感信息
5. 定期备份数据库

详细的生产环境部署指南请参考 `docs/deployment_guide.md`（如有）。

## 11. 项目关闭

```bash
# 停止开发服务器
按 Ctrl+C

# 退出虚拟环境
deactivate
``` 



.\venv\Scripts\activate 


python manage.py runserver