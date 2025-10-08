# Member用户试用许可证申请API文档

## 概述

Member用户试用许可证申请API为普通用户提供了自助申请试用版软件许可证的功能。用户可以浏览可申请的产品、提交试用申请并管理个人许可证。

### 核心特性

- **自助申请**: 用户无需等待审批，系统自动处理试用申请
- **配额管理**: 智能的用户和租户配额限制机制
- **安全控制**: 多重验证和频率限制，防止滥用
- **实时状态**: 提供许可证状态监控和有效期管理
- **租户隔离**: 确保跨租户数据安全

---

## API端点概览

| 端点 | 方法 | 描述 | 权限要求 |
|------|------|------|----------|
| `/api/v1/licenses/member/available-products/` | GET | 获取可申请产品列表 | Member用户 |
| `/api/v1/licenses/member/apply/` | POST | 申请试用许可证 | Member用户 + 申请权限 |
| `/api/v1/licenses/member/my-licenses/` | GET | 查看我的许可证 | Member用户 |

---

## 认证和权限

### JWT认证
所有API都需要在请求头中包含有效的JWT令牌：

```http
Authorization: Bearer <your_jwt_token>
```

### 用户权限要求

1. **Member用户身份**: 必须是Member类型用户，不能是管理员
2. **活跃状态**: 用户状态必须为活跃（active）
3. **有效租户**: 必须属于一个活跃的租户
4. **申请权限**: 申请API还需要额外的试用申请权限

---

## API详细说明

### 1. 获取可申请产品列表

**端点**: `GET /api/v1/licenses/member/available-products/`

**描述**: 获取当前用户可以申请试用许可证的产品列表

#### 请求参数
无

#### 响应格式

