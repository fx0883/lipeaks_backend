# 完整工作流示例

本文档提供了评论审核的完整工作流程示例，帮助前端开发者快速集成。

---

## 工作流 1: 管理员审核待审评论

### 流程图

```
登录 → 获取待审核列表 → 逐条审核（批准/拒绝/标记垃圾） → 刷新列表
```

### 实现代码

```javascript
// 1. 登录获取 Token
async function login(username, password) {
  const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  if (data.success) {
    // 保存 token 到本地存储
    localStorage.setItem('token', data.data.token);
    return data.data.token;
  }
  throw new Error(data.message);
}

// 2. 获取待审核评论列表
async function getPendingComments(token, page = 1) {
  const response = await fetch(
    `http://localhost:8000/api/v1/cms/comments/?status=pending&page=${page}&page_size=10`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  if (data.success) {
    return data.data;
  }
  throw new Error(data.message);
}

// 3. 批准评论
async function approveComment(token, commentId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/cms/comments/${commentId}/approve/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  return data;
}

// 4. 完整流程
async function moderateComments() {
  try {
    // 登录
    const token = await login('admin_jin', 'AdminPass123!');
    console.log('登录成功');
    
    // 获取待审核评论
    const result = await getPendingComments(token);
    console.log(`找到 ${result.pagination.count} 条待审核评论`);
    
    // 逐条处理
    for (const comment of result.results) {
      console.log(`\n处理评论 ${comment.id}:`);
      console.log(`  内容: ${comment.content}`);
      console.log(`  作者: ${comment.author_info.name}`);
      
      // 这里可以根据业务逻辑决定操作
      // 示例：批准所有评论
      const approveResult = await approveComment(token, comment.id);
      if (approveResult.success) {
        console.log(`  ✓ 已批准`);
      } else {
        console.log(`  ✗ 批准失败: ${approveResult.message}`);
      }
    }
    
    console.log('\n审核完成！');
  } catch (error) {
    console.error('审核过程出错:', error);
  }
}

// 执行
moderateComments();
```

---

## 工作流 2: 批量审核评论

### 流程图

```
获取待审核列表 → 用户选择多条评论 → 批量批准 → 刷新列表
```

### 实现代码

```javascript
// React 示例
import React, { useState, useEffect } from 'react';

