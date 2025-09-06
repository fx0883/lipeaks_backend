# 许可证方案管理API

## 概述

许可证方案管理API提供软件产品下不同许可方案的管理功能，包括方案创建、复制、统计等。

**Base URL**: `/api/v1/licenses/admin/plans/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  

## 数据模型

### LicensePlan 字段详解

| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `id` | integer | 只读 | 方案唯一标识符 | 数据库自动生成 |
| `software_product` | integer | 是 | 关联的软件产品ID | 用户选择 |
| `name` | string(100) | 是 | 方案名称 | 用户输入 |
| `plan_type` | string(20) | 是 | 方案类型 | 用户选择 |
| `description` | text | 否 | 方案描述 | 用户输入 |
| `price` | decimal(10,2) | 否 | 方案价格 | 用户输入，默认0.00 |
| `currency` | string(3) | 否 | 货币代码 | 用户输入，默认"CNY" |
| `max_devices` | integer | 否 | 最大设备数限制 | 用户输入，默认1 |
| `validity_days` | integer | 否 | 有效期天数 | 用户输入，默认365 |
| `features` | JSON | 否 | 功能配置 | 用户输入 |
| `status` | string(20) | 否 | 方案状态 | 用户选择，默认"active" |
| `created_at` | datetime | 只读 | 创建时间 | 自动设置 |
| `updated_at` | datetime | 只读 | 更新时间 | 自动更新 |
| `license_count` | integer | 只读 | 许可证数量 | 实时计算 |

### 枚举值说明

#### plan_type可选值:
- `trial` - 试用版：免费试用，功能和时间受限
- `basic` - 基础版：基本功能版本
- `professional` - 专业版：增强功能版本
- `enterprise` - 企业版：完整功能版本
- `custom` - 定制版：根据客户需求定制

#### status可选值:
- `active` - 启用：方案可正常使用
- `inactive` - 禁用：方案暂停使用
- `deprecated` - 已弃用：不再推荐使用

#### currency常用值:
- `CNY` - 人民币
- `USD` - 美元
- `EUR` - 欧元

## API端点详解

### 1. 获取方案列表

#### 请求
```http
GET /api/v1/licenses/admin/plans/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `page` | integer | 否 | 页码 | `page=2` |
| `page_size` | integer | 否 | 每页条数 | `page_size=20` |
| `search` | string | 否 | 搜索关键词 | `search=专业版` |
| `software_product` | integer | 否 | 按产品过滤 | `software_product=1` |
| `plan_type` | string | 否 | 按类型过滤 | `plan_type=professional` |
| `status` | string | 否 | 按状态过滤 | `status=active` |
| `ordering` | string | 否 | 排序字段 | `ordering=-created_at` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "count": 15,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "software_product": {
                    "id": 1,
                    "name": "MyApplication Pro",
                    "code": "MYAPP_PRO"
                },
                "name": "专业版年度订阅",
                "plan_type": "professional",
                "description": "包含所有专业功能的年度订阅方案",
                "price": "999.00",
                "currency": "CNY",
                "max_devices": 5,
                "validity_days": 365,
                "features": {
                    "advanced_analytics": true,
                    "api_access": true,
                    "custom_reports": true
                },
                "status": "active",
                "license_count": 25,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:25:00Z"
            }
        ]
    }
}
```

### 2. 创建许可方案

#### 请求
```http
POST /api/v1/licenses/admin/plans/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "software_product": 1,
    "name": "企业版方案",
    "plan_type": "enterprise",
    "description": "面向企业用户的完整功能方案",
    "price": "2999.00",
    "currency": "CNY",
    "max_devices": 20,
    "validity_days": 365,
    "features": {
        "unlimited_users": true,
        "priority_support": true,
        "custom_integration": true
    }
}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 15,
        "software_product": {
            "id": 1,
            "name": "MyApplication Pro",
            "code": "MYAPP_PRO"
        },
        "name": "企业版方案",
        "plan_type": "enterprise",
        "description": "面向企业用户的完整功能方案",
        "price": "2999.00",
        "currency": "CNY",
        "max_devices": 20,
        "validity_days": 365,
        "features": {
            "unlimited_users": true,
            "priority_support": true,
            "custom_integration": true
        },
        "status": "active",
        "license_count": 0,
        "created_at": "2024-01-25T16:45:00Z",
        "updated_at": "2024-01-25T16:45:00Z"
    }
}
```

### 3. 复制方案

#### 请求
```http
POST /api/v1/licenses/admin/plans/{id}/copy/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "复制的专业版方案",
    "modifications": {
        "price": "1299.00",
        "max_devices": 10
    }
}
```

#### 请求字段
- `name` (string, 必填): 新方案名称
- `modifications` (object, 可选): 需要修改的字段

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 16,
        "name": "复制的专业版方案",
        "plan_type": "professional",
        "price": "1299.00",
        "max_devices": 10,
        "license_count": 0
    },
    "message": "方案复制成功"
}
```

## 使用示例

### Python示例
```python
class PlanManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def create_plan(self, plan_data):
        return self.api.api_call('/admin/plans/', method='POST', json=plan_data)
    
    def copy_plan(self, plan_id, new_name, modifications=None):
        data = {'name': new_name}
        if modifications:
            data['modifications'] = modifications
        return self.api.api_call(f'/admin/plans/{plan_id}/copy/', 
                               method='POST', json=data)

# 创建企业版方案
plan_data = {
    'software_product': 1,
    'name': '企业版年度',
    'plan_type': 'enterprise', 
    'price': '2999.00',
    'max_devices': 50,
    'validity_days': 365,
    'features': {
        'unlimited_users': True,
        'api_access': True,
        'priority_support': True
    }
}

plan_manager = PlanManager(api_client)
new_plan = plan_manager.create_plan(plan_data)
```

## 相关API文档
- [软件产品管理API](./10_admin_products_api.md)
- [许可证管理API](./12_admin_licenses_api.md)
