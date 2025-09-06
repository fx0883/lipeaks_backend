# 机器绑定管理API

## 概述

机器绑定管理API提供许可证与硬件设备绑定关系的查看和管理功能，确保许可证在授权设备上使用。

**Base URL**: `/api/v1/licenses/admin/machine-bindings/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  
**访问权限**: 只读

## 数据模型

### MachineBinding 字段详解

| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `id` | integer | 只读 | 绑定记录唯一标识符 | 数据库自动生成 |
| `license` | integer | 只读 | 关联的许可证ID | 激活时自动设置 |
| `machine_fingerprint` | string(64) | 只读 | 机器硬件指纹 | 客户端激活时生成 |
| `machine_name` | string(100) | 只读 | 机器名称 | 客户端激活时提供 |
| `encrypted_hardware_info` | text | 只读 | 加密的硬件信息 | 激活时自动加密存储 |
| `bound_at` | datetime | 只读 | 绑定时间 | 激活成功时自动设置 |
| `last_seen_at` | datetime | 只读 | 最后活跃时间 | 心跳时更新 |
| `status` | string(20) | 只读 | 绑定状态 | 自动管理 |
| `is_blocked` | boolean | 只读 | 是否被阻止 | 安全检测时设置 |
| `created_at` | datetime | 只读 | 创建时间 | 自动设置 |

### 状态枚举值

#### status字段可选值:
- `active` - 活跃：设备正常使用中
- `inactive` - 非活跃：设备长时间未活跃
- `blocked` - 已阻止：设备被安全策略阻止

## API端点详解

### 1. 获取机器绑定列表

#### 请求
```http
GET /api/v1/licenses/admin/machine-bindings/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `page` | integer | 否 | 页码 | `page=2` |
| `page_size` | integer | 否 | 每页条数 | `page_size=20` |
| `search` | string | 否 | 搜索机器名称、指纹 | `search=DESKTOP-ABC` |
| `license` | integer | 否 | 按许可证过滤 | `license=1` |
| `status` | string | 否 | 按状态过滤 | `status=active` |
| `is_blocked` | boolean | 否 | 按阻止状态过滤 | `is_blocked=false` |
| `last_seen_after` | datetime | 否 | 最后活跃时间晚于 | `last_seen_after=2024-01-01T00:00:00Z` |
| `ordering` | string | 否 | 排序字段 | `ordering=-last_seen_at` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "count": 89,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "license": {
                    "id": 1,
                    "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
                    "customer_name": "张三",
                    "customer_email": "zhangsan@example.com",
                    "status": "active"
                },
                "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
                "machine_name": "DESKTOP-ABC123",
                "bound_at": "2024-01-16T09:15:00Z",
                "last_seen_at": "2024-01-25T14:30:00Z",
                "status": "active",
                "is_blocked": false,
                "created_at": "2024-01-16T09:15:00Z"
            }
        ]
    }
}
```

### 2. 获取机器绑定详情

#### 请求
```http
GET /api/v1/licenses/admin/machine-bindings/{id}/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 1,
        "license": {
            "id": 1,
            "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
            "customer_name": "张三",
            "customer_email": "zhangsan@example.com",
            "status": "active",
            "expires_at": "2025-01-15T10:30:00Z",
            "license_plan": {
                "name": "专业版年度订阅",
                "software_product": {
                    "name": "MyApplication Pro"
                }
            }
        },
        "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
        "machine_name": "DESKTOP-ABC123",
        "bound_at": "2024-01-16T09:15:00Z",
        "last_seen_at": "2024-01-25T14:30:00Z",
        "status": "active",
        "is_blocked": false,
        "activation_history": [
            {
                "id": 1,
                "activated_at": "2024-01-16T09:15:00Z",
                "success": true,
                "ip_address": "192.168.1.100"
            }
        ],
        "heartbeat_history": [
            {
                "timestamp": "2024-01-25T14:30:00Z",
                "ip_address": "192.168.1.100",
                "status": "online"
            }
        ]
    }
}
```

### 3. 解除机器绑定

#### 请求
```http
DELETE /api/v1/licenses/admin/machine-bindings/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "reason": "客户更换设备",
    "force": false
}
```

#### 请求字段
- `reason` (string, 可选): 解除绑定的原因
- `force` (boolean, 可选): 是否强制解除，默认false

#### 响应
```http
HTTP/1.1 204 No Content
```

#### 解除绑定逻辑
- 普通解除：仅标记绑定为非活跃状态
- 强制解除：物理删除绑定记录，释放激活次数

### 4. 阻止/解除阻止机器

#### 阻止机器
```http
POST /api/v1/licenses/admin/machine-bindings/{id}/block/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "reason": "检测到异常行为",
    "permanent": false
}
```

#### 解除阻止
```http
POST /api/v1/licenses/admin/machine-bindings/{id}/unblock/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "reason": "人工审核通过"
}
```

## 使用示例

### Python示例
```python
class MachineBindingManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def get_bindings(self, **filters):
        params = '&'.join(f'{k}={v}' for k, v in filters.items())
        endpoint = f'/admin/machine-bindings/?{params}' if params else '/admin/machine-bindings/'
        return self.api.api_call(endpoint)
    
    def get_inactive_machines(self, days=30):
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        return self.get_bindings(last_seen_before=cutoff_date, status='active')
    
    def unbind_machine(self, binding_id, reason='', force=False):
        return self.api.api_call(f'/admin/machine-bindings/{binding_id}/', 
                               method='DELETE', 
                               json={'reason': reason, 'force': force})
    
    def block_machine(self, binding_id, reason='', permanent=False):
        return self.api.api_call(f'/admin/machine-bindings/{binding_id}/block/', 
                               method='POST',
                               json={'reason': reason, 'permanent': permanent})

# 使用示例
binding_manager = MachineBindingManager(api_client)

# 查找长期未活跃的设备
inactive_machines = binding_manager.get_inactive_machines(days=90)
print(f"90天未活跃的设备数量: {inactive_machines['data']['count']}")

# 批量解除绑定
for binding in inactive_machines['data']['results']:
    binding_manager.unbind_machine(
        binding['id'], 
        reason='长期未活跃，自动清理'
    )
```

## 相关API文档
- [许可证管理API](./12_admin_licenses_api.md) - 查看机器绑定关联的许可证
- [激活记录API](./14_admin_activations_api.md) - 查看机器的激活历史
