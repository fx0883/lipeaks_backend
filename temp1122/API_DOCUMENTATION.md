# 租户隔离API文档

## 概述

本文档描述了实施租户隔离后的API使用方式和注意事项。

## 认证和租户标识

### 请求头

所有API请求都需要包含以下头部：

```http
Authorization: Bearer {TOKEN}
X-Tenant-ID: {TENANT_ID}
```

- **Authorization**: JWT认证Token
- **X-Tenant-ID**: 当前操作的租户ID

### 示例请求

```bash
curl -X GET "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci..." \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json"
```

## 租户隔离行为

### 自动过滤

所有继承自`TenantModelViewSet`的API端点会自动：

1. **查询过滤**: 只返回当前租户的数据
2. **创建操作**: 自动设置tenant_id为当前租户
3. **更新操作**: 只能更新当前租户的数据
4. **删除操作**: 只能删除当前租户的数据

### 错误处理

#### 跨租户访问

尝试访问其他租户的数据会返回404或403错误：

```json
{
  "success": false,
  "code": 4004,
  "message": "资源不存在或无权访问",
  "data": null
}
```

#### 缺少租户ID

如果请求头中缺少`X-Tenant-ID`：

```json
{
  "success": false,
  "code": 4000,
  "message": "缺少租户标识",
  "data": null
}
```

## API端点

### Applications (应用管理)

#### 列表查询

```bash
GET /api/v1/applications/
```

**响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "Success",
  "data": {
    "count": 5,
    "results": [
      {
        "id": 1,
        "name": "示例应用",
        "code": "DEMO_APP",
        "tenant_id": 3,
        "created_at": "2025-11-22T10:00:00Z"
      }
    ]
  }
}
```

**注意**: 只返回当前租户(X-Tenant-ID: 3)的应用

#### 创建应用

```bash
POST /api/v1/applications/
Content-Type: application/json

{
  "name": "新应用",
  "code": "NEW_APP",
  "description": "应用描述"
}
```

**响应**:
```json
{
  "success": true,
  "code": 2001,
  "message": "Created",
  "data": {
    "id": 6,
    "name": "新应用",
    "code": "NEW_APP",
    "tenant_id": 3,  // 自动设置
    "created_at": "2025-11-22T14:00:00Z"
  }
}
```

**注意**: tenant_id会自动设置为请求头中的X-Tenant-ID

#### 更新应用

```bash
PUT /api/v1/applications/6/
Content-Type: application/json

{
  "name": "更新后的应用名"
}
```

**注意**: 只能更新本租户的应用，尝试更新其他租户的应用会返回404

#### 删除应用

```bash
DELETE /api/v1/applications/6/
```

**注意**: 只能删除本租户的应用

### Orders (订单管理)

#### 列表查询

```bash
GET /api/v1/orders/
```

**查询参数**:
- `status`: 订单状态过滤
- `payment_status`: 支付状态过滤
- `page`: 页码
- `page_size`: 每页数量

**响应**: 只返回当前租户的订单

#### 创建订单

```bash
POST /api/v1/orders/
Content-Type: application/json

{
  "order_number": "ORD20251122001",
  "total_amount": 1000.00,
  "payment_status": "pending"
}
```

**注意**: tenant_id自动设置

### Customers (客户管理)

#### 列表查询

```bash
GET /api/v1/customers/
```

**查询参数**:
- `search`: 搜索客户名称、联系人等
- `status`: 状态过滤
- `type`: 类型过滤

**响应**: 只返回当前租户的客户

#### 搜索客户

```bash
GET /api/v1/customers/?search=张三
```

**注意**: 搜索结果会自动限制在当前租户范围内，不同租户可以有同名客户

### Feedbacks (反馈管理)

#### 提交反馈

```bash
POST /api/v1/feedbacks/
Content-Type: application/json

{
  "title": "Bug报告",
  "description": "详细描述",
  "feedback_type": "bug"
}
```

**权限**:
- 普通用户：只能看到自己提交的反馈
- 租户管理员：可以看到租户内所有反馈

### Interactions (用户互动)

#### 收藏文章

```bash
POST /api/v1/interactions/favorites/
Content-Type: application/json

{
  "article_id": 123
}
```

**注意**: 
- 自动设置当前用户和租户
- 同一文章在不同租户可以被独立收藏

### Check System (打卡系统)

#### 查询打卡分类

```bash
GET /api/v1/check-system/categories/
```

**特殊行为**:
- 系统预设分类（is_system=true）对所有租户可见
- 自定义分类按租户隔离

**查询参数**:
- `is_system`: true/false，过滤系统预设或自定义分类

## 最佳实践

### 1. 始终包含租户ID

```bash
# ✅ 正确
curl -H "X-Tenant-ID: 3" ...

