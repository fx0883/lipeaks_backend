# 拒绝评论接口

## 接口概述

拒绝评论，将评论状态设置为已拒绝。被拒绝的评论不会在前端显示。

**接口地址**: `POST /cms/comments/{comment_id}/reject/`

---

## 请求参数

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| comment_id | integer | 是 | 评论 ID |

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| Authorization | string | 是 | Bearer {token} |
| Content-Type | string | 是 | application/json |

### 请求体

无需请求体。

---

## 响应参数

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "评论已拒绝",
  "data": {
    "message": "评论已拒绝",
    "id": 35,
    "status": "rejected"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| code | integer | 业务状态码，2000 表示成功 |
| message | string | 响应消息 |
| data.id | integer | 评论 ID |
| data.status | string | 更新后的状态：`rejected` |

---

## 错误响应

### 1. 评论已是拒绝状态 (400 Bad Request)

```json
{
  "success": false,
  "code": 4000,
  "message": "评论已经是拒绝状态",
  "data": null
}
```

### 2. 无权限 (403 Forbidden)

```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限拒绝此评论",
  "data": null
}
```

### 3. 评论不存在 (404 Not Found)

```json
{
  "success": false,
  "code": 4040,
  "message": "评论不存在",
  "data": null
}
```

---

## 使用示例

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/35/reject/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

### JavaScript (Fetch API)

```javascript
const token = 'your_jwt_token_here';
const commentId = 35;

fetch(`http://localhost:8000/api/v1/cms/comments/${commentId}/reject/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('评论拒绝成功:', data.data);
  } else {
    console.error('拒绝失败:', data.message);
  }
})
.catch(error => console.error('请求失败:', error));
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/cms/comments/35/reject/"
headers = {
    "Authorization": "Bearer your_jwt_token_here",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)
data = response.json()

if data['success']:
    print(f"评论拒绝成功: ID={data['data']['id']}, 状态={data['data']['status']}")
else:
    print(f"拒绝失败: {data['message']}")
```

---

[返回概述](./01_overview.md) | [上一页：批准评论](./02_approve_api.md) | [下一页：标记垃圾](./04_mark_spam_api.md)
