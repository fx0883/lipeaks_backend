# 软件产品管理API

## 概述

软件产品管理API提供软件产品的完整生命周期管理功能，包括产品创建、密钥对管理、统计信息查询等。

**Base URL**: `/api/v1/licenses/admin/products/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  

## 数据模型

### SoftwareProduct 字段详解

| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `id` | integer | 只读 | 产品唯一标识符 | 数据库自动生成 |
| `name` | string(100) | 是 | 产品名称 | 用户输入 |
| `code` | string(50) | 是 | 产品代码，全局唯一 | 用户输入，自动验证唯一性 |
| `description` | text | 否 | 产品描述 | 用户输入 |
| `version` | string(20) | 否 | 产品版本号 | 用户输入，默认"1.0.0" |
| `public_key` | text | 只读 | RSA公钥 | 创建时自动生成 |
| `private_key_hash` | string(64) | 只读 | 私钥哈希值 | 创建时自动生成 |
| `max_activations` | integer | 否 | 最大激活数限制 | 用户输入，默认5 |
| `offline_days` | integer | 否 | 离线允许天数 | 用户输入，默认30 |
| `status` | string(20) | 否 | 产品状态 | 用户选择，默认"active" |
| `created_at` | datetime | 只读 | 创建时间 | 自动设置 |
| `updated_at` | datetime | 只读 | 更新时间 | 自动更新 |
| `license_plans_count` | integer | 只读 | 许可方案数量 | 实时计算 |
| `total_licenses` | integer | 只读 | 许可证总数 | 实时计算 |

### 状态枚举值

#### status字段可选值:
- `active` - 启用：产品可正常使用，支持新许可证生成
- `inactive` - 禁用：产品暂停使用，不支持新许可证生成
- `deprecated` - 已弃用：产品不再维护，建议迁移

## API端点详解

### 1. 获取产品列表

#### 请求
```http
GET /api/v1/licenses/admin/products/
Authorization: Bearer {access_token}
```

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `page` | integer | 否 | 页码，从1开始 | `page=2` |
| `page_size` | integer | 否 | 每页条数，最大100 | `page_size=20` |
| `search` | string | 否 | 搜索关键词，支持产品名、代码、描述 | `search=MyApp` |
| `status` | string | 否 | 按状态过滤 | `status=active` |
| `ordering` | string | 否 | 排序字段 | `ordering=-created_at` |

#### 排序字段选项:
- `name` - 按名称排序
- `created_at` - 按创建时间排序  
- `updated_at` - 按更新时间排序
- 添加`-`前缀表示降序，如`-created_at`

#### 响应示例
```json
{
    "success": true,
    "data": {
        "count": 25,
        "next": "https://api.example.com/api/v1/licenses/admin/products/?page=3",
        "previous": "https://api.example.com/api/v1/licenses/admin/products/?page=1",
        "results": [
            {
                "id": 1,
                "name": "MyApplication Pro",
                "code": "MYAPP_PRO",
                "description": "专业版应用软件",
                "version": "2.1.0",
                "max_activations": 10,
                "offline_days": 30,
                "status": "active",
                "license_plans_count": 3,
                "total_licenses": 150,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:25:00Z"
            }
        ]
    }
}
```

#### 权限说明
- **超级管理员**: 查看所有产品
- **租户管理员**: 仅查看有配额授权的产品（通过`TenantLicenseQuota`关联）

### 2. 创建软件产品

#### 请求
```http
POST /api/v1/licenses/admin/products/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "新产品名称",
    "code": "NEW_PRODUCT_CODE",
    "description": "产品描述信息",
    "version": "1.0.0",
    "max_activations": 5,
    "offline_days": 30,
    "generate_keypair": true
}
```

#### 请求字段详解

| 字段名 | 类型 | 必填 | 说明 | 验证规则 |
|--------|------|------|------|----------|
| `name` | string | 是 | 产品名称 | 最大100字符 |
| `code` | string | 是 | 产品代码 | 最大50字符，全局唯一，建议使用大写字母和下划线 |
| `description` | string | 否 | 产品描述 | 无限制 |
| `version` | string | 否 | 版本号 | 最大20字符，建议语义化版本 |
| `max_activations` | integer | 否 | 最大激活数 | 正整数，默认5 |
| `offline_days` | integer | 否 | 离线天数 | 正整数，默认30 |
| `generate_keypair` | boolean | 否 | 是否生成密钥对 | 默认true |

#### 密钥对生成逻辑
当 `generate_keypair=true` 时（默认值），系统会：
1. 生成2048位RSA密钥对
2. 私钥进行SHA-256哈希存储
3. 公钥以PEM格式存储
4. 私钥仅在内存中处理，不持久化原文

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 15,
        "name": "新产品名称",
        "code": "NEW_PRODUCT_CODE",
        "description": "产品描述信息",
        "version": "1.0.0",
        "max_activations": 5,
        "offline_days": 30,
        "status": "active",
        "license_plans_count": 0,
        "total_licenses": 0,
        "created_at": "2024-01-25T16:45:00Z",
        "updated_at": "2024-01-25T16:45:00Z"
    },
    "message": "软件产品创建成功"
}
```

