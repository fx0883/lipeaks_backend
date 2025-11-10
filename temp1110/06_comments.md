# 6. 评论系统 API 集成指南

## 🎯 概述

评论系统提供完整的文章评论功能，包括发表评论、回复评论、管理评论等。支持层级评论结构（父子关系）、评论审核、评论统计等高级功能。

## 📋 API 列表

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取文章评论列表](#获取文章评论列表) | GET | `/cms/comments/` | 获取文章的评论列表 |
| [获取单条评论详情](#获取单条评论详情) | GET | `/cms/comments/{id}/` | 获取单条评论详情 |
| [发表评论](#发表评论) | POST | `/cms/comments/` | 为文章发表新评论 |
| [回复评论](#回复评论) | POST | `/cms/comments/{id}/replies/` | 回复指定的评论 |
| [更新评论](#更新评论) | PUT/PATCH | `/cms/comments/{id}/` | 更新自己的评论 |
| [删除评论](#删除评论) | DELETE | `/cms/comments/{id}/` | 删除评论（软删除） |
| [获取评论回复](#获取评论回复) | GET | `/cms/comments/{id}/replies/` | 获取评论的所有回复 |
| [点赞评论](#点赞评论) | POST | `/cms/comments/{id}/like/` | 点赞评论 |
| [取消点赞评论](#取消点赞评论) | DELETE | `/cms/comments/{id}/like/` | 取消点赞评论 |
| [举报评论](#举报评论) | POST | `/cms/comments/{id}/report/` | 举报不当评论 |
| [审核评论](#审核评论) | POST | `/cms/comments/{id}/moderate/` | 管理员审核评论 |

---

## 获取文章评论列表

### 接口信息
- **接口地址**: `GET /api/v1/cms/comments/`
- **权限要求**: 无需认证，公开访问（根据文章权限控制）
- **功能说明**: 获取指定文章的所有评论，支持分页和筛选

### 请求头（可选）
```bash
X-Tenant-ID: {tenant_id}  # 按租户过滤
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| article | integer | 是 | 文章ID | 42 | 有效的文章ID |
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大50 | 20 | 1-50之间的整数 |
| parent | integer | 否 | 只显示顶级评论（不传值）或指定父评论的回复 | null | 有效的评论ID |
| status | string | 否 | 评论状态筛选 | "approved" | approved/pending/rejected/spam |
| ordering | string | 否 | 排序方式 | "-created_at" | created_at/-created_at/likes_count/-likes_count |
| include_replies | boolean | 否 | 是否包含回复，默认false | true | true/false |

### 使用示例

#### cURL 命令 - 获取文章评论
```bash
curl -X GET "https://your-domain.com/api/v1/cms/comments/?article=42&page=1&page_size=20&ordering=-created_at" \
  -H "X-Tenant-ID: 1"
```

#### cURL 命令 - 获取顶级评论（不含回复）
```bash
curl -X GET "https://your-domain.com/api/v1/cms/comments/?article=42&parent=null&page=1" \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取文章评论
```javascript
const getArticleComments = async (articleId, params = {}) => {
  const queryParams = new URLSearchParams({
    article: articleId,
    page: params.page || 1,
    page_size: params.pageSize || 20,
    parent: params.parent || '',  // 空字符串表示顶级评论
    status: params.status || 'approved',
    ordering: params.ordering || '-created_at',
    include_replies: params.includeReplies ? 'true' : 'false'
  });

  // 过滤空参数
  for (const [key, value] of queryParams.entries()) {
    if (!value && value !== 'false') {
      queryParams.delete(key);
    }
  }

  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/comments/?${queryParams}`, {
      method: 'GET',
      headers: {
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('文章评论:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取文章评论失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 25,
    "next": "https://your-domain.com/api/v1/cms/comments/?article=42&page=2&page_size=20",
    "previous": null,
    "results": [
      {
        "id": 123,
        "content": "这篇文章写得很好，很有帮助！",
        "content_type": "text",
        "status": "approved",
        "is_approved": true,
        "parent": null,
        "article": 42,
        "author_info": {
          "id": 5,
          "username": "member001",
          "nick_name": "技术爱好者",
          "avatar": "/media/avatars/avatar_5.jpg",
          "is_member": true
        },
        "likes_count": 8,
        "replies_count": 3,
        "is_liked_by_user": false,
        "created_at": "2024-01-20T14:30:00Z",
        "updated_at": "2024-01-20T14:30:00Z",
        "replies": [
          {
            "id": 124,
            "content": "同意楼上的观点！",
            "content_type": "text",
            "status": "approved",
            "is_approved": true,
            "parent": 123,
            "article": 42,
            "author_info": {
              "id": 8,
              "username": "member002",
              "nick_name": "学习者",
              "avatar": "/media/avatars/avatar_8.jpg",
              "is_member": true
            },
            "likes_count": 2,
            "replies_count": 0,
            "is_liked_by_user": true,
            "created_at": "2024-01-20T14:45:00Z",
            "updated_at": "2024-01-20T14:45:00Z"
          }
        ]
      }
    ]
  }
}
```

---

## 发表评论

### 接口信息
- **接口地址**: `POST /api/v1/cms/comments/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 为指定文章发表新评论

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| article | integer | 是 | 评论所属文章ID | 42 | 有效的文章ID，必须已发布且允许评论 |
| content | string | 是 | 评论内容 | "这篇文章写得很好！" | 1-1000字符 |
| content_type | string | 否 | 内容类型 | "text" | text/markdown/html，默认text |
| parent | integer | 否 | 父评论ID（用于回复） | 123 | 有效的评论ID |

### 使用示例

#### cURL 命令 - 发表评论
```bash
curl -X POST "https://your-domain.com/api/v1/cms/comments/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 42,
    "content": "这篇文章写得很好，很有帮助！",
    "content_type": "text"
  }'
```

#### JavaScript 发表评论
```javascript
const postComment = async (articleId, content, options = {}) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/cms/comments/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        article: articleId,
        content: content,
        content_type: options.contentType || 'text',
        parent: options.parentId || null
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('评论发表成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('发表评论失败:', error);
    throw error;
  }
};

// 使用示例
const commentForm = document.getElementById('comment-form');
commentForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const content = document.getElementById('comment-content').value.trim();
  const articleId = parseInt(commentForm.dataset.articleId);

  if (!content) {
    alert('请输入评论内容');
    return;
  }

  try {
    const newComment = await postComment(articleId, content);
    // 重新加载评论列表
    loadComments(articleId);
    // 清空表单
    document.getElementById('comment-content').value = '';
    showToast('评论发表成功');
  } catch (error) {
    showToast('评论发表失败: ' + error.message, 'error');
  }
});
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "评论发表成功",
  "data": {
    "id": 125,
    "content": "这篇文章写得很好，很有帮助！",
    "content_type": "text",
    "status": "approved",
    "is_approved": true,
    "parent": null,
    "article": 42,
    "author_info": {
      "id": 5,
      "username": "member001",
      "nick_name": "技术爱好者",
      "avatar": "/media/avatars/avatar_5.jpg",
      "is_member": true
    },
    "likes_count": 0,
    "replies_count": 0,
    "is_liked_by_user": false,
    "created_at": "2024-01-21T09:15:00Z",
    "updated_at": "2024-01-21T09:15:00Z"
  }
}
```

---

## 回复评论

### 接口信息
- **接口地址**: `POST /api/v1/cms/comments/{id}/replies/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 回复指定的评论

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 被回复的评论ID | 123 | 有效的评论ID |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| content | string | 是 | 回复内容 | "谢谢您的建议！" | 1-1000字符 |
| content_type | string | 否 | 内容类型 | "text" | text/markdown/html，默认text |

### 使用示例

#### cURL 命令 - 回复评论
```bash
curl -X POST "https://your-domain.com/api/v1/cms/comments/123/replies/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "谢谢您的建议！我会尝试一下。",
    "content_type": "text"
  }'
```

#### JavaScript 回复评论
```javascript
const replyToComment = async (commentId, content, options = {}) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/comments/${commentId}/replies/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: content,
        content_type: options.contentType || 'text'
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('回复发表成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('回复评论失败:', error);
    throw error;
  }
};

// 使用示例
const replyButtons = document.querySelectorAll('.reply-btn');
replyButtons.forEach(btn => {
  btn.addEventListener('click', (e) => {
    const commentId = parseInt(btn.dataset.commentId);
    const replyForm = createReplyForm(commentId);

    // 在评论下方插入回复表单
    const commentElement = btn.closest('.comment-item');
    commentElement.appendChild(replyForm);
  });
});

function createReplyForm(commentId) {
  const form = document.createElement('form');
  form.className = 'reply-form';
  form.innerHTML = `
    <textarea placeholder="写下你的回复..." required></textarea>
    <div class="form-actions">
      <button type="submit">发表回复</button>
      <button type="button" class="cancel-btn">取消</button>
    </div>
  `;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const textarea = form.querySelector('textarea');
    const content = textarea.value.trim();

    if (!content) return;

    try {
      await replyToComment(commentId, content);
      form.remove(); // 移除表单
      // 重新加载评论
      loadComments();
    } catch (error) {
      alert('回复失败: ' + error.message);
    }
  });

  form.querySelector('.cancel-btn').addEventListener('click', () => {
    form.remove();
  });

  return form;
}
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "回复发表成功",
  "data": {
    "id": 126,
    "content": "谢谢您的建议！我会尝试一下。",
    "content_type": "text",
    "status": "approved",
    "is_approved": true,
    "parent": 123,
    "article": 42,
    "author_info": {
      "id": 5,
      "username": "member001",
      "nick_name": "技术爱好者",
      "avatar": "/media/avatars/avatar_5.jpg",
      "is_member": true
    },
    "likes_count": 0,
    "replies_count": 0,
    "is_liked_by_user": false,
    "created_at": "2024-01-21T09:30:00Z",
    "updated_at": "2024-01-21T09:30:00Z"
  }
}
```

---

## 点赞评论

### 接口信息
- **接口地址**: `POST /api/v1/cms/comments/{id}/like/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 点赞指定的评论

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| id | integer | 是 | 评论ID | 123 | 有效的评论ID |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/cms/comments/123/like/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 点赞评论
```javascript
const likeComment = async (commentId) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/comments/${commentId}/like/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    if (response.status === 201) {
      console.log('点赞成功');
      // 更新UI
      updateCommentLikeStatus(commentId, true);
      return true;
    } else {
      const result = await response.json();
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('点赞失败:', error);
    throw error;
  }
};
```

### 成功响应
```http
HTTP/1.1 201 Created
```

---

## 审核评论

### 接口信息
- **接口地址**: `POST /api/v1/cms/comments/{id}/moderate/`
- **权限要求**: 需要管理员权限
- **功能说明**: 管理员审核评论状态

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| id | integer | 是 | 评论ID | 123 | 有效的评论ID |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|------|----------|
| action | string | 是 | 审核动作 | "approve" | approve/reject/spam |
| reason | string | 否 | 审核理由 | "内容不适当" | 最长255字符 |

### 使用示例

#### cURL 命令 - 通过评论
```bash
curl -X POST "https://your-domain.com/api/v1/cms/comments/123/moderate/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve"
  }'
```

#### cURL 命令 - 拒绝评论
```bash
curl -X POST "https://your-domain.com/api/v1/cms/comments/124/moderate/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "reason": "包含不当内容"
  }'
```

#### JavaScript 审核评论
```javascript
const moderateComment = async (commentId, action, reason = '') => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/comments/${commentId}/moderate/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: action,
        reason: reason
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('评论审核成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('审核评论失败:', error);
    throw error;
  }
};

// 使用示例 - 批量审核
const bulkModerate = async (commentIds, action) => {
  const results = [];

  for (const commentId of commentIds) {
    try {
      const result = await moderateComment(commentId, action);
      results.push({ id: commentId, success: true, data: result });
    } catch (error) {
      results.push({ id: commentId, success: false, error: error.message });
    }
  }

  return results;
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "评论审核成功",
  "data": {
    "id": 123,
    "status": "approved",
    "moderated_by": {
      "id": 1,
      "username": "admin",
      "nick_name": "管理员"
    },
    "moderated_at": "2024-01-21T10:00:00Z",
    "moderation_reason": ""
  }
}
```

---

## 🔧 前端集成最佳实践

### 1. 评论列表组件
```javascript
class CommentList {
  constructor(container, articleId, options = {}) {
    this.container = container;
    this.articleId = articleId;
    this.options = {
      pageSize: 20,
      maxDepth: 3,
      showReplies: true,
      allowLikes: true,
      allowReplies: true,
      ...options
    };

    this.comments = [];
    this.currentPage = 1;
    this.loading = false;

    this.init();
  }

  async init() {
    await this.loadComments();
    this.render();
    this.bindEvents();
  }

  async loadComments(page = 1) {
    if (this.loading) return;

    this.loading = true;
    this.showLoading();

    try {
      const params = new URLSearchParams({
        article: this.articleId,
        page: page,
        page_size: this.options.pageSize,
        ordering: '-created_at',
        include_replies: this.options.showReplies ? 'true' : 'false'
      });

      const response = await fetch(`/api/v1/cms/comments/?${params}`, {
        headers: {
          'X-Tenant-ID': '1'
        }
      });

      const result = await response.json();

      if (result.success) {
        if (page === 1) {
          this.comments = result.data.results;
        } else {
          this.comments = [...this.comments, ...result.data.results];
        }

        this.currentPage = page;
        this.hasNextPage = !!result.data.next;

        this.render();
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('加载评论失败:', error);
      this.showError(error.message);
    } finally {
      this.loading = false;
      this.hideLoading();
    }
  }

  render() {
    const html = this.comments.map(comment => this.renderComment(comment)).join('');
    this.container.innerHTML = html;

    // 添加加载更多按钮
    if (this.hasNextPage) {
      const loadMoreBtn = document.createElement('button');
      loadMoreBtn.className = 'load-more-btn';
      loadMoreBtn.textContent = '加载更多评论';
      loadMoreBtn.addEventListener('click', () => {
        this.loadComments(this.currentPage + 1);
      });
      this.container.appendChild(loadMoreBtn);
    }
  }

  renderComment(comment, depth = 0) {
    const indentClass = depth > 0 ? `comment-reply depth-${depth}` : 'comment-item';
    const likedClass = comment.is_liked_by_user ? 'liked' : '';

    let html = `
      <div class="${indentClass}" data-id="${comment.id}">
        <div class="comment-header">
          <div class="comment-author">
            <img src="${comment.author_info.avatar || '/static/images/default-avatar.png'}"
                 alt="${comment.author_info.nick_name}" class="avatar">
            <span class="author-name">${comment.author_info.nick_name}</span>
          </div>
          <div class="comment-meta">
            <span class="comment-time">${this.formatTime(comment.created_at)}</span>
            ${comment.status !== 'approved' ?
              `<span class="comment-status status-${comment.status}">${this.getStatusText(comment.status)}</span>` : ''}
          </div>
        </div>

        <div class="comment-content">
          ${this.formatContent(comment.content, comment.content_type)}
        </div>

        <div class="comment-actions">
          ${this.options.allowLikes ? `
            <button class="like-btn ${likedClass}" data-id="${comment.id}">
              👍 ${comment.likes_count}
            </button>
          ` : ''}

          ${this.options.allowReplies && depth < this.options.maxDepth ? `
            <button class="reply-btn" data-id="${comment.id}">回复</button>
          ` : ''}

          ${comment.replies_count > 0 ? `
            <button class="toggle-replies-btn" data-id="${comment.id}">
              ${comment.showing_replies ? '收起回复' : `查看${comment.replies_count}条回复`}
            </button>
          ` : ''}
        </div>
      </div>
    `;

    // 渲染回复
    if (comment.replies && comment.replies.length > 0 && comment.showing_replies) {
      html += '<div class="comment-replies">';
      comment.replies.forEach(reply => {
        html += this.renderComment(reply, depth + 1);
      });
      html += '</div>';
    }

    return html;
  }

  formatContent(content, type) {
    // 根据内容类型格式化
    if (type === 'markdown') {
      return this.markdownToHtml(content);
    } else if (type === 'html') {
      return content; // 假设后端已过滤HTML
    } else {
      return content.replace(/\n/g, '<br>');
    }
  }

  markdownToHtml(markdown) {
    // 简化的markdown转换
    return markdown
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  formatTime(timeString) {
    const date = new Date(timeString);
    const now = new Date();
    const diff = now - date;

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 30) return `${days}天前`;

    return date.toLocaleDateString('zh-CN');
  }

  getStatusText(status) {
    const statusMap = {
      'approved': '已通过',
      'pending': '待审核',
      'rejected': '已拒绝',
      'spam': '垃圾评论'
    };
    return statusMap[status] || status;
  }

  bindEvents() {
    this.container.addEventListener('click', async (e) => {
      const commentId = e.target.dataset.id;

      if (e.target.classList.contains('like-btn')) {
        await this.handleLike(commentId, e.target);
      } else if (e.target.classList.contains('reply-btn')) {
        this.showReplyForm(commentId, e.target);
      } else if (e.target.classList.contains('toggle-replies-btn')) {
        this.toggleReplies(commentId, e.target);
      }
    });
  }

  async handleLike(commentId, button) {
    try {
      const isLiked = button.classList.contains('liked');

      if (isLiked) {
        // 取消点赞
        const response = await fetch(`/api/v1/cms/comments/${commentId}/like/`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'X-Tenant-ID': '1'
          }
        });

        if (response.status === 204) {
          button.classList.remove('liked');
          const count = parseInt(button.textContent.match(/\d+/)[0]) - 1;
          button.innerHTML = `👍 ${count}`;
        }
      } else {
        // 点赞
        const response = await fetch(`/api/v1/cms/comments/${commentId}/like/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'X-Tenant-ID': '1'
          }
        });

        if (response.status === 201) {
          button.classList.add('liked');
          const count = parseInt(button.textContent.match(/\d+/)[0]) + 1;
          button.innerHTML = `👍 ${count}`;
        }
      }
    } catch (error) {
      console.error('点赞操作失败:', error);
    }
  }

  showReplyForm(commentId, button) {
    // 移除现有的回复表单
    const existingForm = this.container.querySelector('.reply-form');
    if (existingForm) {
      existingForm.remove();
    }

    const commentElement = button.closest('.comment-item, .comment-reply');
    const form = this.createReplyForm(commentId);
    commentElement.appendChild(form);
  }

  createReplyForm(commentId) {
    const form = document.createElement('form');
    form.className = 'reply-form';
    form.innerHTML = `
      <div class="form-group">
        <textarea placeholder="写下你的回复..." required maxlength="1000"></textarea>
      </div>
      <div class="form-actions">
        <button type="submit">发表回复</button>
        <button type="button" class="cancel-btn">取消</button>
      </div>
    `;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const textarea = form.querySelector('textarea');
      const content = textarea.value.trim();

      if (!content) return;

      try {
        await replyToComment(commentId, content);
        form.remove();
        // 重新加载评论
        await this.loadComments(1);
      } catch (error) {
        alert('回复失败: ' + error.message);
      }
    });

    form.querySelector('.cancel-btn').addEventListener('click', () => {
      form.remove();
    });

    return form;
  }

  toggleReplies(commentId, button) {
    const comment = this.comments.find(c => c.id.toString() === commentId);
    if (!comment) return;

    comment.showing_replies = !comment.showing_replies;
    button.textContent = comment.showing_replies ?
      '收起回复' : `查看${comment.replies_count}条回复`;

    this.render();
  }

  showLoading() {
    // 显示加载状态
  }

  hideLoading() {
    // 隐藏加载状态
  }

  showError(message) {
    this.container.innerHTML = `<div class="error">加载失败: ${message}</div>`;
  }

  // 刷新评论列表
  async refresh() {
    this.comments = [];
    this.currentPage = 1;
    await this.loadComments(1);
  }
}

