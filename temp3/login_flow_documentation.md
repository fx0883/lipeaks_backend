# 多租户用户管理系统登录流程详细文档

## 1. 系统概述

本系统采用基于JWT的认证机制，支持多租户架构，包含两种用户类型：
- **管理员用户（User）**：包括超级管理员和租户管理员
- **普通成员（Member）**：包括普通成员和子账号

## 2. 用户类型与模型架构

### 2.1 用户模型结构

#### BaseUserModel（抽象基类）
位置：`users/models.py`
```python
class BaseUserModel(AbstractUser):
    # 租户关联
    tenant = models.ForeignKey('tenants.Tenant', ...)
    
    # 用户信息
    phone = models.CharField(...)
    email = models.EmailField(...)
    nick_name = models.CharField(...)
    avatar = models.CharField(...)
    wechat_id = models.CharField(...)
    
    # 状态管理
    status = models.CharField(...)  # active, suspended, inactive
    is_deleted = models.BooleanField(...)
    last_login_ip = models.CharField(...)
```

#### User（管理员用户）
```python
class User(BaseUserModel):
    is_admin = models.BooleanField(default=True)
    is_super_admin = models.BooleanField(default=False)
    
    # 超级管理员：不关联租户，全局权限
    # 租户管理员：关联特定租户，租户内权限
```

#### Member（普通成员）
```python
class Member(BaseUserModel):
    parent = models.ForeignKey('self', ...)  # 子账号功能
    
    # 普通成员：关联租户，基础权限
    # 子账号：不允许登录，仅作为数据展示
```

### 2.2 租户隔离机制

- **超级管理员**：无租户关联，可通过`X-Tenant-ID`请求头访问任意租户数据
- **租户管理员**：固定关联特定租户，只能访问所属租户数据
- **普通成员**：固定关联特定租户，登录时必须携带`X-Tenant-ID`请求头

## 3. JWT认证机制

### 3.1 JWT令牌结构

#### 访问令牌（Access Token）
```python
access_payload = {
    'user_id': user.id,
    'username': user.username,
    'exp': token_expiry,  # 过期时间
    'model_type': 'user' | 'member',  # 用户类型标识
    'is_admin': bool,
    'is_super_admin': bool
}
```

#### 刷新令牌（Refresh Token）
```python
refresh_payload = {
    'user_id': user.id,
    'model_type': 'user' | 'member',
    'exp': refresh_expiry,
    'token_type': 'refresh'
}
```

### 3.2 JWT认证类
位置：`common/authentication/jwt_auth.py`

```python
class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # 1. 提取Bearer令牌
        # 2. 验证令牌有效性和过期时间
        # 3. 根据model_type获取对应用户
        # 4. 检查用户状态和租户状态
        # 5. 返回(user, token)元组
```

## 4. 登录流程图

### 4.1 完整登录流程

```mermaid
flowchart TD
    A[客户端发起登录请求] --> B{检查请求头X-Tenant-ID}
    
    B -->|有X-Tenant-ID| C[成员登录流程]
    B -->|无X-Tenant-ID| D[管理员登录流程]
    
    %% 成员登录流程
    C --> C1[验证X-Tenant-ID格式]
    C1 -->|无效| C2[返回4001错误]
    C1 -->|有效| C3[在Member表中查找用户]
    C3 --> C4{找到匹配成员?}
    C4 -->|否| C5[检查是否匹配管理员账号]
    C5 -->|是管理员| C6[返回4001错误：管理员禁用Header]
    C5 -->|非管理员| C7[返回登录失败]
    C4 -->|是| C8[验证密码]
    C8 -->|失败| C7
    C8 -->|成功| C9[检查成员状态]
    
    %% 管理员登录流程  
    D --> D1[在User表中查找用户]
    D1 --> D2{找到匹配用户?}
    D2 -->|否| D3[检查是否为成员且需要Header]
    D3 -->|是成员| D4[返回4001错误：成员必须使用Header]
    D3 -->|非成员| D5[返回登录失败]
    D2 -->|是| D6[验证密码]
    D6 -->|失败| D5
    D6 -->|成功| D7[检查管理员状态]
    
    %% 状态检查
    C9 --> E[通用状态检查]
    D7 --> E
    E --> E1{用户是否激活?}
    E1 -->|否| E2[返回用户已禁用错误]
    E1 -->|是| E3{是否被删除?}
    E3 -->|是| E4[返回用户已删除错误]
    E3 -->|否| E5{是否为子账号?}
    E5 -->|是| E6[返回子账号不允许登录错误]
    E5 -->|否| E7{租户状态检查}
    E7 -->|租户异常| E8[返回租户状态异常错误]
    E7 -->|租户正常| F[生成JWT令牌]
    
    %% JWT令牌生成
    F --> F1[生成访问令牌]
    F1 --> F2[生成刷新令牌]
    F2 --> F3[记录登录IP和时间]
    F3 --> F4[构建用户信息响应]
    F4 --> G[返回登录成功响应]
    
    %% 错误处理
    C2 --> H[记录错误日志]
    C6 --> H
    C7 --> H
    D4 --> H
    D5 --> H
    E2 --> H
    E4 --> H
    E6 --> H
    E8 --> H
    H --> I[返回错误响应]
    
    %% 成功响应
    G --> J[客户端接收令牌]
    J --> K[后续请求携带Bearer令牌]
```

