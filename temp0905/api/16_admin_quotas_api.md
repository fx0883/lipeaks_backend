# 租户配额管理API

## 概述

租户配额管理API提供租户对软件产品访问权限的配置和管理功能，控制租户可以创建的许可证数量。

**Base URL**: `/api/v1/licenses/admin/quotas/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  

## 数据模型

### TenantLicenseQuota 字段详解

| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `id` | integer | 只读 | 配额记录唯一标识符 | 数据库自动生成 |
| `tenant` | integer | 是 | 关联的租户ID | 用户选择 |
| `software_product` | integer | 是 | 关联的软件产品ID | 用户选择 |
| `max_licenses` | integer | 是 | 最大许可证数量 | 用户设置 |
| `used_licenses` | integer | 只读 | 已使用许可证数量 | 实时计算 |
| `expires_at` | datetime | 否 | 配额过期时间 | 用户设置 |
| `is_active` | boolean | 否 | 是否启用 | 默认true |
| `created_at` | datetime | 只读 | 创建时间 | 自动设置 |
| `updated_at` | datetime | 只读 | 更新时间 | 自动更新 |

## API端点详解

### 1. 获取配额列表

#### 请求
```http
GET /api/v1/licenses/admin/quotas/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `page` | integer | 否 | 页码 | `page=2` |
| `page_size` | integer | 否 | 每页条数 | `page_size=20` |
| `tenant` | integer | 否 | 按租户过滤 | `tenant=1` |
| `software_product` | integer | 否 | 按产品过滤 | `software_product=1` |
| `is_active` | boolean | 否 | 按激活状态过滤 | `is_active=true` |
| `expires_before` | date | 否 | 过期时间早于 | `expires_before=2024-12-31` |
| `usage_rate_gte` | float | 否 | 使用率大于等于 | `usage_rate_gte=0.8` |
| `ordering` | string | 否 | 排序字段 | `ordering=-created_at` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "count": 25,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "tenant": {
                    "id": 2,
                    "name": "示例公司",
                    "code": "DEMO_COMPANY"
                },
                "software_product": {
                    "id": 1,
                    "name": "MyApplication Pro",
                    "code": "MYAPP_PRO"
                },
                "max_licenses": 100,
                "used_licenses": 75,
                "usage_rate": 75.0,
                "remaining_licenses": 25,
                "expires_at": "2024-12-31T23:59:59Z",
                "is_active": true,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:25:00Z"
            }
        ]
    }
}
```

### 2. 创建配额

#### 请求
```http
POST /api/v1/licenses/admin/quotas/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "tenant": 2,
    "software_product": 1,
    "max_licenses": 200,
    "expires_at": "2024-12-31T23:59:59Z"
}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 15,
        "tenant": {
            "id": 2,
            "name": "示例公司"
        },
        "software_product": {
            "id": 1,
            "name": "MyApplication Pro"
        },
        "max_licenses": 200,
        "used_licenses": 0,
        "usage_rate": 0.0,
        "remaining_licenses": 200,
        "expires_at": "2024-12-31T23:59:59Z",
        "is_active": true
    },
    "message": "租户配额创建成功"
}
```

### 3. 更新配额

#### 请求
```http
PATCH /api/v1/licenses/admin/quotas/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "max_licenses": 300,
    "expires_at": "2025-12-31T23:59:59Z"
}
```

### 4. 配额使用统计

#### 请求
```http
GET /api/v1/licenses/admin/quotas/usage_statistics/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "total_quotas": 25,
        "active_quotas": 23,
        "expired_quotas": 2,
        "usage_overview": {
            "total_allocated": 2500,
            "total_used": 1875,
            "overall_usage_rate": 75.0
        },
        "by_tenant": [
            {
                "tenant_id": 2,
                "tenant_name": "示例公司",
                "total_quota": 300,
                "total_used": 225,
                "usage_rate": 75.0,
                "products_count": 3
            }
        ],
        "high_usage_quotas": [
            {
                "id": 1,
                "tenant_name": "示例公司",
                "product_name": "MyApplication Pro",
                "usage_rate": 95.0,
                "remaining_licenses": 5
            }
        ]
    }
}
```

## 使用示例

### Python示例
```python
class QuotaManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def create_quota(self, tenant_id, product_id, max_licenses, expires_at=None):
        data = {
            'tenant': tenant_id,
            'software_product': product_id,
            'max_licenses': max_licenses
        }
        if expires_at:
            data['expires_at'] = expires_at
        
        return self.api.api_call('/admin/quotas/', method='POST', json=data)
    
    def get_quota_alerts(self, threshold=0.9):
        """获取使用率超过阈值的配额"""
        quotas = self.api.api_call(f'/admin/quotas/?usage_rate_gte={threshold}')
        return quotas['data']['results']
    
    def extend_quota_expiry(self, quota_id, new_expiry_date):
        return self.api.api_call(f'/admin/quotas/{quota_id}/', 
                               method='PATCH', 
                               json={'expires_at': new_expiry_date})

# 使用示例
quota_manager = QuotaManager(api_client)

# 为租户创建产品配额
new_quota = quota_manager.create_quota(
    tenant_id=2,
    product_id=1,
    max_licenses=500,
    expires_at='2024-12-31T23:59:59Z'
)

# 检查高使用率配额
high_usage = quota_manager.get_quota_alerts(threshold=0.85)
for quota in high_usage:
    print(f"配额 {quota['id']} 使用率: {quota['usage_rate']:.1f}%")
```

## 相关API文档
- [软件产品管理API](./10_admin_products_api.md) - 配额关联的产品管理
- [许可证管理API](./12_admin_licenses_api.md) - 配额限制的许可证创建