#### 可能的错误

##### 400 Bad Request - 产品代码重复
```json
{
    "success": false,
    "error": "产品代码已存在",
    "code": "DUPLICATE_PRODUCT_CODE",
    "details": {
        "field": "code",
        "value": "EXISTING_CODE"
    }
}
```

##### 400 Bad Request - 验证失败
```json
{
    "success": false,
    "error": "数据验证失败",
    "code": "VALIDATION_ERROR",
    "details": {
        "name": ["此字段是必需的"],
        "max_activations": ["确保这个值大于或等于 1"]
    }
}
```

### 3. 获取产品详情

#### 请求
```http
GET /api/v1/licenses/admin/products/{id}/
Authorization: Bearer {access_token}
```

#### 路径参数
- `id` (integer): 产品ID

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "MyApplication Pro",
        "code": "MYAPP_PRO",
        "description": "专业版应用软件，支持高级功能",
        "version": "2.1.0",
        "max_activations": 10,
        "offline_days": 30,
        "status": "active",
        "license_plans_count": 3,
        "total_licenses": 150,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-20T14:25:00Z"
    }
}
```

### 4. 更新软件产品

#### 完整更新 (PUT)
```http
PUT /api/v1/licenses/admin/products/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "更新的产品名称",
    "code": "UPDATED_CODE",
    "description": "更新后的描述",
    "version": "2.0.0",
    "max_activations": 15,
    "offline_days": 45,
    "status": "active"
}
```

#### 部分更新 (PATCH)
```http
PATCH /api/v1/licenses/admin/products/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "status": "inactive",
    "max_activations": 20
}
```

#### 注意事项
- `code`字段更新时仍需保持全局唯一性
- 状态改为`inactive`会影响新许可证的生成
- 已有许可证不受产品更新影响

### 5. 删除软件产品

#### 请求
```http
DELETE /api/v1/licenses/admin/products/{id}/
Authorization: Bearer {access_token}
```

#### 响应
```http
HTTP/1.1 204 No Content
```

#### 删除逻辑
- 执行软删除，设置`is_deleted=true`
- 相关许可证不会被删除，但无法创建新的许可证
- 可以通过数据库直接恢复（设置`is_deleted=false`）

#### 删除限制
如果产品下存在活跃的许可证，可能会返回错误：
```json
{
    "success": false,
    "error": "无法删除含有活跃许可证的产品",
    "code": "PRODUCT_HAS_ACTIVE_LICENSES",
    "details": {
        "active_licenses_count": 25
    }
}
```

## 自定义操作

### 1. 重新生成密钥对

#### 请求
```http
POST /api/v1/licenses/admin/products/{id}/regenerate_keypair/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "confirm": true,
    "reason": "密钥泄露，需要重新生成"
}
```

#### 请求字段
- `confirm` (boolean, 必填): 确认操作，必须为true
- `reason` (string, 可选): 重新生成原因，用于审计

#### 响应示例
```json
{
    "success": true,
    "message": "密钥对重新生成成功",
    "data": {
        "public_key_preview": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEF...",
        "generated_at": "2024-01-25T17:30:00Z"
    }
}
```

#### 重要说明
- 重新生成后，旧的许可证签名验证可能失效
- 建议在维护窗口期执行此操作
- 操作会记录在安全审计日志中

### 2. 获取产品统计信息

#### 请求
```http
GET /api/v1/licenses/admin/products/{id}/statistics/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "product_id": 1,
        "product_name": "MyApplication Pro",
        "licenses": {
            "total": 150,
            "active": 120,
            "expired": 25,
            "revoked": 5
        },
        "activations": {
            "total": 450,
            "successful": 430,
            "failed": 20,
            "last_30_days": 45
        },
        "machine_bindings": {
            "total": 380,
            "active_machines": 340,
            "blocked_machines": 15
        },
        "generated_at": "2024-01-25T18:00:00Z"
    }
}
```

#### 统计字段说明

##### licenses统计
- `total`: 产品下所有许可证总数
- `active`: 状态为已激活的许可证数
- `expired`: 已过期的许可证数  
- `revoked`: 已撤销的许可证数

##### activations统计
- `total`: 总激活次数
- `successful`: 成功激活次数
- `failed`: 失败激活次数
- `last_30_days`: 最近30天激活次数

##### machine_bindings统计
- `total`: 总机器绑定数
- `active_machines`: 活跃机器数
- `blocked_machines`: 被阻止的机器数

## 使用示例

### JavaScript示例

```javascript
class ProductManager {
    constructor(apiClient) {
        this.api = apiClient;
    }
    
