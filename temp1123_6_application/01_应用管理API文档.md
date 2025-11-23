# 应用管理 API 文档

## 概述

应用管理API提供了对租户应用的完整CRUD操作，以及应用统计和关联文章查询功能。

**基础URL**: `http://localhost:8000/api/v1`

**认证方式**: Bearer Token (JWT)

**权限要求**: 租户管理员

## API 列表

| 序号 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 1 | GET | `/applications/` | 获取应用列表 |
| 2 | POST | `/applications/` | 创建应用 |
| 3 | GET | `/applications/{id}/` | 获取应用详情 |
| 4 | PUT | `/applications/{id}/` | 完整更新应用 |
| 5 | PATCH | `/applications/{id}/` | 部分更新应用 |
| 6 | DELETE | `/applications/{id}/` | 删除应用 |
| 7 | GET | `/applications/{id}/statistics/` | 获取应用统计 |
| 8 | GET | `/applications/{id}/articles/` | 获取应用关联文章 |

---

## 1. 获取应用列表

### 接口信息

- **请求方法**: `GET`
- **请求路径**: `/api/v1/applications/`
- **权限要求**: 租户管理员

### 请求参数

#### Query参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认10 |

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 6,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 1,
        "name": "测试应用API",
        "code": "test-api-app",
        "description": "curl完整更新测试",
        "logo": "",
        "current_version": "1.2.0",
        "status": "active",
        "is_active": true,
        "created_at": "2025-11-21T14:31:49.522138Z",
        "updated_at": "2025-11-23T13:21:06.925074Z"
      }
    ]
  }
}
```

### cURL示例

```bash
curl -X GET "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 2. 创建应用

### 接口信息

- **请求方法**: `POST`
- **请求路径**: `/api/v1/applications/`
- **权限要求**: 租户管理员

### 请求参数

#### Body参数 (JSON)

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 应用名称，最大100字符 |
| code | string | 是 | 应用代码，最大50字符，租户内唯一 |
| description | string | 否 | 应用描述 |
| logo | string | 否 | Logo URL地址 |
| website | string | 否 | 官方网站URL |
| contact_email | string | 否 | 联系邮箱 |
| current_version | string | 否 | 当前版本，默认"1.0.0" |
| owner | string | 否 | 负责人姓名，最大100字符 |
| team | string | 否 | 开发团队名称，最大200字符 |
| status | string | 否 | 状态，可选值见下表，默认"active" |
| is_active | boolean | 否 | 是否启用，默认true |
| tags | array | 否 | 标签列表，JSON数组 |
| metadata | object | 否 | 元数据，JSON对象 |

**status可选值**:
- `development`: 开发中
- `testing`: 测试中
- `active`: 运行中
- `maintenance`: 维护中
- `deprecated`: 已弃用
- `archived`: 已归档

### 请求示例

```json
{
  "name": "示例应用",
  "code": "example-app",
  "description": "这是一个示例应用",
  "logo": "https://example.com/logo.png",
  "website": "https://example.com",
  "contact_email": "contact@example.com",
  "current_version": "1.0.0",
  "owner": "张三",
  "team": "产品研发部",
  "status": "development",
  "is_active": true,
  "tags": ["示例", "测试"],
  "metadata": {
    "category": "工具类"
  }
}
```

### 响应示例

```json
{
  "success": true,
  "code": "example-app",
  "message": "操作成功",
  "data": {
    "name": "示例应用",
    "code": "example-app",
    "description": "这是一个示例应用",
    "logo": "https://example.com/logo.png",
    "website": "https://example.com",
    "contact_email": "contact@example.com",
    "current_version": "1.0.0",
    "owner": "张三",
    "team": "产品研发部",
    "status": "development",
    "is_active": true,
    "tags": ["示例", "测试"],
    "metadata": {
      "category": "工具类"
    }
  }
}
```

### cURL示例

```bash
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "示例应用",
    "code": "example-app",
    "description": "这是一个示例应用",
    "current_version": "1.0.0",
    "status": "development"
  }'
```

### 错误响应

**应用代码重复**:
```json
{
  "success": false,
  "code": 4000,
  "message": "应用代码 'example-app' 在当前租户下已存在"
}
```

---

## 3. 获取应用详情

### 接口信息

- **请求方法**: `GET`
- **请求路径**: `/api/v1/applications/{id}/`
- **权限要求**: 租户管理员

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 应用ID |

### 响应示例

```json
{
  "success": true,
  "code": "test-api-app",
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "测试应用API",
    "code": "test-api-app",
    "description": "完整的应用描述",
    "logo": "https://example.com/logo.png",
    "website": "https://example.com",
    "contact_email": "contact@example.com",
    "current_version": "1.2.0",
    "owner": "张三",
    "team": "技术部",
    "status": "active",
    "is_active": true,
    "tags": ["标签1", "标签2"],
    "metadata": {},
    "license_count": 5,
    "feedback_count": 3,
    "article_count": 10,
    "created_at": "2025-11-21T14:31:49.522138Z",
    "updated_at": "2025-11-23T13:21:06.925074Z"
  }
}
```

### 响应字段说明

除了基本字段外，详情接口还包含以下统计字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| license_count | integer | 许可证总数 |
| feedback_count | integer | 反馈总数 |
| article_count | integer | 关联文章总数 |

### cURL示例

