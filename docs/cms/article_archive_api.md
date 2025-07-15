# 归档文章API

## API 端点

```
POST /api/v1/cms/articles/{id}/archive/
```

## 描述

将文章状态改为归档。

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
  "message": "文章已归档",
  "data": {
    "id": 15,
    "status": "archived"
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
| data.status | string | 文章状态，应为"archived" |

### 错误响应

#### 400 Bad Request

```json
{
  "detail": "文章已经是归档状态"
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
  'http://localhost:8000/api/v1/cms/articles/15/archive/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### Python示例

```python
import requests

article_id = 15
url = f'http://localhost:8000/api/v1/cms/articles/{article_id}/archive/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers, json={})
print(response.status_code)
print(response.json())
```

## 注意事项

1. 归档文章后，文章将不再显示在默认的文章列表中，除非明确指定查询归档状态的文章
2. 归档文章可以通过更新API重新设置状态为草稿或发布状态
3. 归档操作不会删除文章内容，只是改变文章的状态 