    // 获取产品列表
    async getProducts(filters = {}) {
        const params = new URLSearchParams(filters);
        return await this.api.apiCall(`/admin/products/?${params}`);
    }
    
    // 创建产品
    async createProduct(productData) {
        return await this.api.apiCall('/admin/products/', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    }
    
    // 获取产品详情
    async getProduct(productId) {
        return await this.api.apiCall(`/admin/products/${productId}/`);
    }
    
    // 更新产品
    async updateProduct(productId, updates) {
        return await this.api.apiCall(`/admin/products/${productId}/`, {
            method: 'PATCH',
            body: JSON.stringify(updates)
        });
    }
    
    // 重新生成密钥对
    async regenerateKeypair(productId, reason = '') {
        return await this.api.apiCall(`/admin/products/${productId}/regenerate_keypair/`, {
            method: 'POST',
            body: JSON.stringify({
                confirm: true,
                reason: reason
            })
        });
    }
    
    // 获取产品统计
    async getProductStats(productId) {
        return await this.api.apiCall(`/admin/products/${productId}/statistics/`);
    }
}

// 使用示例
const productManager = new ProductManager(apiClient);

// 创建新产品
const newProduct = await productManager.createProduct({
    name: "新软件产品",
    code: "NEW_SOFTWARE",
    description: "这是一个新的软件产品",
    version: "1.0.0",
    max_activations: 10,
    offline_days: 30
});

// 获取产品列表（仅活跃状态）
const activeProducts = await productManager.getProducts({
    status: 'active',
    ordering: '-created_at'
});

// 获取产品统计信息
const stats = await productManager.getProductStats(1);
console.log(`产品总许可证数: ${stats.data.licenses.total}`);
```

### Python示例

```python
class ProductManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def get_products(self, **filters):
        """获取产品列表"""
        params = '&'.join(f'{k}={v}' for k, v in filters.items())
        endpoint = f'/admin/products/?{params}' if params else '/admin/products/'
        return self.api.api_call(endpoint)
    