// 使用示例
document.addEventListener('DOMContentLoaded', () => {
  const articleId = parseInt(document.getElementById('article').dataset.id);
  const commentList = new CommentList(
    document.getElementById('comment-list'),
    articleId,
    {
      pageSize: 20,
      maxDepth: 3,
      showReplies: true,
      allowLikes: true,
      allowReplies: true
    }
  );

  // 发表新评论后刷新列表
  window.addEventListener('commentPosted', () => {
    commentList.refresh();
  });
});
```

### 2. 评论表单组件
```javascript
class CommentForm {
  constructor(formElement, articleId, options = {}) {
    this.form = formElement;
    this.articleId = articleId;
    this.options = {
      maxLength: 1000,
      placeholder: '写下你的评论...',
      submitText: '发表评论',
      ...options
    };

    this.init();
  }

  init() {
    this.setupForm();
    this.bindEvents();
  }

  setupForm() {
    this.form.innerHTML = `
      <div class="comment-form-group">
        <textarea
          name="content"
          placeholder="${this.options.placeholder}"
          maxlength="${this.options.maxLength}"
          required
        ></textarea>
        <div class="char-counter">
          <span class="current-count">0</span>/${this.options.maxLength}
        </div>
      </div>
      <div class="comment-form-actions">
        <button type="submit" class="submit-btn">${this.options.submitText}</button>
        ${this.options.showCancel ? '<button type="button" class="cancel-btn">取消</button>' : ''}
      </div>
    `;
  }

