# 取消发布文章API

## API 端点

```
POST /api/v1/cms/articles/{id}/unpublish/
```

## 描述

将已发布文章的状态改为草稿。

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

请求体可以为空。

## 响应

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "文章已取消发布",
  "data": {
    "id": 15,
    "status": "draft"
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
| data.status | string | 文章状态，应为"draft" |

### 错误响应

#### 400 Bad Request

```json
{
  "detail": "文章不是发布状态，无法取消发布"
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
curl -X 'POST' \
  'http://localhost:8000/api/v1/cms/articles/15/unpublish/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### Python示例

```python
import requests

article_id = 15
url = f'http://localhost:8000/api/v1/cms/articles/{article_id}/unpublish/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers, json={})
print(response.status_code)
print(response.json())
```

## 注意事项

1. 只有处于已发布状态(published)的文章才能被取消发布
2. 取消发布不会清除文章的published_at字段
3. 只有文章作者或管理员才能取消发布文章
4. 如果文章不是发布状态，API会返回400错误 