# 许可证管理系统 API 文档

## 📋 系统概述

LiPeaks许可证管理系统是一套完整的软件许可证颁发、管理和验证解决方案。本文档详细介绍了管理端许可证API的使用方法。

### 🎯 核心功能
- **软件产品管理** - 管理需要授权的软件产品
- **许可方案管理** - 定义不同级别的许可证类型
- **许可证生命周期管理** - 颁发、激活、撤销、延期
- **机器绑定管控** - 限制和监控设备使用
- **安全审计跟踪** - 完整的操作日志记录
- **租户隔离** - 多租户环境下的数据隔离

## 🔐 认证与权限

### 认证方式
使用JWT Bearer Token认证：

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

### 权限要求
- **超级管理员**: 可访问所有租户数据
- **租户管理员**: 只能访问所属租户的数据

### JWT Token解析示例
```json
{
  "user_id": 2,
  "username": "admin_jin", 
  "exp": 1757593277,
  "model_type": "user",
  "is_admin": true,
  "is_super_admin": false
}
```

## 🚀 许可证管理API

### 基础信息

**基础URL**: `http://localhost:8000/api/v1/licenses/admin/licenses/`

**支持的HTTP方法**: `GET` `POST` `PUT` `PATCH` `DELETE`

### 1. 获取许可证列表

**端点**: `GET /api/v1/licenses/admin/licenses/`

#### 请求示例
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | integer | 否 | 页码，默认1 |
| `page_size` | integer | 否 | 每页数量，默认20 |
| `product` | integer | 否 | 按产品ID过滤 |
| `plan` | integer | 否 | 按方案ID过滤 |
| `status` | string | 否 | 按状态过滤: `generated`, `activated`, `suspended`, `revoked`, `expired` |
| `tenant` | integer | 否 | 按租户ID过滤（仅超级管理员可用） |
| `search` | string | 否 | 搜索许可证密钥、客户名称或邮箱 |
| `ordering` | string | 否 | 排序字段: `issued_at`, `expires_at`, `customer_name`, `-issued_at` |

#### 响应示例
```json
{
  "success": true,
  "data": {
    "count": 156,
    "next": "http://localhost:8000/api/v1/licenses/admin/licenses/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "product": 1,
        "product_name": "SuperApp Pro",
        "plan": 2,
        "plan_name": "专业版",
        "tenant": 3,
        "tenant_name": "科技有限公司",
        "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
        "customer_name": "张三",
        "customer_email": "zhangsan@example.com",
        "max_activations": 5,
        "current_activations": 2,
        "issued_at": "2024-09-01T10:00:00Z",
        "expires_at": "2025-09-01T10:00:00Z",
        "last_verified_at": "2024-09-10T08:30:00Z",
        "status": "activated",
        "machine_bindings_count": 2,
        "days_until_expiry": 356,
        "notes": "年度企业许可证"
      }
    ]
  }
}
```

### 2. 创建许可证

**端点**: `POST /api/v1/licenses/admin/licenses/`

#### 请求示例
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "product": 1,
    "plan": 2,
    "tenant": 3,
    "customer_info": {
      "name": "李四",
      "email": "lisi@example.com",
      "company": "创新科技",
      "phone": "13800138000"
    },
    "max_activations": 10,
    "validity_days": 365,
    "notes": "企业定制版许可证"
  }'
```

#### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `product` | integer | 是 | 软件产品ID |
| `plan` | integer | 是 | 许可方案ID |
| `tenant` | integer | 是 | 租户ID |
| `customer_info` | object | 是 | 客户信息对象 |
| `customer_info.name` | string | 是 | 客户姓名 |
| `customer_info.email` | string | 是 | 客户邮箱 |
| `customer_info.company` | string | 否 | 客户公司 |
| `customer_info.phone` | string | 否 | 客户电话 |
| `max_activations` | integer | 否 | 最大激活数，默认从方案继承 |
| `validity_days` | integer | 否 | 有效天数，默认从方案继承 |
| `notes` | string | 否 | 备注信息 |

#### 响应示例
```json
{
  "success": true,
  "message": "许可证创建成功",
  "data": {
    "id": 157,
    "license_key": "SAPP-PRO-2024-WXYZ-9876-5432",
    "status": "generated",
    "issued_at": "2024-09-10T14:30:00Z",
    "expires_at": "2025-09-10T14:30:00Z"
  }
}
```

### 3. 获取许可证详情

**端点**: `GET /api/v1/licenses/admin/licenses/{id}/`

#### 请求示例
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/1/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "id": 1,
    "product": 1,
    "product_name": "SuperApp Pro",
    "plan": 2,
    "plan_name": "专业版",
    "tenant": 3,
    "tenant_name": "科技有限公司",
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "customer_name": "张三",
    "customer_email": "zhangsan@example.com",
    "max_activations": 5,
    "current_activations": 2,
    "issued_at": "2024-09-01T10:00:00Z",
    "expires_at": "2025-09-01T10:00:00Z",
    "last_verified_at": "2024-09-10T08:30:00Z",
    "status": "activated",
    "notes": "年度企业许可证",
    "metadata": {
      "created_by": "admin",
      "source": "manual_creation"
    },
    "machine_bindings": [
      {
        "id": 10,
        "machine_id": "DESKTOP-ABC123",
        "hardware_summary": {
          "cpu": "Intel i7-10700K",
          "memory": "32GB",
          "gpu": "RTX 3080"
        },
        "os_info": {
          "name": "Windows 11",
          "version": "10.0.22000"
        },
        "last_ip_address": "192.168.1.100",
        "status": "active",
        "first_seen_at": "2024-09-01T12:00:00Z",
        "last_seen_at": "2024-09-10T08:30:00Z",
        "days_since_last_seen": 0
      }
    ],
    "recent_activations": [
      {
        "id": 25,
        "activation_type": "online",
        "activation_code": "ACT-2024-XYZ789",
        "client_version": "2.1.0",
        "ip_address": "192.168.1.100",
        "result": "success",
        "activated_at": "2024-09-01T12:00:00Z"
      }
    ],
    "usage_stats": {
      "total_usage_logs": 1245,
      "recent_usage_logs": 89
    }
  }
}
```

