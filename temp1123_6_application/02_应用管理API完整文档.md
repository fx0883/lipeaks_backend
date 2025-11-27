# 应用管理API完整文档

**版本**: v1  
**基础URL**: `http://localhost:8000/api/v1/applications/`  
**认证方式**: Bearer Token (JWT)  
**测试日期**: 2025-11-24

---

## 目录

1. [认证说明](#认证说明)
2. [通用响应格式](#通用响应格式)
3. [API列表](#api列表)
4. [详细API文档](#详细api文档)
5. [错误码说明](#错误码说明)

---

## 认证说明

### 租户管理员认证

所有API都需要Bearer Token认证。租户管理员的tenant_id会自动从token中提取，**无需手动传递tenant_id参数**。

**请求头格式**:
```http
Authorization: Bearer {TOKEN}
Content-Type: application/json
```

**租户管理员Token示例**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM
```

### 权限说明

- **GET请求**: 所有认证用户（包括租户管理员和普通成员）
- **POST/PUT/PATCH/DELETE**: 仅租户管理员

---

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    // 响应数据
  }
}
```

### 错误响应
```json
{
  "success": false,
  "code": 4000,
  "message": "错误描述",
  "data": null,
  "error_code": "ERROR_CODE"
}
```

---

## API列表

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /applications/ | 获取应用列表 | 所有认证用户 |
| POST | /applications/ | 创建新应用 | 租户管理员 |
| GET | /applications/{id}/ | 获取应用详情 | 所有认证用户 |
| PUT | /applications/{id}/ | 完整更新应用 | 租户管理员 |
| PATCH | /applications/{id}/ | 部分更新应用 | 租户管理员 |
| DELETE | /applications/{id}/ | 删除应用（软删除） | 租户管理员 |
| GET | /applications/{id}/articles/ | 获取应用关联文章 | 所有认证用户 |
| GET | /applications/{id}/statistics/ | 获取应用统计信息 | 所有认证用户 |

---

## 详细API文档

### 1. 获取应用列表

**接口**: `GET /api/v1/applications/`

**描述**: 获取当前租户的所有应用列表，支持分页、过滤、搜索和排序

**权限**: 所有认证用户

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量 |
| status | string | 否 | - | 按状态过滤（development/testing/active/maintenance/deprecated/archived） |
| is_active | boolean | 否 | - | 按是否启用过滤（true/false） |
| search | string | 否 | - | 搜索关键词（在name、code、description中搜索） |
| ordering | string | 否 | -created_at | 排序字段（created_at/updated_at/name/code，前缀-表示倒序） |

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
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
      "count": 11,
      "next": "http://localhost:8000/api/v1/applications/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 2
    },
    "results": [
      {
        "id": 1,
        "name": "测试应用",
        "code": "test-app",
        "description": "应用描述",
        "logo": "https://example.com/logo.png",
        "current_version": "1.0.0",
        "status": "active",
        "is_active": true,
        "created_at": "2025-11-21T14:31:49.522138Z",
        "updated_at": "2025-11-21T14:31:49.522138Z"
      }
    ]
  }
}
```

**字段说明**:
- `id`: 应用ID
- `name`: 应用名称
- `code`: 应用代码（唯一标识）
- `description`: 应用描述
- `logo`: 应用Logo URL
- `current_version`: 当前版本号
- `status`: 状态（development/testing/active/maintenance/deprecated/archived）
- `is_active`: 是否激活
- `created_at`: 创建时间
- `updated_at`: 更新时间

**过滤示例**:

1. 按状态过滤：
```bash
curl -X GET "http://localhost:8000/api/v1/applications/?status=active" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

2. 按启用状态过滤：
```bash
curl -X GET "http://localhost:8000/api/v1/applications/?is_active=true" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

3. 搜索应用：
```bash
curl -X GET "http://localhost:8000/api/v1/applications/?search=测试" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

4. 按名称排序：
```bash
curl -X GET "http://localhost:8000/api/v1/applications/?ordering=name" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

5. 组合过滤：
```bash
curl -X GET "http://localhost:8000/api/v1/applications/?status=development&search=测试&ordering=-created_at" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 2. 创建新应用

**接口**: `POST /api/v1/applications/`

**描述**: 创建新的应用，自动关联当前租户

**权限**: 租户管理员

**请求体参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 应用名称 |
| code | string | 是 | 应用代码（租户内唯一） |
| description | string | 否 | 应用描述 |
| logo | string | 否 | Logo URL |
| website | string | 否 | 官网地址 |
| contact_email | string | 否 | 联系邮箱 |
| current_version | string | 否 | 当前版本（默认1.0.0） |
| owner | string | 否 | 负责人 |
| team | string | 否 | 所属团队 |
| status | string | 否 | 状态（默认development） |
| tags | array | 否 | 标签数组 |
| metadata | object | 否 | 元数据JSON对象 |

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的应用",
    "code": "my-app",
    "description": "这是一个测试应用",
    "current_version": "1.0.0",
    "status": "development",
    "website": "https://example.com",
    "contact_email": "contact@example.com",
    "owner": "张三",
    "team": "开发团队",
    "tags": ["测试", "开发"]
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": "my-app",
  "message": "操作成功",
  "data": {
    "name": "我的应用",
    "code": "my-app",
    "description": "这是一个测试应用",
    "logo": null,
    "website": "https://example.com",
    "contact_email": "contact@example.com",
    "current_version": "1.0.0",
    "owner": "张三",
    "team": "开发团队",
    "status": "development",
    "is_active": true,
    "tags": ["测试", "开发"],
    "metadata": {}
  }
}
```

**状态值说明**:
- `development`: 开发中
- `testing`: 测试中
- `active`: 已发布
- `inactive`: 已下线
- `deprecated`: 已废弃

**错误响应示例**:
```json
{
  "success": false,
  "code": 4000,
  "message": "code字段在当前租户下必须唯一",
  "data": null
}
```

---

### 3. 获取应用详情

**接口**: `GET /api/v1/applications/{id}/`

**描述**: 获取指定应用的详细信息，包含许可证、反馈、文章统计

**权限**: 所有认证用户

**路径参数**:
- `id`: 应用ID

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": "test-app",
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "测试应用",
    "code": "test-app",
    "description": "应用描述",
    "logo": "https://example.com/logo.png",
    "website": "https://example.com",
    "contact_email": "contact@example.com",
    "current_version": "2.1.0",
    "owner": "张三",
    "team": "开发团队",
    "status": "active",
    "is_active": true,
    "tags": ["测试"],
    "metadata": {},
    "license_count": 5,
    "feedback_count": 3,
    "article_count": 10,
    "created_at": "2025-11-21T14:31:49.522138Z",
    "updated_at": "2025-11-23T13:26:20.830823Z"
  }
}
```

**额外字段说明**:
- `license_count`: 许可证总数
- `feedback_count`: 反馈总数
- `article_count`: 关联文章总数

---

### 4. 完整更新应用

**接口**: `PUT /api/v1/applications/{id}/`

**描述**: 完整更新应用信息（所有字段都需要提供）

**权限**: 租户管理员

**路径参数**:
- `id`: 应用ID

**请求体参数**: 同创建接口，所有字段都需要提供

**curl示例**:
```bash
curl -X PUT "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的应用名称",
    "code": "updated-app",
    "description": "更新后的描述",
    "current_version": "2.0.0",
    "status": "testing",
    "website": "https://updated.com",
    "contact_email": "updated@example.com",
    "owner": "李四",
    "team": "测试团队",
    "tags": ["更新", "测试"]
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": "updated-app",
  "message": "操作成功",
  "data": {
    "name": "更新后的应用名称",
    "code": "updated-app",
    "description": "更新后的描述",
    "logo": null,
    "website": "https://updated.com",
    "contact_email": "updated@example.com",
    "current_version": "2.0.0",
    "owner": "李四",
    "team": "测试团队",
    "status": "testing",
    "is_active": true,
    "tags": ["更新", "测试"],
    "metadata": {}
  }
}
```

---

### 5. 部分更新应用

**接口**: `PATCH /api/v1/applications/{id}/`

**描述**: 部分更新应用信息（只需提供需要更新的字段）

**权限**: 租户管理员

**路径参数**:
- `id`: 应用ID

**请求体参数**: 可选的字段，只需提供要更新的字段

**curl示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "current_version": "2.5.0",
    "description": "仅更新版本和描述"
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": "test-app",
  "message": "操作成功",
  "data": {
    "name": "测试应用",
    "code": "test-app",
    "description": "仅更新版本和描述",
    "logo": "https://example.com/logo.png",
    "website": "https://example.com",
    "contact_email": "contact@example.com",
    "current_version": "2.5.0",
    "owner": "张三",
    "team": "开发团队",
    "status": "active",
    "is_active": true,
    "tags": ["测试"],
    "metadata": {}
  }
}
```

---

### 6. 删除应用

**接口**: `DELETE /api/v1/applications/{id}/`

**描述**: 软删除应用（仅标记为已删除，不实际删除数据）

**权限**: 租户管理员

**路径参数**:
- `id`: 应用ID

**curl示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

**成功响应** (204 No Content):
```
(无响应体)
```

**说明**:
- 删除成功返回HTTP 204状态码
- 使用软删除，数据不会真正删除，只是标记为`is_deleted=True`
- 软删除后的应用不会在列表API中显示
- 如果应用有关联的许可证、反馈等数据，不影响删除操作

---

### 7. 获取应用关联文章

**接口**: `GET /api/v1/applications/{id}/articles/`

**描述**: 获取指定应用关联的所有文章

**权限**: 所有认证用户

**路径参数**:
- `id`: 应用ID

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/articles/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 10001,
      "title": "应用使用指南",
      "slug": "app-guide",
      "excerpt": "详细的使用说明",
      "author_info": {
        "id": 3,
        "username": "admin",
        "email": "admin@example.com"
      },
      "status": "published",
      "created_at": "2025-11-20T10:00:00Z",
      "updated_at": "2025-11-20T10:00:00Z"
    }
  ]
}
```

