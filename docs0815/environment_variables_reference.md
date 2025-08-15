# 环境变量参考文档

## 概述

本文档详细说明多租户后端系统支持的所有环境变量，包括新增的数据库快照导入功能相关配置。

## 环境变量分类

### 🔧 数据库配置

| 变量名 | 默认值 | 必需 | 说明 |
|--------|--------|------|------|
| `DB_NAME` | `multi_tenant_db_dev` | ✅ | 数据库名称 |
| `DB_USER` | `django` | ✅ | 数据库用户名 |
| `DB_PASSWORD` | `django_password` | ✅ | 数据库密码 |
| `DB_HOST` | `db` | ✅ | 数据库主机地址 |
| `DB_PORT` | `3306` | ✅ | 数据库端口 |

**示例：**
```bash
DB_NAME=my_database
DB_USER=my_user
DB_PASSWORD=my_secure_password
DB_HOST=mysql.example.com
DB_PORT=3306
```

### 🔐 Django 配置

| 变量名 | 默认值 | 必需 | 说明 |
|--------|--------|------|------|
| `SECRET_KEY` | `your_production_secret_key_here` | ✅ | Django 密钥 |
| `DEBUG` | `True` | ❌ | 调试模式开关 |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | ❌ | 允许的主机列表 |
| `DJANGO_SETTINGS_MODULE` | `core.settings_docker` | ❌ | Django 设置模块 |

**示例：**
```bash
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com
```

### 👤 超级用户配置

| 变量名 | 默认值 | 必需 | 说明 |
|--------|--------|------|------|
| `CREATE_SUPERUSER` | `true` | ❌ | 是否创建超级用户 |
| `SUPERUSER_USERNAME` | `admin` | ❌ | 超级用户名 |
| `SUPERUSER_EMAIL` | `admin@example.com` | ❌ | 超级用户邮箱 |
| `SUPERUSER_PASSWORD` | `admin_main` | ❌ | 超级用户密码 |

**示例：**
```bash
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@company.com
SUPERUSER_PASSWORD=secure_password_123
```

### 📊 日志配置

| 变量名 | 默认值 | 必需 | 说明 |
|--------|--------|------|------|
| `LOG_TO_CONSOLE` | `True` | ❌ | 日志输出到控制台 |
| `DEBUG_LOG_ENABLED` | `True` | ❌ | 启用调试日志 |

**示例：**
```bash
LOG_TO_CONSOLE=True
DEBUG_LOG_ENABLED=True
```

### 🗄️ 数据库快照导入配置

| 变量名 | 默认值 | 必需 | 说明 |
|--------|--------|------|------|
| `IMPORT_DB_SNAPSHOT` | `false` | ❌ | **数据库快照导入开关** |

**示例：**
```bash
IMPORT_DB_SNAPSHOT=true
```

### 📧 邮件配置

| 变量名 | 默认值 | 必需 | 说明 |
|--------|--------|------|------|
| `EMAIL_HOST_USER` | `` | ❌ | QQ邮箱地址 |
| `EMAIL_HOST_PASSWORD` | `` | ❌ | QQ邮箱授权码 |
| `DEFAULT_FROM_EMAIL` | `` | ❌ | 发件人邮箱 |
| `FRONTEND_URL` | `http://localhost:3000` | ❌ | 前端URL |

**示例：**
```bash
EMAIL_HOST_USER=your-email@qq.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@company.com
FRONTEND_URL=https://app.company.com
```

## 配置方式

### 方式 1: docker-compose.yml 文件

```yaml
version: '3.8'
services:
  web:
    image: lipeaks_backend:latest
    environment:
      # 数据库配置
      - DB_NAME=multi_tenant_db_dev
      - DB_USER=django
      - DB_PASSWORD=django_password
      - DB_HOST=db
      - DB_PORT=3306
      
      # Django 配置
      - SECRET_KEY=your_production_secret_key_here
      - DEBUG=True
      - LOG_TO_CONSOLE=True
      
      # 超级用户配置
      - CREATE_SUPERUSER=true
      - SUPERUSER_USERNAME=admin
      - SUPERUSER_EMAIL=admin@example.com
      - SUPERUSER_PASSWORD=admin_main
      
      # 数据库快照导入
      - IMPORT_DB_SNAPSHOT=false
```