  bindEvents() {
    const textarea = this.form.querySelector('textarea');

    // 字符计数
    textarea.addEventListener('input', (e) => {
      const count = e.target.value.length;
      this.form.querySelector('.current-count').textContent = count;

      // 字符数接近限制时高亮
      if (count > this.options.maxLength * 0.9) {
        this.form.querySelector('.char-counter').classList.add('warning');
      } else {
        this.form.querySelector('.char-counter').classList.remove('warning');
      }
    });

    // 表单提交
    this.form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.submitComment();
    });

    // 取消按钮
    const cancelBtn = this.form.querySelector('.cancel-btn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        this.onCancel();
      });
    }
  }

  async submitComment() {
    const textarea = this.form.querySelector('textarea');
    const content = textarea.value.trim();

    if (!content) {
      alert('请输入评论内容');
      return;
    }

    if (content.length > this.options.maxLength) {
      alert(`评论内容不能超过${this.options.maxLength}字符`);
      return;
    }

    const submitBtn = this.form.querySelector('.submit-btn');
    const originalText = submitBtn.textContent;

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = '发表中...';

      const response = await fetch('/api/v1/cms/comments/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'X-Tenant-ID': '1',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          article: this.articleId,
          content: content,
          content_type: 'text'
        })
      });

      const result = await response.json();

      if (result.success) {
        // 清空表单
        textarea.value = '';
        this.form.querySelector('.current-count').textContent = '0';

        // 触发事件通知其他组件
        window.dispatchEvent(new CustomEvent('commentPosted', {
          detail: { comment: result.data }
        }));

        showToast('评论发表成功');
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('发表评论失败:', error);
      showToast('评论发表失败: ' + error.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  }

  onCancel() {
    // 清空表单
    const textarea = this.form.querySelector('textarea');
    textarea.value = '';
    this.form.querySelector('.current-count').textContent = '0';

    // 触发取消事件
    this.form.dispatchEvent(new CustomEvent('commentCancelled'));
  }

  // 设置回复模式
  setReplyMode(parentCommentId, authorName) {
    const textarea = this.form.querySelector('textarea');
    textarea.placeholder = `回复 @${authorName}...`;
    this.form.querySelector('.submit-btn').textContent = '发表回复';

    // 存储父评论ID
    this.parentCommentId = parentCommentId;
  }

  // 重置为普通评论模式
  resetToCommentMode() {
    const textarea = this.form.querySelector('textarea');
    textarea.placeholder = this.options.placeholder;
    this.form.querySelector('.submit-btn').textContent = this.options.submitText;
    this.parentCommentId = null;
  }
}

// 使用示例
document.addEventListener('DOMContentLoaded', () => {
  const articleId = parseInt(document.getElementById('article').dataset.id);
  const commentForm = new CommentForm(
    document.getElementById('main-comment-form'),
    articleId,
    {
      maxLength: 1000,
      placeholder: '写下你的评论...',
      submitText: '发表评论'
    }
  );
});
```