**空数据响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": []
}
```

---

### 8. 获取应用统计信息

**接口**: `GET /api/v1/applications/{id}/statistics/`

**描述**: 获取应用的许可证、反馈、文章统计数据

**权限**: 所有认证用户

**路径参数**:
- `id`: 应用ID

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/statistics/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "licenses": {
      "total": 10,
      "active": 7
    },
    "feedbacks": {
      "total": 15,
      "open": 5
    },
    "articles": {
      "total": 8
    }
  }
}
```

**字段说明**:
- `licenses.total`: 许可证总数
- `licenses.active`: 激活的许可证数
- `feedbacks.total`: 反馈总数
- `feedbacks.open`: 未关闭的反馈数
- `articles.total`: 关联文章总数

---

## 错误码说明

| 错误码 | HTTP状态 | 描述 |
|--------|---------|------|
| 2000 | 200 | 操作成功 |
| 4000 | 400 | 请求参数错误 |
| 4001 | 401 | 未授权（Token无效或过期） |
| 4003 | 403 | 权限不足 |
| 4004 | 404 | 资源不存在 |
| 5000 | 500 | 服务器内部错误 |

---

## 常见问题

### Q1: 为什么不需要传递tenant_id？
A: 租户管理员的tenant_id会自动从JWT Token中提取，系统会自动进行租户隔离。

