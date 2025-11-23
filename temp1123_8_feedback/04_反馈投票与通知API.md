# 反馈投票与通知 API 文档

## 概述

本文档介绍反馈投票功能和邮件通知设置API。投票功能帮助识别用户最关注的问题，通知设置允许用户控制是否接收邮件更新。

---

## 投票功能

### 1. 对反馈投票

#### 基本信息
- **接口**: `POST /api/v1/feedbacks/feedbacks/{id}/vote/`
- **权限**: 需要认证
- **说明**: 
  - 为反馈投票（点赞或点踩）
  - 每个用户对每个反馈只能投一票
  - 可以修改投票类型（从点赞改为点踩，或反之）
  - 投票会影响反馈的 `vote_count`

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 反馈ID |

#### 请求参数

| 参数 | 类型 | 必填 | 说明 | 可选值 |
|------|------|------|------|--------|
| vote_type | int | 是 | 投票类型 | 1 (点赞), -1 (点踩) |

#### 请求示例

```json
{
    "vote_type": 1
}
```

#### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "Vote recorded",
    "data": {
        "message": "Vote recorded",
        "vote_type": 1,
        "total_votes": 1
    }
}
```

#### curl 示例

```bash
# 点赞（支持）
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vote_type": 1
  }'

# 点踩（不支持）
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vote_type": -1
  }'
```

---

### 2. 取消投票

#### 基本信息
- **接口**: `DELETE /api/v1/feedbacks/feedbacks/{id}/vote/`
- **权限**: 需要认证
- **说明**: 
  - 取消之前的投票
  - 会减少反馈的 `vote_count`

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 反馈ID |

#### 响应

成功返回 HTTP 204 No Content

#### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/27/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 投票规则说明

#### 投票计数规则

| 操作 | 影响 |
|------|------|
| 首次点赞 (+1) | vote_count +1 |
| 首次点踩 (-1) | vote_count -1 |
| 从点赞改为点踩 | vote_count -2 |
| 从点踩改为点赞 | vote_count +2 |
| 取消点赞 | vote_count -1 |
| 取消点踩 | vote_count +1 |

#### 示例流程

```bash
# 假设初始 vote_count = 0

# 用户A点赞
POST /vote/ {"vote_type": 1}
# vote_count = 1

# 用户B点赞
POST /vote/ {"vote_type": 1}
# vote_count = 2

# 用户C点踩
POST /vote/ {"vote_type": -1}
# vote_count = 1

# 用户A改为点踩
POST /vote/ {"vote_type": -1}
# vote_count = -1

# 用户B取消投票
DELETE /vote/
# vote_count = 0
```

---

### 使用场景

#### 场景1：识别热门反馈

```bash
# 1. 获取投票最多的反馈
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?ordering=-vote_count" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 为关注的问题投票
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": 1}'
```

#### 场景2：用户改变想法

```bash
# 1. 先投了赞成票
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": 1}'

# 2. 改为反对票
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": -1}'

# 3. 取消投票
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/27/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 通知设置

### 切换邮件通知

#### 基本信息
- **接口**: `PATCH /api/v1/feedbacks/feedbacks/{id}/notifications/`
- **权限**: 需要认证，仅反馈创建者
- **说明**: 
  - 切换反馈的邮件通知开关
  - 开启时，有新回复会收到邮件通知
  - 关闭时，不会收到任何邮件通知

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 反馈ID |

#### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 27,
        "title": "页面加载缓慢",
        "email_notification_enabled": false,
        "... 其他字段 ...": "..."
    }
}
```

#### curl 示例

```bash
# 切换通知设置（开/关）
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 通知机制说明

#### 触发邮件通知的事件

| 事件 | 条件 | 通知对象 |
|------|------|----------|
| 新回复 | `email_notification_enabled = true`<br>`is_internal_note = false` | 反馈提交者 |
| 状态变更 | `email_notification_enabled = true` | 反馈提交者 |
| 邮箱验证 | 匿名提交反馈 | 提供的邮箱 |

#### 不会触发通知的情况

- 内部备注（`is_internal_note = true`）
- 通知已关闭（`email_notification_enabled = false`）
- 邮箱未验证（匿名用户且 `email_verified = false`）
- 用户自己的回复（不会给自己发邮件）

---

### 使用场景

#### 场景1：减少邮件干扰

用户提交了多个反馈，但只想关注某些重要的：

```bash
# 1. 关闭不重要反馈的通知
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/100/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 保持重要反馈的通知开启（默认开启，无需操作）

# 3. 查看当前状态
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/100/" \
  -H "Authorization: Bearer YOUR_TOKEN" | grep email_notification_enabled
```

#### 场景2：临时关闭通知

