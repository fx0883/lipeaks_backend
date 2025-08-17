# 多租户应用平台项目概述

## 项目简介

本项目是一个基于Django和REST框架构建的多租户应用平台，采用先进的多租户架构设计，为不同的组织或客户（租户）提供隔离的应用环境。平台内集成了用户管理系统和打卡系统等功能模块，并提供了可扩展的框架以支持更多应用的集成。

## 核心功能

### 多租户架构
- 支持租户隔离，每个租户拥有独立的数据和用户
- 租户资源配额管理，控制用户数量、管理员数量及存储空间
- 租户状态管理（活跃、暂停、已删除）

### 用户管理系统
- 多级用户角色：超级管理员、租户管理员、普通用户、子账号
- JWT认证机制，安全的用户身份验证
- 用户权限管理

### 打卡系统
- 支持创建和管理多种类型的打卡任务
- 灵活的打卡频率设置（每日、每周、每月、自定义）
- 打卡记录管理和统计
- 打卡任务模板功能

### 系统通用功能
- 标准化API响应
- 增强的API日志记录
- 国际化支持（多语言）
- API文档自动生成

## 技术栈

- **后端框架**：Django REST Framework
- **数据库**：MySQL
- **认证机制**：JWT（JSON Web Token）
- **API文档**：drf-spectacular (OpenAPI 3.0)
- **国际化**：Django内置i18n功能
- **日志管理**：自定义日志中间件

## 系统架构

### 应用模块
- **core**：核心配置和URL路由
- **users**：用户管理模块
- **tenants**：租户管理模块
- **check_system**：打卡系统模块
- **common**：通用功能模块（中间件、认证、异常处理等）
- **docs_view**：文档查看模块

### 数据模型
- **Tenant**：租户信息和配额管理
- **User**：扩展Django用户模型，支持租户隔离和多角色
- **Task**、**TaskCategory**、**CheckRecord**：打卡系统相关模型

### 中间件
- **TenantMiddleware**：租户上下文处理
- **EnhancedAPILoggingMiddleware**：API请求日志记录
- **ResponseStandardizationMiddleware**：响应格式标准化

## API接口

系统提供了完整的REST API，遵循RESTful设计原则：

- **/api/v1/auth/**：认证相关接口（登录、注册、刷新token等）
- **/api/v1/users/**：用户管理接口
- **/api/v1/tenants/**：租户管理接口
- **/api/v1/check-system/**：打卡系统接口
- **/api/v1/common/**：通用功能接口

所有API接口均通过Swagger UI和ReDoc提供交互式文档，便于开发和调试。

### API文档访问
- Swagger UI: `/api/v1/docs/`
- ReDoc: `/api/v1/redoc/`
- OpenAPI Schema: `/api/v1/schema/`

## 安全特性

- JWT认证，确保API安全访问
- 数据隔离，防止跨租户数据泄露
- 请求日志记录，便于安全审计
- 配额限制，防止资源滥用

## 扩展性设计

项目采用模块化设计，便于功能扩展：

1. 可轻松添加新的应用模块
2. 租户隔离架构支持多种业务场景
3. 通用组件可在不同模块间复用
4. API设计支持版本控制

## 部署指南

### 环境要求
- Python 3.9+
- MySQL 5.7+
- 适当的服务器配置（根据预期负载）
- HTTPS配置（生产环境）

### 快速部署步骤
1. 克隆代码仓库
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. 创建虚拟环境并安装依赖
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. 配置环境变量（创建.env文件）
   ```
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,localhost
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

4. 运行数据库迁移
   ```bash
   python manage.py migrate
   ```

5. 创建超级管理员
   ```bash
   python manage.py createsuperuser
   ```

6. 收集静态文件
   ```bash
   python manage.py collectstatic --noinput
   ```

7. 创建租户管理员（可选）
   ```bash
   python create_tenant_admin.py
   ```

8. 启动服务器
   ```bash
   gunicorn core.wsgi:application --bind 0.0.0.0:8000
   ```

### 生产环境部署
详细的生产环境部署指南请参考 `docs/setup_guide.md`

## 开发流程

项目采用标准的Django开发流程，支持以下开发活动：

- 使用Django迁移系统管理数据库变更
- 通过Django Shell进行调试和数据操作
- 使用Django测试框架进行单元测试和集成测试
- 遵循Django最佳实践进行代码组织和管理

## 项目维护

### 日志管理
日志文件存储在 `logs/` 目录下，默认配置包括：
- `debug.log`：系统日志，每天自动轮换，保留30天

### 数据备份
建议定期备份数据库，保障数据安全：
```bash
mysqldump -u <user> -p <database_name> > backup_$(date +%Y%m%d).sql
```

### 定期维护
- 检查日志文件大小和轮换状态
- 更新依赖包版本
- 检查系统安全漏洞 