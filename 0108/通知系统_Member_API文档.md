# 通知系统 Member API 文档

本文档详细说明了通知系统成员端的所有API接口，供普通用户（Member）查看和管理自己的通知。

---

## 通用说明

### 基础URL
```
http://localhost:8000/api/v1/notifications/
```

### 认证方式

#### GET请求（查询操作）
**不需要JWT认证**，但需要提供以下参数：
- Header中指定租户ID: `X-Tenant-ID: {TENANT_ID}`
- Query参数中指定成员ID: `member_id={MEMBER_ID}`

```bash
# GET请求示例（无需token）
curl -X GET "http://localhost:8000/api/v1/notifications/?member_id=123" \
  -H "X-Tenant-ID: 3"
```

#### POST请求（操作）
需要JWT认证，请在Header中添加：
```
Authorization: Bearer {JWT_TOKEN}
```

### 租户ID
多租户环境下，需要在Header中指定租户ID：
```
X-Tenant-ID: {TENANT_ID}
```

### 响应格式
所有响应遵循标准格式：
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": { ... }
}
```

### 错误码说明
- 2xxx: 成功
- 4000: 请求参数错误
- 4001: 未认证
- 4003: 权限不足
- 4004: 资源不存在
- 5000: 服务器内部错误

---

## 一、通知查询 API

### 1.1 获取我的通知列表

**接口**: `GET /api/v1/notifications/`

**权限**: 不需要认证（需要member_id参数）

**功能说明**: 获取指定Member的所有已发布通知，按发布时间倒序排列

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| member_id | int | 是 | 成员ID（必须提供） |
| application | int | 否 | 关联应用ID，筛选特定应用的通知 |
| is_read | bool | 否 | 是否已读：true/false |
| type | string | 否 | 类型：info, warning, error, update, announcement |
| priority | string | 否 | 优先级：low, normal, high, urgent |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |

**curl命令示例（无需token）**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications/?member_id=123&page=1&page_size=10" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 25,
    "next": "http://localhost:8000/api/v1/notifications/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1001,
        "notification_id": 1,
        "title": "系统维护通知",
        "scope": "tenant",
        "scope_display": "面向租户",
        "application": null,
        "application_name": null,
        "notification_type": "info",
        "type_display": "信息通知",
        "priority": "normal",
        "priority_display": "普通",
        "published_at": "2024-01-08T10:00:00Z",
        "is_read": false,
        "read_at": null,
        "created_at": "2024-01-08T10:00:00Z"
      },
      {
        "id": 1002,
        "notification_id": 2,
        "title": "新功能发布",
        "scope": "application",
        "scope_display": "面向应用",
        "application": 5,
        "application_name": "博客系统",
        "notification_type": "update",
        "type_display": "更新通知",
        "priority": "high",
        "priority_display": "高",
        "published_at": "2024-01-08T11:00:00Z",
        "is_read": true,
        "read_at": "2024-01-08T11:30:00Z",
        "created_at": "2024-01-08T11:00:00Z"
      }
    ]
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | int | 接收记录ID（非通知ID） |
| notification_id | int | 通知ID |
| title | string | 通知标题 |
| scope | string | 通知范围 |
| scope_display | string | 通知范围显示名称 |
| application | int | 关联应用ID |
| application_name | string | 应用名称 |
| notification_type | string | 通知类型 |
| type_display | string | 通知类型显示名称 |
| priority | string | 优先级 |
| priority_display | string | 优先级显示名称 |
| published_at | datetime | 发布时间 |
| is_read | bool | 是否已读 |
| read_at | datetime | 阅读时间 |
| created_at | datetime | 创建时间 |

---

### 1.2 获取未读通知列表

**curl命令示例（无需token）**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications/?member_id=123&is_read=false&page=1" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 8,
    "results": [
      {
        "id": 1001,
        "notification_id": 1,
        "title": "系统维护通知",
        "notification_type": "info",
        "priority": "normal",
        "is_read": false,
        "published_at": "2024-01-08T10:00:00Z"
      }
    ]
  }
}
```