### 4. 更新许可证

**端点**: `PUT /api/v1/licenses/admin/licenses/{id}/` 或 `PATCH /api/v1/licenses/admin/licenses/{id}/`

#### 请求示例
```bash
curl -X 'PATCH' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/1/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "max_activations": 8,
    "notes": "更新激活数限制",
    "status": "activated"
  }'
```

#### 响应示例
```json
{
  "success": true,
  "message": "许可证更新成功",
  "data": {
    "id": 1,
    "max_activations": 8,
    "notes": "更新激活数限制",
    "status": "activated",
    "updated_at": "2024-09-10T14:35:00Z"
  }
}
```

### 5. 删除许可证

**端点**: `DELETE /api/v1/licenses/admin/licenses/{id}/`

#### 请求示例
```bash
curl -X 'DELETE' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/1/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

#### 响应示例
```json
{
  "success": true,
  "message": "许可证已软删除"
}
```

## 🔧 自定义操作

### 1. 撤销许可证

**端点**: `POST /api/v1/licenses/admin/licenses/{id}/revoke/`

#### 请求示例
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/1/revoke/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "reason": "客户申请退款"
  }'
```

#### 响应示例
```json
{
  "success": true,
  "message": "许可证撤销成功"
}
```

### 2. 延长许可证有效期

**端点**: `POST /api/v1/licenses/admin/licenses/{id}/extend/`

#### 请求示例
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/1/extend/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "days": 90
  }'
```

#### 响应示例
```json
{
  "success": true,
  "message": "许可证有效期已延长90天",
  "new_expiry": "2025-12-10T14:30:00Z"
}
```

### 3. 获取许可证使用统计

**端点**: `GET /api/v1/licenses/admin/licenses/{id}/usage_stats/`

#### 请求示例
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/1/usage_stats/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

#### 响应示例
```json
{
  "license_id": 1,
  "customer_name": "张三",
  "statistics": {
    "total_activations": 15,
    "successful_activations": 12,
    "failed_activations": 3,
    "unique_machines": 2,
    "total_usage_hours": 456.5,
    "last_activity": "2024-09-10T08:30:00Z",
    "average_daily_usage": 6.2
  },
  "machine_usage": [
    {
      "machine_id": "DESKTOP-ABC123",
      "usage_hours": 320.5,
      "last_seen": "2024-09-10T08:30:00Z"
    },
    {
      "machine_id": "LAPTOP-XYZ789",
      "usage_hours": 136.0,
      "last_seen": "2024-09-09T20:15:00Z"
    }
  ],
  "daily_usage_trend": {
    "2024-09-01": 8.5,
    "2024-09-02": 6.2,
    "2024-09-03": 4.8,
    "...": "..."
  }
}
```

### 4. 批量操作许可证

**端点**: `POST /api/v1/licenses/admin/licenses/batch_operation/`

#### 批量撤销示例
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "license_ids": [1, 2, 3, 4, 5],
    "operation": "revoke",
    "reason": "批量清理过期许可证"
  }'
```

#### 批量延期示例
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "license_ids": [10, 11, 12],
    "operation": "extend",
    "parameters": {
      "days": 30
    },
    "reason": "VIP客户服务延期"
  }'