### 方式 2: .env 文件

```bash
# 创建 .env 文件
cat > .env << EOF
# 数据库配置
DB_NAME=multi_tenant_db_dev
DB_USER=django
DB_PASSWORD=django_password
DB_HOST=db
DB_PORT=3306

# Django 配置
SECRET_KEY=your_production_secret_key_here
DEBUG=True
LOG_TO_CONSOLE=True

# 超级用户配置
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=admin_main

# 数据库快照导入
IMPORT_DB_SNAPSHOT=false
EOF
```

### 方式 3: 命令行环境变量

```bash
# 设置环境变量
export DB_NAME=my_database
export DB_USER=my_user
export DB_PASSWORD=my_password
export IMPORT_DB_SNAPSHOT=true

# 启动服务
docker-compose up -d
```

## 配置场景示例

### 开发环境配置

```bash
# .env.development
DEBUG=True
LOG_TO_CONSOLE=True
CREATE_SUPERUSER=true
IMPORT_DB_SNAPSHOT=false
SECRET_KEY=dev-secret-key-not-for-production
```

### 生产环境配置

```bash
# .env.production
DEBUG=False
LOG_TO_CONSOLE=False
CREATE_SUPERUSER=false
IMPORT_DB_SNAPSHOT=false
SECRET_KEY=your-very-secure-production-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 测试环境配置

```bash
# .env.testing
DEBUG=True
LOG_TO_CONSOLE=True
CREATE_SUPERUSER=true
IMPORT_DB_SNAPSHOT=true
DB_NAME=test_database
```

## 环境变量优先级

环境变量的优先级从高到低：

1. **命令行环境变量** (最高优先级)
2. **.env 文件**
3. **docker-compose.yml 中的 environment 配置**
4. **默认值** (最低优先级)

## 验证环境变量

### 检查当前环境变量

```bash
# 查看所有环境变量
docker-compose exec web env

# 查看特定环境变量
docker-compose exec web env | grep IMPORT_DB_SNAPSHOT
docker-compose exec web env | grep DB_
```

### 测试环境变量配置

```bash
# 测试数据库连接
docker-compose exec web python -c "
import os
print(f'DB_NAME: {os.getenv(\"DB_NAME\")}')
print(f'DB_HOST: {os.getenv(\"DB_HOST\")}')
print(f'IMPORT_DB_SNAPSHOT: {os.getenv(\"IMPORT_DB_SNAPSHOT\")}')
"
```

## 安全建议

### 生产环境安全

1. **使用强密码**
   ```bash
   # 生成强密码
   openssl rand -base64 32
   ```

2. **使用环境变量文件**
   ```bash
   # 设置文件权限
   chmod 600 .env
   ```

3. **定期轮换密钥**
   ```bash
   # 生成新的 SECRET_KEY
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

### 敏感信息处理

1. **不要在代码中硬编码**
2. **使用密钥管理服务**
3. **定期审计环境变量**
4. **限制环境变量文件访问权限**

## 故障排除

### 常见问题

1. **环境变量未生效**
   ```bash
   # 重新构建镜像
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **环境变量文件未加载**
   ```bash
   # 检查文件位置和权限
   ls -la .env
   cat .env
   ```

3. **特殊字符问题**
   ```bash
   # 使用引号包围包含特殊字符的值
   SECRET_KEY="your-secret-key-with-special-chars"
   ```

### 调试命令

```bash
# 查看容器环境变量
docker-compose exec web printenv

# 查看特定变量
docker-compose exec web printenv IMPORT_DB_SNAPSHOT

# 检查配置文件
docker-compose config
```

## 更新日志

### v1.0 (2025-08-15)
- 新增 `IMPORT_DB_SNAPSHOT` 环境变量
- 完善环境变量文档
- 添加安全建议和故障排除

---

**相关文档：**
- [快速开始指南](./quick_start_guide.md)
- [完整部署指南](./docker_deployment_guide.md)