问题已解决但管理员还在补充信息：

```bash
# 1. 临时关闭通知
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 等管理员更新完毕后再开启
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 批量操作示例

### 批量投票

```bash
#!/bin/bash
# bulk_vote.sh - 为多个反馈投票

TOKEN="YOUR_TOKEN"
FEEDBACK_IDS=(27 28 29 30)

for id in "${FEEDBACK_IDS[@]}"; do
  echo "Voting for feedback $id..."
  curl -s -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/$id/vote/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"vote_type": 1}' | python3 -m json.tool
done
```

### 批量管理通知

```bash
#!/bin/bash
# manage_notifications.sh - 批量管理通知设置

TOKEN="YOUR_TOKEN"

# 获取我的所有反馈
MY_FEEDBACKS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer $TOKEN")

# 提取反馈ID（需要jq工具）
FEEDBACK_IDS=$(echo $MY_FEEDBACKS | jq -r '.data[].id')

# 批量关闭通知
for id in $FEEDBACK_IDS; do
  echo "Disabling notifications for feedback $id..."
  curl -s -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/$id/notifications/" \
    -H "Authorization: Bearer $TOKEN"
done
```

---

## 最佳实践

### 投票功能

1. **用户引导**：
   - 在UI中清晰说明投票的含义
   - 显示当前总票数
   - 高亮用户已投的票

2. **防止滥用**：
   - 限制每个用户每个反馈一票
   - 记录投票历史用于审计
   - 可选：限制投票频率

3. **数据分析**：
   ```bash
   # 分析投票趋势
   curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
     -H "Authorization: Bearer YOUR_TOKEN" | jq '.data.most_voted'
   ```

### 通知管理

1. **默认设置**：
   - 新反馈默认开启通知
   - 给用户明确的控制权

2. **通知频率**：
   - 合并通知（避免频繁邮件）
   - 提供通知摘要选项
   - 允许选择通知时间段

3. **退订链接**：
   - 邮件中包含退订链接
   - 一键关闭通知

---

## 错误处理

### 投票相关错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|----------|------|----------|
| 400 | Invalid vote type | 投票类型不是1或-1 | 使用正确的值 |
| 404 | Feedback not found | 反馈不存在 | 检查反馈ID |
| 404 | Vote not found | 尝试删除不存在的投票 | 确认已投票 |

### 通知相关错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|----------|------|----------|
| 403 | Permission denied | 不是反馈创建者 | 只能管理自己的通知 |
| 404 | Feedback not found | 反馈不存在 | 检查反馈ID |

---

## 前端集成示例

### React 投票组件

```javascript
// VoteButtons.jsx
import { useState } from 'react';

function VoteButtons({ feedbackId, initialVote, initialCount }) {
  const [vote, setVote] = useState(initialVote); // 1, -1, or null
  const [count, setCount] = useState(initialCount);

  const handleVote = async (voteType) => {
    if (vote === voteType) {
      // 取消投票
      await fetch(`/api/v1/feedbacks/feedbacks/${feedbackId}/vote/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setVote(null);
      setCount(count - voteType);
    } else {
      // 投票或改票
      const response = await fetch(`/api/v1/feedbacks/feedbacks/${feedbackId}/vote/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ vote_type: voteType })
      });
      const data = await response.json();
      setVote(voteType);
      setCount(data.data.total_votes);
    }
  };

  return (
    <div className="vote-buttons">
      <button 
        className={vote === 1 ? 'active' : ''}
        onClick={() => handleVote(1)}
      >
        👍 {vote === 1 ? '已赞' : '赞'}
      </button>
      <span>{count}</span>
      <button 
        className={vote === -1 ? 'active' : ''}
        onClick={() => handleVote(-1)}
      >
        👎 {vote === -1 ? '已踩' : '踩'}
      </button>
    </div>
  );
}
```

### Vue 通知开关组件

```vue
<!-- NotificationToggle.vue -->
<template>
  <div class="notification-toggle">
    <label>
      <input 
        type="checkbox" 
        v-model="enabled" 
        @change="toggleNotifications"
      />
      <span>接收邮件通知</span>
    </label>
  </div>
</template>

<script>
export default {
  props: ['feedbackId', 'initialEnabled'],
  data() {
    return {
      enabled: this.initialEnabled
    };
  },
  methods: {
    async toggleNotifications() {
      try {
        await fetch(`/api/v1/feedbacks/feedbacks/${this.feedbackId}/notifications/`, {
          method: 'PATCH',
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        this.$message.success('通知设置已更新');
      } catch (error) {
        this.$message.error('更新失败');
        this.enabled = !this.enabled; // 回滚
      }
    }
  }
};
</script>
```
