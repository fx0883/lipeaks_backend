# 批准评论接口

## 接口概述

批准待审核的评论，使其在前端显示。只有租户管理员和文章作者可以执行此操作。

**接口地址**: `POST /cms/comments/{comment_id}/approve/`

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
  "message": "评论已批准",
  "data": {
    "message": "评论已批准",
    "id": 3,
    "status": "approved"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| code | integer | 业务状态码，2000 表示成功 |
| message | string | 响应消息 |
| data.id | integer | 评论 ID |
| data.status | string | 更新后的状态：`approved` |

---

## 错误响应

### 1. 评论已是批准状态 (400 Bad Request)

```json
{
  "success": false,
  "code": 4000,
  "message": "评论已经是批准状态",
  "data": null
}
```

**原因**: 评论当前状态已经是 `approved`，无需重复操作。

---

### 2. 无权限 (403 Forbidden)

```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限批准此评论",
  "data": null
}
```

**原因**: 
- 用户是普通成员 (Member)，无审核权限
- 用户既不是管理员，也不是该文章的作者

---

### 3. 未认证 (401 Unauthorized)

```json
{
  "success": false,
  "code": 4010,
  "message": "未认证",
  "data": null
}
```

**原因**: 
- 未提供 Authorization 头
- Token 已过期或无效

---

### 4. 评论不存在 (404 Not Found)

```json
{
  "success": false,
  "code": 4040,
  "message": "评论不存在",
  "data": null
}
```

**原因**: 
- comment_id 不存在
- 用户无权访问该租户的评论

---

## 使用示例

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/3/approve/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6ImFkbWluX2ppbiIsImV4cCI6MTc2MzY5ODIxMCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.Dil_3r5QEhKMFZhVmg0-CVFGAem_mSs7xGQGnJymafw" \
  -H "Content-Type: application/json"
```

### JavaScript (Fetch API)

```javascript
const token = 'your_jwt_token_here';
const commentId = 3;

fetch(`http://localhost:8000/api/v1/cms/comments/${commentId}/approve/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('评论批准成功:', data.data);
    alert(`评论 ${data.data.id} 已批准`);
  } else {
    console.error('批准失败:', data.message);
    alert(`批准失败: ${data.message}`);
  }
})
.catch(error => {
  console.error('请求失败:', error);
  alert('请求失败，请检查网络连接');
});
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const token = 'your_jwt_token_here';
const commentId = 3;

axios.post(
  `http://localhost:8000/api/v1/cms/comments/${commentId}/approve/`,
  {},
  {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }
)
.then(response => {
  const data = response.data;
  if (data.success) {
    console.log('评论批准成功:', data.data);
  } else {
    console.error('批准失败:', data.message);
  }
})
.catch(error => {
  if (error.response) {
    console.error('服务器错误:', error.response.data);
  } else {
    console.error('请求失败:', error.message);
  }
});
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/cms/comments/3/approve/"
headers = {
    "Authorization": "Bearer your_jwt_token_here",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)
data = response.json()

if data['success']:
    print(f"评论批准成功: ID={data['data']['id']}, 状态={data['data']['status']}")
else:
    print(f"批准失败: {data['message']}")
```

### TypeScript (Fetch API)

```typescript
interface ApproveResponse {
  success: boolean;
  code: number;
  message: string;
  data: {
    message: string;
    id: number;
    status: string;
  } | null;
}

async function approveComment(commentId: number, token: string): Promise<void> {
  const url = `http://localhost:8000/api/v1/cms/comments/${commentId}/approve/`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data: ApproveResponse = await response.json();
    
    if (data.success && data.data) {
      console.log(`评论 ${data.data.id} 已批准`);
    } else {
      console.error(`批准失败: ${data.message}`);
    }
  } catch (error) {
    console.error('请求失败:', error);
  }
}

// 使用示例
approveComment(3, 'your_jwt_token_here');
```

---

## 注意事项

1. **幂等性**: 重复批准同一评论会返回 400 错误，提示"评论已经是批准状态"
2. **权限检查**: 系统会自动验证用户是否有权限批准该评论
3. **租户隔离**: 租户管理员只能批准本租户内的评论
4. **状态变更**: 批准操作会将评论状态从 `pending` 改为 `approved`
5. **文章计数**: 批准后会更新文章的评论计数

---

## 业务流程

1. 用户发起批准请求
2. 系统验证 JWT token 有效性
3. 系统检查用户是否有权限：
   - 超级管理员：通过
   - 租户管理员：检查评论是否属于本租户
   - 文章作者：检查是否为该文章作者
   - 普通成员：拒绝
4. 系统检查评论当前状态是否已批准
5. 更新评论状态为 `approved`
6. 更新文章的评论计数
7. 记录操作日志
8. 返回成功响应

---

[返回概述](./01_overview.md) | [下一页：拒绝评论](./03_reject_api.md)
