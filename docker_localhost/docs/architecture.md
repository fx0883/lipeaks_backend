# 多租户用户管理系统 - 系统架构设计

## 1. 系统概述

多租户用户管理系统是一个基于Django和Django REST Framework构建的后端服务，用于管理多个租户及其用户。系统支持租户隔离、用户角色管理、资源配额控制等核心功能，为SaaS应用提供基础的用户与权限管理能力。

## 2. 技术栈

- **后端框架**: Django 5.2
- **API框架**: Django REST Framework 
- **数据库**: MySQL
- **认证方式**: JWT (JSON Web Token)
- **API文档**: drf-spectacular
- **跨域支持**: django-cors-headers
- **环境变量管理**: python-dotenv

## 3. 系统架构

系统采用分层架构设计，主要分为以下几层：

1. **数据访问层**: 使用Django ORM实现，包含models定义
2. **业务逻辑层**: 包括权限验证、租户隔离等核心业务逻辑
3. **API接口层**: 基于Django REST Framework实现REST API
4. **跨层组件**: 包括认证机制、异常处理、日志记录等

### 3.1 核心应用架构

系统划分为三个主要应用：

1. **users**: 用户管理模块
   - 用户认证相关功能
   - 用户信息管理
   - 用户角色管理

2. **tenants**: 租户管理模块
   - 租户信息管理
   - 租户配额控制
   - 租户状态管理

3. **common**: 通用功能模块
   - 分页组件
   - 异常处理
   - 中间件
   - JWT认证
   - API日志记录

## 4. 数据模型

### 4.1 核心模型关系

```
User (users.models)
├── id: 主键
├── username: 用户名
├── email: 邮箱
├── password: 密码
├── tenant: 外键 -> Tenant
├── is_admin: 是否为管理员
├── is_super_admin: 是否为超级管理员
└── ...

Tenant (tenants.models)
├── id: 主键
├── name: 租户名称
├── status: 租户状态
├── contact_name: 联系人姓名
└── ...

TenantQuota (tenants.models)
├── id: 主键
├── tenant: 外键 -> Tenant
├── max_users: 最大用户数
├── max_admins: 最大管理员数
└── ...

APILog (common.models)
├── id: 主键
├── user: 外键 -> User
├── tenant: 外键 -> Tenant
├── request_method: 请求方法
├── request_path: 请求路径
└── ...
```

## 5. 认证与权限

### 5.1 认证机制

系统使用JWT认证机制，主要实现在`common.authentication.jwt_auth`模块：

- `JWTAuthentication`: 自定义的DRF认证类
- `generate_jwt_token`: 生成JWT令牌函数
- `refresh_jwt_token`: 刷新JWT令牌函数

认证流程：
1. 用户通过登录API获取JWT令牌
2. 用户在后续请求中通过Authorization头携带令牌
3. 服务器验证令牌有效性并识别用户身份

### 5.2 权限控制

系统采用多层权限控制：

1. **超级管理员**: 可以管理所有租户和用户
2. **租户管理员**: 可以管理所属租户内的用户
3. **普通用户**: 只能访问自己的信息和有限的资源

权限验证通过自定义的Permission类实现。

## 6. API设计

API遵循RESTful设计原则，主要分为以下几类：

1. **认证类API**:
   - `/api/v1/auth/login/`: 用户登录
   - `/api/v1/auth/refresh/`: 刷新令牌
   - `/api/v1/auth/verify/`: 验证令牌

2. **用户类API**:
   - `/api/v1/users/me/`: 获取当前用户信息
   - `/api/v1/users/`: 用户列表和创建
   - `/api/v1/users/<id>/`: 用户详情、更新和删除

3. **租户类API**:
   - `/api/v1/tenants/`: 租户列表和创建
   - `/api/v1/tenants/<id>/`: 租户详情、更新和删除
   - `/api/v1/tenants/<id>/quota/`: 租户配额管理

API响应格式统一为：

```json
{
  "success": true/false,
  "code": 2000,
  "message": "操作成功/失败信息",
  "data": { ... }
}
```

## 7. 中间件

系统实现了两个核心中间件：

1. **TenantMiddleware**: 处理租户上下文，实现租户隔离
2. **APILoggingMiddleware**: 记录API请求日志，便于审计和调试

## 8. 异常处理

系统实现了统一的异常处理机制，主要通过`common.exceptions.custom_exception_handler`函数实现，处理包括：

- DRF内置异常
- 自定义业务异常
- 系统未捕获异常

所有异常响应统一格式化，确保API响应格式一致性。

## 9. 部署架构

系统可以采用以下部署架构：

1. **开发环境**: 单机部署，使用Django内置服务器
2. **生产环境**: Nginx + Gunicorn + Django + MySQL

推荐使用Docker容器化部署，可以使用docker-compose编排服务。

## 10. 安全考虑

1. **传输安全**: 使用HTTPS加密传输
2. **认证安全**: 基于JWT的身份验证，定期轮换密钥
3. **权限控制**: 细粒度的权限控制机制
4. **数据隔离**: 租户数据隔离，防止越权访问
5. **日志记录**: 关键操作日志记录，便于审计

## 11. 扩展性设计

系统设计考虑了以下扩展性因素：

1. **水平扩展**: 无状态API设计，便于负载均衡
2. **功能扩展**: 模块化设计，便于添加新功能
3. **租户隔离**: 多租户设计，支持业务隔离 