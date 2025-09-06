# 许可证管理API

## 概述

许可证管理API提供许可证的完整生命周期管理，包括许可证创建、状态管理、批量操作等核心功能。

**Base URL**: `/api/v1/licenses/admin/licenses/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  

## 数据模型

### License 字段详解

| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `id` | integer | 只读 | 许可证唯一标识符 | 数据库自动生成 |
| `license_plan` | integer | 是 | 关联的许可方案ID | 用户选择 |
| `tenant` | integer | 是 | 所属租户ID | 自动设置为当前用户租户 |
| `license_key` | string(255) | 只读 | 许可证密钥 | 创建时自动生成 |
| `customer_name` | string(100) | 是 | 客户姓名 | 用户输入 |
| `customer_email` | string(254) | 是 | 客户邮箱 | 用户输入 |
| `customer_company` | string(100) | 否 | 客户公司 | 用户输入 |
| `encrypted_customer_info` | text | 只读 | 加密的客户信息 | 基于客户信息自动加密 |
| `status` | string(20) | 否 | 许可证状态 | 默认"generated" |
| `issued_at` | datetime | 只读 | 签发时间 | 创建时自动设置 |
| `expires_at` | datetime | 只读 | 过期时间 | 基于方案有效期计算 |
| `max_activations` | integer | 否 | 最大激活次数 | 继承自产品设置 |
| `activation_count` | integer | 只读 | 当前激活次数 | 实时统计 |
| `created_at` | datetime | 只读 | 创建时间 | 自动设置 |
| `updated_at` | datetime | 只读 | 更新时间 | 自动更新 |

### 状态枚举值

#### status字段可选值:
- `generated` - 已生成：许可证已创建但未激活
- `active` - 已激活：许可证正在使用中
- `suspended` - 已挂起：暂时停用，可恢复
- `revoked` - 已撤销：永久停用，不可恢复
- `expired` - 已过期：超过有效期

## API端点详解

### 1. 获取许可证列表

#### 请求
```http
GET /api/v1/licenses/admin/licenses/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `page` | integer | 否 | 页码 | `page=2` |
| `page_size` | integer | 否 | 每页条数 | `page_size=20` |
| `search` | string | 否 | 搜索客户信息、许可证密钥 | `search=john@example.com` |
| `license_plan` | integer | 否 | 按方案过滤 | `license_plan=1` |
| `status` | string | 否 | 按状态过滤 | `status=active` |
| `customer_email` | string | 否 | 按客户邮箱精确匹配 | `customer_email=user@company.com` |
| `expires_before` | date | 否 | 过期时间早于指定日期 | `expires_before=2024-12-31` |
| `expires_after` | date | 否 | 过期时间晚于指定日期 | `expires_after=2024-01-01` |
| `ordering` | string | 否 | 排序字段 | `ordering=-created_at` |

#### 排序字段选项:
- `created_at` - 按创建时间排序
- `expires_at` - 按过期时间排序
- `customer_name` - 按客户姓名排序
- `activation_count` - 按激活次数排序

#### 响应示例
```json
{
    "success": true,
    "data": {
        "count": 150,
        "next": "https://api.example.com/api/v1/licenses/admin/licenses/?page=3",
        "previous": "https://api.example.com/api/v1/licenses/admin/licenses/?page=1",
        "results": [
            {
                "id": 1,
                "license_plan": {
                    "id": 1,
                    "name": "专业版年度订阅",
                    "plan_type": "professional",
                    "software_product": {
                        "id": 1,
                        "name": "MyApplication Pro"
                    }
                },
                "tenant": {
                    "id": 2,
                    "name": "示例公司"
                },
                "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
                "customer_name": "张三",
                "customer_email": "zhangsan@example.com",
                "customer_company": "示例科技有限公司",
                "status": "active",
                "issued_at": "2024-01-15T10:30:00Z",
                "expires_at": "2025-01-15T10:30:00Z",
                "max_activations": 5,
                "activation_count": 2,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:25:00Z"
            }
        ]
    }
}
```

### 2. 创建许可证

#### 请求
```http
POST /api/v1/licenses/admin/licenses/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "license_plan": 1,
    "customer_name": "李四",
    "customer_email": "lisi@example.com",
    "customer_company": "新兴科技公司",
    "max_activations": 10,
    "custom_validity_days": 180
}
```

#### 请求字段详解
| 字段名 | 类型 | 必填 | 说明 | 验证规则 |
|--------|------|------|------|----------|
| `license_plan` | integer | 是 | 许可方案ID | 必须存在且用户有权限 |
| `customer_name` | string | 是 | 客户姓名 | 最大100字符 |
| `customer_email` | string | 是 | 客户邮箱 | 有效邮箱格式 |
| `customer_company` | string | 否 | 客户公司 | 最大100字符 |
| `max_activations` | integer | 否 | 自定义激活次数 | 覆盖产品默认设置 |
| `custom_validity_days` | integer | 否 | 自定义有效期天数 | 覆盖方案默认设置 |