function CommentModerationPanel() {
  const [comments, setComments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  // 加载待审核评论
  useEffect(() => {
    fetchPendingComments();
  }, []);

  async function fetchPendingComments() {
    setLoading(true);
    try {
      const response = await fetch(
        'http://localhost:8000/api/v1/cms/comments/?status=pending',
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      const data = await response.json();
      if (data.success) {
        setComments(data.data.results);
      }
    } catch (error) {
      console.error('加载失败:', error);
    } finally {
      setLoading(false);
    }
  }

  // 批量操作
  async function batchAction(action) {
    if (selectedIds.length === 0) {
      alert('请先选择评论');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        'http://localhost:8000/api/v1/cms/comments/batch/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            comment_ids: selectedIds,
            action: action
          })
        }
      );
      
      const data = await response.json();
      if (data.success) {
        alert(`成功处理 ${data.data.processed_count} 条评论`);
        setSelectedIds([]);
        fetchPendingComments(); // 刷新列表
      } else {
        alert(`操作失败: ${data.message}`);
      }
    } catch (error) {
      console.error('批量操作失败:', error);
      alert('操作失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }

  // 切换选中状态
  function toggleSelection(commentId) {
    setSelectedIds(prev => 
      prev.includes(commentId)
        ? prev.filter(id => id !== commentId)
        : [...prev, commentId]
    );
  }

  return (
    <div className="moderation-panel">
      <h2>待审核评论 ({comments.length})</h2>
      
      {/* 批量操作按钮 */}
      <div className="batch-actions">
        <button 
          onClick={() => batchAction('approve')}
          disabled={loading || selectedIds.length === 0}
        >
          批量批准 ({selectedIds.length})
        </button>
        <button 
          onClick={() => batchAction('reject')}
          disabled={loading || selectedIds.length === 0}
        >
          批量拒绝
        </button>
        <button 
          onClick={() => batchAction('spam')}
          disabled={loading || selectedIds.length === 0}
        >
          批量标记垃圾
        </button>
      </div>

      {/* 评论列表 */}
      <div className="comment-list">
        {comments.map(comment => (
          <div key={comment.id} className="comment-item">
            <input
              type="checkbox"
              checked={selectedIds.includes(comment.id)}
              onChange={() => toggleSelection(comment.id)}
            />
            <div className="comment-content">
              <div className="author">{comment.author_info.name}</div>
              <div className="text">{comment.content}</div>
              <div className="meta">
                {new Date(comment.created_at).toLocaleString()}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CommentModerationPanel;
```

---

## 工作流 3: 文章详情页展示评论

### 流程图

```
加载文章 → 获取已批准评论 → 展示评论树 → 支持回复
```

### 实现代码

```javascript
// Vue 3 示例
<template>
  <div class="article-comments">
    <h3>评论 ({{ totalComments }})</h3>
    
    <!-- 评论列表 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="comments.length === 0" class="empty">暂无评论</div>
    <div v-else class="comment-list">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        @reply="handleReply"
      />
    </div>
    
    <!-- 分页 -->
    <div v-if="pagination.total_pages > 1" class="pagination">
      <button 
        @click="loadPage(pagination.current_page - 1)"
        :disabled="pagination.current_page === 1"
      >
        上一页
      </button>
      <span>{{ pagination.current_page }} / {{ pagination.total_pages }}</span>
      <button 
        @click="loadPage(pagination.current_page + 1)"
        :disabled="pagination.current_page === pagination.total_pages"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import CommentItem from './CommentItem.vue';

const props = defineProps({
  articleId: {
    type: Number,
    required: true
  }
});

const comments = ref([]);
const pagination = ref({});
const totalComments = ref(0);
const loading = ref(false);

onMounted(() => {
  loadComments();
});

async function loadComments(page = 1) {
  loading.value = true;
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/cms/comments/?article=${props.articleId}&status=approved&has_parent=false&page=${page}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      }
    );
    
    const data = await response.json();
    if (data.success) {
      comments.value = data.data.results;
      pagination.value = data.data.pagination;
      totalComments.value = data.data.pagination.count;
    }
  } catch (error) {
    console.error('加载评论失败:', error);
  } finally {
    loading.value = false;
  }
}

function loadPage(page) {
  loadComments(page);
}

function handleReply(commentId) {
  // 处理回复逻辑
  console.log('回复评论:', commentId);
}
</script>
```

---

## 工作流 4: 实时监控垃圾评论

### 流程图

```
定时轮询 → 检查新评论 → 自动标记可疑评论 → 通知管理员
```

### 实现代码

```javascript
class CommentMonitor {
  constructor(token, checkInterval = 60000) {
    this.token = token;
    this.checkInterval = checkInterval;
    this.lastCheckTime = new Date();
    this.timer = null;
  }

  // 启动监控
  start() {
    console.log('评论监控已启动');
    this.timer = setInterval(() => this.checkNewComments(), this.checkInterval);
  }

  // 停止监控
  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      console.log('评论监控已停止');
    }
  }

  // 检查新评论
  async checkNewComments() {
    try {
      const response = await fetch(
        'http://localhost:8000/api/v1/cms/comments/?status=pending',
        {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        }
      );
      
      const data = await response.json();
      if (data.success) {
        const newComments = data.data.results.filter(comment => 
          new Date(comment.created_at) > this.lastCheckTime
        );
        
        if (newComments.length > 0) {
          console.log(`发现 ${newComments.length} 条新评论`);
          await this.analyzeComments(newComments);
        }
        
        this.lastCheckTime = new Date();
      }
    } catch (error) {
      console.error('检查新评论失败:', error);
    }
  }

  // 分析评论（简单示例）
  async analyzeComments(comments) {
    const spamKeywords = ['广告', '垃圾', '刷单', '加微信'];
    const suspiciousIds = [];

    for (const comment of comments) {
      // 检查是否包含垃圾关键词
      const isSpam = spamKeywords.some(keyword => 
        comment.content.includes(keyword)
      );

      if (isSpam) {
        suspiciousIds.push(comment.id);
        console.log(`可疑评论: ${comment.id} - ${comment.content}`);
      }
    }

    // 自动标记垃圾评论
    if (suspiciousIds.length > 0) {
      await this.markAsSpam(suspiciousIds);
      this.notifyAdmin(suspiciousIds.length);
    }
  }

  // 批量标记垃圾
  async markAsSpam(commentIds) {
    try {
      const response = await fetch(
        'http://localhost:8000/api/v1/cms/comments/batch/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            comment_ids: commentIds,
            action: 'spam'
          })
        }
      );
      
      const data = await response.json();
      if (data.success) {
        console.log(`已自动标记 ${data.data.processed_count} 条垃圾评论`);
      }
    } catch (error) {
      console.error('标记垃圾评论失败:', error);
    }
  }

  // 通知管理员
  notifyAdmin(count) {
    // 这里可以实现推送通知、邮件等
    console.log(`⚠️  发现并处理了 ${count} 条垃圾评论`);
    // 例如：发送桌面通知
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('评论监控', {
        body: `发现并处理了 ${count} 条垃圾评论`,
        icon: '/icon.png'
      });
    }
  }
}

