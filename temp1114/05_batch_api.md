# 批量操作评论接口

## 接口概述

批量处理多个评论，支持批准、拒绝、标记垃圾和删除操作。这个接口允许一次性处理多条评论，提高审核效率。

**接口地址**: `POST /cms/comments/batch/`

---

## 请求参数

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| Authorization | string | 是 | Bearer {token} |
| Content-Type | string | 是 | application/json |

### 请求体

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| comment_ids | array | 是 | 评论 ID 数组，如 [1, 2, 3] |
| action | string | 是 | 操作类型：`approve`、`reject`、`spam`、`delete` |

**请求体示例**:
```json
{
  "comment_ids": [37, 38, 39],
  "action": "approve"
}
```

### action 参数说明

| 值 | 说明 | 状态变更 |
|---|------|---------|
| approve | 批量批准评论 | pending → approved |
| reject | 批量拒绝评论 | pending → rejected |
| spam | 批量标记为垃圾评论 | any → spam |
| delete | 批量删除评论（软删除） | any → trash |

---

## 响应参数

### 成功响应 (200 OK)

#### 批量批准
```json
{
  "success": true,
  "code": 2000,
  "message": "评论批量批准成功",
  "data": {
    "message": "评论批量批准成功",
    "requested_count": 2,
    "processed_count": 2,
    "processed_ids": [37, 38]
  }
}
```

#### 批量拒绝
```json
{
  "success": true,
  "code": 2000,
  "message": "评论批量拒绝成功",
  "data": {
    "message": "评论批量拒绝成功",
    "requested_count": 1,
    "processed_count": 1,
    "processed_ids": [39]
  }
}
```

#### 批量标记垃圾
```json
{
  "success": true,
  "code": 2000,
  "message": "评论批量标记为垃圾成功",
  "data": {
    "message": "评论批量标记为垃圾成功",
    "requested_count": 1,
    "processed_count": 1,
    "processed_ids": [39]
  }
}
```

#### 批量删除
```json
{
  "success": true,
  "code": 2000,
  "message": "评论批量删除成功",
  "data": {
    "message": "评论批量删除成功",
    "requested_count": 2,
    "processed_count": 2,
    "processed_ids": [40, 41]
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| code | integer | 业务状态码 |
| message | string | 响应消息 |
| data.requested_count | integer | 请求处理的评论数量 |
| data.processed_count | integer | 实际成功处理的评论数量 |
| data.processed_ids | array | 成功处理的评论 ID 列表 |

**注意**: `processed_count` 可能小于 `requested_count`，因为用户可能没有权限操作某些评论。

---

## 错误响应

### 1. 缺少必填参数 (400 Bad Request)

```json
{
  "success": false,
  "code": 4000,
  "message": "缺少必填字段: comment_ids 和 action",
  "data": null
}
```

### 2. 无效的操作类型 (400 Bad Request)

```json
{
  "success": false,
  "code": 4000,
  "message": "无效的操作类型。允许的操作: approve, reject, spam, delete",
  "data": null
}
```

### 3. 无权限 (403 Forbidden)

```json
{
  "success": false,
  "code": 4030,
  "message": "普通成员没有权限进行此操作",
  "data": null
}
```

---

## 使用示例

### cURL - 批量批准

```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [37, 38],
    "action": "approve"
  }'
```

### cURL - 批量标记垃圾

```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [39, 40, 41],
    "action": "spam"
  }'
```

### cURL - 批量删除

```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [42, 43],
    "action": "delete"
  }'
```

### JavaScript (Fetch API)

```javascript
const token = 'your_jwt_token_here';
const commentIds = [37, 38, 39];
const action = 'approve';  // 或 'reject', 'spam', 'delete'

fetch('http://localhost:8000/api/v1/cms/comments/batch/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    comment_ids: commentIds,
    action: action
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`成功处理 ${data.data.processed_count}/${data.data.requested_count} 条评论`);
    console.log('处理的评论ID:', data.data.processed_ids);
  } else {
    console.error('批量操作失败:', data.message);
  }
})
.catch(error => console.error('请求失败:', error));
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const token = 'your_jwt_token_here';