#### 许可证密钥生成逻辑
许可证密钥格式：`{产品代码}-{类型简码}-{随机部分}`
- 产品代码：来自关联软件产品的code字段
- 类型简码：根据方案类型生成(PRO/ENT/BAS等)
- 随机部分：4组4位字符，确保唯一性

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 151,
        "license_key": "MYAPP-PRO-A1B2-C3D4-E5F6-G7H8",
        "customer_name": "李四",
        "customer_email": "lisi@example.com",
        "customer_company": "新兴科技公司",
        "status": "generated",
        "issued_at": "2024-01-25T16:45:00Z",
        "expires_at": "2024-07-23T16:45:00Z",
        "max_activations": 10,
        "activation_count": 0
    },
    "message": "许可证创建成功"
}
```

### 3. 获取许可证详情

#### 请求
```http
GET /api/v1/licenses/admin/licenses/{id}/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 1,
        "license_plan": {
            "id": 1,
            "name": "专业版年度订阅",
            "plan_type": "professional",
            "price": "999.00",
            "currency": "CNY",
            "software_product": {
                "id": 1,
                "name": "MyApplication Pro",
                "code": "MYAPP_PRO",
                "version": "2.1.0"
            }
        },
        "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
        "customer_name": "张三",
        "customer_email": "zhangsan@example.com",
        "customer_company": "示例科技有限公司",
        "status": "active",
        "issued_at": "2024-01-15T10:30:00Z",
        "expires_at": "2025-01-15T10:30:00Z",
        "max_activations": 5,
        "activation_count": 2,
        "machine_bindings": [
            {
                "id": 1,
                "machine_fingerprint": "abc123def456",
                "machine_name": "DESKTOP-ABC123",
                "bound_at": "2024-01-16T09:15:00Z",
                "status": "active"
            }
        ],
        "activation_history": [
            {
                "id": 1,
                "activated_at": "2024-01-16T09:15:00Z",
                "machine_fingerprint": "abc123def456",
                "success": true
            }
        ]
    }
}
```

### 4. 更新许可证状态

#### 挂起许可证
```http
PATCH /api/v1/licenses/admin/licenses/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "status": "suspended",
    "reason": "客户申请暂停使用"
}
```

#### 撤销许可证
```http
PATCH /api/v1/licenses/admin/licenses/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "status": "revoked",
    "reason": "违反使用条款"
}
```

#### 恢复许可证
```http
PATCH /api/v1/licenses/admin/licenses/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "status": "active"
}
```

### 5. 批量操作

#### 批量更新状态
```http
POST /api/v1/licenses/admin/licenses/batch_update_status/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "license_ids": [1, 2, 3, 4, 5],
    "status": "suspended",
    "reason": "批量维护操作"
}
```

#### 批量创建许可证
```http
POST /api/v1/licenses/admin/licenses/batch_create/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "license_plan": 1,
    "licenses": [
        {
            "customer_name": "客户1",
            "customer_email": "customer1@example.com",
            "customer_company": "公司1"
        },
        {
            "customer_name": "客户2", 
            "customer_email": "customer2@example.com",
            "customer_company": "公司2"
        }
    ]
}
```

### 6. 许可证导出

#### 导出CSV
```http
GET /api/v1/licenses/admin/licenses/export/?format=csv&status=active
Authorization: Bearer {access_token}
```

#### 导出Excel
```http
GET /api/v1/licenses/admin/licenses/export/?format=excel&license_plan=1
Authorization: Bearer {access_token}
```

## 使用示例

### JavaScript示例
```javascript
class LicenseManager {
    constructor(apiClient) {
        this.api = apiClient;
    }
    
    async createLicense(licenseData) {
        return await this.api.apiCall('/admin/licenses/', {
            method: 'POST',
            body: JSON.stringify(licenseData)
        });
    }
    
    async batchCreateLicenses(planId, customerList) {
        return await this.api.apiCall('/admin/licenses/batch_create/', {
            method: 'POST',
            body: JSON.stringify({
                license_plan: planId,
                licenses: customerList
            })
        });
    }
    