---

### 1.3 获取特定应用的通知

**curl命令示例（无需token）**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications/?member_id=123&application=5" \
  -H "X-Tenant-ID: 3"
```

---

### 1.4 获取高优先级通知

**curl命令示例（无需token）**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications/?member_id=123&priority=high" \
  -H "X-Tenant-ID: 3"
```

---

### 1.5 获取通知详情

**接口**: `GET /api/v1/notifications/{id}/`

**权限**: 不需要认证

**功能说明**: 
- 获取通知的完整内容
- 自动标记为已读（如果未读）

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 通知接收记录ID（非通知ID） |

**curl命令示例（无需token）**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications/1001/" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1001,
    "notification_id": 1,
    "title": "系统维护通知",
    "content": "我们将在今晚22:00-23:00进行系统维护，期间服务可能会暂时中断，请提前做好准备。感谢您的理解与支持！",
    "scope": "tenant",
    "scope_display": "面向租户",
    "application": null,
    "application_name": null,
    "notification_type": "info",
    "type_display": "信息通知",
    "priority": "normal",
    "priority_display": "普通",
    "published_at": "2024-01-08T10:00:00Z",
    "is_read": true,
    "read_at": "2024-01-08T15:30:00Z",
    "created_at": "2024-01-08T10:00:00Z"
  }
}
```

**注意**: 调用此接口后，通知会自动被标记为已读，`is_read`变为`true`，`read_at`记录当前时间。

---

## 二、通知操作 API

### 2.1 标记单条通知为已读

**接口**: `POST /api/v1/notifications/{id}/read/`

**权限**: 需要Member用户认证

**功能说明**: 手动标记某条通知为已读

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 通知接收记录ID |

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/1001/read/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "标记成功",
  "data": {
    "id": 1001,
    "notification_id": 1,
    "title": "系统维护通知",
    "content": "我们将在今晚22:00-23:00进行系统维护...",
    "is_read": true,
    "read_at": "2024-01-08T15:35:00Z",
    "published_at": "2024-01-08T10:00:00Z"
  }
}
```

---

### 2.2 标记所有通知为已读

**接口**: `POST /api/v1/notifications/read-all/`

**权限**: 需要Member用户认证