```json
{
    "success": true,
    "data": {
        "count": 3,
        "products": [
            {
                "id": 1,
                "name": "PDF压缩工具",
                "code": "pdf_compress",
                "description": "高效的PDF文件压缩工具，支持批量处理",
                "version": "1.2.0",
                "trial_plan": {
                    "id": 10,
                    "name": "试用版",
                    "default_validity_days": 30,
                    "default_max_activations": 1,
                    "features": {
                        "compression_level": "basic",
                        "batch_processing": false,
                        "watermark": true
                    },
                    "price": 0.0,
                    "currency": "CNY"
                },
                "already_applied": false
            }
        ]
    }
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `success` | boolean | 请求是否成功 |
| `data.count` | integer | 可申请产品总数 |
| `data.products` | array | 产品列表 |
| `products[].id` | integer | 产品ID |
| `products[].name` | string | 产品名称 |
| `products[].code` | string | 产品代码 |
| `products[].description` | string | 产品描述 |
| `products[].version` | string | 产品版本 |
| `products[].trial_plan` | object | 试用方案信息 |
| `trial_plan.id` | integer | 方案ID |
| `trial_plan.name` | string | 方案名称 |
| `trial_plan.default_validity_days` | integer | 默认有效天数 |
| `trial_plan.default_max_activations` | integer | 默认最大激活数 |
| `trial_plan.features` | object | 功能配置 |
| `trial_plan.price` | float | 价格（试用版通常为0） |
| `trial_plan.currency` | string | 货币代码 |
| `products[].already_applied` | boolean | 是否已申请过 |

#### 错误响应

```json
{
    "success": false,
    "error": "获取产品列表失败，请稍后重试",
    "code": "FETCH_PRODUCTS_FAILED"
}
```

---

### 2. 申请试用许可证

**端点**: `POST /api/v1/licenses/member/apply/`

**描述**: 申请指定产品的试用许可证

#### 请求参数

```json
{
    "product_id": 1,
    "reason": "产品评估和测试",
    "user_info": {
        "company": "测试公司",
        "job_title": "产品经理",
        "phone": "13800138000",
        "intended_use": "用于评估产品功能，决定是否购买正式版"
    }
}
```

#### 请求字段说明

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `product_id` | integer | 是 | 要申请的产品ID |
| `reason` | string | 否 | 申请原因（默认："试用版申请"） |
| `user_info` | object | 否 | 用户补充信息 |
| `user_info.company` | string | 否 | 公司名称 |
| `user_info.job_title` | string | 否 | 职位 |
| `user_info.phone` | string | 否 | 手机号 |
| `user_info.intended_use` | string | 否 | 使用用途 |

#### 成功响应

```json
{
    "success": true,
    "message": "试用许可证申请成功",
    "data": {
        "license_id": 123,
        "assignment_id": 456,
        "license_key": "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY",
        "expires_at": "2024-02-15T10:30:00Z",
        "product_name": "PDF压缩工具",
        "plan_name": "试用版",
        "max_activations": 1
    }
}
```

#### 成功响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `data.license_id` | integer | 许可证ID |
| `data.assignment_id` | integer | 分配记录ID |
| `data.license_key` | string | 许可证密钥 |
| `data.expires_at` | string | 过期时间（ISO 8601格式） |
| `data.product_name` | string | 产品名称 |
| `data.plan_name` | string | 方案名称 |
| `data.max_activations` | integer | 最大激活数 |

#### 业务错误响应

```json
{
    "success": false,
    "error": "您已经申请过该产品的许可证",
    "code": "APPLICATION_FAILED"
}
```

#### 常见业务错误

| 错误信息 | 错误代码 | 说明 |
|----------|----------|------|
| "您已经申请过该产品的许可证" | APPLICATION_FAILED | 重复申请同一产品 |
| "您的试用许可证数量已达上限（1个）" | APPLICATION_FAILED | 超出个人配额限制 |
| "24小时内申请次数过多，请稍后再试" | APPLICATION_FAILED | 触发频率限制 |
| "产品不存在或不可用" | APPLICATION_FAILED | 无效的产品ID |
| "该产品没有可用的试用方案" | APPLICATION_FAILED | 产品无试用版 |
| "租户许可证配额已满" | APPLICATION_FAILED | 租户配额限制 |
| "用户账户已被禁用" | APPLICATION_FAILED | 用户状态异常 |

#### 频率限制

- **申请频率**: 每天最多5次申请
- **业务限制**: 24小时内最多3次申请
- **用户配额**: 最多持有1个试用许可证

---

### 3. 查看我的许可证

**端点**: `GET /api/v1/licenses/member/my-licenses/`

**描述**: 获取当前用户的所有许可证列表及统计信息

#### 请求参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `status` | string | 否 | 过滤状态：active, expired, revoked, pending |
| `plan_type` | string | 否 | 过滤方案类型：trial, basic, professional, enterprise |

#### 请求示例

```http
GET /api/v1/licenses/member/my-licenses/?status=active&plan_type=trial
```

#### 成功响应

```json
{
    "success": true,
    "data": {
        "count": 2,
        "active_count": 1,
        "trial_count": 1,
        "expiring_soon_count": 0,
        "licenses": [
            {
                "id": 456,
                "product_name": "PDF压缩工具",
                "product_code": "pdf_compress",
                "product_version": "1.2.0",
                "plan_name": "试用版",
                "plan_type": "trial",
                "license_key_preview": "ABCDE...VWXYZ",
                "status": "active",
                "status_display": "有效",
                "assignment_type": "direct",
                "assigned_at": "2024-01-15T10:30:00Z",
                "activated_at": "2024-01-15T10:30:00Z",
                "expires_at": "2024-02-15T10:30:00Z",
                "days_until_expiry": 25,
                "assignment_reason": "试用版申请",
                "can_activate_license": true,
                "activation_info": {
                    "current_activations": 0,
                    "max_activations": 1,
                    "available_slots": 1
                },
                "usage_count": 5,
                "last_used_at": "2024-01-20T14:25:30Z",
                "last_heartbeat": "2024-01-20T14:25:30Z",
                "can_activate": true,
                "can_deactivate": false,
                "can_share": false,
                "max_devices_per_user": 1
            }
        ]
    }
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `data.count` | integer | 许可证总数 |
| `data.active_count` | integer | 有效许可证数量 |
| `data.trial_count` | integer | 试用版许可证数量 |
| `data.expiring_soon_count` | integer | 即将过期许可证数量（7天内） |
| `data.licenses` | array | 许可证列表 |

#### 许可证对象字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `id` | integer | 分配记录ID |
| `product_name` | string | 产品名称 |
| `product_code` | string | 产品代码 |
| `product_version` | string | 产品版本 |
| `plan_name` | string | 方案名称 |
| `plan_type` | string | 方案类型 |
| `license_key_preview` | string | 许可证密钥预览（隐私保护） |
| `status` | string | 状态代码 |
| `status_display` | string | 状态显示名称 |
| `assignment_type` | string | 分配类型 |
| `assigned_at` | string | 分配时间 |
| `activated_at` | string | 激活时间 |
| `expires_at` | string | 过期时间 |
| `days_until_expiry` | integer | 距离过期天数 |
| `assignment_reason` | string | 分配原因 |
| `can_activate_license` | boolean | 是否可以激活许可证 |
| `activation_info` | object | 激活信息 |
| `activation_info.current_activations` | integer | 当前激活数 |
| `activation_info.max_activations` | integer | 最大激活数 |
| `activation_info.available_slots` | integer | 可用激活配额 |
| `usage_count` | integer | 使用次数 |
| `last_used_at` | string | 最后使用时间 |
| `last_heartbeat` | string | 最后心跳时间 |
| `can_activate` | boolean | 允许激活 |
| `can_deactivate` | boolean | 允许停用 |
| `can_share` | boolean | 允许共享 |
| `max_devices_per_user` | integer | 用户最大设备数 |

---

## 状态码说明

### HTTP状态码

| 状态码 | 描述 | 场景 |
|--------|------|------|
| 200 | 成功 | GET请求成功 |
| 201 | 创建成功 | POST申请成功 |
| 400 | 请求错误 | 参数验证失败、业务规则限制 |
| 401 | 未认证 | 缺少或无效的JWT令牌 |
| 403 | 权限不足 | 非Member用户或权限不足 |
| 429 | 请求过多 | 触发频率限制 |
| 500 | 服务器错误 | 内部系统错误 |

### 业务状态字段

#### 许可证状态（status）

| 状态值 | 显示名称 | 描述 |
|--------|----------|------|
| active | 有效 | 许可证正常使用中 |
| pending | 待激活 | 待用户激活 |
| suspended | 已挂起 | 临时停用 |
| revoked | 已撤销 | 永久撤销 |
| expired | 已过期 | 超出有效期 |

#### 方案类型（plan_type）

| 类型值 | 显示名称 | 描述 |
|--------|----------|------|
| trial | 试用版 | 免费试用版本 |
| basic | 基础版 | 基础功能版本 |
| professional | 专业版 | 专业功能版本 |
| enterprise | 企业版 | 企业级版本 |
| custom | 定制版 | 定制化版本 |

---

## 业务规则

### 申请限制

1. **产品限制**: 每个产品只能申请一次试用许可证
2. **个人配额**: 每个用户最多持有1个试用许可证（可配置）
3. **频率限制**: 24小时内最多申请3次
4. **租户配额**: 受租户许可证配额限制

### 有效期管理

1. **自动设置**: 试用版有效期根据方案配置自动设置（通常30天）
2. **提醒机制**: 系统会在许可证即将过期时提醒用户
3. **过期处理**: 过期后许可证自动变为不可用状态

### 激活管理

1. **激活配额**: 根据方案配置限制激活设备数量
2. **设备绑定**: 激活时绑定设备硬件信息
3. **解绑功能**: 支持主动解绑设备以释放激活配额

---

## 安全机制

### 认证安全

- **JWT令牌**: 使用安全的JWT认证机制
- **令牌过期**: 定期更新令牌，防止令牌泄露
- **权限验证**: 多层权限验证，确保用户身份

### 数据安全

- **租户隔离**: 严格的租户数据隔离
- **隐私保护**: 许可证密钥部分隐藏显示
- **审计日志**: 记录所有重要操作的审计日志

### 防滥用机制

- **频率限制**: API调用频率限制
- **申请限制**: 业务层面的申请频率控制
- **配额管理**: 多层配额限制机制
- **异常检测**: 检测可疑申请行为

---

## 错误处理

### 错误响应格式

```json
{
    "success": false,
    "error": "错误描述信息",
    "code": "ERROR_CODE"
}
```

### 验证错误格式

```json
{
    "success": false,
    "errors": {
        "product_id": ["产品不存在或不可用"],
        "user_info": {
            "phone": ["手机号格式无效"]
        }
    }
}
```

### 错误处理最佳实践

1. **用户友好**: 提供清晰的错误信息
2. **错误代码**: 使用标准化的错误代码
3. **详细信息**: 在开发环境提供详细错误信息
4. **日志记录**: 记录所有错误信息用于调试

---

## 最佳实践

### 前端集成建议

1. **错误处理**: 妥善处理各种错误情况
2. **用户体验**: 提供清晰的状态反馈
3. **数据验证**: 前端进行基本数据验证
4. **缓存策略**: 合理使用缓存提升性能

### 安全建议

1. **令牌管理**: 安全存储和使用JWT令牌
2. **HTTPS通信**: 始终使用HTTPS进行API通信
3. **输入验证**: 对所有用户输入进行验证
4. **敏感信息**: 不在客户端存储敏感信息

### 性能优化

1. **请求合并**: 避免频繁的API调用
2. **分页处理**: 对大量数据使用分页
3. **缓存利用**: 合理使用缓存机制
4. **异步处理**: 使用异步请求提升用户体验

---

## 版本信息

- **API版本**: v1
- **文档版本**: 1.0.0
- **最后更新**: 2024-09-29
- **兼容性**: Django 4.2+, DRF 3.14+
