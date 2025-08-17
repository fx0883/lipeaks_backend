# 🚀 LiPeaks Backend - 企业级多租户SaaS平台后端系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 项目简介

LiPeaks Backend 是一个基于 Django 5.2 构建的企业级多租户 SaaS 平台后端系统。采用先进的多租户架构设计，为不同的组织或客户（租户）提供完全隔离的应用环境。

## ✨ 核心功能特性

- 🔐 **多租户架构** - 数据完全隔离，支持无限租户扩展
- 👥 **用户权限管理** - RBAC权限系统，细粒度控制
- 📝 **内容管理系统** - 文章、媒体、模板管理
- 💼 **客户关系管理** - 客户信息、分类、跟踪
- 📋 **订单管理系统** - 业务流程、费用管理
- ⏰ **打卡系统** - 任务管理、统计分析
- 🍽️ **菜单管理** - 动态菜单、权限控制
- 📊 **图表分析** - 数据可视化、报表生成

## 🏗️ 技术架构

- **后端框架**: Django 5.2 + Django REST Framework
- **数据库**: MySQL 8.0+ (PyMySQL驱动)
- **认证机制**: JWT + RBAC权限系统
- **API文档**: OpenAPI 3.0 + Swagger UI
- **部署方式**: Docker + Nginx + Gunicorn

## 🚀 快速开始

### 环境要求
- Python 3.9+
- MySQL 8.0+
- Redis 6.0+ (可选)

### Docker 一键部署
```bash
# 克隆项目
git clone https://github.com/fx0883/lipeaks_backend.git
cd lipeaks_backend

# 启动服务
docker-compose up -d

# 初始化数据库
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Python 环境部署
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.sample .env
# 编辑 .env 文件

# 数据库迁移
python manage.py migrate
python manage.py createsuperuser

# 启动服务
python manage.py runserver
```

## 📚 API 文档

- **Swagger UI**: `/api/v1/docs/`
- **ReDoc**: `/api/v1/redoc/`
- **OpenAPI Schema**: `/api/v1/schema/`

## 🔧 配置说明

### 环境变量
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=lipeaks_db
DB_USER=lipeaks_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

### 数据库配置
```sql
CREATE DATABASE lipeaks_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lipeaks_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON lipeaks_db.* TO 'lipeaks_user'@'localhost';
```

## 🛠️ 开发指南

### 项目结构
```
lipeaks_backend/
├── core/           # 核心配置
├── users/          # 用户管理
├── tenants/        # 租户管理
├── rbac/           # 权限管理
├── cms/            # 内容管理
├── customers/      # 客户管理
├── orders/         # 订单管理
├── check_system/   # 打卡系统
├── menus/          # 菜单管理
├── charts/         # 图表分析
└── common/         # 通用功能
```

### 开发环境
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码格式化
black .
isort .

# 运行测试
python manage.py test
```

## 🚀 部署指南

### 生产环境部署
```bash
# 使用 Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000

# 使用 Docker
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx 配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 安全特性

- JWT 认证机制
- 租户数据隔离
- RBAC 权限控制
- CSRF 防护
- XSS 防护
- SQL 注入防护

## 📈 监控与运维

### 日志管理
- 结构化日志记录
- 日志轮转和保留
- 错误监控和报告

### 性能优化
- 数据库查询优化
- Redis 缓存支持
- 静态文件优化

## ❓ 常见问题

**Q: 如何添加新的业务模块？**
A: 继承 BaseModel 即可自动获得租户隔离功能

**Q: 如何优化数据库性能？**
A: 使用 TenantManager 和合理设置索引

**Q: 生产环境如何配置？**
A: 设置 DEBUG=False，配置生产数据库，启用 HTTPS

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)

## 📞 联系我们

- **邮箱**: contact@lipeaks.com
- **问题反馈**: [GitHub Issues](https://github.com/fx0883/lipeaks_backend/issues)
- **技术交流群**: QQ群/微信群

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐ Star！**

Made with ❤️ by [LiPeaks Team](https://github.com/fx0883)

</div>
