# 租户管理员 客户管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的客户信息
- 租户管理员只能管理自己租户下的客户

## 基础信息
- 前缀：`/api/v1/customers/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

---

## 1. 获取客户列表

### 接口信息
- 路径：GET `/api/v1/customers/`
- 说明：获取本租户下的所有客户列表

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| status | string | 否 | 客户状态 |
| search | string | 否 | 搜索关键词（名称、邮箱、电话） |
| ordering | string | 否 | 排序字段 |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 0,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": []
  }
}
```

**注意：** 请求时需要带上 `tenant_id` 参数，例如：`/api/v1/customers/?tenant_id=1`

### curl 调用示例
```bash
# 获取客户列表
curl -X GET "http://localhost:8000/api/v1/customers/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 搜索客户
curl -X GET "http://localhost:8000/api/v1/customers/?search=张三" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按状态筛选
curl -X GET "http://localhost:8000/api/v1/customers/?status=active" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建客户

### 接口信息
- 路径：POST `/api/v1/customers/`
- 说明：创建新客户

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 客户名称 |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 电话 |
| company | string | 否 | 公司名称 |
| address | string | 否 | 地址 |
| status | string | 否 | 状态，默认active |
| level | string | 否 | 客户等级 |
| remark | string | 否 | 备注 |

### 请求体示例
```json
{
  "name": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "company": "测试公司",
  "address": "北京市朝阳区xxx",
  "level": "normal"
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/customers/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "company": "测试公司"
  }'
```

---

## 3. 获取客户详情

### 接口信息
- 路径：GET `/api/v1/customers/{id}/`

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/customers/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新客户

### 接口信息
- 路径：PUT/PATCH `/api/v1/customers/{id}/`

### curl 调用示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/customers/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "level": "vip"
  }'
```

---

## 5. 删除客户

### 接口信息
- 路径：DELETE `/api/v1/customers/{id}/`

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/customers/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 6. 客户-会员关系管理

### 获取关系列表
- 路径：GET `/api/v1/customers/members/relations/`
- 说明：获取客户与会员的关联关系列表

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/customers/members/relations/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

### 创建关系
- 路径：POST `/api/v1/customers/members/relations/`

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/customers/members/relations/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "member_id": 10,
    "relation_type": "owner"
  }'
```

### 删除关系
- 路径：DELETE `/api/v1/customers/members/relations/{id}/`

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/customers/members/relations/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 7. 客户-租户关系管理

### 获取关系列表
- 路径：GET `/api/v1/customers/tenants/relations/`
- 说明：获取客户与租户的关联关系列表

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/customers/tenants/relations/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 8. 租户视角获取客户

### 接口信息
- 路径：GET `/api/v1/customers/tenants/view/`
- 说明：从租户视角获取关联的客户列表

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/customers/tenants/view/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 客户状态说明

| 状态 | 说明 |
|------|------|
| active | 活跃 |
| inactive | 非活跃 |
| blocked | 已拉黑 |

## 客户等级说明

| 等级 | 说明 |
|------|------|
| normal | 普通客户 |
| silver | 银牌客户 |
| gold | 金牌客户 |
| vip | VIP客户 |

## 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|-------|-----------|------|
| 2000 | 200 | 操作成功 |
| 2001 | 201 | 创建成功 |
| 4000 | 400 | 参数验证失败 |
| 4001 | 401 | 认证失败 |
| 4003 | 403 | 权限不足 |
| 4004 | 404 | 资源不存在 |
| 5000 | 500 | 服务器内部错误 |