**功能说明**: 一键将当前用户的所有未读通知标记为已读

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/read-all/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "已将 8 条通知标记为已读",
  "data": {
    "detail": "已将 8 条通知标记为已读",
    "updated_count": 8
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| detail | string | 操作结果描述 |
| updated_count | int | 实际更新的通知数量 |

---

## 三、统计信息 API

### 3.1 获取未读通知数量

**接口**: `GET /api/v1/notifications/unread-count/`

**权限**: 不需要认证（需要member_id参数）

**功能说明**: 获取指定用户的未读通知总数，常用于页面顶部的消息提醒角标

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| member_id | int | 否 | 成员ID（如已认证可不提供） |

**curl命令示例（无需token）**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications/unread-count/?member_id=123" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "unread_count": 8
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| unread_count | int | 未读通知数量 |

---

## 四、数据字典

### 4.1 通知范围 (scope)

| 值 | 说明 |
|---|------|
| tenant | 面向租户（全员通知） |
| application | 面向应用（特定应用的通知） |
| members | 面向特定成员（定向通知） |

### 4.2 通知类型 (notification_type)

| 值 | 说明 | 建议UI样式 |
|---|------|----------|
| info | 信息通知 | 蓝色、信息图标 |
| warning | 警告通知 | 橙色、警告图标 |
| error | 错误通知 | 红色、错误图标 |
| update | 更新通知 | 绿色、更新图标 |
| announcement | 公告 | 紫色、公告图标 |

### 4.3 优先级 (priority)

| 值 | 说明 | 建议处理 |
|---|------|---------|
| low | 低 | 普通显示 |
| normal | 普通 | 普通显示 |
| high | 高 | 高亮显示、置顶 |
| urgent | 紧急 | 弹窗提醒、高亮显示 |

---

## 五、使用场景示例

### 5.1 页面首次加载 - 获取未读数量

```bash
# 用于页面头部显示未读消息数量
curl -X GET "http://localhost:8000/api/v1/notifications/unread-count/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"

# 响应: { "data": { "unread_count": 8 } }
```

### 5.2 打开通知中心 - 获取通知列表

```bash
# 获取所有通知（未读的在前）
curl -X GET "http://localhost:8000/api/v1/notifications/?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
```

### 5.3 查看通知详情

```bash
# 点击通知项查看详情（自动标记为已读）
curl -X GET "http://localhost:8000/api/v1/notifications/1001/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"

# 响应会包含完整的通知内容，且 is_read 变为 true
```

### 5.4 清空所有未读

```bash
# 用户点击"全部已读"按钮
curl -X POST "http://localhost:8000/api/v1/notifications/read-all/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"

# 响应: { "data": { "updated_count": 8 } }
```

### 5.5 筛选特定应用的通知

```bash
# 在应用详情页查看该应用的通知
curl -X GET "http://localhost:8000/api/v1/notifications/?application=5&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
```

### 5.6 只查看未读通知

```bash
# 筛选未读通知
curl -X GET "http://localhost:8000/api/v1/notifications/?is_read=false" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
```

---

## 六、前端集成建议

### 6.1 通知中心组件设计

```javascript
// 1. 初始化时获取未读数量
async function loadUnreadCount() {
  const response = await fetch('/api/v1/notifications/unread-count/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': tenantId
    }
  });
  const data = await response.json();
  // 显示在页面头部的消息图标上
  updateBadge(data.data.unread_count);
}

// 2. 打开通知列表
async function loadNotifications(page = 1) {
  const response = await fetch(
    `/api/v1/notifications/?page=${page}&page_size=20`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId
      }
    }
  );
  const data = await response.json();
  renderNotificationList(data.data.results);
}

// 3. 查看通知详情（自动标记为已读）
async function viewNotification(id) {
  const response = await fetch(`/api/v1/notifications/${id}/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': tenantId
    }
  });
  const data = await response.json();
  showNotificationDetail(data.data);
  // 刷新未读数量
  loadUnreadCount();
}