### 4.2 中间件认证流程

```mermaid
flowchart TD
    A[API请求到达] --> B[APIAuthMiddleware]
    B --> B1{是否为API路径?}
    B1 -->|否| B2[跳过JWT认证]
    B1 -->|是| B3{是否有Bearer令牌?}
    B3 -->|否| B4[跳过JWT认证，继续处理]
    B3 -->|是| B5[解析JWT令牌]
    
    B5 --> B6{令牌是否有效?}
    B6 -->|否| B7[返回401认证失败]
    B6 -->|是| B8[根据model_type获取用户]
    B8 --> B9{用户是否存在且激活?}
    B9 -->|否| B10[返回401用户不存在]
    B9 -->|是| B11[设置request.user]
    B11 --> B12[标记auth_type=jwt]
    
    B12 --> C[TenantMiddleware]
    C --> C1{路径是否需要租户验证?}
    C1 -->|否| C2[跳过租户验证]
    C1 -->|是| C3[提取租户信息]
    
    C3 --> C4[从X-Tenant-ID获取租户ID]
    C4 --> C5[从用户关联获取租户ID]
    C5 --> C6{用户类型检查}
    
    C6 --> C7{是否超级管理员?}
    C7 -->|是| C8[允许跨租户访问]
    C7 -->|否| C9[验证租户权限]
    C9 --> C10{租户ID是否匹配?}
    C10 -->|否| C11[返回403权限不足]
    C10 -->|是| C12[设置租户上下文]
    
    C8 --> D[进入业务处理]
    C12 --> D
    C2 --> D
    B2 --> D
    B4 --> D
```

### 4.3 令牌刷新流程

```mermaid
flowchart TD
    A[客户端发起刷新请求] --> B[TokenRefreshView]
    B --> B1[验证请求数据]
    B1 --> B2{刷新令牌格式正确?}
    B2 -->|否| B3[返回400无效令牌]
    B2 -->|是| B4[解析刷新令牌]
    
    B4 --> B5{令牌是否过期?}
    B5 -->|是| B6[返回401令牌过期]
    B5 -->|否| B7{是否为刷新令牌类型?}
    B7 -->|否| B8[返回401令牌类型错误]
    B7 -->|是| B9[获取用户ID和类型]
    
    B9 --> B10{用户是否存在?}
    B10 -->|否| B11[返回401用户不存在]
    B10 -->|是| B12[检查用户状态]
    B12 --> B13{状态是否正常?}
    B13 -->|否| B14[返回401状态异常]
    B13 -->|是| B15[检查租户状态]
    
    B15 --> B16{租户状态正常?}
    B16 -->|否| B17[返回401租户异常]
    B16 -->|是| B18[生成新的令牌对]
    B18 --> B19[返回新令牌]
```

## 5. 核心组件详解

### 5.1 认证视图类

#### LoginView
位置：`users/views/auth_views.py`

**主要功能**：
- 处理用户登录请求
- 支持用户名/邮箱登录
- 区分管理员和成员登录
- 租户头验证
- JWT令牌生成

**关键方法**：
```python
def post(self, request):
    # 1. 数据验证（LoginSerializer）
    # 2. 用户认证和状态检查
    # 3. JWT令牌生成
    # 4. 登录信息记录
    # 5. 响应构建
```

#### TokenRefreshView
**主要功能**：
- 刷新访问令牌
- 验证刷新令牌有效性
- 用户状态重新检查
- 生成新的令牌对

#### TokenVerifyView
**主要功能**：
- 验证当前令牌有效性
- 返回用户信息
- 需要认证访问

### 5.2 序列化器

#### LoginSerializer
位置：`users/serializers.py`

**核心验证逻辑**：
```python
def validate(self, data):
    # 1. 获取X-Tenant-ID请求头
    # 2. 根据请求头决定登录流程
    # 3. 成员流程：在Member表中查找
    # 4. 管理员流程：在User表中查找
    # 5. 交叉验证：防止类型混淆
    # 6. 状态检查：激活、删除、子账号等
```

**租户头规则**：
- 有`X-Tenant-ID` → 强制成员流程
- 无`X-Tenant-ID` → 仅允许管理员流程
- 管理员携带租户头 → 返回4001错误
- 成员不携带租户头 → 返回4001错误

### 5.3 中间件组件

#### APIAuthMiddleware
位置：`common/middleware/api_auth_middleware.py`

**处理流程**：
1. 检查请求路径（仅处理`/api/`路径）
2. 提取Bearer令牌
3. 验证JWT令牌
4. 获取用户对象
5. 状态检查
6. 设置`request.user`

**跳过条件**：
- 非API路径
- 静态资源路径
- API文档路径
- 无Bearer令牌

#### TenantMiddleware
位置：`common/middleware/tenant_middleware.py`

