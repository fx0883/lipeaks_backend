# 记录文章阅读API

## API 端点

```
POST /api/v1/cms/articles/{id}/view/
```

## 描述

记录文章的阅读行为，更新阅读统计。

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

```json
{
  "session_id": "string",
  "reading_time": 0,
  "referrer": "string"
}
```

### 请求参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | string | 否 | 会话ID，用于跟踪唯一访客 |
| reading_time | integer | 否 | 阅读时长(秒) |
| referrer | string | 否 | 来源URL |

## 响应

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "阅读记录已保存",
  "data": {}
}
```

### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 是否成功 |
| code | integer | 状态码 |
| message | string | 操作结果描述 |
| data | object | 返回数据，通常为空对象 |

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
curl -X 'POST' \
  'http://localhost:8000/api/v1/cms/articles/15/view/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
  "session_id": "user_session_123",
  "reading_time": 120,
  "referrer": "https://example.com/blog"
}'
```

### Python示例

```python
import requests

article_id = 15
url = f'http://localhost:8000/api/v1/cms/articles/{article_id}/view/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}
data = {
    'session_id': 'user_session_123',
    'reading_time': 120,
    'referrer': 'https://example.com/blog'
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.json())
```

## 注意事项

1. 此API用于前端记录用户阅读文章的行为，通常在页面加载和用户离开页面时调用
2. 提供reading_time参数可以帮助系统计算平均阅读时间
3. 系统会自动更新文章的浏览次数和其他相关统计数据
4. 如果提供了session_id，系统可以更准确地统计独立访客数量
5. 此API不需要用户登录即可调用，适用于公开文章的访问统计 