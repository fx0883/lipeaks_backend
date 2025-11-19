# 查询评论接口

## 接口概述

获取评论列表，支持按状态、文章等条件筛选，支持分页。管理员可以查看所有状态的评论，包括待审核的评论。

**接口地址**: `GET /cms/comments/`

---

## 请求参数

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| Authorization | string | 是 | Bearer {token} |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|-------|------|------|------|------|
| status | string | 否 | 评论状态筛选 | `pending`、`approved`、`spam`、`rejected`、`trash` |
| article | integer | 否 | 文章 ID，筛选特定文章的评论 | `10247` |
| page | integer | 否 | 页码，默认为 1 | `1` |
| page_size | integer | 否 | 每页数量，默认为 10，最大 100 | `20` |
| has_parent | string | 否 | 筛选一级评论或回复 | `false`（一级评论）、`true`（回复） |
| ordering | string | 否 | 排序方式 | `-created_at`（时间倒序）、`created_at`（时间正序） |

### 状态参数说明

| 值 | 说明 | 可见性 |
|---|------|--------|
| pending | 待审核 | 仅管理员可见 |
| approved | 已批准 | 所有用户可见 |
| spam | 垃圾评论 | 仅管理员可见 |
| rejected | 已拒绝 | 仅管理员可见 |
| trash | 已删除 | 仅管理员可见 |

---

## 响应参数

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 15,
      "next": "http://localhost:8000/api/v1/cms/comments/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 2
    },
    "results": [
      {
        "id": 3,
        "article": 10247,
        "parent": null,
        "user": null,
        "member": null,
        "author_info": {
          "name": "测试游客",
          "email": "guest@example.com",
          "website": null,
          "type": "guest"
        },
        "author_type": "guest",
        "guest_name": "测试游客",
        "guest_email": "guest@example.com",
        "guest_website": null,
        "content": "这是游客的测试评论",
        "status": "pending",
        "ip_address": "127.0.0.1",
        "user_agent": "curl/8.7.1",
        "created_at": "2025-11-13T02:48:39.207993Z",
        "updated_at": "2025-11-13T02:48:39.208009Z",
        "is_pinned": false,
        "likes_count": 0,
        "tenant": 1,
        "replies_count": 0
      }
    ]
  }
}
```

### 响应字段说明

#### 分页信息 (pagination)

| 字段 | 类型 | 说明 |
|------|------|------|
| count | integer | 总记录数 |
| next | string/null | 下一页 URL，最后一页时为 null |
| previous | string/null | 上一页 URL，第一页时为 null |
| page_size | integer | 每页记录数 |
| current_page | integer | 当前页码 |
| total_pages | integer | 总页数 |

#### 评论对象 (results[])

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 评论 ID |
| article | integer | 文章 ID |
| parent | integer/null | 父评论 ID，一级评论时为 null |
| user | integer/null | 管理员用户 ID（如果是管理员评论） |
| member | integer/null | 成员用户 ID（如果是成员评论） |
| author_info | object | 作者信息对象 |
| author_info.name | string | 作者显示名称 |
| author_info.email | string | 作者邮箱 |
| author_info.website | string/null | 作者网站（仅游客） |
| author_info.type | string | 作者类型：`guest`、`member`、`admin` |
| author_type | string | 作者类型简化版 |
| guest_name | string/null | 游客名称 |
| guest_email | string/null | 游客邮箱 |
| guest_website | string/null | 游客网站 |
| content | string | 评论内容 |
| status | string | 评论状态 |
| ip_address | string | IP 地址 |
| user_agent | string | 用户代理 |
| created_at | string | 创建时间（ISO 8601） |
| updated_at | string | 更新时间（ISO 8601） |
| is_pinned | boolean | 是否置顶 |
| likes_count | integer | 点赞数 |
| tenant | integer | 租户 ID |
| replies_count | integer | 回复数量 |

---

## 使用示例

### cURL - 查询待审核评论

```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?status=pending" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### cURL - 查询特定文章的待审核评论

```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?status=pending&article=10247" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### cURL - 分页查询

```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?status=pending&page=2&page_size=20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### cURL - 查询一级评论（非回复）

```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?has_parent=false&article=10247" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### JavaScript (Fetch API)

```javascript
const token = 'your_jwt_token_here';

// 构建查询参数
const params = new URLSearchParams({
  status: 'pending',
  article: '10247',
  page: '1',
  page_size: '10'
});

fetch(`http://localhost:8000/api/v1/cms/comments/?${params}`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`找到 ${data.data.pagination.count} 条待审核评论`);
    
    data.data.results.forEach(comment => {
      console.log(`评论 ${comment.id}: ${comment.content}`);
      console.log(`  作者: ${comment.author_info.name}`);
      console.log(`  状态: ${comment.status}`);
      console.log(`  时间: ${comment.created_at}`);
    });
    
    // 处理分页
    if (data.data.pagination.next) {
      console.log('还有更多评论...');
    }
  } else {
    console.error('查询失败:', data.message);
  }
})
.catch(error => console.error('请求失败:', error));
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const token = 'your_jwt_token_here';