### Q2: 删除应用后数据还能恢复吗？
A: 可以。系统使用软删除机制，数据只是被标记为已删除，数据库中的数据仍然存在。

### Q3: code字段有什么限制？
A: code字段在同一租户内必须唯一，且只能包含字母、数字、中划线和下划线。

### Q4: 如何处理Token过期？
A: Token过期后需要重新登录获取新的Token。Token有效期见JWT配置。

### Q5: 支持批量操作吗？
A: 当前版本不支持批量创建、更新或删除。需要逐个操作。

---

## 测试记录

**测试日期**: 2025-11-24  
**测试环境**: localhost:8000  
**测试结果**: 所有8个API全部通过

| API | 测试状态 | HTTP状态码 |
|-----|---------|-----------|
| GET /applications/ | ✅ | 200 |
| POST /applications/ | ✅ | 200 |
| GET /applications/{id}/ | ✅ | 200 |
| PUT /applications/{id}/ | ✅ | 200 |
| PATCH /applications/{id}/ | ✅ | 200 |
| DELETE /applications/{id}/ | ✅ | 204 |
| GET /applications/{id}/articles/ | ✅ | 200 |
| GET /applications/{id}/statistics/ | ✅ | 200 |

---

## 更新日志

### v1.1.0 (2025-11-24)
- ✅ 添加列表过滤功能（status、is_active）
- ✅ 添加搜索功能（name、code、description）
- ✅ 添加排序功能（created_at、updated_at、name、code）
- ✅ 支持组合过滤、搜索和排序
- ✅ 优化TenantManager自动过滤is_deleted
- ✅ 清理15处冗余的手动is_deleted过滤

### v1.0.0 (2025-11-24)
- ✅ 实施租户隔离机制
- ✅ 支持软删除
- ✅ 添加统计信息API
- ✅ 添加文章关联API
- ✅ 完善权限控制
- ✅ 优化响应格式

---

**文档维护**: 本文档基于实际curl测试结果编写，确保所有示例真实有效。