// 4. 全部已读
async function markAllAsRead() {
  const response = await fetch('/api/v1/notifications/read-all/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': tenantId
    }
  });
  const data = await response.json();
  showToast(data.message);
  // 刷新列表和未读数量
  loadNotifications();
  loadUnreadCount();
}
```

### 6.2 轮询检查新通知

```javascript
// 每30秒检查一次是否有新通知
setInterval(async () => {
  const response = await fetch('/api/v1/notifications/unread-count/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': tenantId
    }
  });
  const data = await response.json();
  const newCount = data.data.unread_count;
  
  if (newCount > currentUnreadCount) {
    // 有新通知，显示提示
    showNewNotificationToast();
    updateBadge(newCount);
  }
  currentUnreadCount = newCount;
}, 30000);
```

### 6.3 UI交互建议

1. **未读标识**: 未读通知用粗体显示或加蓝点标识
2. **优先级样式**: 
   - urgent: 红色背景或红色边框
   - high: 橙色或高亮显示
   - normal/low: 普通样式
3. **类型图标**: 根据notification_type显示不同图标
4. **时间显示**: published_at显示相对时间（如"2小时前"）
5. **分页**: 使用无限滚动或分页器
6. **全部已读按钮**: 放在通知列表顶部显眼位置

---

## 七、注意事项

1. **自动标记已读**:
   - 调用详情接口（GET /{id}/）会自动标记为已读
   - 如果只想预览不标记已读，不要调用详情接口

2. **ID说明**:
   - 列表和详情API中的`id`是通知接收记录ID，不是通知ID
   - `notification_id`才是真正的通知ID
   - 所有操作都使用接收记录ID

3. **权限控制**:
   - Member只能查看和操作自己的通知
   - 无法查看其他Member的通知
   - 无法创建、编辑或删除通知

4. **通知显示规则**:
   - 只显示status=published的通知
   - 已归档(archived)的通知不会显示
   - 已被管理员移除的通知不会显示

5. **性能优化**:
   - 未读数量接口响应快，可以频繁调用
   - 列表接口建议分页加载，避免一次加载过多数据
   - 考虑使用前端缓存减少重复请求

---

## 八、常见问题

**Q: 为什么我看不到某些通知？**

可能的原因：
1. 通知状态不是published（可能是draft或archived）
2. 你不是该通知的接收者（针对scope=members的通知）
3. 通知已被管理员移除
4. 租户ID不匹配

**Q: 查看详情后通知自动变成已读，如何避免？**

详情接口设计为自动标记已读。如果需要预览功能，建议：
1. 在列表中显示部分内容摘要
2. 或使用modal弹窗显示列表中已有的信息，不调用详情接口

**Q: 如何按优先级排序通知？**

API默认按发布时间倒序。前端可以：
1. 获取数据后在前端按priority字段排序
2. 或分别请求不同优先级的通知

**Q: 未读数量和列表数量不一致？**

这是正常的：
- unread_count返回所有未读通知总数
- 列表接口可能有筛选条件（如application、type等）

**Q: 如何实现实时通知推送？**

目前API不支持WebSocket推送。建议：
1. 使用轮询方式定期检查未读数量
2. 或集成第三方推送服务（如Firebase、极光推送）
3. 或实现WebSocket长连接（需要后端支持）

---

## 九、完整工作流程示例

### 9.1 用户登录后的通知流程

```bash
# 1. 用户登录成功
# 登录API返回token和租户ID

# 2. 页面加载，获取未读数量
curl -X GET "http://localhost:8000/api/v1/notifications/unread-count/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
# 响应: { "data": { "unread_count": 5 } }

# 3. 用户点击通知图标，打开通知中心
curl -X GET "http://localhost:8000/api/v1/notifications/?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
# 显示通知列表

# 4. 用户点击某条通知查看详情
curl -X GET "http://localhost:8000/api/v1/notifications/1001/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
# 显示详情，自动标记为已读

# 5. 用户点击"全部已读"
curl -X POST "http://localhost:8000/api/v1/notifications/read-all/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
# 所有通知标记为已读

# 6. 刷新未读数量
curl -X GET "http://localhost:8000/api/v1/notifications/unread-count/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
# 响应: { "data": { "unread_count": 0 } }
```

---

## 十、API端点总览

| 方法 | 端点 | 说明 | 自动标记已读 |
|-----|------|------|------------|
| GET | `/api/v1/notifications/` | 获取通知列表 | 否 |
| GET | `/api/v1/notifications/{id}/` | 获取通知详情 | 是 |
| POST | `/api/v1/notifications/{id}/read/` | 标记单条已读 | 是 |
| POST | `/api/v1/notifications/read-all/` | 标记全部已读 | 是 |
| GET | `/api/v1/notifications/unread-count/` | 获取未读数量 | 否 |

---

## 十一、测试建议

### 11.1 功能测试用例

1. **获取通知列表**
   - 验证分页功能
   - 验证未读/已读筛选
   - 验证应用筛选
   - 验证优先级筛选

2. **查看通知详情**
   - 验证未读通知查看后自动标记为已读
   - 验证已读通知查看不重复更新read_at

3. **标记已读**
   - 验证单条标记功能
   - 验证全部标记功能
   - 验证已读通知重复标记不报错

4. **未读数量**
   - 验证数量准确性
   - 验证标记后数量更新

### 11.2 边界测试

1. 无通知时的响应
2. 大量通知时的性能
3. 并发标记已读
4. 非自己的通知访问（应返回404或403）

---

**文档版本**: v1.0  
**更新日期**: 2024-01-08  
**维护者**: 后端开发团队
