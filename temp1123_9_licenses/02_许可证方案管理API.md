# 许可证方案管理API文档

## 概述

许可证方案（LicensePlan）定义了许可证的模板配置，包括默认有效期、激活数、功能权限、价格等。每个产品可以有多个方案（如试用版、基础版、专业版等）。

## API列表

### 1. 获取方案列表

**接口**: `GET /api/v1/licenses/admin/plans/`

**权限**: 租户管理员

**描述**: 获取current租户下所有许可证方案的分页列表

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |
| application | int | 否 | 按产品ID过滤 |
| plan_type | string | 否 | 方案类型: trial/basic/professional/enterprise/custom |
| status | string | 否 | 状态: active/inactive |
| search | string | 否 | 搜索关键词（名称、代码） |
| ordering | string | 否 | 排序: name/-name/price/-price/created_at/-created_at |

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/plans/?application=1&plan_type=trial" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 3,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 15,
        "application": 1,
        "application_name": "测试应用",
        "name": "试用版",
        "code": "trial",
        "plan_type": "trial",
        "default_max_activations": 10,
        "default_validity_days": 35,
        "features": {
          "max_users": 5,
          "storage_gb": 10,
          "api_calls_per_day": 1000
        },
        "price": "0.00",
        "currency": "CNY",
        "status": "active",
        "licenses_count": 3,
        "created_at": "2025-10-18T02:05:29.529998Z",
        "updated_at": "2025-10-18T02:05:29.530011Z"
      }
    ]
  }
}
```

---

### 2. 创建方案

**接口**: `POST /api/v1/licenses/admin/plans/`

**权限**: 租户管理员

**描述**: 为指定产品创建新的许可证方案

**请求体**:
```json
{
  "application": 1,
  "name": "专业版",
  "code": "professional",
  "plan_type": "professional",
  "default_max_activations": 50,
  "default_validity_days": 365,
  "features": {
    "max_users": 100,
    "storage_gb": 500,
    "api_calls_per_day": 100000,
    "support_level": "premium",
    "custom_branding": true
  },
  "price": "9999.00",
  "currency": "CNY",
  "status": "active"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| application | int | 是 | 产品ID |
| name | string | 是 | 方案名称 |
| code | string | 是 | 方案代码（产品内唯一） |
| plan_type | string | 是 | 方案类型 |
| default_max_activations | int | 是 | 默认最大激活数 |
| default_validity_days | int | 是 | 默认有效天数 |
| features | object | 否 | 功能配置JSON对象 |
| price | decimal | 否 | 价格，默认0 |
| currency | string | 否 | 货币，默认CNY |
| status | string | 否 | 状态，默认active |

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/plans/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "application": 1,
    "name": "企业版",
    "code": "enterprise",
    "plan_type": "enterprise",
    "default_max_activations": 100,
    "default_validity_days": 365,
    "features": {
      "max_users": "unlimited",
      "storage_gb": "unlimited",
      "api_calls_per_day": "unlimited",
      "dedicated_support": true,
      "sla": "99.99%"
    },
    "price": "29999.00",
    "currency": "CNY",
    "status": "active"
  }'
```

---

### 3. 获取方案详情

**接口**: `GET /api/v1/licenses/admin/plans/{id}/`

**权限**: 租户管理员

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/plans/15/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

---

### 4. 更新方案

**接口**: `PUT /api/v1/licenses/admin/plans/{id}/`

**权限**: 租户管理员

**描述**: 完整更新方案信息

**curl示例**:
```bash
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/plans/15/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "application": 1,
    "name": "试用版（升级）",
    "code": "trial",
    "plan_type": "trial",
    "default_max_activations": 15,
    "default_validity_days": 45,
    "features": {
      "max_users": 10,
      "storage_gb": 20
    },
    "price": "0.00",
    "currency": "CNY",
    "status": "active"
  }'
```

---

### 5. 部分更新方案

**接口**: `PATCH /api/v1/licenses/admin/plans/{id}/`

**权限**: 租户管理员

**描述**: 部分更新方案信息

**curl示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/plans/15/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "default_validity_days": 60,
    "price": "99.00"
  }'
```

---

### 6. 删除方案

**接口**: `DELETE /api/v1/licenses/admin/plans/{id}/`

**权限**: 租户管理员

**描述**: 软删除方案

**curl示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/admin/plans/15/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

---

### 7. 复制方案

**接口**: `POST /api/v1/licenses/admin/plans/{id}/duplicate/`

**权限**: 租户管理员

**描述**: 复制现有方案创建副本（新方案默认为inactive状态）

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/plans/15/duplicate/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (201 Created):
```json
{
  "success": true,
  "message": "方案复制成功",
  "data": {
    "id": 18,
    "application": 1,
    "application_name": "测试应用",
    "name": "试用版 (副本)",
    "code": "trial_copy_20251123_142030",
    "plan_type": "trial",
    "default_max_activations": 10,
    "default_validity_days": 35,
    "features": {
      "max_users": 5,
      "storage_gb": 10
    },
    "price": "0.00",
    "currency": "CNY",
    "status": "inactive",
    "licenses_count": 0,
    "created_at": "2025-11-23T14:20:30.123456Z",
    "updated_at": "2025-11-23T14:20:30.123456Z"
  }
}
```

---

## 方案类型说明

### trial - 试用版
- 通常免费或低价
- 有效期较短（7-30天）
- 功能受限
- 用于产品体验

### basic - 基础版
- 入门级付费版本
- 提供核心功能
- 适合个人或小团队

### professional - 专业版
- 完整功能
- 适合中小企业
- 价格适中

### enterprise - 企业版
- 所有功能解锁
- 定制化支持
- SLA保障
- 价格较高

### custom - 定制版
- 根据客户需求定制
- 灵活配置
- 特殊定价

---

## Features配置示例

```json
{
  "features": {
    // 用户限制
    "max_users": 100,
    "max_teams": 10,
    
    // 存储限制
    "storage_gb": 500,
    "max_file_size_mb": 100,
    
    // API限制
    "api_calls_per_day": 100000,
    "api_rate_limit_per_minute": 1000,
    
    // 功能开关
    "custom_branding": true,
    "white_label": false,
    "api_access": true,
    "export_data": true,
    "advanced_analytics": true,
    
    // 支持服务
    "support_level": "premium",
    "response_time_hours": 4,
    "dedicated_support": true,
    
    // SLA
    "sla": "99.99%",
    "backup_frequency": "daily",
    
    // 其他
    "custom_integrations": true,
    "priority_updates": true
  }
}
```

---

## 注意事项

1. **代码唯一性**: 方案代码在同一产品内必须唯一
2. **价格精度**: 价格支持2位小数
3. **Features灵活性**: features字段为JSON，可自定义任意功能配置
4. **默认值**: 新建许可证时会继承方案的默认配置
5. **方案变更**: 修改方案不影响已生成的许可证
6. **复制功能**: 复制的方案默认为inactive状态，需要手动激活