**租户验证逻辑**：
1. 路径筛选（仅CMS相关路径需要租户）
2. 租户ID提取（查询参数 > 请求头 > 用户关联）
3. 用户类型检查
4. 权限验证
5. 租户上下文设置

**特殊规则**：
- 超级管理员可通过`X-Tenant-ID`跨租户访问
- GET请求允许匿名但需租户ID
- 非GET请求需要认证和租户关联

## 6. API接口规范

### 6.1 登录接口

#### 管理员登录
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
    "username": "admin@example.com",
    "password": "password123"
}
```

**响应**：
```json
{
    "success": true,
    "code": 2000,
    "message": "登录成功",
    "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "is_admin": true,
            "is_super_admin": false,
            "is_member": false,
            "tenant_id": 1,
            "tenant_name": "示例租户"
        }
    }
}
```

#### 成员登录
```http
POST /api/v1/auth/login/
Content-Type: application/json
X-Tenant-ID: 1

{
    "username": "member@example.com", 
    "password": "password123"
}
```

**响应**：
```json
{
    "success": true,
    "code": 2000,
    "message": "登录成功",
    "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "id": 1,
            "username": "member",
            "email": "member@example.com",
            "is_admin": false,
            "is_super_admin": false,
            "is_member": true,
            "is_sub_account": false,
            "tenant_id": 1,
            "tenant_name": "示例租户"
        }
    }
}
```

### 6.2 令牌刷新接口

```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 6.3 令牌验证接口

```http
GET /api/v1/auth/verify/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 6.4 注册接口

#### 管理员注册
```http
POST /api/v1/auth/register/
Content-Type: application/json

{
    "username": "newadmin",
    "email": "newadmin@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "tenant_id": 1
}
```

#### 成员注册
```http
POST /api/v1/auth/member/register/
Content-Type: application/json
X-Tenant-ID: 1

{
    "username": "newmember",
    "email": "newmember@example.com", 
    "password": "password123",
    "password_confirm": "password123"
}
```

## 7. 安全机制

### 7.1 密码安全
- **密码验证**：使用Django内置密码验证器
- **密码哈希**：采用PBKDF2算法存储
- **密码重置**：基于邮箱的安全重置流程

### 7.2 令牌安全
- **访问令牌过期**：短期有效（通常1小时）
- **刷新令牌过期**：长期有效（通常7天）
- **令牌撤销**：支持令牌黑名单机制
- **算法安全**：使用HS256算法签名

### 7.3 租户隔离
- **数据隔离**：基于租户ID的数据访问控制
- **权限验证**：中间件层面的租户权限检查
- **跨租户访问**：仅超级管理员允许

### 7.4 请求安全
- **IP记录**：记录登录IP地址
- **频率限制**：防止暴力破解攻击
- **请求验证**：严格的参数验证和类型检查

## 8. 错误处理和响应码

### 8.1 认证错误
- **4001**：认证失败（令牌无效、过期、用户不存在等）
- **4002**：用户名/密码错误
- **4003**：权限不足（租户不匹配、角色权限等）

### 8.2 验证错误
- **4000**：请求数据验证失败
- **TenantHeaderInvalidOrMissing**：租户头缺失或无效

### 8.3 服务器错误
- **5000**：内部服务器错误

## 9. 配置和环境

### 9.1 JWT配置
```python
# settings.py
JWT_AUTH = {
    'JWT_SECRET_KEY': 'your-secret-key',
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRATION_DELTA': 3600,  # 1小时
    'JWT_REFRESH_EXPIRATION_DELTA': 604800,  # 7天
}
```

### 9.2 中间件配置
```python
MIDDLEWARE = [
    # ... 其他中间件
    'common.middleware.api_auth_middleware.APIAuthMiddleware',
    'common.middleware.tenant_middleware.TenantMiddleware',
    # ... 其他中间件
]
```

### 9.3 认证配置
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'common.authentication.jwt_auth.JWTAuthentication',
        # ... 其他认证类
    ],
}
```

## 10. 部署和维护

### 10.1 日志记录
系统在关键节点记录详细日志：
- 登录成功/失败
- 令牌刷新
- 权限检查
- 错误处理

### 10.2 监控指标
建议监控的关键指标：
- 登录成功率
- 令牌刷新频率
- 认证失败次数
- 响应时间

### 10.3 安全审计
定期检查：
- 令牌有效期设置
- 密码强度策略
- 访问日志审计
- 异常登录行为

---

## 附录：相关文件清单

### 核心文件
- `users/models.py` - 用户模型定义
- `users/views/auth_views.py` - 认证视图
- `users/serializers.py` - 序列化器
- `users/urls/auth_urls.py` - 认证路由
- `common/authentication/jwt_auth.py` - JWT认证类
- `common/middleware/api_auth_middleware.py` - API认证中间件
- `common/middleware/tenant_middleware.py` - 租户中间件

### 工具文件
- `common/utils/tenant_header.py` - 租户头处理工具
- `common/exceptions/__init__.py` - 自定义异常
- `common/utils/tenant_context.py` - 租户上下文管理

该文档详细描述了整个登录认证系统的架构、流程和实现细节，为系统维护和新功能开发提供了完整的参考。