    async updateLicenseStatus(licenseId, status, reason = '') {
        return await this.api.apiCall(`/admin/licenses/${licenseId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ status, reason })
        });
    }
    
    async getLicenses(filters = {}) {
        const params = new URLSearchParams(filters);
        return await this.api.apiCall(`/admin/licenses/?${params}`);
    }
}

// 使用示例
const licenseManager = new LicenseManager(apiClient);

// 创建单个许可证
const newLicense = await licenseManager.createLicense({
    license_plan: 1,
    customer_name: '新客户',
    customer_email: 'new@example.com',
    customer_company: '新公司',
    max_activations: 5
});

// 批量创建许可证
const customers = [
    { customer_name: '客户A', customer_email: 'a@example.com' },
    { customer_name: '客户B', customer_email: 'b@example.com' }
];
const batchResult = await licenseManager.batchCreateLicenses(1, customers);

// 挂起许可证
await licenseManager.updateLicenseStatus(1, 'suspended', '客户要求暂停');
```

### Python示例
```python
class LicenseManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def create_license(self, license_data):
        return self.api.api_call('/admin/licenses/', method='POST', json=license_data)
    
    def batch_create_licenses(self, plan_id, customer_list):
        data = {
            'license_plan': plan_id,
            'licenses': customer_list
        }
        return self.api.api_call('/admin/licenses/batch_create/', 
                               method='POST', json=data)
    
    def update_status(self, license_id, status, reason=''):
        data = {'status': status}
        if reason:
            data['reason'] = reason
        return self.api.api_call(f'/admin/licenses/{license_id}/', 
                               method='PATCH', json=data)
    
    def get_expiring_licenses(self, days=30):
        from datetime import datetime, timedelta
        expires_before = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        return self.api.api_call(f'/admin/licenses/?expires_before={expires_before}&status=active')

# 使用示例
license_manager = LicenseManager(api_client)

# 创建许可证
new_license = license_manager.create_license({
    'license_plan': 1,
    'customer_name': '测试客户',
    'customer_email': 'test@example.com',
    'max_activations': 3
})

# 查找即将过期的许可证
expiring_licenses = license_manager.get_expiring_licenses(30)
print(f"30天内过期的许可证数量: {expiring_licenses['data']['count']}")

# 批量挂起即将过期的许可证
license_ids = [license['id'] for license in expiring_licenses['data']['results']]
batch_result = license_manager.api.api_call('/admin/licenses/batch_update_status/', 
                                          method='POST', 
                                          json={
                                              'license_ids': license_ids,
                                              'status': 'suspended',
                                              'reason': '即将过期，预防性挂起'
                                          })
```

## 业务场景示例

### 场景1: 企业客户批量许可证发放
```python
# 为企业客户批量生成许可证
enterprise_customers = [
    {'customer_name': '员工1', 'customer_email': 'emp1@company.com'},
    {'customer_name': '员工2', 'customer_email': 'emp2@company.com'},
    {'customer_name': '员工3', 'customer_email': 'emp3@company.com'}
]

result = license_manager.batch_create_licenses(
    plan_id=2,  # 企业版方案
    customer_list=enterprise_customers
)

print(f"成功创建 {len(result['data']['created'])} 个许可证")
```

### 场景2: 许可证到期管理
```python
# 查找即将在7天内过期的许可证
expiring_soon = license_manager.get_expiring_licenses(7)

# 发送续费提醒邮件（需要集成邮件服务）
for license_info in expiring_soon['data']['results']:
    send_renewal_reminder(
        email=license_info['customer_email'],
        license_key=license_info['license_key'],
        expires_at=license_info['expires_at']
    )
```

### 场景3: 异常许可证处理
```python
# 查找激活次数异常的许可证（可能存在滥用）
suspicious_licenses = license_manager.api.api_call(
    '/admin/licenses/?activation_count__gte=max_activations'
)

for license_info in suspicious_licenses['data']['results']:
    # 挂起可疑许可证
    license_manager.update_status(
        license_info['id'], 
        'suspended', 
        '激活次数超限，需要人工审核'
    )
```

## 常见问题

### Q: 为什么创建许可证时看不到某些许可方案？
A: 租户管理员只能看到授权产品下的方案。检查`TenantLicenseQuota`配置。

### Q: 许可证状态修改后，客户端多久能感知到？
A: 客户端下次调用验证或心跳API时会获取最新状态，通常在几秒内。

### Q: 如何处理客户要求延长许可证有效期？
A: 目前需要创建新许可证，或通过数据库直接修改`expires_at`字段。

### Q: 批量操作失败如何处理？
A: 批量操作是事务性的，任一项失败会回滚所有操作。检查返回的错误详情进行修正。

## 相关API文档
- [许可证方案管理API](./11_admin_plans_api.md) - 管理许可证方案
- [机器绑定管理API](./13_admin_machines_api.md) - 查看许可证的设备绑定
- [激活记录API](./14_admin_activations_api.md) - 查看许可证激活历史
