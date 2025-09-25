# 积分系统API - 详细文档

## 📋 目录

- [用户等级API](#用户等级api)
- [用户标签API](#用户标签api)
- [用户档案API](#用户档案api)
- [积分记录API](#积分记录api)
- [使用示例](#使用示例)

---

## 🎯 用户等级API

### 获取用户等级列表

**端点**: `GET /api/v1/points/user-levels/`

**描述**: 获取系统中所有可用的用户等级配置

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `is_active` | boolean | 否 | - | 过滤激活状态 |
| `is_default` | boolean | 否 | - | 过滤默认等级 |
| `search` | string | 否 | - | 搜索等级名称、代码、描述 |
| `ordering` | string | 否 | `level_order` | 排序字段 |
| `page` | integer | 否 | 1 | 页码 |
| `page_size` | integer | 否 | 20 | 每页条数 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/user-levels/?is_active=true&ordering=level_order" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### 响应格式

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "level_name": "青铜会员",
      "level_code": "BRONZE",
      "level_order": 1,
      "min_points": 0,
      "max_points": 999,
      "permissions": {
        "can_view_basic_content": true,
        "discount_rate": 0.05,
        "priority_support": false
      },
      "quota_config": {
        "max_downloads_per_day": 10,
        "max_api_calls_per_hour": 100
      },
      "level_color": "#CD7F32",
      "level_icon": "🥉",
      "level_description": "新用户的起始等级",
      "is_active": true,
      "is_default": true,
      "created_at": "2025-09-25T10:00:00Z",
      "updated_at": "2025-09-25T10:00:00Z"
    },
    {
      "id": 2,
      "level_name": "白银会员",
      "level_code": "SILVER",
      "level_order": 2,
      "min_points": 1000,
      "max_points": 4999,
      "permissions": {
        "can_view_basic_content": true,
        "can_view_premium_content": true,
        "discount_rate": 0.10,
        "priority_support": false
      },
      "quota_config": {
        "max_downloads_per_day": 20,
        "max_api_calls_per_hour": 200
      },
      "level_color": "#C0C0C0",
      "level_icon": "🥈",
      "level_description": "中级会员等级",
      "is_active": true,
      "is_default": false,
      "created_at": "2025-09-25T10:00:00Z",
      "updated_at": "2025-09-25T10:00:00Z"
    }
  ]
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer | 等级唯一标识 |
| `level_name` | string | 等级显示名称 |
| `level_code` | string | 等级代码（唯一） |
| `level_order` | integer | 等级排序（越大等级越高） |
| `min_points` | integer | 达到该等级的最低积分 |
| `max_points` | integer | 该等级的最高积分（null表示无上限） |
| `permissions` | object | 等级权限配置 |
| `quota_config` | object | 等级配额配置 |
| `level_color` | string | 等级颜色（十六进制） |
| `level_icon` | string | 等级图标 |
| `level_description` | string | 等级描述 |
| `is_active` | boolean | 是否激活 |
| `is_default` | boolean | 是否为默认等级 |

---

## 🏷️ 用户标签API

### 获取用户标签列表

**端点**: `GET /api/v1/points/user-type-tags/`

**描述**: 获取系统中所有可用的用户标签定义

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `tag_type` | string | 否 | - | 过滤标签类型 |
| `is_active` | boolean | 否 | - | 过滤激活状态 |
| `is_assignable` | boolean | 否 | - | 过滤可分配状态 |
| `requires_payment` | boolean | 否 | - | 过滤付费状态 |
| `search` | string | 否 | - | 搜索标签名称、代码、描述 |
| `ordering` | string | 否 | `-tag_level,tag_name` | 排序字段 |

#### 响应格式

```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "tag_name": "VIP金牌",
      "tag_code": "VIP_GOLD",
      "tag_type": "vip",
      "tag_color": "#FFD700",
      "tag_icon": "👑",
      "tag_description": "最高级别的VIP会员",
      "permission_modifiers": {
        "discount_rate_bonus": 0.10,
        "priority_support": true,
        "exclusive_content_access": true
      },
      "quota_modifiers": {
        "download_multiplier": 2.0,
        "api_calls_multiplier": 3.0
      },
      "price_config": {
        "monthly_price": 99.00,
        "yearly_price": 999.00,
        "currency": "CNY"
      },
      "default_duration_days": 30,
      "max_duration_days": 365,
      "tag_level": 10,
      "is_active": true,
      "is_assignable": true,
      "requires_payment": true,
      "created_at": "2025-09-25T10:00:00Z",
      "updated_at": "2025-09-25T10:00:00Z"
    }
  ]
}
```

#### 标签类型说明

| 类型 | 代码 | 说明 |
|------|------|------|
| VIP | `vip` | VIP会员标签 |
| 特权 | `privilege` | 特殊权限标签 |
| 临时 | `temporary` | 临时活动标签 |
| 系统 | `system` | 系统内置标签 |

---

## 👤 用户档案API

### 获取用户档案列表

**端点**: `GET /api/v1/points/profiles/`

**描述**: 获取当前租户下的所有用户积分档案

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `tenant` | integer | 否 | - | 过滤租户ID |
| `current_level` | integer | 否 | - | 过滤当前等级 |
| `is_points_enabled` | boolean | 否 | - | 过滤积分启用状态 |
| `search` | string | 否 | - | 搜索用户名、邮箱 |
| `ordering` | string | 否 | `-total_points` | 排序字段 |

#### 响应示例

```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "member": 123,
      "tenant": 456,
      "total_points": 2500,
      "available_points": 2300,
      "current_level": 3,
      "level_updated_at": "2025-09-20T14:30:00Z",
      "points_earned_total": 3000,
      "points_spent_total": 500,
      "points_expired_total": 0,
      "last_points_update": "2025-09-25T15:45:00Z",
      "last_level_check": "2025-09-25T16:00:00Z",
      "consecutive_login_days": 15,
      "last_login_date": "2025-09-25",
      "points_multiplier": "1.20",
      "is_points_enabled": true,
      "member_info": {
        "id": 123,
        "username": "john_doe",
        "email": "john@example.com",
        "is_active": true
      },
      "tenant_info": {
        "id": 456,
        "name": "ACME Corp",
        "is_active": true
      },
      "current_level_info": {
        "id": 3,
        "level_name": "黄金会员",
        "level_code": "GOLD",
        "level_order": 3,
        "min_points": 2000,
        "max_points": 9999,
        "level_color": "#FFD700",
        "level_icon": "🏆"
      },
      "points_summary": {
        "total_points": 2500,
        "current_level": "黄金会员",
        "points_multiplier": 1.20,
        "summary_period_days": 30,
        "earned": {
          "total": 300,
          "categories": {
            "login": 150,
            "license": 100,
            "referral": 50
          }
        },
        "spent": {
          "total": 100,
          "categories": {
            "vip_upgrade": 100
          }
        },
        "net_change": 200,
        "category_breakdown": [
          {
            "category": "login",
            "earned": 150,
            "spent": 0,
            "net": 150
          }
        ]
      },
      "active_tags": [
        {
          "id": 1,
          "tag_name": "VIP金牌",
          "tag_code": "VIP_GOLD",
          "tag_type": "vip",
          "tag_color": "#FFD700",
          "expires_at": "2025-12-31T23:59:59Z",
          "status": "active",
          "vip_status": {
            "is_active": true,
            "is_expired": false,
            "is_in_grace_period": false,
            "days_until_expiry": 97
          }
        }
      ],
      "effective_permissions": {
        "can_view_basic_content": true,
        "can_view_premium_content": true,
        "can_view_exclusive_content": true,
        "discount_rate": 0.25,
        "priority_support": true,
        "can_earn_points": true,
        "can_spend_points": true,
        "can_manage_points": false
      },
      "created_at": "2025-08-15T10:00:00Z",
      "updated_at": "2025-09-25T16:00:00Z"
    }
  ]
}
```

### 获取用户积分摘要

**端点**: `GET /api/v1/points/profiles/{id}/summary/`

**描述**: 获取指定用户的积分详细摘要信息

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `days` | integer | 否 | 30 | 统计天数 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/profiles/123/summary/?days=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 响应示例

```json
{
  "total_points": 2500,
  "current_level": "黄金会员",
  "points_multiplier": 1.20,
  "summary_period_days": 30,
  "earned": {
    "total": 300,
    "by_category": {
      "login": 150,
      "license": 100,
      "referral": 50
    },
    "by_day": [
      {
        "date": "2025-09-25",
        "points": 15
      },
      {
        "date": "2025-09-24", 
        "points": 25
      }
    ]
  },
  "spent": {
    "total": 100,
    "by_category": {
      "vip_upgrade": 100
    },
    "by_day": [
      {
        "date": "2025-09-20",
        "points": 100
      }
    ]
  },
  "net_change": 200,
  "level_progress": {
    "current_level": {
      "name": "黄金会员",
      "color": "#FFD700",
      "min_points": 2000,
      "max_points": 9999
    },
    "current_points": 2500,
    "next_level": {
      "name": "钻石会员",
      "color": "#B9F2FF",
      "min_points": 10000
    },
    "points_to_next": 7500,
    "progress_percentage": 6.67
  },
  "predictions": {
    "estimated_days_to_next_level": 125,
    "monthly_average_earned": 300,
    "trend": "increasing"
  }
}
```

### 用户获得积分

**端点**: `POST /api/v1/points/profiles/{id}/earn_points/`

**描述**: 为指定用户增加积分

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `points_amount` | integer | 是 | 积分数量（>0） |
| `category` | string | 是 | 业务分类 |
| `subcategory` | string | 否 | 子分类 |
| `reason` | string | 否 | 操作原因 |
| `expires_at` | datetime | 否 | 过期时间 |
| `source_type` | string | 否 | 来源类型（默认manual） |
| `source_id` | integer | 否 | 关联源记录ID |

#### 业务分类说明

| 分类 | 代码 | 说明 |
|------|------|------|
| 登录奖励 | `login` | 每日登录获得积分 |
| 许可证 | `license` | 许可证相关操作 |
| 推荐奖励 | `referral` | 推荐新用户奖励 |
| 社区活动 | `community` | 社区互动奖励 |
| 付费返点 | `payment` | 付费获得积分 |
| 手动调整 | `manual` | 管理员手动操作 |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/profiles/123/earn_points/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points_amount": 100,
    "category": "login",
    "subcategory": "daily_login",
    "reason": "每日登录奖励",
    "expires_at": "2026-09-25T16:00:00Z",
    "source_type": "system",
    "source_id": null
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "成功获得 100 积分",
  "record_id": 789,
  "new_total_points": 2600,
  "level_change": {
    "upgraded": false,
    "previous_level": "黄金会员",
    "current_level": "黄金会员"
  },
  "applied_multiplier": 1.20,
  "actual_points_added": 120,
  "timestamp": "2025-09-25T16:00:00Z"
}
```

### 用户消费积分

**端点**: `POST /api/v1/points/profiles/{id}/spend_points/`

**描述**: 扣除指定用户的积分

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `points_amount` | integer | 是 | 消费积分数量（>0） |
| `category` | string | 是 | 业务分类 |
| `subcategory` | string | 否 | 子分类 |
| `reason` | string | 否 | 消费原因 |
| `source_type` | string | 否 | 来源类型 |
| `source_id` | integer | 否 | 关联源记录ID |

#### 消费分类说明

| 分类 | 代码 | 说明 |
|------|------|------|
| VIP升级 | `vip_upgrade` | 购买VIP服务 |
| 许可证折扣 | `license_discount` | 许可证购买折扣 |
| 功能解锁 | `feature_unlock` | 解锁特殊功能 |
| 优先支持 | `priority_support` | 购买优先技术支持 |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/profiles/123/spend_points/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points_amount": 500,
    "category": "vip_upgrade",
    "subcategory": "monthly_vip",
    "reason": "购买月度VIP会员",
    "source_type": "order",
    "source_id": 456
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "成功消费 500 积分",
  "record_id": 790,
  "new_total_points": 2100,
  "remaining_points": 1900,
  "timestamp": "2025-09-25T16:05:00Z"
}
```

### 手动调整积分

**端点**: `POST /api/v1/points/profiles/{id}/adjust_points/`

**描述**: 管理员手动调整用户积分（可正可负）

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `points_amount` | integer | 是 | 调整积分数量 |
| `is_negative` | boolean | 否 | 是否为负数调整 |
| `category` | string | 否 | 业务分类（默认manual） |
| `subcategory` | string | 否 | 子分类 |
| `reason` | string | 是 | 调整原因 |
| `source_type` | string | 否 | 来源类型（默认manual） |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/profiles/123/adjust_points/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points_amount": 200,
    "is_negative": false,
    "category": "manual",
    "reason": "客服补偿积分",
    "source_type": "manual"
  }'
```

### 获取用户权限

**端点**: `GET /api/v1/points/profiles/{id}/permissions/`

**描述**: 获取用户的综合权限信息

#### 响应示例

```json
{
  "user_id": 123,
  "tenant_id": 456,
  "base_permissions": {
    "can_view_basic_content": true,
    "can_use_basic_features": true
  },
  "level_permissions": {
    "level_name": "黄金会员",
    "can_view_premium_content": true,
    "discount_rate": 0.15,
    "priority_support": false
  },
  "vip_tag_permissions": {
    "VIP_GOLD": {
      "discount_rate_bonus": 0.10,
      "priority_support": true,
      "exclusive_content_access": true
    }
  },
  "effective_permissions": {
    "can_view_basic_content": true,
    "can_view_premium_content": true,
    "can_view_exclusive_content": true,
    "discount_rate": 0.25,
    "priority_support": true,
    "can_earn_points": true,
    "can_spend_points": true,
    "max_downloads_per_day": 40,
    "max_api_calls_per_hour": 600
  },
  "permission_calculation": {
    "base_discount": 0.0,
    "level_discount": 0.15,
    "vip_bonus": 0.10,
    "final_discount": 0.25
  }
}
```

---

## 📊 积分记录API

### 获取积分记录列表

**端点**: `GET /api/v1/points/points-records/`

**描述**: 获取积分操作记录

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `tenant` | integer | 否 | - | 过滤租户 |
| `point_type` | string | 否 | - | 积分类型（earn/spend/adjust/expire） |
| `category` | string | 否 | - | 业务分类 |
| `status` | string | 否 | - | 记录状态（active/expired/cancelled） |
| `is_manual` | boolean | 否 | - | 是否手动操作 |
| `source_type` | string | 否 | - | 来源类型 |
| `created_at__gte` | datetime | 否 | - | 创建时间起始 |
| `created_at__lte` | datetime | 否 | - | 创建时间结束 |
| `ordering` | string | 否 | `-created_at` | 排序字段 |

#### 响应示例

```json
{
  "count": 2,
  "results": [
    {
      "id": 789,
      "tenant_user_profile": 1,
      "member": 123,
      "tenant": 456,
      "point_type": "earn",
      "category": "login",
      "subcategory": "daily_login",
      "points": 120,
      "balance_before": 2480,
      "balance_after": 2600,
      "tenant_multiplier": "1.20",
      "original_points": 100,
      "source_type": "system",
      "source_id": null,
      "source_description": "每日登录奖励",
      "earned_at": "2025-09-25T16:00:00Z",
      "expires_at": "2026-09-25T16:00:00Z",
      "expired_at": null,
      "operation_reason": "每日登录奖励",
      "operator_id": null,
      "batch_id": null,
      "status": "active",
      "is_manual": false,
      "member_info": {
        "id": 123,
        "username": "john_doe"
      },
      "tenant_info": {
        "id": 456,
        "name": "ACME Corp"
      },
      "profile_info": {
        "id": 1,
        "total_points": 2600,
        "current_level_name": "黄金会员"
      },
      "is_expired": false,
      "days_until_expiry": 365,
      "created_at": "2025-09-25T16:00:00Z",
      "created_by_id": null
    }
  ]
}
```

### 获取积分记录统计

**端点**: `GET /api/v1/points/points-records/summary/`

**描述**: 获取积分记录的统计摘要

#### 响应示例

```json
{
  "total_records": 1500,
  "by_type": {
    "earn": 1200,
    "spend": 250,
    "adjust": 30,
    "expire": 20
  },
  "by_category": {
    "login": 800,
    "license": 200,
    "vip_upgrade": 150,
    "manual": 100,
    "referral": 50
  },
  "by_status": {
    "active": 1450,
    "expired": 30,
    "cancelled": 20
  },
  "total_points_flow": {
    "earned": 150000,
    "spent": 25000,
    "net": 125000
  }
}
```

---

## 💡 使用示例

### 完整的积分操作流程

#### 1. 新用户注册后初始化积分档案

```bash
# 查看默认等级
curl -X GET \
  "http://localhost:8000/api/v1/points/user-levels/?is_default=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 为新用户创建档案（通常由系统自动创建）
# 档案会自动分配默认等级
```

#### 2. 用户每日登录获得积分

```bash
# 获得每日登录积分
curl -X POST \
  "http://localhost:8000/api/v1/points/profiles/123/earn_points/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points_amount": 10,
    "category": "login",
    "subcategory": "daily_login",
    "reason": "每日登录奖励",
    "source_type": "system"
  }'