    def create_product(self, product_data):
        """创建产品"""
        return self.api.api_call('/admin/products/', 
                                method='POST', 
                                json=product_data)
    
    def get_product(self, product_id):
        """获取产品详情"""
        return self.api.api_call(f'/admin/products/{product_id}/')
    
    def update_product(self, product_id, updates):
        """更新产品"""
        return self.api.api_call(f'/admin/products/{product_id}/', 
                                method='PATCH', 
                                json=updates)
    
    def regenerate_keypair(self, product_id, reason=''):
        """重新生成密钥对"""
        return self.api.api_call(
            f'/admin/products/{product_id}/regenerate_keypair/',
            method='POST',
            json={'confirm': True, 'reason': reason}
        )
    
    def get_product_stats(self, product_id):
        """获取产品统计"""
        return self.api.api_call(f'/admin/products/{product_id}/statistics/')

# 使用示例
product_manager = ProductManager(api_client)

# 创建产品
new_product = product_manager.create_product({
    'name': '新软件产品',
    'code': 'NEW_SOFTWARE',
    'description': '这是一个新的软件产品',
    'version': '1.0.0',
    'max_activations': 10,
    'offline_days': 30
})

# 获取产品列表
products = product_manager.get_products(status='active', ordering='-created_at')

# 更新产品状态
product_manager.update_product(1, {'status': 'inactive'})

# 获取统计信息
stats = product_manager.get_product_stats(1)
print(f"总许可证数: {stats['data']['licenses']['total']}")
```

## 业务场景示例

### 场景1: 新产品上线
```python
# 1. 创建新产品
product = product_manager.create_product({
    'name': '企业版CRM系统',
    'code': 'ENTERPRISE_CRM',
    'description': '面向企业客户的CRM管理系统',
    'version': '1.0.0',
    'max_activations': 50,
    'offline_days': 7  # 企业版要求更严格的在线验证
})

# 2. 创建产品的许可方案（需要调用许可方案API）
# 3. 设置租户配额（需要调用配额API）
# 4. 生成初始许可证（需要调用许可证API）
```

### 场景2: 产品版本升级
```python
# 1. 更新产品版本
product_manager.update_product(product_id, {
    'version': '2.0.0',
    'max_activations': 100,  # 新版本支持更多激活
    'description': '2.0版本新增AI功能'
})

# 2. 检查升级影响
stats = product_manager.get_product_stats(product_id)
print(f"当前活跃许可证: {stats['data']['licenses']['active']}")
```

### 场景3: 安全事件处理
```python
# 密钥泄露，需要重新生成
result = product_manager.regenerate_keypair(
    product_id, 
    reason='检测到密钥可能泄露，执行预防性重新生成'
)

# 暂停产品，阻止新的许可证生成
product_manager.update_product(product_id, {'status': 'inactive'})

# 监控统计数据
stats = product_manager.get_product_stats(product_id)
```

## 常见问题

### Q: 为什么租户管理员看不到某些产品？
A: 租户管理员只能看到通过`TenantLicenseQuota`授权的产品。需要超级管理员为租户分配产品配额。

### Q: 重新生成密钥对会影响已有许可证吗？
A: 会影响。新生成的许可证将使用新密钥签名，旧许可证的验证可能失效。建议配合客户端更新进行。

### Q: 如何批量管理多个产品？
A: 目前API不支持批量操作。可以在客户端实现批量逻辑，循环调用单个API。

### Q: 产品删除后如何恢复？
A: 产品删除为软删除，可以通过数据库操作恢复：
```sql
UPDATE licenses_software_product SET is_deleted = false WHERE id = {product_id};
```

## 相关API文档

- [许可证方案管理API](./11_admin_plans_api.md) - 管理产品下的许可方案
- [许可证管理API](./12_admin_licenses_api.md) - 管理产品的许可证
- [租户配额管理API](./16_admin_quotas_api.md) - 配置租户对产品的访问权限
