# 认证和权限详解

## 认证系统概述

Licenses API使用基于JWT (JSON Web Token) 的认证机制，支持多租户环境下的精细权限控制。

## JWT认证流程

### 1. 获取访问令牌

#### 请求
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
    "username": "admin@company.com",
    "password": "your_password"
}
```

#### 响应
```json
{
    "success": true,
    "data": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "admin@company.com",
            "is_super_admin": true,
            "tenant": {
                "id": 1,
                "name": "示例公司"
            }
        }
    }
}
```

#### 字段说明
- `access` - 访问令牌，有效期通常为1小时
- `refresh` - 刷新令牌，用于获取新的访问令牌
- `user.is_super_admin` - 是否为超级管理员
- `user.tenant` - 用户所属租户信息

### 2. 使用访问令牌

在所有需要认证的API请求中包含Authorization头：

```http
GET /api/v1/licenses/admin/products/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

### 3. 刷新访问令牌

当访问令牌过期时，使用刷新令牌获取新的访问令牌：

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 用户角色和权限

### 用户类型

#### 1. 超级管理员 (Super Admin)
**标识**: `user.is_super_admin = true`

**权限范围**:
- 访问所有租户的数据
- 创建和管理租户
- 管理系统级配置
- 查看全局统计和报告

**API访问权限**:
```json
{
    "管理API": "全部可访问",
    "客户端API": "全部可访问", 
    "报告API": "全部可访问",
    "数据范围": "所有租户数据"
}
```

#### 2. 租户管理员 (Tenant Admin)
**标识**: `user.tenant` 存在且不为空

**权限范围**:
- 仅访问自己租户的数据
- 管理租户内的产品和许可证
- 查看租户内的统计报告

**API访问权限**:
```json
{
    "管理API": "租户范围内可访问",
    "客户端API": "需要许可证验证",
    "报告API": "租户范围内可访问", 
    "数据范围": "仅本租户数据"
}
```

#### 3. 匿名用户 (Anonymous)
**标识**: 无JWT Token或Token无效

**权限范围**:
- 仅访问公开的客户端API
- 需要提供有效的许可证信息进行验证

**API访问权限**:
```json
{
    "管理API": "禁止访问",
    "客户端API": "部分可访问(需许可证验证)",
    "报告API": "禁止访问",
    "数据范围": "仅许可证相关数据"
}
```

## 权限验证机制

### 1. 认证类 (Authentication Classes)
所有管理API使用 `JWTAuthentication`:

```python
authentication_classes = [JWTAuthentication]
```

客户端API使用 `AllowAny` 或基于许可证的验证:

```python
permission_classes = [AllowAny]
# 在视图函数内进行许可证验证
```

### 2. 权限类 (Permission Classes)
管理API使用 `IsSuperAdminOrTenantAdmin`:

```python
permission_classes = [IsSuperAdminOrTenantAdmin]
```

**权限逻辑**:
- 超级管理员：允许所有操作
- 租户管理员：仅允许本租户范围内的操作
- 其他用户：拒绝访问

### 3. 数据过滤 (QuerySet Filtering)
每个ViewSet的 `get_queryset()` 方法实现租户级数据隔离：

```python
def get_queryset(self):
    queryset = Model.objects.filter(is_deleted=False)
    
    if self.request.user.is_super_admin:
        return queryset
    
    # 租户管理员只能访问本租户数据
    if hasattr(self.request.user, 'tenant'):
        return queryset.filter(tenant=self.request.user.tenant)
    
    return queryset.none()
```

## 具体API权限说明

### 管理API权限矩阵

| API端点 | 超级管理员 | 租户管理员 | 数据范围 |
|---------|-----------|-----------|----------|
| 软件产品管理 | ✅ 全部 | ✅ 有配额的产品 | 通过租户配额关联 |
| 许可证方案管理 | ✅ 全部 | ✅ 授权产品的方案 | 产品权限继承 |
| 许可证管理 | ✅ 全部 | ✅ 本租户许可证 | tenant字段过滤 |
| 机器绑定管理 | ✅ 全部 | ✅ 本租户设备 | 通过许可证关联 |
| 激活记录查看 | ✅ 全部 | ✅ 本租户记录 | 通过许可证关联 |
| 安全审计日志 | ✅ 全部 | ✅ 本租户+全局日志 | tenant字段过滤 |
| 租户配额管理 | ✅ 全部 | ✅ 本租户配额 | tenant字段过滤 |

### 客户端API权限说明

| API端点 | 认证要求 | 验证方式 |
|---------|----------|----------|
| 许可证激活 | 无需JWT | 许可证密钥验证 |
| 激活状态验证 | 无需JWT | 激活码+机器指纹 |
| 心跳检测 | 无需JWT | 激活码验证 |
| 许可证信息查询 | 无需JWT | 许可证密钥验证 |
| 服务状态查询 | 无需JWT | 无验证 |

## 安全最佳实践

### 1. Token安全
- **安全存储**: 在客户端安全存储JWT Token
- **HTTPS传输**: 仅在HTTPS连接上传输Token
- **及时刷新**: 在Token过期前主动刷新
- **安全清除**: 登出时清除所有Token