async function batchApproveComments(commentIds) {
  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/cms/comments/batch/',
      {
        comment_ids: commentIds,
        action: 'approve'
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const data = response.data;
    console.log(`成功批准 ${data.data.processed_count} 条评论`);
    return data.data.processed_ids;
  } catch (error) {
    console.error('批量批准失败:', error.response?.data || error.message);
    throw error;
  }
}

// 使用示例
batchApproveComments([37, 38, 39]);
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/cms/comments/batch/"
headers = {
    "Authorization": "Bearer your_jwt_token_here",
    "Content-Type": "application/json"
}
payload = {
    "comment_ids": [37, 38, 39],
    "action": "approve"  # 或 'reject', 'spam', 'delete'
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()

if data['success']:
    print(f"成功处理 {data['data']['processed_count']}/{data['data']['requested_count']} 条评论")
    print(f"处理的评论ID: {data['data']['processed_ids']}")
else:
    print(f"批量操作失败: {data['message']}")
```

### TypeScript

```typescript
interface BatchActionRequest {
  comment_ids: number[];
  action: 'approve' | 'reject' | 'spam' | 'delete';
}

interface BatchActionResponse {
  success: boolean;
  code: number;
  message: string;
  data: {
    message: string;
    requested_count: number;
    processed_count: number;
    processed_ids: number[];
  } | null;
}

async function batchActionComments(
  commentIds: number[],
  action: BatchActionRequest['action'],
  token: string
): Promise<number[]> {
  const url = 'http://localhost:8000/api/v1/cms/comments/batch/';
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      comment_ids: commentIds,
      action: action
    })
  });
  
  const data: BatchActionResponse = await response.json();
  
  if (data.success && data.data) {
    console.log(`成功处理 ${data.data.processed_count}/${data.data.requested_count} 条评论`);
    return data.data.processed_ids;
  } else {
    throw new Error(data.message);
  }
}

// 使用示例
batchActionComments([37, 38, 39], 'approve', 'your_jwt_token_here')
  .then(ids => console.log('处理的ID:', ids))
  .catch(error => console.error('错误:', error));
```

---

## 权限说明

批量操作的权限规则与单个操作相同：

1. **超级管理员**: 可以批量操作所有租户的评论
2. **租户管理员**: 可以批量操作本租户内的评论
3. **文章作者（管理员）**: 可以批量操作自己文章下的评论
4. **普通成员**: 无权限

**重要**: 如果请求的评论列表中包含用户无权操作的评论，这些评论会被自动跳过，`processed_count` 将小于 `requested_count`。

---

## 注意事项

1. **部分成功**: 批量操作可能部分成功。检查 `processed_count` 和 `processed_ids` 确认实际处理的评论
2. **权限过滤**: 系统会自动过滤掉用户无权操作的评论，不会返回错误
3. **性能**: 建议每次批量操作不超过 100 条评论
4. **事务**: 每条评论的操作是独立的，某条失败不影响其他评论
5. **日志记录**: 每条评论的操作都会记录在操作日志中

---

## 使用场景

### 场景 1: 批量审核待审评论

```javascript
// 获取所有待审核评论ID
const pendingCommentIds = [1, 2, 3, 4, 5];

// 全部批准
batchActionComments(pendingCommentIds, 'approve', token);
```

### 场景 2: 清理垃圾评论

```javascript
// 标记多条评论为垃圾
const spamIds = [10, 11, 12];
batchActionComments(spamIds, 'spam', token);
```

### 场景 3: 批量删除违规评论

```javascript
// 删除违规评论
const violationIds = [20, 21, 22];
batchActionComments(violationIds, 'delete', token);
```

---

[返回概述](./01_overview.md) | [上一页：标记垃圾](./04_mark_spam_api.md) | [下一页：查询评论](./06_query_api.md)