```

#### 响应示例
```json
{
  "success": true,
  "message": "批量操作完成，成功: 4/5",
  "results": [
    {
      "license_id": 1,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 2,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 3,
      "success": false,
      "error": "许可证已经是撤销状态"
    },
    {
      "license_id": 4,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 5,
      "success": true,
      "message": "撤销成功"
    }
  ]
}
```

## 📊 相关API端点

### 软件产品管理
- `GET /api/v1/licenses/admin/products/` - 获取产品列表
- `POST /api/v1/licenses/admin/products/` - 创建产品
- `GET /api/v1/licenses/admin/products/{id}/` - 获取产品详情
- `POST /api/v1/licenses/admin/products/{id}/regenerate_keypair/` - 重新生成密钥对
- `GET /api/v1/licenses/admin/products/{id}/statistics/` - 获取产品统计

### 许可方案管理  
- `GET /api/v1/licenses/admin/plans/` - 获取方案列表
- `POST /api/v1/licenses/admin/plans/` - 创建方案
- `POST /api/v1/licenses/admin/plans/{id}/duplicate/` - 复制方案

### 机器绑定管理
- `GET /api/v1/licenses/admin/machine-bindings/` - 获取机器绑定列表
- `GET /api/v1/licenses/admin/machine-bindings/{id}/` - 获取绑定详情
- `POST /api/v1/licenses/admin/machine-bindings/{id}/block/` - 阻止机器绑定

### 激活记录管理
- `GET /api/v1/licenses/admin/activations/` - 获取激活记录
- `GET /api/v1/licenses/admin/activations/{id}/` - 获取激活详情

### 安全审计日志
- `GET /api/v1/licenses/admin/audit-logs/` - 获取审计日志
- `GET /api/v1/licenses/admin/audit-logs/{id}/` - 获取日志详情

### 租户配额管理
- `GET /api/v1/licenses/admin/quotas/` - 获取配额列表
- `POST /api/v1/licenses/admin/quotas/` - 创建配额

## ❌ 错误处理

### 标准错误响应格式
```json
{
  "success": false,
  "code": 4001,
  "message": "未提供租户ID，无法访问CMS资源",
  "errors": {
    "field_name": ["具体错误信息"]
  }
}
```

### 常见错误码
| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 401 | 401 | 未认证或Token过期 |
| 403 | 403 | 权限不足 |
| 404 | 404 | 资源不存在 |
| 4001 | 400 | 租户ID缺失 |
| 4002 | 400 | 租户不存在 |
| 4003 | 403 | 租户访问权限不足 |
| 500 | 500 | 服务器内部错误 |

### 常见错误场景

#### 1. 认证失败
```json
{
  "success": false,
  "detail": "Invalid token header. Token string should not contain spaces."
}
```

#### 2. 权限不足
```json
{
  "success": false,
  "detail": "You do not have permission to perform this action."
}
```

#### 3. 参数验证失败
```json
{
  "success": false,
  "errors": {
    "customer_info": ["客户信息缺少必要字段: email"],
    "max_activations": ["确保该值大于或等于1。"]
  }
}
```

#### 4. 业务逻辑错误
```json
{
  "success": false,
  "error": "许可证已经是撤销状态，无法重复撤销"
}
```

## 📚 最佳实践

### 1. 认证Token管理
- Token有效期为30天，建议在过期前刷新
- 使用HTTPS传输保护Token安全
- 客户端应实现Token自动刷新机制

### 2. 分页处理建议
```javascript
// 前端分页处理示例
async function getAllLicenses() {
  let allLicenses = [];
  let page = 1;
  let hasMore = true;
  
  while (hasMore) {
    const response = await fetch(`/api/v1/licenses/admin/licenses/?page=${page}`);
    const data = await response.json();
    
    allLicenses = allLicenses.concat(data.data.results);
    hasMore = data.data.next !== null;
    page++;
  }
  
  return allLicenses;
}
```

### 3. 错误重试策略
```javascript
// 带重试的API调用示例
async function apiCallWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.status === 429) { // 限流
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        continue;
      }
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### 4. 批量操作最佳实践
- 单次批量操作建议不超过100条记录
- 大量数据处理时采用分批处理
- 监控批量操作的成功率并做好错误处理

### 5. 租户隔离
- 多租户环境下，确保只访问授权租户的数据
- 超级管理员操作时需要明确指定租户ID
- 定期审计跨租户访问行为

## 🔄 版本更新

### 当前版本: v1.0

### 更新记录
- **2024-09-10**: 创建初始版本文档
- **功能特性**: 完整的CRUD操作、批量操作、统计报告等

### 向后兼容性
- API接口保持向后兼容
- 新增字段采用可选参数
- 废弃功能会提前至少一个版本通知

## 📞 技术支持

如果您在使用过程中遇到问题，请联系技术支持团队：

- **邮箱**: tech-support@lipeaks.com
- **文档**: https://docs.lipeaks.com/licenses
- **API状态**: https://status.lipeaks.com

---

*本文档最后更新时间：2024年9月10日*