```

#### 3. 用户购买许可证获得积分

```bash
# 许可证激活奖励
curl -X POST \
  "http://localhost:8000/api/v1/points/profiles/123/earn_points/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points_amount": 100,
    "category": "license",
    "subcategory": "activation",
    "reason": "激活专业版许可证",
    "source_type": "license",
    "source_id": 789
  }'
```

#### 4. 检查等级升级

```bash
# 获取用户当前状态
curl -X GET \
  "http://localhost:8000/api/v1/points/profiles/123/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 查看积分摘要和等级进度
curl -X GET \
  "http://localhost:8000/api/v1/points/profiles/123/summary/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 5. 用户消费积分购买VIP

```bash
# 消费积分购买VIP
curl -X POST \
  "http://localhost:8000/api/v1/points/profiles/123/spend_points/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points_amount": 1000,
    "category": "vip_upgrade",
    "subcategory": "monthly_vip",
    "reason": "购买VIP金牌月卡",
    "source_type": "order",
    "source_id": 456
  }'
```

#### 6. 管理员调整积分

```bash
# 客服补偿积分
curl -X POST \
  "http://localhost:8000/api/v1/points/profiles/123/adjust_points/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points_amount": 500,
    "is_negative": false,
    "reason": "客服补偿：系统故障导致积分丢失",
    "category": "manual",
    "source_type": "manual"
  }'
```

#### 7. 查看积分记录

```bash
# 查看用户最近的积分记录
curl -X GET \
  "http://localhost:8000/api/v1/points/points-records/?member=123&ordering=-created_at&page_size=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## ⚠️ 常见错误

### 积分不足

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_POINTS",
    "message": "积分余额不足",
    "details": {
      "required_points": 1000,
      "available_points": 800,
      "shortage": 200
    }
  }
}
```

### 积分已禁用

```json
{
  "success": false,
  "error": {
    "code": "POINTS_DISABLED",
    "message": "该用户未启用积分功能"
  }
}
```

### 每日限额

```json
{
  "success": false,
  "error": {
    "code": "DAILY_LIMIT_EXCEEDED",
    "message": "今日登录积分已达上限",
    "details": {
      "daily_limit": 50,
      "earned_today": 50
    }
  }
}
```

---

下一步查看: [03_VIP标签管理API.md](./03_VIP标签管理API.md) 了解VIP标签管理的详细API使用方法。
