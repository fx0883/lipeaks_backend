# 批量删除文章API文档

## API 端点

```
POST /api/v1/cms/articles/batch-delete/
```

## 描述

此API用于批量删除多篇文章。可以选择软删除（默认）或强制删除（真实删除）。

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | Bearer token认证 |
| Content-Type | string | 是 | application/json |
| X-CSRFTOKEN | string | 否 | CSRF令牌（如果需要） |
| X-Tenant-ID | string | 否 | 租户ID |

## 请求体

请求体应为JSON格式，包含以下字段：

```json
{
  "article_ids": [1, 2, 3],  // 要删除的文章ID数组（必填）
  "force": false             // 是否强制删除，默认为false（软删除）
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| article_ids | array | 是 | 要删除的文章ID列表 |
| force | boolean | 否 | 是否强制删除，默认为false（软删除） |

## 响应

### 成功响应 (200 OK)

```json
{
  "message": "文章批量删除成功",
  "requested_count": 3,
  "deleted_count": 2,
  "deleted_ids": [1, 3]
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| message | string | 操作结果描述 |
| requested_count | integer | 请求删除的文章数量 |
| deleted_count | integer | 实际删除的文章数量 |
| deleted_ids | array | 实际删除的文章ID列表 |

### 错误响应

#### 400 Bad Request

```json
{
  "detail": "未提供要删除的文章ID"
}
```

或

```json
{
  "detail": "文章ID列表格式错误，必须是整数列表"
}
```

#### 403 Forbidden

```json
{
  "detail": "您没有执行此操作的权限"
}
```

#### 404 Not Found

```json
{
  "detail": "未找到可删除的文章"
}
```

## 示例

### cURL示例

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/cms/articles/batch-delete/' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
  "article_ids": [1, 2, 3],
  "force": false
}'
```

### Python示例

```python
import requests

url = 'http://localhost:8000/api/v1/cms/articles/batch-delete/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}
data = {
    'article_ids': [1, 2, 3],
    'force': False
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.json())
```

## 注意事项

1. 此API需要管理员权限
2. 软删除（force=false）将文章状态改为"archived"，而不是真正从数据库删除
3. 强制删除（force=true）将永久从数据库删除文章，无法恢复
4. 只有有权限操作的文章才会被删除，其他文章会被忽略 