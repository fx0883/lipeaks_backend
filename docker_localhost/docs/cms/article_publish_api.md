# 发布文章API

## API 端点

```
POST /api/v1/cms/articles/{id}/publish/
```

## 描述

将文章状态改为已发布，并设置发布时间。

## 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | Bearer token认证 |
| Content-Type | string | 是 | application/json |
| X-Tenant-ID | string | 否 | 租户ID |

## 请求体

请求体可以为空，或者包含以下字段：

```json
{
  "published_at": "2025-06-22T13:39:48.918Z"
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| published_at | string | 否 | 指定发布时间，如不提供则使用当前时间 |

## 响应

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "文章已成功发布",
  "data": {
    "id": 15,
    "status": "published",
    "published_at": "2025-06-22T13:39:35.243186Z"
  }
}
```

### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 是否成功 |
| code | integer | 状态码 |
| message | string | 操作结果描述 |
| data | object | 返回数据 |
| data.id | integer | 文章ID |
| data.status | string | 文章状态，应为"published" |
| data.published_at | string | 发布时间 |

### 错误响应

#### 400 Bad Request

```json
{
  "detail": "文章已经是发布状态"
}
```

#### 401 Unauthorized

```json
{
  "detail": "身份认证信息未提供。"
}
```

#### 403 Forbidden

```json
{
  "detail": "您没有执行此操作的权限。"
}
```

#### 404 Not Found

```json
{
  "detail": "未找到。"
}
```

## 示例

### cURL示例

```bash
# 使用当前时间发布
curl -X 'POST' \
  'http://localhost:8000/api/v1/cms/articles/15/publish/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{}'

# 指定发布时间
curl -X 'POST' \
  'http://localhost:8000/api/v1/cms/articles/15/publish/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
  "published_at": "2025-06-22T13:39:48.918Z"
}'
```

### Python示例

```python
import requests

article_id = 15
url = f'http://localhost:8000/api/v1/cms/articles/{article_id}/publish/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}

# 使用当前时间发布
response = requests.post(url, headers=headers, json={})
print(response.status_code)
print(response.json())

# 指定发布时间
data = {
    'published_at': '2025-06-22T13:39:48.918Z'
}
response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.json())
```

## 注意事项

1. 只有处于非发布状态(draft, pending, archived)的文章才能被发布
2. 发布文章会自动设置published_at字段为当前时间，除非在请求中指定了发布时间
3. 只有文章作者或管理员才能发布文章
4. 如果文章已经是发布状态，API会返回400错误 