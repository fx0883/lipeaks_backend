# VIP标签管理API - 详细文档

## 📋 目录

- [VIP标签概述](#vip标签概述)
- [VIP标签列表API](#vip标签列表api)
- [VIP标签授予API](#vip标签授予api)
- [VIP标签续期API](#vip标签续期api)
- [VIP标签撤销API](#vip标签撤销api)
- [VIP状态查询API](#vip状态查询api)
- [过期管理API](#过期管理api)
- [业务场景示例](#业务场景示例)

---

## 💎 VIP标签概述

### VIP标签系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    VIP标签生命周期                          │
├─────────────────────────────────────────────────────────────┤
│  申请/购买 → 授予 → 激活 → 使用 → 续期 → 过期 → 宽限期 → 撤销 │
│     ↓         ↓      ↓      ↓      ↓      ↓       ↓       ↓  │
│   用户请求   管理员  自动   享受   付费   时间   缓冲    最终 │
│   支付验证   审核    生效   权益   延期   到达   期间    失效 │
└─────────────────────────────────────────────────────────────┘
```

### VIP标签状态

| 状态 | 代码 | 说明 |
|------|------|------|
| 激活 | `active` | 正常使用中 |
| 已过期 | `expired` | 已过期，权益失效 |
| 宽限期 | `grace_period` | 过期后的缓冲期 |
| 已撤销 | `revoked` | 管理员主动撤销 |
| 暂停 | `suspended` | 临时暂停 |

### VIP标签类型

| 类型 | 代码 | 说明 | 特点 |
|------|------|------|------|
| VIP会员 | `vip` | 付费VIP服务 | 需要付费，有明确期限 |
| 特权标签 | `privilege` | 特殊权限 | 可免费授予，灵活期限 |
| 临时标签 | `temporary` | 活动标签 | 短期有效，通常免费 |
| 系统标签 | `system` | 系统内置 | 系统管理，不可撤销 |

---

## 📄 VIP标签列表API

### 获取VIP标签列表

**端点**: `GET /api/v1/points/vip-tags/`

**描述**: 获取当前租户下的所有VIP标签分配记录

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `tenant` | integer | 否 | 当前租户 | 过滤租户ID |
| `tag` | integer | 否 | - | 过滤标签类型ID |
| `status` | string | 否 | - | 过滤状态 |
| `is_active` | boolean | 否 | - | 过滤激活状态 |
| `auto_renewal` | boolean | 否 | - | 过滤自动续期状态 |
| `grant_method` | string | 否 | - | 过滤授予方式 |
| `expires_at__gte` | datetime | 否 | - | 过期时间起始 |
| `expires_at__lte` | datetime | 否 | - | 过期时间结束 |
| `search` | string | 否 | - | 搜索授予原因、备注 |
| `ordering` | string | 否 | `-granted_at` | 排序字段 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/vip-tags/?status=active&ordering=-granted_at" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### 响应示例

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/points/vip-tags/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "tenant_user_profile": 1,
      "tag": 3,
      "member": 123,
      "tenant": 456,
      "granted_at": "2025-09-25T10:00:00Z",
      "granted_by_id": 789,
      "grant_reason": "用户购买VIP金牌月卡",
      "grant_method": "payment",
      "expires_at": "2025-10-25T10:00:00Z",
      "original_duration_days": 30,
      "extended_days": 0,
      "auto_renewal": true,
      "renewal_count": 0,
      "grace_period_days": 7,
      "reminder_sent_at": null,
      "renewal_reminder_sent": false,
      "last_used_at": "2025-09-25T15:30:00Z",
      "usage_count": 15,
      "benefits_used": [
        "premium_download",
        "priority_support",
        "exclusive_content"
      ],
      "payment_id": "pay_123456789",
      "payment_amount": "99.00",
      "payment_currency": "CNY",
      "is_active": true,
      "status": "active",
      "notes": "正常付费用户",
      "metadata": {
        "purchase_source": "mobile_app",
        "promotion_code": "NEWUSER2025"
      },
      "tag_info": {
        "id": 3,
        "tag_name": "VIP金牌",
        "tag_code": "VIP_GOLD",
        "tag_type": "vip",
        "tag_color": "#FFD700",
        "tag_icon": "👑",
        "tag_description": "最高级别的VIP会员",
        "requires_payment": true,
        "default_duration_days": 30
      },
      "member_info": {
        "id": 123,
        "username": "john_doe"
      },
      "tenant_info": {
        "id": 456,
        "name": "ACME Corp"
      },
      "vip_status": {
        "is_active": true,
        "is_expired": false,
        "is_in_grace_period": false,
        "days_until_expiry": 30,
        "can_renew": true,
        "auto_renewal_enabled": true
      },
      "days_until_expiry": 30,
      "usage_summary": {
        "usage_count": 15,
        "last_used_at": "2025-09-25T15:30:00Z",
        "total_benefits_used": 3,
        "renewal_count": 0,
        "auto_renewal": true
      },
      "created_at": "2025-09-25T10:00:00Z",
      "updated_at": "2025-09-25T15:30:00Z"
    }
  ]
}
```

#### 字段详细说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer | VIP标签分配记录ID |
| `tenant_user_profile` | integer | 用户档案ID |
| `tag` | integer | VIP标签定义ID |
| `member` | integer | 用户ID |
| `tenant` | integer | 租户ID |
| `granted_at` | datetime | 授予时间 |
| `granted_by_id` | integer | 授予操作员ID |
| `grant_reason` | string | 授予原因 |
| `grant_method` | string | 授予方式（payment/manual/system/promotion） |
| `expires_at` | datetime | 过期时间 |
| `original_duration_days` | integer | 原始有效期天数 |
| `extended_days` | integer | 延期天数 |
| `auto_renewal` | boolean | 是否自动续期 |
| `renewal_count` | integer | 续期次数 |
| `grace_period_days` | integer | 宽限期天数 |
| `reminder_sent_at` | datetime | 提醒发送时间 |
| `renewal_reminder_sent` | boolean | 是否已发送续期提醒 |
| `last_used_at` | datetime | 最后使用时间 |
| `usage_count` | integer | 使用次数 |
| `benefits_used` | array | 已使用的权益列表 |
| `payment_id` | string | 支付订单ID |
| `payment_amount` | decimal | 支付金额 |
| `payment_currency` | string | 支付货币 |
| `is_active` | boolean | 是否激活 |
| `status` | string | 状态 |
| `notes` | text | 备注 |
| `metadata` | json | 元数据 |

---

## 🎁 VIP标签授予API

### 授予VIP标签

**端点**: `POST /api/v1/points/vip-tags/grant_vip_tag/`

**描述**: 为指定用户授予VIP标签

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `member_id` | integer | 是 | 目标用户ID |
| `tag_id` | integer | 是 | VIP标签ID |
| `duration_days` | integer | 否 | 有效期天数（使用标签默认值） |
| `grant_method` | string | 否 | 授予方式（默认manual） |
| `reason` | string | 否 | 授予原因 |
| `payment_info` | object | 否 | 支付信息 |

#### 授予方式说明

| 方式 | 代码 | 说明 |
|------|------|------|
| 手动授予 | `manual` | 管理员手动操作 |
| 付费购买 | `payment` | 用户付费购买 |
| 系统自动 | `system` | 系统自动授予 |
| 促销活动 | `promotion` | 促销活动获得 |
| 积分兑换 | `points_exchange` | 积分兑换获得 |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/vip-tags/grant_vip_tag/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 123,
    "tag_id": 3,
    "duration_days": 30,
    "grant_method": "payment",
    "reason": "用户购买VIP金牌月卡",
    "payment_info": {
      "payment_id": "pay_123456789",
      "amount": 99.00,
      "currency": "CNY",
      "payment_method": "alipay",
      "transaction_id": "2025092516001004100200123456"
    }
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "成功授予 VIP金牌 标签",
  "tag_assignment_id": 1,
  "expires_at": "2025-10-25T16:00:00Z",
  "benefits_activated": [
    "premium_download",
    "priority_support", 
    "exclusive_content",
    "ad_free_experience"
  ],
  "effective_permissions": {
    "discount_rate_bonus": 0.10,
    "priority_support": true,
    "exclusive_content_access": true,
    "download_multiplier": 2.0
  },
  "auto_renewal_enabled": true,
  "grace_period_days": 7,
  "timestamp": "2025-09-25T16:00:00Z"
}
```

---

## 🔄 VIP标签续期API

### 续期VIP标签

**端点**: `POST /api/v1/points/vip-tags/{id}/renew/`

**描述**: 为指定的VIP标签分配续期

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `duration_days` | integer | 是 | 续期天数 |
| `renewal_method` | string | 否 | 续期方式（默认manual） |
| `reason` | string | 否 | 续期原因 |
| `payment_info` | object | 否 | 支付信息 |

#### 续期方式说明

| 方式 | 代码 | 说明 |
|------|------|------|
| 自动续期 | `auto` | 系统自动续期 |
| 手动续期 | `manual` | 手动操作续期 |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/vip-tags/1/renew/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_days": 30,
    "renewal_method": "manual",
    "reason": "用户手动续费VIP服务",
    "payment_info": {
      "payment_id": "pay_987654321",
      "amount": 99.00,
      "currency": "CNY"
    }
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "成功续期 VIP金牌 标签 30 天",
  "new_expires_at": "2025-11-24T16:00:00Z",
  "extended_days": 30,
  "renewal_count": 1,
  "total_duration_days": 60,
  "auto_renewal_status": {
    "enabled": true,
    "next_renewal_date": "2025-11-17T16:00:00Z"
  },
  "timestamp": "2025-09-25T16:00:00Z"
}
```

---

## ❌ VIP标签撤销API

### 撤销VIP标签

**端点**: `POST /api/v1/points/vip-tags/{id}/revoke/`

**描述**: 撤销指定的VIP标签分配

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | 否 | 撤销原因（默认"管理员撤销"） |

#### 请求示例

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/vip-tags/1/revoke/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "用户违反服务条款"
  }'
```

#### 响应示例

```json
{
  "success": true,
  "message": "成功撤销 VIP金牌 标签",
  "revoked_at": "2025-09-25T16:00:00Z",
  "revoke_reason": "用户违反服务条款",
  "refund_info": {
    "eligible_for_refund": true,
    "refund_amount": 66.00,
    "refund_reason": "剩余20天按比例退费"
  },
  "affected_permissions": [
    "premium_download",
    "priority_support",
    "exclusive_content"
  ],
  "timestamp": "2025-09-25T16:00:00Z"
}
```

---

## 📊 VIP状态查询API

### 获取VIP标签详细状态

**端点**: `GET /api/v1/points/vip-tags/{id}/status/`

**描述**: 获取指定VIP标签的详细状态信息

#### 响应示例

```json
{
  "tag_assignment_id": 1,
  "tag_name": "VIP金牌",
  "member": "john_doe",
  "vip_status": {
    "is_active": true,
    "is_expired": false,
    "is_in_grace_period": false,
    "status_code": "active",
    "status_description": "正常使用中",
    "days_until_expiry": 30,
    "hours_until_expiry": 720,
    "expiry_timestamp": "2025-10-25T16:00:00Z"
  },
  "renewal_info": {
    "can_renew": true,
    "auto_renewal_enabled": true,
    "next_renewal_attempt": "2025-10-18T16:00:00Z",
    "renewal_count": 0,
    "renewal_history": []
  },
  "usage_statistics": {
    "usage_count": 15,
    "last_used_at": "2025-09-25T15:30:00Z",
    "daily_usage_average": 2.1,
    "total_benefits_used": 3,
    "most_used_benefit": "premium_download"
  },
  "payment_info": {
    "payment_id": "pay_123456789",
    "amount_paid": "99.00",
    "currency": "CNY",
    "payment_date": "2025-09-25T10:00:00Z",
    "refund_eligible": true,
    "refund_amount": "66.00"
  },
  "permissions": {
    "current_permissions": {
      "discount_rate_bonus": 0.10,
      "priority_support": true,
      "exclusive_content_access": true,
      "download_multiplier": 2.0
    },
    "permissions_on_expiry": {
      "will_lose": [
        "priority_support",
        "exclusive_content_access"
      ],
      "will_retain": [
        "basic_member_benefits"
      ]
    }
  },
  "timeline": [
    {
      "event": "granted",
      "timestamp": "2025-09-25T10:00:00Z",
      "description": "VIP标签授予"
    },
    {
      "event": "first_use",
      "timestamp": "2025-09-25T10:30:00Z",
      "description": "首次使用VIP权益"
    },
    {
      "event": "payment_confirmed",
      "timestamp": "2025-09-25T10:05:00Z", 
      "description": "支付确认"
    }
  ]
}
```

---

## ⏰ 过期管理API

### 获取即将过期的VIP标签

**端点**: `GET /api/v1/points/vip-tags/expiring_soon/`

**描述**: 获取即将过期的VIP标签列表

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `days` | integer | 否 | 7 | 预警天数 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/vip-tags/expiring_soon/?days=14" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 响应示例

```json
{
  "count": 5,
  "days": 14,
  "expiring_tags": [
    {
      "id": 1,
      "member_info": {
        "id": 123,
        "username": "john_doe",
        "email": "john@example.com"
      },
      "tag_info": {
        "id": 3,
        "tag_name": "VIP金牌",
        "tag_type": "vip"
      },
      "expires_at": "2025-10-05T16:00:00Z",
      "days_until_expiry": 10,
      "auto_renewal": true,
      "renewal_status": {
        "next_attempt": "2025-09-28T16:00:00Z",
        "payment_method_valid": true,
        "balance_sufficient": true
      },
      "notification_status": {
        "reminder_sent": false,
        "email_notifications_enabled": true,
        "sms_notifications_enabled": false
      }
    }
  ],
  "summary": {
    "total_expiring": 5,
    "auto_renewal_enabled": 3,
    "manual_renewal_needed": 2,
    "notification_pending": 4
  }
}
```

---

## 💼 业务场景示例

### 场景1：用户购买VIP会员

#### 流程图

```
用户选择VIP套餐 → 创建订单 → 支付成功 → 授予VIP标签 → 发送确认通知
       ↓              ↓           ↓          ↓            ↓
   浏览VIP特权    生成订单号   第三方支付   API调用      邮件/短信
   选择期限      记录用户信息  处理支付     更新权限      推送通知
```

#### 1. 用户支付成功后，系统调用授予API

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/vip-tags/grant_vip_tag/" \
  -H "Authorization: Bearer SYSTEM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 123,
    "tag_id": 3,
    "duration_days": 30,
    "grant_method": "payment",
    "reason": "用户购买VIP金牌月卡",
    "payment_info": {
      "payment_id": "pay_2025092516001",
      "amount": 99.00,
      "currency": "CNY",
      "payment_method": "wechat_pay"
    }
  }'
```

#### 2. 检查授予结果

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/vip-tags/1/status/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 场景2：VIP会员自动续期

#### 自动续期流程

```
系统定时检查 → 发现即将过期 → 验证支付方式 → 自动扣费 → 续期成功 → 发送通知
       ↓              ↓              ↓           ↓         ↓         ↓
   每日凌晨运行    7天过期预警     检查绑定卡片   第三方API  延长期限   确认邮件
   扫描到期用户    标记需要续期     余额是否充足   处理续费   更新数据   用户通知
```

#### 模拟自动续期

```bash
# 系统调用续期API
curl -X POST \
  "http://localhost:8000/api/v1/points/vip-tags/1/renew/" \
  -H "Authorization: Bearer SYSTEM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_days": 30,
    "renewal_method": "auto",
    "reason": "自动续期VIP服务",
    "payment_info": {
      "payment_id": "pay_auto_2025092516002",
      "amount": 99.00,
      "currency": "CNY"
    }
  }'
```

### 场景3：管理员处理客服投诉

#### 投诉处理流程

```
用户投诉 → 客服受理 → 调查核实 → 决定补偿 → 授予VIP → 记录处理结果
    ↓         ↓         ↓         ↓        ↓          ↓
  服务问题   工单系统   查看日志   管理层决策  API操作   更新工单
  体验不佳   分配客服   技术分析   补偿方案   权限生效   结案归档
```

#### 管理员免费授予VIP作为补偿

```bash
curl -X POST \
  "http://localhost:8000/api/v1/points/vip-tags/grant_vip_tag/" \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 456,
    "tag_id": 2,
    "duration_days": 15,
    "grant_method": "manual",
    "reason": "客服补偿：因系统故障影响用户体验",
    "payment_info": null
  }'
```

### 场景4：批量VIP管理

#### 促销活动批量授予

```bash
# 为参与活动的用户批量授予临时VIP
# 注意：这需要循环调用或使用批量接口

users=(123 456 789 101112)
for user_id in "${users[@]}"
do
  curl -X POST \
    "http://localhost:8000/api/v1/points/vip-tags/grant_vip_tag/" \
    -H "Authorization: Bearer TENANT_ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"member_id\": $user_id,
      \"tag_id\": 4,
      \"duration_days\": 7,
      \"grant_method\": \"promotion\",
      \"reason\": \"中秋节特别活动赠送\"
    }"
done
```

### 场景5：VIP权益使用监控

#### 查看VIP使用情况

```bash
# 获取当前租户所有活跃VIP用户
curl -X GET \
  "http://localhost:8000/api/v1/points/vip-tags/?status=active&ordering=-last_used_at" \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN"

# 分析本租户VIP使用统计
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/" \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN"
```

---

## ⚠️ 常见错误和解决方案

### VIP标签已存在

```json
{
  "success": false,
  "error": {
    "code": "VIP_TAG_ALREADY_EXISTS",
    "message": "该用户已拥有此类型的VIP标签",
    "details": {
      "existing_tag_id": 5,
      "expires_at": "2025-12-31T23:59:59Z"
    }
  }
}
```

**解决方案**: 检查现有标签，决定是续期还是升级

### 支付信息无效

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PAYMENT_INFO",
    "message": "支付信息验证失败",
    "details": {
      "payment_id": "未找到对应的支付记录",
      "amount": "支付金额与标签价格不匹配"
    }
  }
}
```

**解决方案**: 验证支付记录的真实性和完整性

### VIP标签不可撤销

```json
{
  "success": false,
  "error": {
    "code": "VIP_TAG_NOT_REVOCABLE",
    "message": "该VIP标签不允许撤销",
    "details": {
      "reason": "系统内置标签不支持撤销操作"
    }
  }
}
```

**解决方案**: 检查标签类型和撤销策略

---

## 📈 最佳实践

### 1. VIP权益设计原则

- **层次清晰**: 不同VIP等级提供明显差异化的权益
- **价值感知**: 确保用户能够感受到VIP的价值
- **渐进式**: 权益递增，鼓励用户升级

### 2. 过期管理策略

- **提前提醒**: 在过期前7天、3天、1天发送提醒
- **宽限期**: 提供1-7天的缓冲期
- **平滑降级**: 权益逐步而非立即失效

### 3. 自动续期优化

- **用户控制**: 用户可以随时开启/关闭自动续期
- **支付验证**: 续期前验证支付方式的有效性
- **失败处理**: 续期失败时的重试和通知机制

### 4. 数据分析建议

- **使用行为**: 追踪VIP权益的实际使用情况
- **续费率**: 监控不同VIP类型的续费率
- **价值分析**: 分析VIP对用户留存和收入的影响

---

下一步查看: [04_许可证分配API.md](./04_许可证分配API.md) 了解许可证分配管理的详细API使用方法。
