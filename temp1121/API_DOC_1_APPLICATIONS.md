# Applications API 文档

## 基础信息

**Base URL**: `http://localhost:8000/api/v1`  
**认证方式**: JWT Bearer Token  
**必需请求头**:
- `Authorization: Bearer {token}`
- `Tenant-ID: {tenant_id}`

---

## 获取Token

```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}' \
  | jq -r '.data.token')
```

---

## API端点

### 1. 获取应用列表

**GET** `/applications/`

```bash
curl "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "name": "LiPeaks CMS",
        "code": "lipeaks-cms",
        "description": "内容管理系统",
        "logo": null,
        "current_version": "1.0.0",
        "status": "active",
        "is_active": true,
        "created_at": "2024-11-21T10:00:00Z",
        "updated_at": "2024-11-21T10:00:00Z"
      }
    ]
  }
}
```

**查询参数**:
- `search` - 搜索关键词（name, code）
- `status` - 状态过滤（active, inactive, archived）
- `page` - 页码
- `page_size` - 每页数量

---

### 2. 创建应用

**POST** `/applications/`

```bash
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新应用",
    "code": "new-app",
    "description": "应用描述",
    "owner": "开发团队",
    "team": "技术部",
    "current_version": "1.0.0"
  }'
```

**请求体字段**:
- `name` - 应用名称（必填）
- `code` - 应用代码（必填，唯一）
- `description` - 描述（可选）
- `owner` - 负责人（可选）
- `team` - 团队（可选）
- `current_version` - 当前版本（可选，默认"1.0.0"）
- `logo` - Logo URL（可选）
- `website` - 官网（可选）
- `contact_email` - 联系邮箱（可选）

**响应示例**:
```json
{
  "success": true,
  "code": "new-app",
  "message": "操作成功",
  "data": {
    "name": "新应用",
    "code": "new-app",
    "description": "应用描述",
    "current_version": "1.0.0",
    "status": "active",
    "is_active": true
  }
}
```

---

### 3. 获取应用详情

**GET** `/applications/{id}/`

```bash
curl "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "LiPeaks CMS",
    "code": "lipeaks-cms",
    "description": "内容管理系统",
    "logo": null,
    "website": "https://example.com",
    "contact_email": "support@example.com",
    "current_version": "1.0.0",
    "owner": "技术团队",
    "team": "开发部",
    "status": "active",
    "is_active": true,
    "tags": ["cms", "content"],
    "metadata": {},
    "created_at": "2024-11-21T10:00:00Z",
    "updated_at": "2024-11-21T10:00:00Z"
  }
}
```

---

### 4. 更新应用

**PATCH** `/applications/{id}/`

```bash
curl -X PATCH "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "current_version": "2.0.0",
    "description": "更新后的描述"
  }'
```

**可更新字段**: 除`id`, `code`外的所有字段

**响应**: 同详情接口

---

### 5. 删除应用

**DELETE** `/applications/{id}/`

```bash
curl -X DELETE "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "删除成功"
}
```

**注意**: 软删除，设置`is_deleted=True`

---

### 6. 获取应用统计

**GET** `/applications/{id}/statistics/`

```bash
curl "http://localhost:8000/api/v1/applications/1/statistics/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "licenses": {
      "total": 50,
      "active": 45,
      "expired": 5
    },
    "feedbacks": {
      "total": 120,
      "pending": 30,
      "in_progress": 50,
      "resolved": 40
    },
    "categories": {
      "total": 10
    }
  }
}
```

---

## 完整测试示例

```bash
# 1. 登录获取Token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  | jq -r '.data.token')

# 2. 创建应用
APP_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试应用",
    "code": "test-app",
    "description": "这是一个测试应用"
  }')

APP_ID=$(echo "$APP_RESPONSE" | jq -r '.data.id')
echo "创建的应用ID: $APP_ID"

# 3. 获取应用详情
curl "http://localhost:8000/api/v1/applications/$APP_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" | jq

# 4. 更新版本
curl -X PATCH "http://localhost:8000/api/v1/applications/$APP_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"current_version": "1.1.0"}' | jq

# 5. 获取统计
curl "http://localhost:8000/api/v1/applications/$APP_ID/statistics/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" | jq
```

---

## 错误响应

```json
{
  "success": false,
  "code": 4000,
  "message": "错误信息",
  "data": null
}
```

**常见错误码**:
- `4001` - 参数错误
- `4010` - 未授权
- `4030` - 权限不足
- `4040` - 资源不存在
- `5000` - 服务器错误

---

## 注意事项

1. **ApplicationVersion已删除** - 不再支持独立的版本管理
2. **版本字段** - 使用`current_version`字段（字符串类型）
3. **租户隔离** - 所有请求必须包含`Tenant-ID`请求头
4. **软删除** - 删除操作不会物理删除数据