# ❌ 错误 - 缺少租户ID
curl ...
```

### 2. 不要在请求体中包含tenant_id

```bash
# ✅ 正确 - 系统自动设置
POST /api/v1/applications/
{
  "name": "新应用",
  "code": "NEW_APP"
}

# ❌ 错误 - 不要手动设置tenant_id
POST /api/v1/applications/
{
  "name": "新应用",
  "code": "NEW_APP",
  "tenant_id": 3  // 不需要，会被忽略
}
```

### 3. 处理跨租户引用

如果需要引用其他模型的对象（如分配许可证给用户），确保被引用的对象也属于当前租户：

```bash
POST /api/v1/licenses/assignments/
{
  "license_id": 10,  // 必须属于当前租户
  "member_id": 5     // 必须属于当前租户
}
```

### 4. 搜索和过滤

搜索总是在当前租户范围内：

```bash
# 只搜索当前租户的客户
GET /api/v1/customers/?search=公司名
```

### 5. 分页

分页参数正常使用，结果集已经过租户过滤：

```bash
GET /api/v1/applications/?page=1&page_size=20
```

## 安全注意事项

### 1. Token验证

系统会验证Token中的租户信息与X-Tenant-ID是否匹配。不匹配会返回403错误。

### 2. 超级管理员

超级管理员可以访问所有租户的数据，但仍需要提供X-Tenant-ID来指定操作的租户。

### 3. 数据泄露防护

- 所有查询自动过滤租户
- 直接ID访问也会验证租户所有权
- 批量操作限制在当前租户范围

## 常见问题

### Q: 可以同时查询多个租户的数据吗？

A: 不可以。每个请求只能操作一个租户的数据。如需访问多个租户，需要发送多个请求。

### Q: 如何切换租户？

A: 更改请求头中的X-Tenant-ID，确保使用的Token有权访问目标租户。

### Q: 为什么我的搜索结果比预期少？

A: 搜索结果会自动限制在当前租户范围内。其他租户的数据不会出现在结果中。

### Q: 系统预设数据如何处理？

A: 某些数据（如打卡系统的系统预设分类）设计为跨租户共享，会对所有租户可见。

### Q: 删除操作是物理删除还是软删除？

A: 大部分资源使用软删除（is_deleted=true），数据仍保留在数据库中。

## 测试示例

### 测试脚本

```bash
#!/bin/bash

# 配置
BASE_URL="http://localhost:8000/api/v1"
TENANT_ID="3"
TOKEN="your_jwt_token_here"

# 测试1: 查询应用列表
echo "测试1: 查询应用列表"
curl -X GET "${BASE_URL}/applications/" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  | jq .

# 测试2: 创建应用
echo "测试2: 创建应用"
curl -X POST "${BASE_URL}/applications/" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test App",
    "code": "TEST_APP"
  }' | jq .

# 测试3: 尝试跨租户访问（应该失败）
echo "测试3: 跨租户访问测试"
curl -X GET "${BASE_URL}/applications/1/" \
  -H "X-Tenant-ID: 999" \
  -H "Authorization: Bearer ${TOKEN}" \
  | jq .
```

## 性能考虑

### 查询性能

租户过滤通过数据库索引优化，性能影响极小（< 10%）。

### 索引

确保以下字段有索引：
- `tenant_id`
- `tenant_id, created_at`（复合索引）
- `tenant_id, is_deleted`（复合索引）

### 缓存策略

考虑对热点数据使用租户级别的缓存：

```python
cache_key = f"tenant:{tenant_id}:applications"
```

## 迁移指南

### 从无租户系统迁移

1. 为所有旧数据分配默认租户
2. 更新客户端代码添加X-Tenant-ID头
3. 测试所有API端点
4. 验证数据隔离

### 前端集成

```javascript
// 配置axios默认头部
axios.defaults.headers.common['X-Tenant-ID'] = getCurrentTenantId();
axios.defaults.headers.common['Authorization'] = `Bearer ${getToken()}`;

// 发送请求
axios.get('/api/v1/applications/')
  .then(response => {
    // 只返回当前租户的数据
    console.log(response.data);
  });
```

## 更新日志

### 2025-11-22
- ✅ 实施全面租户隔离
- ✅ 重构24个核心ViewSets
- ✅ 性能测试通过
- ✅ 安全测试通过

---

**文档版本**: 1.0
**最后更新**: 2025-11-22
**维护者**: 开发团队