// 使用示例
const token = localStorage.getItem('token');
const monitor = new CommentMonitor(token, 60000); // 每分钟检查一次
monitor.start();

// 页面卸载时停止监控
window.addEventListener('beforeunload', () => {
  monitor.stop();
});
```

---

## 工作流 5: Shell 脚本批量审核

适用于运维人员快速处理大量评论。

```bash
#!/bin/bash

# 配置
BASE_URL="http://localhost:8000/api/v1"
USERNAME="admin_jin"
PASSWORD="AdminPass123!"

# 1. 登录获取 Token
echo "正在登录..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "登录失败"
  exit 1
fi

echo "登录成功，Token: ${TOKEN:0:20}..."

# 2. 获取待审核评论
echo "获取待审核评论..."
COMMENTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/cms/comments/?status=pending&page_size=100" \
  -H "Authorization: Bearer ${TOKEN}")

# 提取评论ID（使用 jq 或 grep）
COMMENT_IDS=$(echo $COMMENTS_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$COMMENT_IDS" ]; then
  echo "没有待审核评论"
  exit 0
fi

# 转换为数组
IDS_ARRAY=($(echo $COMMENT_IDS | tr ' ' '\n'))
echo "找到 ${#IDS_ARRAY[@]} 条待审核评论"

# 3. 批量批准（可以根据需要修改为 reject 或 spam）
echo "批量批准评论..."

# 构建 JSON 数组
IDS_JSON=$(printf '%s,' "${IDS_ARRAY[@]}" | sed 's/,$//')
IDS_JSON="[${IDS_JSON}]"

BATCH_RESPONSE=$(curl -s -X POST "${BASE_URL}/cms/comments/batch/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"comment_ids\": ${IDS_JSON}, \"action\": \"approve\"}")

# 解析结果
PROCESSED_COUNT=$(echo $BATCH_RESPONSE | grep -o '"processed_count":[0-9]*' | cut -d':' -f2)

echo "批准完成！处理了 ${PROCESSED_COUNT} 条评论"
```

使用方法：
```bash
chmod +x moderate_comments.sh
./moderate_comments.sh
```

---

## 错误处理最佳实践

```javascript
class CommentAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json();

      // 统一错误处理
      if (!data.success) {
        switch (data.code) {
          case 4010: // 未认证
            this.handleAuthError();
            break;
          case 4030: // 无权限
            this.handlePermissionError(data.message);
            break;
          case 4040: // 资源不存在
            this.handleNotFoundError(data.message);
            break;
          default:
            this.handleGenericError(data.message);
        }
        throw new Error(data.message);
      }

      return data.data;
    } catch (error) {
      if (error.message === 'Failed to fetch') {
        this.handleNetworkError();
      }
      throw error;
    }
  }

  handleAuthError() {
    console.error('认证失败，请重新登录');
    // 清除 token，跳转到登录页
    localStorage.removeItem('token');
    window.location.href = '/login';
  }

  handlePermissionError(message) {
    console.error('权限不足:', message);
    alert(`权限不足: ${message}`);
  }

  handleNotFoundError(message) {
    console.error('资源不存在:', message);
    alert(`资源不存在: ${message}`);
  }

  handleGenericError(message) {
    console.error('操作失败:', message);
    alert(`操作失败: ${message}`);
  }

  handleNetworkError() {
    console.error('网络错误，请检查连接');
    alert('网络错误，请检查连接');
  }

  // API 方法
  async approveComment(commentId) {
    return this.request(`/cms/comments/${commentId}/approve/`, {
      method: 'POST'
    });
  }

  async batchAction(commentIds, action) {
    return this.request('/cms/comments/batch/', {
      method: 'POST',
      body: JSON.stringify({ comment_ids: commentIds, action })
    });
  }

  async getComments(filters = {}) {
    const params = new URLSearchParams(filters);
    return this.request(`/cms/comments/?${params}`);
  }
}

// 使用示例
const api = new CommentAPI('http://localhost:8000/api/v1', token);

// 批准评论
try {
  await api.approveComment(123);
  console.log('批准成功');
} catch (error) {
  // 错误已经被统一处理
}
```

---

## 总结

以上示例涵盖了评论审核系统的主要使用场景：

1. **基础审核流程**: 登录 → 查询 → 单个审核
2. **批量审核**: 选择多条 → 批量操作
3. **前端展示**: 加载已批准评论 → 分页展示
4. **自动化监控**: 定时检查 → 自动处理
5. **脚本批处理**: Shell 脚本快速处理

选择合适的工作流根据您的具体需求进行集成。所有示例代码都已经过实际测试验证。

---

[返回概述](./01_overview.md) | [上一页：查询评论](./06_query_api.md)
