# 许可证分配API - 详细文档

## 📋 目录

- [许可证分配概述](#许可证分配概述)
- [分配列表API](#分配列表api)
- [创建分配API](#创建分配api)
- [分配激活API](#分配激活api)
- [分配撤销API](#分配撤销api)
- [批量操作API](#批量操作api)
- [统计分析API](#统计分析api)
- [业务场景示例](#业务场景示例)

---

## 📄 许可证分配概述

### 许可证分配系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                  许可证分配生命周期                         │
├─────────────────────────────────────────────────────────────┤
│ 需求评估 → 分配创建 → 权限配置 → 激活 → 使用 → 监控 → 到期/撤销 │
│     ↓         ↓         ↓        ↓     ↓      ↓         ↓    │
│  用户申请   管理员      设置      生效  享受   追踪     回收  │
│  业务需求   审核        权限      激活  服务   使用     许可  │
└─────────────────────────────────────────────────────────────┘
```

### 分配类型

| 类型 | 代码 | 说明 | 特点 |
|------|------|------|------|
| 直接分配 | `direct` | 直接分配给用户 | 用户独享，不可共享 |
| 共享分配 | `shared` | 多用户共享使用 | 按需分配，资源共享 |
| 临时分配 | `temporary` | 临时试用分配 | 有明确期限 |
| 升级分配 | `upgrade` | 升级现有许可 | 替换低级许可 |

### 分配状态

| 状态 | 代码 | 说明 |
|------|------|------|
| 待激活 | `pending` | 已分配，等待激活 |
| 已激活 | `active` | 正常使用中 |
| 已暂停 | `suspended` | 临时暂停使用 |
| 已过期 | `expired` | 超过有效期 |
| 已撤销 | `revoked` | 管理员撤销 |

---

## 📋 分配列表API

### 获取许可证分配列表

**端点**: `GET /api/v1/licenses/admin/assignments/`

**描述**: 获取当前租户下的所有许可证分配记录

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `tenant` | integer | 否 | 当前租户 | 过滤租户ID |
| `license` | integer | 否 | - | 过滤许可证ID |
| `member` | integer | 否 | - | 过滤用户ID |
| `assignment_type` | string | 否 | - | 过滤分配类型 |
| `status` | string | 否 | - | 过滤分配状态 |
| `is_primary` | boolean | 否 | - | 过滤主要分配 |
| `can_activate` | boolean | 否 | - | 过滤激活权限 |
| `priority` | string | 否 | - | 过滤优先级 |
| `expires_at__gte` | datetime | 否 | - | 过期时间起始 |
| `expires_at__lte` | datetime | 否 | - | 过期时间结束 |
| `search` | string | 否 | - | 搜索分配原因、撤销原因 |
| `ordering` | string | 否 | `-assigned_at` | 排序字段 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/assignments/?status=active&ordering=-assigned_at" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### 响应示例

```json
{
  "count": 50,
  "next": "http://localhost:8000/api/v1/licenses/admin/assignments/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "member": 123,
      "license": 456,
      "tenant": 789,
      "assignment_type": "direct",
      "assignment_reason": "用户申请专业版许可证",
      "priority": "normal",
      "can_activate": true,
      "can_deactivate": true,
      "can_share": false,
      "max_devices_per_user": 3,
      "assigned_at": "2025-09-25T10:00:00Z",
      "activated_at": "2025-09-25T10:30:00Z",
      "expires_at": "2026-09-25T10:00:00Z",
      "last_used_at": "2025-09-25T15:45:00Z",
      "status": "active",
      "is_primary": true,
      "usage_count": 25,
      "last_heartbeat": "2025-09-25T15:45:00Z",
      "revoked_at": null,
      "revoke_reason": null,
      "assignment_metadata": {
        "application_id": "APP-123",
        "department": "Development",
        "project": "ProjectX"
      },
      "assigned_by": 999,
      "revoked_by": null,
      "member_info": {
        "id": 123,
        "username": "john_doe",
        "email": "john@example.com",
        "is_active": true
      },
      "license_info": {
        "id": 456,
        "license_key": "****-****-****-1234",
        "product_name": "专业开发工具",
        "plan_name": "专业版",
        "status": "active",
        "max_activations": 10,
        "current_activations": 3,
        "expires_at": "2026-09-25T10:00:00Z"
      },
      "tenant_info": {
        "id": 789,
        "name": "ACME Corp",
        "is_active": true
      },
      "assigned_by_info": {
        "id": 999,
        "username": "admin_user"
      },
      "revoked_by_info": null,
      "is_expired": false,
      "days_until_expiry": 365,
      "effective_permissions": {
        "can_use_advanced_features": true,
        "can_export_data": true,
        "api_rate_limit": 1000,
        "storage_quota": "10GB"
      },
      "usage_summary": {
        "usage_count": 25,
        "last_used_at": "2025-09-25T15:45:00Z",
        "last_heartbeat": "2025-09-25T15:45:00Z",
        "is_primary": true,
        "can_activate": true,
        "can_deactivate": true,
        "can_share": false,
        "max_devices_per_user": 3
      },
      "created_at": "2025-09-25T10:00:00Z",
      "updated_at": "2025-09-25T15:45:00Z"
    }
  ]
}
```

#### 字段详细说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer | 分配记录唯一标识 |
| `member` | integer | 被分配用户ID |
| `license` | integer | 许可证ID |
| `tenant` | integer | 租户ID |
| `assignment_type` | string | 分配类型 |
| `assignment_reason` | string | 分配原因 |
| `priority` | string | 优先级（high/normal/low） |
| `can_activate` | boolean | 是否可以激活 |
| `can_deactivate` | boolean | 是否可以停用 |
| `can_share` | boolean | 是否可以共享 |
| `max_devices_per_user` | integer | 用户最大设备数 |
| `assigned_at` | datetime | 分配时间 |
| `activated_at` | datetime | 激活时间 |
| `expires_at` | datetime | 过期时间 |
| `last_used_at` | datetime | 最后使用时间 |
| `status` | string | 分配状态 |
| `is_primary` | boolean | 是否为主要分配 |
| `usage_count` | integer | 使用次数 |
| `last_heartbeat` | datetime | 最后心跳时间 |
| `assignment_metadata` | json | 分配元数据 |

---

## ➕ 创建分配API

### 创建许可证分配

**端点**: `POST /api/v1/licenses/admin/assignments/`

**描述**: 为指定用户创建新的许可证分配

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `member_id` | integer | 是 | - | 目标用户ID |
| `license_id` | integer | 是 | - | 许可证ID |
| `assignment_type` | string | 否 | `direct` | 分配类型 |
| `assignment_reason` | string | 否 | - | 分配原因 |
| `priority` | string | 否 | `normal` | 优先级 |
| `can_activate` | boolean | 否 | true | 是否可以激活 |
| `can_deactivate` | boolean | 否 | true | 是否可以停用 |
| `can_share` | boolean | 否 | false | 是否可以共享 |
| `max_devices_per_user` | integer | 否 | 1 | 用户最大设备数 |
| `expires_at` | datetime | 否 | - | 过期时间 |
| `assignment_metadata` | json | 否 | {} | 分配元数据 |

#### 优先级说明

| 优先级 | 代码 | 说明 |
|--------|------|------|
| 高优先级 | `high` | 关键用户，优先保障 |
| 普通优先级 | `normal` | 正常业务用户 |
| 低优先级 | `low` | 临时或测试用户 |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 123,
    "license_id": 456,
    "assignment_type": "direct",
    "assignment_reason": "用户申请专业版许可证",
    "priority": "high",
    "can_activate": true,
    "can_deactivate": true,
    "can_share": false,
    "max_devices_per_user": 3,
    "expires_at": "2026-09-25T10:00:00Z",
    "assignment_metadata": {
      "application_id": "APP-123",
      "department": "Development",
      "project": "ProjectX",
      "cost_center": "CC-1001"
    }
  }'
```

#### 响应示例

```json
{
  "id": 1,
  "member": 123,
  "license": 456,
  "tenant": 789,
  "assignment_type": "direct",
  "assignment_reason": "用户申请专业版许可证",
  "priority": "high",
  "can_activate": true,
  "can_deactivate": true,
  "can_share": false,
  "max_devices_per_user": 3,
  "assigned_at": "2025-09-25T16:00:00Z",
  "activated_at": null,
  "expires_at": "2026-09-25T10:00:00Z",
  "last_used_at": null,
  "status": "pending",
  "is_primary": false,
  "usage_count": 0,
  "last_heartbeat": null,
  "revoked_at": null,
  "revoke_reason": null,
  "assignment_metadata": {
    "application_id": "APP-123",
    "department": "Development",
    "project": "ProjectX",
    "cost_center": "CC-1001"
  },
  "assigned_by": 999,
  "revoked_by": null,
  "member_info": {
    "id": 123,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true
  },
  "license_info": {
    "id": 456,
    "license_key": "****-****-****-1234",
    "product_name": "专业开发工具",
    "plan_name": "专业版",
    "status": "active",
    "max_activations": 10,
    "current_activations": 2,
    "expires_at": "2026-09-25T10:00:00Z"
  },
  "next_steps": [
    "用户需要激活许可证",
    "配置客户端软件",
    "开始使用专业版功能"
  ],
  "activation_instructions": {
    "method": "license_key",
    "license_key": "PROF-2025-ABC123-DEF456",
    "activation_url": "https://app.example.com/activate",
    "support_contact": "support@example.com"
  },
  "created_at": "2025-09-25T16:00:00Z",
  "updated_at": "2025-09-25T16:00:00Z"
}
```

---

## ✅ 分配激活API

### 激活许可证分配

**端点**: `POST /api/v1/licenses/admin/assignments/{id}/activate/`

**描述**: 激活指定的许可证分配

#### 请求参数

无需请求体，通过URL路径传递分配ID

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/1/activate/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### 响应示例

```json
{
  "success": true,
  "message": "许可证分配激活成功",
  "activated_at": "2025-09-25T16:05:00Z",
  "license_status": {
    "current_activations": 3,
    "max_activations": 10,
    "remaining_activations": 7
  },
  "user_permissions": {
    "can_use_advanced_features": true,
    "can_export_data": true,
    "api_rate_limit": 1000,
    "storage_quota": "10GB"
  },
  "activation_details": {
    "activation_method": "api",
    "client_info": {
      "ip_address": "192.168.1.100",
      "user_agent": "MyApp/1.0"
    },
    "device_fingerprint": "fp_abc123def456"
  },
  "points_awarded": {
    "points": 100,
    "reason": "许可证激活奖励"
  },
  "timestamp": "2025-09-25T16:05:00Z"
}
```

---

## ❌ 分配撤销API

### 撤销许可证分配

**端点**: `POST /api/v1/licenses/admin/assignments/{id}/revoke/`

**描述**: 撤销指定的许可证分配

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | 否 | 撤销原因（默认"管理员撤销"） |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/1/revoke/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "用户离职，回收许可证"
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "许可证分配撤销成功",
  "revoked_at": "2025-09-25T16:10:00Z",
  "revoke_reason": "用户离职，回收许可证",
  "license_status": {
    "current_activations": 2,
    "max_activations": 10,
    "freed_slots": 1
  },
  "affected_devices": [
    {
      "device_id": "device_123",
      "last_seen": "2025-09-25T15:45:00Z",
      "status": "deactivated"
    }
  ],
  "data_retention": {
    "user_data_retained": true,
    "retention_period_days": 30,
    "deletion_date": "2025-10-25T16:10:00Z"
  },
  "timestamp": "2025-09-25T16:10:00Z"
}
```

---

## 📊 使用记录API

### 记录许可证使用

**端点**: `POST /api/v1/licenses/admin/assignments/{id}/record_usage/`

**描述**: 记录许可证分配的使用情况

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/1/record_usage/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### 响应示例

```json
{
  "success": true,
  "message": "使用情况记录成功",
  "usage_count": 26,
  "last_used_at": "2025-09-25T16:15:00Z",
  "last_heartbeat": "2025-09-25T16:15:00Z",
  "session_info": {
    "session_duration": "02:30:45",
    "features_used": [
      "advanced_analytics",
      "data_export",
      "api_access"
    ],
    "data_transferred": "125MB"
  },
  "usage_analytics": {
    "daily_usage_hours": 6.5,
    "weekly_usage_hours": 32.0,
    "most_used_feature": "advanced_analytics"
  },
  "timestamp": "2025-09-25T16:15:00Z"
}
```

---

## 🔍 权限查询API

### 获取分配权限

**端点**: `GET /api/v1/licenses/admin/assignments/{id}/permissions/`

**描述**: 获取许可证分配的有效权限

#### 响应示例

```json
{
  "assignment_id": 1,
  "member": "john_doe",
  "license_key": "****-1234",
  "effective_permissions": {
    "product_permissions": {
      "can_use_basic_features": true,
      "can_use_advanced_features": true,
      "can_use_premium_features": false
    },
    "plan_permissions": {
      "api_rate_limit": 1000,
      "storage_quota": "10GB",
      "concurrent_sessions": 3,
      "export_formats": ["CSV", "JSON", "XML"]
    },
    "assignment_permissions": {
      "can_activate_devices": true,
      "can_share_license": false,
      "max_devices": 3,
      "priority_level": "high"
    },
    "user_level_permissions": {
      "level_name": "黄金会员",
      "level_bonus": {
        "api_rate_bonus": 200,
        "storage_bonus": "2GB"
      }
    },
    "vip_tag_permissions": {
      "VIP_GOLD": {
        "priority_support": true,
        "beta_features_access": true,
        "custom_integrations": true
      }
    }
  },
  "permission_calculation": {
    "base_api_limit": 1000,
    "level_bonus": 200,
    "final_api_limit": 1200,
    "storage_base": "10GB",
    "storage_bonus": "2GB",
    "final_storage": "12GB"
  },
  "restrictions": {
    "geo_restrictions": ["CN", "US", "EU"],
    "time_restrictions": {
      "business_hours_only": false,
      "timezone": "UTC+8"
    },
    "feature_limitations": []
  },
  "expires_at": "2026-09-25T10:00:00Z",
  "last_permission_check": "2025-09-25T16:15:00Z"
}
```

---

## 👤 个人分配API

### 获取我的许可证分配

**端点**: `GET /api/v1/licenses/admin/assignments/my_assignments/`

**描述**: 获取当前用户的所有许可证分配

#### 响应示例

```json
{
  "count": 3,
  "assignments": [
    {
      "id": 1,
      "license_info": {
        "id": 456,
        "product_name": "专业开发工具",
        "plan_name": "专业版",
        "license_key": "****-****-****-1234"
      },
      "status": "active",
      "activated_at": "2025-09-25T10:30:00Z",
      "expires_at": "2026-09-25T10:00:00Z",
      "usage_summary": {
        "usage_count": 26,
        "last_used_at": "2025-09-25T16:15:00Z",
        "daily_average_hours": 6.5
      },
      "current_devices": [
        {
          "device_id": "device_123",
          "device_name": "MacBook Pro",
          "last_seen": "2025-09-25T16:15:00Z",
          "status": "active"
        }
      ],
      "available_features": [
        "advanced_analytics",
        "data_export",
        "api_access"
      ]
    }
  ],
  "summary": {
    "total_assignments": 3,
    "active_assignments": 2,
    "pending_assignments": 1,
    "total_devices_used": 4,
    "max_devices_allowed": 6
  }
}
```

---

## 📦 批量操作API

### 批量分配许可证

**端点**: `POST /api/v1/licenses/admin/assignments/batch_assign/`

**描述**: 为多个用户批量分配同一个许可证

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `member_ids` | array | 是 | 用户ID列表（1-50个） |
| `license_id` | integer | 是 | 许可证ID |
| `assignment_type` | string | 否 | 分配类型（默认direct） |
| `assignment_reason` | string | 否 | 分配原因 |
| `expires_at` | datetime | 否 | 过期时间 |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/batch_assign/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_ids": [123, 456, 789],
    "license_id": 999,
    "assignment_type": "direct",
    "assignment_reason": "新员工入职批量分配",
    "expires_at": "2026-09-25T10:00:00Z"
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "成功批量分配 3 个许可证",
  "assignment_ids": [10, 11, 12],
  "summary": {
    "total_requested": 3,
    "successful_assignments": 3,
    "failed_assignments": 0,
    "license_slots_used": 3,
    "remaining_slots": 7
  },
  "assignment_details": [
    {
      "member_id": 123,
      "assignment_id": 10,
      "status": "success"
    },
    {
      "member_id": 456,
      "assignment_id": 11,
      "status": "success"
    },
    {
      "member_id": 789,
      "assignment_id": 12,
      "status": "success"
    }
  ],
  "next_steps": [
    "通知用户激活许可证",
    "提供激活指导文档",
    "监控激活状态"
  ],
  "timestamp": "2025-09-25T16:20:00Z"
}
```

### 批量撤销许可证

**端点**: `POST /api/v1/licenses/admin/assignments/batch_revoke/`

**描述**: 批量撤销多个许可证分配

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `assignment_ids` | array | 是 | 分配ID列表 |
| `reason` | string | 否 | 撤销原因（默认"批量撤销"） |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/batch_revoke/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_ids": [10, 11, 12],
    "reason": "项目结束，回收许可证"
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "成功批量撤销 3 个许可证分配",
  "summary": {
    "total_requested": 3,
    "successful_revocations": 3,
    "failed_revocations": 0,
    "license_slots_freed": 3
  },
  "revocation_details": [
    {
      "assignment_id": 10,
      "member_id": 123,
      "status": "success",
      "revoked_at": "2025-09-25T16:25:00Z"
    },
    {
      "assignment_id": 11,
      "member_id": 456,
      "status": "success",
      "revoked_at": "2025-09-25T16:25:00Z"
    },
    {
      "assignment_id": 12,
      "member_id": 789,
      "status": "success",
      "revoked_at": "2025-09-25T16:25:00Z"
    }
  ],
  "timestamp": "2025-09-25T16:25:00Z"
}
```

---

## ⏰ 过期管理API

### 获取即将过期的分配

**端点**: `GET /api/v1/licenses/admin/assignments/expiring_soon/`

**描述**: 获取即将过期的许可证分配列表

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `days` | integer | 否 | 30 | 预警天数 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/assignments/expiring_soon/?days=14" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 响应示例

```json
{
  "count": 8,
  "days": 14,
  "expiring_assignments": [
    {
      "id": 5,
      "member_info": {
        "id": 123,
        "username": "john_doe",
        "email": "john@example.com"
      },
      "license_info": {
        "id": 456,
        "product_name": "专业开发工具",
        "plan_name": "专业版"
      },
      "expires_at": "2025-10-05T10:00:00Z",
      "days_until_expiry": 10,
      "usage_frequency": "daily",
      "last_used_at": "2025-09-25T15:45:00Z",
      "renewal_options": [
        {
          "type": "extend_current",
          "duration": "1 year",
          "cost": "$299"
        },
        {
          "type": "upgrade_plan",
          "plan": "企业版",
          "cost": "$499"
        }
      ],
      "notification_status": {
        "email_sent": false,
        "reminder_count": 0
      }
    }
  ],
  "summary": {
    "total_expiring": 8,
    "high_priority": 3,
    "daily_users": 5,
    "inactive_users": 1,
    "auto_renewable": 2
  },
  "recommended_actions": [
    "发送续期提醒邮件",
    "联系高优先级用户",
    "准备许可证续期方案"
  ]
}
```

---

## 📈 统计分析API

### 获取分配统计信息

**端点**: `GET /api/v1/licenses/admin/assignments/statistics/`

**描述**: 获取许可证分配的统计分析数据

#### 响应示例

```json
{
  "total_assignments": 150,
  "status_distribution": {
    "active": 120,
    "pending": 15,
    "expired": 10,
    "revoked": 5
  },
  "assignment_type_distribution": {
    "direct": 100,
    "shared": 30,
    "temporary": 15,
    "upgrade": 5
  },
  "priority_distribution": {
    "high": 20,
    "normal": 100,
    "low": 30
  },
  "usage_statistics": {
    "total_usage_count": 5250,
    "average_usage_per_assignment": 35,
    "active_in_last_30_days": 110,
    "never_used": 8,
    "peak_usage_hour": "14:00",
    "peak_usage_day": "Tuesday"
  },
  "license_utilization": {
    "total_license_slots": 200,
    "assigned_slots": 150,
    "utilization_rate": 0.75,
    "available_slots": 50
  },
  "trend_analysis": {
    "assignments_this_month": 25,
    "assignments_last_month": 18,
    "growth_rate": 0.39,
    "revocations_this_month": 3,
    "revocation_rate": 0.02
  },
  "expiry_forecast": {
    "expiring_next_30_days": 12,
    "expiring_next_90_days": 35,
    "renewal_rate_last_quarter": 0.82
  },
  "top_users": [
    {
      "username": "power_user_1",
      "usage_count": 150,
      "last_used": "2025-09-25T16:00:00Z"
    },
    {
      "username": "heavy_user_2", 
      "usage_count": 145,
      "last_used": "2025-09-25T15:30:00Z"
    }
  ],
  "license_health": {
    "healthy_assignments": 140,
    "warning_assignments": 8,
    "critical_assignments": 2,
    "health_score": 0.93
  }
}
```

---

## 💼 业务场景示例

### 场景1：新员工入职许可证分配

#### 流程图

```
HR创建员工档案 → IT审核需求 → 分配许可证 → 发送激活邮件 → 员工激活 → 开始工作
       ↓              ↓           ↓           ↓           ↓         ↓
   员工信息录入    确认岗位需求   API调用     自动邮件     用户操作   许可生效
   权限申请表    选择许可类型   批量分配     激活指导     客户端配置  开始使用
```

#### 1. 批量为新员工分配许可证

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/batch_assign/" \
  -H "Authorization: Bearer HR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_ids": [1001, 1002, 1003],
    "license_id": 500,
    "assignment_type": "direct",
    "assignment_reason": "2025年9月新员工入职",
    "expires_at": "2026-09-25T10:00:00Z"
  }'
```

#### 2. 发送激活通知（伪代码）

```python
# 获取新分配的许可证信息
assignments = [10, 11, 12]  # 从上一步响应中获取
for assignment_id in assignments:
    send_activation_email(assignment_id)
```

### 场景2：许可证到期续期管理

#### 1. 检查即将过期的许可证

```bash
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/assignments/expiring_soon/?days=30" \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN"
```

#### 2. 为重要用户手动续期

```bash
# 为高优先级用户续期许可证
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/" \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 123,
    "license_id": 456,
    "assignment_type": "direct",
    "assignment_reason": "重要用户许可证续期",
    "priority": "high",
    "expires_at": "2027-09-25T10:00:00Z"
  }'
```

### 场景3：项目结束资源回收

#### 批量回收项目组许可证

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/batch_revoke/" \
  -H "Authorization: Bearer PROJECT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_ids": [15, 16, 17, 18, 19],
    "reason": "ProjectX项目结束，回收开发工具许可证"
  }'
```

### 场景4：许可证使用监控

#### 1. 获取使用统计

```bash
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/assignments/statistics/" \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN"
```

#### 2. 查看特定用户的许可证使用情况

```bash
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/assignments/?member=123&ordering=-last_used_at" \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN"
```

### 场景5：自助服务门户

#### 用户查看自己的许可证

```bash
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/assignments/my_assignments/" \
  -H "Authorization: Bearer USER_TOKEN"
```

#### 用户激活自己的许可证

```bash
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/assignments/1/activate/" \
  -H "Authorization: Bearer USER_TOKEN"
```

---

## ⚠️ 常见错误和解决方案

### 许可证配额不足

```json
{
  "success": false,
  "error": {
    "code": "LICENSE_QUOTA_EXCEEDED",
    "message": "许可证激活配额已满",
    "details": {
      "max_activations": 10,
      "current_activations": 10,
      "requested_assignments": 3
    }
  }
}
```

**解决方案**: 
1. 升级许可证计划
2. 回收未使用的分配
3. 联系供应商增加配额

### 用户已有活跃分配

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_ASSIGNMENT",
    "message": "该用户已拥有此许可证的活跃分配",
    "details": {
      "existing_assignment_id": 5,
      "expires_at": "2026-09-25T10:00:00Z"
    }
  }
}
```

**解决方案**: 
1. 检查现有分配是否需要更新
2. 考虑升级现有分配的权限
3. 撤销旧分配后重新分配

### 分配不可撤销

```json
{
  "success": false,
  "error": {
    "code": "ASSIGNMENT_NOT_REVOCABLE",
    "message": "该分配当前不可撤销",
    "details": {
      "reason": "许可证正在使用中",
      "active_sessions": 2,
      "last_heartbeat": "2025-09-25T16:00:00Z"
    }
  }
}
```

**解决方案**: 
1. 通知用户保存工作并退出
2. 等待用户会话结束后再撤销
3. 强制撤销（可能导致数据丢失）

---

## 📋 最佳实践

### 1. 许可证分配策略

- **按需分配**: 根据实际工作需求分配许可证
- **优先级管理**: 为关键用户设置高优先级
- **定期审核**: 定期检查许可证使用情况

### 2. 生命周期管理

- **自动化流程**: 建立自动化的分配和回收流程
- **提前预警**: 在许可证过期前提前通知
- **数据备份**: 撤销前确保用户数据安全

### 3. 监控和优化

- **使用分析**: 定期分析许可证使用模式
- **成本优化**: 基于使用情况优化许可证购买
- **合规管理**: 确保许可证使用符合软件许可协议

### 4. 用户体验

- **自助服务**: 提供用户自助查看和激活功能
- **清晰指导**: 提供详细的激活和使用指导
- **及时支持**: 建立技术支持响应机制

---

下一步查看: [05_统计分析API.md](./05_统计分析API.md) 了解积分统计和数据分析的详细API使用方法。