async function fetchPendingComments(articleId, page = 1, pageSize = 10) {
  try {
    const response = await axios.get('http://localhost:8000/api/v1/cms/comments/', {
      params: {
        status: 'pending',
        article: articleId,
        page: page,
        page_size: pageSize
      },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = response.data;
    return {
      comments: data.data.results,
      pagination: data.data.pagination
    };
  } catch (error) {
    console.error('获取评论失败:', error.response?.data || error.message);
    throw error;
  }
}

// 使用示例
fetchPendingComments(10247, 1, 10)
  .then(result => {
    console.log(`共 ${result.pagination.count} 条评论`);
    result.comments.forEach(comment => {
      console.log(`${comment.id}: ${comment.content}`);
    });
  });
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/cms/comments/"
headers = {
    "Authorization": "Bearer your_jwt_token_here"
}
params = {
    "status": "pending",
    "article": 10247,
    "page": 1,
    "page_size": 10
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

if data['success']:
    pagination = data['data']['pagination']
    print(f"找到 {pagination['count']} 条待审核评论")
    print(f"第 {pagination['current_page']}/{pagination['total_pages']} 页")
    
    for comment in data['data']['results']:
        print(f"\n评论 {comment['id']}:")
        print(f"  作者: {comment['author_info']['name']}")
        print(f"  内容: {comment['content']}")
        print(f"  状态: {comment['status']}")
        print(f"  时间: {comment['created_at']}")
else:
    print(f"查询失败: {data['message']}")
```

### TypeScript

```typescript
interface Comment {
  id: number;
  article: number;
  parent: number | null;
  author_info: {
    name: string;
    email: string;
    website: string | null;
    type: 'guest' | 'member' | 'admin';
  };
  content: string;
  status: 'pending' | 'approved' | 'spam' | 'rejected' | 'trash';
  created_at: string;
  updated_at: string;
  replies_count: number;
}

interface CommentsResponse {
  success: boolean;
  code: number;
  message: string;
  data: {
    pagination: {
      count: number;
      next: string | null;
      previous: string | null;
      page_size: number;
      current_page: number;
      total_pages: number;
    };
    results: Comment[];
  };
}

async function fetchComments(
  token: string,
  filters: {
    status?: string;
    article?: number;
    page?: number;
    page_size?: number;
  } = {}
): Promise<CommentsResponse['data']> {
  const params = new URLSearchParams();
  
  if (filters.status) params.append('status', filters.status);
  if (filters.article) params.append('article', filters.article.toString());
  if (filters.page) params.append('page', filters.page.toString());
  if (filters.page_size) params.append('page_size', filters.page_size.toString());
  
  const url = `http://localhost:8000/api/v1/cms/comments/?${params}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data: CommentsResponse = await response.json();
  
  if (data.success) {
    return data.data;
  } else {
    throw new Error(data.message);
  }
}

// 使用示例
fetchComments('your_token', { status: 'pending', article: 10247 })
  .then(data => {
    console.log(`找到 ${data.pagination.count} 条评论`);
    data.results.forEach(comment => {
      console.log(`${comment.id}: ${comment.content}`);
    });
  })
  .catch(error => console.error('错误:', error));
```

---

## 使用场景

### 场景 1: 获取待审核评论列表

用于管理后台的评论审核页面。

```javascript
fetchComments(token, {
  status: 'pending',
  page: 1,
  page_size: 20
});
```

### 场景 2: 获取特定文章的所有评论

用于文章详情页显示评论。

```javascript
fetchComments(token, {
  article: 10247,
  status: 'approved',  // 只显示已批准的评论
  has_parent: 'false'  // 只获取一级评论
});
```

### 场景 3: 分页加载评论

实现无限滚动或分页功能。

```javascript
async function loadMoreComments(currentPage) {
  const data = await fetchComments(token, {
    status: 'approved',
    page: currentPage + 1,
    page_size: 10
  });
  
  // 将评论添加到列表
  appendCommentsToUI(data.results);
  
  // 检查是否还有更多
  if (data.pagination.next) {
    showLoadMoreButton();
  } else {
    hideLoadMoreButton();
  }
}
```

---

## 注意事项

1. **权限影响**: 
   - 管理员可以查看所有状态的评论
   - 普通用户只能查看已批准（`approved`）的评论

2. **租户隔离**: 
   - 租户管理员只能查看本租户的评论
   - 超级管理员可以查看所有租户的评论

3. **性能优化**: 
   - 建议使用分页，避免一次性加载过多评论
   - 默认按创建时间倒序排列（最新的在前）

4. **回复评论**: 
   - 一级评论的 `parent` 字段为 `null`
   - 回复评论的 `parent` 字段为父评论的 ID
   - 使用 `has_parent` 参数可以只获取一级评论或回复

---

[返回概述](./01_overview.md) | [上一页：批量操作](./05_batch_api.md) | [下一页：工作流示例](./07_workflow_examples.md)