```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 4. 完整更新应用

### 接口信息

- **请求方法**: `PUT`
- **请求路径**: `/api/v1/applications/{id}/`
- **权限要求**: 租户管理员

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 应用ID |

### 请求参数

Body参数与"创建应用"相同，但需要提供所有必填字段。

### 请求示例

```json
{
  "name": "测试应用-已更新",
  "code": "test-app-updated",
  "description": "完整更新后的描述",
  "current_version": "2.0.0",
  "status": "active",
  "logo": "https://example.com/logo-new.png",
  "website": "https://newexample.com",
  "contact_email": "updated@example.com",
  "owner": "新负责人",
  "team": "新团队",
  "tags": ["更新", "测试"],
  "is_active": true
}
```

### 响应示例

```json
{
  "success": true,
  "code": "test-app-updated",
  "message": "操作成功",
  "data": {
    "name": "测试应用-已更新",
    "code": "test-app-updated",
    "description": "完整更新后的描述",
    "logo": "https://example.com/logo-new.png",
    "website": "https://newexample.com",
    "contact_email": "updated@example.com",
    "current_version": "2.0.0",
    "owner": "新负责人",
    "team": "新团队",
    "status": "active",
    "is_active": true,
    "tags": ["更新", "测试"],
    "metadata": {}
  }
}
```

### cURL示例

```bash
curl -X PUT "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试应用-已更新",
    "code": "test-app-updated",
    "description": "完整更新后的描述",
    "current_version": "2.0.0",
    "status": "active"
  }'
```

---

## 5. 部分更新应用

### 接口信息

- **请求方法**: `PATCH`
- **请求路径**: `/api/v1/applications/{id}/`
- **权限要求**: 租户管理员

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 应用ID |

### 请求参数

可以只提供需要更新的字段，不需要提供所有字段。

### 请求示例

```json
{
  "current_version": "2.1.0",
  "description": "部分更新：只修改版本号和描述"
}
```

### 响应示例

```json
{
  "success": true,
  "code": "test-app",
  "message": "操作成功",
  "data": {
    "name": "测试应用",
    "code": "test-app",
    "description": "部分更新：只修改版本号和描述",
    "logo": "https://example.com/logo.png",
    "website": "https://example.com",
    "contact_email": "contact@example.com",
    "current_version": "2.1.0",
    "owner": "张三",
    "team": "技术部",
    "status": "active",
    "is_active": true,
    "tags": [],
    "metadata": {}
  }
}
```

### cURL示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_version": "2.1.0"
  }'
```

---

## 6. 删除应用

### 接口信息

- **请求方法**: `DELETE`
- **请求路径**: `/api/v1/applications/{id}/`
- **权限要求**: 租户管理员

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 应用ID |

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": null
}
```

### cURL示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 注意事项

- 删除应用时，关联的许可证、反馈等数据会根据数据库外键约束进行处理
- 建议先检查应用的关联数据后再执行删除操作

---

## 7. 获取应用统计信息

### 接口信息

- **请求方法**: `GET`
- **请求路径**: `/api/v1/applications/{id}/statistics/`
- **权限要求**: 租户管理员

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 应用ID |

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "licenses": {
      "total": 10,
      "active": 8
    },
    "feedbacks": {
      "total": 25,
      "open": 5
    },
    "articles": {
      "total": 15
    }
  }
}
```

### 响应字段说明

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| licenses.total | integer | 许可证总数 |
| licenses.active | integer | 已激活的许可证数 |
| feedbacks.total | integer | 反馈总数 |
| feedbacks.open | integer | 未关闭的反馈数 |
| articles.total | integer | 关联文章总数 |

### cURL示例

```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 8. 获取应用关联文章

### 接口信息

- **请求方法**: `GET`
- **请求路径**: `/api/v1/applications/{id}/articles/`
- **权限要求**: 租户管理员

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 应用ID |

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "title": "应用使用指南",
      "slug": "app-usage-guide",
      "excerpt": "本文介绍应用的基本使用方法...",
      "author_info": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com"
      },
      "author_type": "admin",
      "status": "published",
      "is_featured": false,
      "is_pinned": true,
      "cover_image": "http://localhost:8000/media/articles/cover1.jpg",
      "cover_image_small": "http://localhost:8000/media/articles/cover1_small.jpg",
      "published_at": "2025-11-20T10:00:00Z",
      "created_at": "2025-11-20T09:00:00Z",
      "updated_at": "2025-11-20T10:00:00Z",
      "categories": [
        {
          "id": 1,
          "name": "教程",
          "slug": "tutorial",
          "color": "#3B82F6"
        }
      ],
      "tags": [
        {
          "id": 1,
          "name": "入门",
          "slug": "beginner",
          "color": "#10B981"
        }
      ],
      "comments_count": 5,
      "likes_count": 20,
      "views_count": 150,
      "parent": null,
      "parent_info": null,
      "children_count": 2
    }
  ]
}
```

### cURL示例

```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/articles/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 通用说明

### 认证

所有接口都需要在请求头中携带JWT Token：

```
Authorization: Bearer YOUR_JWT_TOKEN
```

### 租户隔离

- 租户管理员只能操作自己租户下的应用
- tenant_id自动从Token中获取，不需要手动传递
- 所有查询、创建、更新、删除操作都会自动进行租户隔离

### 错误响应格式

```json
{
  "success": false,
  "code": 4000,
  "message": "错误信息描述",
  "data": null,
  "error_code": "ERROR_CODE"
}
```

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| 4000 | 请求参数错误 |
| 4001 | 认证失败 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 5000 | 服务器内部错误 |

---

## 完整测试脚本

参见 `test_all_apis.sh` 文件，可直接运行完整测试：

```bash
chmod +x test_all_apis.sh
./test_all_apis.sh
```
