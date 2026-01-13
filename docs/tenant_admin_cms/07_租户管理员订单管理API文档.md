# 租户管理员 订单管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的订单
- 租户管理员只能管理自己租户下的订单

## 基础信息
- 前缀：`/api/v1/orders/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

---

## 1. 获取订单列表

### 接口信息
- 路径：GET `/api/v1/orders/`
- 说明：获取本租户下的所有订单列表

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| status | string | 否 | 订单状态 |
| customer_id | integer | 否 | 客户ID |
| member_id | integer | 否 | 会员ID |
| search | string | 否 | 搜索关键词 |
| date_from | string | 否 | 起始日期（YYYY-MM-DD） |
| date_to | string | 否 | 截止日期（YYYY-MM-DD） |
| ordering | string | 否 | 排序字段 |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 50,
    "next": "http://example.com/api/v1/orders/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "order_no": "ORD20240120001",
        "customer": {
          "id": 1,
          "name": "张三"
        },
        "member": {
          "id": 10,
          "username": "member001"
        },
        "total_amount": "199.00",
        "status": "completed",
        "payment_status": "paid",
        "created_at": "2024-01-20T10:30:00Z",
        "updated_at": "2024-01-20T15:00:00Z"
      }
    ]
  }
}
```

### curl 调用示例
```bash
# 获取订单列表
curl -X GET "http://localhost:8000/api/v1/orders/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按状态筛选
curl -X GET "http://localhost:8000/api/v1/orders/?status=completed" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按日期范围筛选
curl -X GET "http://localhost:8000/api/v1/orders/?date_from=2024-01-01&date_to=2024-01-31" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建订单

### 接口信息
- 路径：POST `/api/v1/orders/`
- 说明：创建新订单

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| customer_id | integer | 否 | 客户ID |
| member_id | integer | 否 | 会员ID |
| items | array | 是 | 订单项列表 |
| remark | string | 否 | 订单备注 |

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/orders/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "items": [
      {"product_id": 1, "quantity": 2, "price": "99.00"}
    ],
    "remark": "订单备注"
  }'
```

---

## 3. 获取订单详情

### 接口信息
- 路径：GET `/api/v1/orders/{id}/`

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/orders/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新订单

### 接口信息
- 路径：PUT/PATCH `/api/v1/orders/{id}/`

### curl 调用示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/orders/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "status": "processing"
  }'
```

---

## 5. 删除订单

### 接口信息
- 路径：DELETE `/api/v1/orders/{id}/`

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/orders/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 6. 获取订单历史记录

### 接口信息
- 路径：GET `/api/v1/orders/{order_id}/history/`
- 说明：获取订单的状态变更历史

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "order_id": 1,
      "status": "pending",
      "remark": "订单创建",
      "operator": "admin",
      "created_at": "2024-01-20T10:30:00Z"
    },
    {
      "id": 2,
      "order_id": 1,
      "status": "processing",
      "remark": "开始处理",
      "operator": "admin",
      "created_at": "2024-01-20T11:00:00Z"
    }
  ]
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/orders/1/history/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 7. 获取客户订单列表

### 接口信息
- 路径：GET `/api/v1/orders/customers/{customer_id}/orders/`
- 说明：获取指定客户的所有订单

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/orders/customers/1/orders/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 8. 获取会员订单列表

### 接口信息
- 路径：GET `/api/v1/orders/members/{member_id}/orders/`
- 说明：获取指定会员的所有订单

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/orders/members/10/orders/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 订单状态说明

| 状态 | 说明 |
|------|------|
| pending | 待处理 |
| processing | 处理中 |
| completed | 已完成 |
| cancelled | 已取消 |
| refunded | 已退款 |

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
