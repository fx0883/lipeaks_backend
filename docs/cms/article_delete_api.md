# 删除文章API

## API 端点

```
DELETE /api/v1/cms/articles/{id}/
```

## 描述

删除指定ID的文章，支持软删除（默认）和强制删除。

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

## 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| force | boolean | 否 | 是否强制删除，默认false（软删除） |

## 响应

### 成功响应 (204 No Content)

删除成功时，服务器返回204状态码，无响应体。

### 错误响应

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
# 软删除（默认）
curl -X 'DELETE' \
  'http://localhost:8000/api/v1/cms/articles/16/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

# 强制删除
curl -X 'DELETE' \
  'http://localhost:8000/api/v1/cms/articles/16/?force=true' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

### Python示例

```python
import requests

article_id = 16
url = f'http://localhost:8000/api/v1/cms/articles/{article_id}/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}

# 软删除（默认）
response = requests.delete(url, headers=headers)
print(response.status_code)

# 强制删除
params = {'force': 'true'}
response = requests.delete(url, headers=headers, params=params)
print(response.status_code)
```

## 注意事项

1. 默认情况下，删除文章是软删除，即将文章状态改为archived，不会从数据库中真正删除
2. 如果需要彻底删除文章及其相关数据，可以使用force=true参数进行强制删除
3. 强制删除后的文章无法恢复，请谨慎操作
4. 只有文章作者或管理员才能删除文章
5. 如果需要批量删除多篇文章，请使用批量删除API 