### 2. 权限验证
- **最小权限原则**: 仅授予必要的权限
- **定期审查**: 定期检查用户权限
- **异常监控**: 监控权限异常访问

### 3. 租户隔离
- **数据隔离**: 严格的租户级数据过滤
- **API隔离**: 不同租户无法访问其他租户的API
- **日志记录**: 记录跨租户访问尝试

## 错误处理

### 认证错误

#### 401 Unauthorized - 未认证
```json
{
    "success": false,
    "error": "Authentication credentials were not provided.",
    "code": "NOT_AUTHENTICATED"
}
```

**常见原因**:
- 未提供Authorization头
- Token格式错误
- Token已过期

**解决方法**:
- 检查Authorization头格式
- 使用refresh token获取新的access token

#### 401 Unauthorized - Token无效
```json
{
    "success": false,
    "error": "Given token not valid for any token type",
    "code": "TOKEN_NOT_VALID"
}
```

**常见原因**:
- Token被篡改
- Token签名无效
- 使用了已撤销的Token

### 授权错误

#### 403 Forbidden - 权限不足
```json
{
    "success": false,
    "error": "You do not have permission to perform this action.",
    "code": "PERMISSION_DENIED"
}
```

**常见原因**:
- 用户角色权限不足
- 尝试访问其他租户的数据
- 操作超出权限范围

## 频率限制

### 限制规则
- **认证API**: 每小时10次登录尝试
- **管理API**: 每分钟100次请求
- **客户端API**: 每小时50次激活请求

### 限制响应
```json
{
    "success": false,
    "error": "Request was throttled. Expected available in 60 seconds.",
    "code": "THROTTLED",
    "retry_after": 60
}
```

### 避免限制
- 实现请求缓存
- 使用批量操作接口
- 合理的重试间隔

## 代码示例

### JavaScript/Node.js示例
```javascript
class LicenseAPIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.accessToken = null;
        this.refreshToken = null;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        if (data.success) {
            this.accessToken = data.data.access;
            this.refreshToken = data.data.refresh;
        }
        return data;
    }
    
    async apiCall(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        
        let response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers
        });
        
        // 自动刷新token
        if (response.status === 401 && this.refreshToken) {
            await this.refreshAccessToken();
            headers['Authorization'] = `Bearer ${this.accessToken}`;
            response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers
            });
        }
        
        return response.json();
    }
    
    async refreshAccessToken() {
        const response = await fetch(`${this.baseURL}/auth/token/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: this.refreshToken })
        });
        
        const data = await response.json();
        if (data.success) {
            this.accessToken = data.access;
        }
        return data;
    }
}

// 使用示例
const client = new LicenseAPIClient('https://api.example.com/api/v1/licenses');

// 登录
await client.login('admin@company.com', 'password');

// 调用API
const products = await client.apiCall('/admin/products/');
```

### Python示例
```python
import requests
import json
from typing import Optional

class LicenseAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()
    
    def login(self, username: str, password: str) -> dict:
        response = self.session.post(
            f"{self.base_url}/auth/login/",
            json={"username": username, "password": password}
        )
        data = response.json()
        
        if data.get('success'):
            self.access_token = data['data']['access']
            self.refresh_token = data['data']['refresh']
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
        
        return data
    
    def api_call(self, endpoint: str, method: str = 'GET', **kwargs) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        
        # 自动刷新token
        if response.status_code == 401 and self.refresh_token:
            self.refresh_access_token()
            response = self.session.request(method, url, **kwargs)
        
        return response.json()
    
    def refresh_access_token(self) -> dict:
        response = self.session.post(
            f"{self.base_url}/auth/token/refresh/",
            json={"refresh": self.refresh_token}
        )
        data = response.json()
        
        if data.get('success'):
            self.access_token = data['access']
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
        
        return data

# 使用示例
client = LicenseAPIClient('https://api.example.com/api/v1/licenses')

# 登录
login_result = client.login('admin@company.com', 'password')

# 调用API
products = client.api_call('/admin/products/')
```

## 调试指南

### 1. 验证Token有效性
使用JWT调试工具验证Token内容：
- 访问 https://jwt.io
- 粘贴Token查看负载信息
- 检查exp字段确认过期时间

### 2. 检查权限设置
```python
# Django shell中验证用户权限
from users.models import User
user = User.objects.get(username='your_username')
print(f"Is Super Admin: {user.is_super_admin}")
print(f"Tenant: {user.tenant.name if user.tenant else 'None'}")
```

### 3. 监控认证日志
查看认证相关的日志文件：
```bash
# 查看认证失败日志
grep "Authentication failed" /var/log/licenses/auth.log

# 查看权限拒绝日志  
grep "Permission denied" /var/log/licenses/auth.log
```

## 下一步

了解具体API的使用方法：
- [软件产品管理API](./10_admin_products_api.md)
- [许可证管理API](./12_admin_licenses_api.md)
- [客户端激活API](./20_client_activation_api.md)
