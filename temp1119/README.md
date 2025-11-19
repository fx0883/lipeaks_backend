# 文章点赞功能 - 前端集成文档

## 📚 文档导航

欢迎使用文章点赞功能 API！本目录包含完整的前端集成文档，帮助您快速集成点赞功能。

### 文档列表

1. **[01-文章点赞功能概述.md](./01-文章点赞功能概述.md)**
   - 功能介绍
   - 权限要求
   - 快速开始
   - 典型使用场景

2. **[02-API接口详细说明.md](./02-API接口详细说明.md)**
   - 6个 API 接口的详细说明
   - 请求参数
   - 响应示例
   - cURL 和多语言代码示例

3. **[03-数据结构说明.md](./03-数据结构说明.md)**
   - 完整的数据结构定义
   - TypeScript 类型定义
   - 枚举值说明
   - 响应码对照表

4. **[04-前端集成指南-React.md](./04-前端集成指南-React.md)**
   - React 完整代码示例
   - Custom Hooks
   - 组件封装

5. **[05-前端集成指南-Vue.md](./05-前端集成指南-Vue.md)**
   - Vue 3 Composition API 示例
   - Composables 封装
   - 组件实现

6. **[06-错误处理与常见问题.md](./06-错误处理与常见问题.md)**
   - 错误码对照表
   - 常见错误处理
   - 调试技巧
   - FAQ

---

## 🚀 快速开始（5分钟集成）

### 第 1 步：获取 Token

```bash
POST /api/v1/auth/member/login/
Content-Type: application/json
X-Tenant-ID: 1

{
  "username": "your_username",
  "password": "your_password"
}
```

保存返回的 `access_token` 和 `tenant_id`。

### 第 2 步：点赞文章

```bash
POST /api/v1/interactions/article-likes/
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json

{
  "article": 100
}
```

### 第 3 步：检查点赞状态

```bash
GET /api/v1/interactions/article-likes/check/100/
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

---

## 📊 核心功能

### ✅ 已实现功能

- **点赞/取消点赞**: 对文章进行点赞操作
- **状态检查**: 快速查询文章是否已被点赞
- **列表查询**: 查看我点赞的文章 / 文章的点赞用户
- **实时统计**: 自动更新文章的点赞数
- **防重复**: 不能重复点赞同一文章
- **租户隔离**: 严格的权限控制

### 🔐 权限要求

- ✅ Member 用户可以使用
- ❌ Admin 用户不能使用
- ❌ 未登录用户不能使用

---

## 🌐 API 端点总览

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/v1/interactions/article-likes/` | 点赞文章 |
| DELETE | `/api/v1/interactions/article-likes/by-article/{id}/` | 取消点赞 |
| GET | `/api/v1/interactions/article-likes/check/{id}/` | 检查点赞状态 |
| GET | `/api/v1/interactions/article-likes/` | 我点赞的文章列表 |
| GET | `/api/v1/interactions/article-likes/by-article/{id}/likers/` | 文章的点赞用户 |

---

## 💻 代码示例

### React

```typescript
import { useArticleLike } from './hooks/useArticleLike';

function ArticleDetail({ articleId, initialLikes }) {
  const { isLiked, likesCount, toggleLike } = useArticleLike(articleId, initialLikes);

  return (
    <button onClick={toggleLike}>
      {isLiked ? '❤️' : '🤍'} {likesCount}
    </button>
  );
}
```

### Vue 3

```vue
<template>
  <button @click="toggleLike">
    {{ isLiked ? '❤️' : '🤍' }} {{ likesCount }}
  </button>
</template>

<script setup>
import { useArticleLike } from './composables/useArticleLike';

const { isLiked, likesCount, toggleLike } = useArticleLike(articleId, initialLikes);
</script>
```

### 原生 JavaScript

```javascript
// 点赞
fetch('/api/v1/interactions/article-likes/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Tenant-ID': tenantId,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ article: articleId })
});
```

---

## 🔗 相关资源

- **Swagger 文档**: `http://localhost:8000/api/v1/docs/`
- **ReDoc 文档**: `http://localhost:8000/api/v1/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/schema/`

---

## ⚠️ 重要注意事项

### 1. 必须携带的请求头

```
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 2. Token 过期处理

Token 有效期为一定时间，过期后需要使用 `refresh_token` 刷新或重新登录。

### 3. 用户类型检查

前端应该检查当前用户是否为 Member 类型，如果不是应该隐藏点赞功能。

```typescript
if (user.user_type !== 'member') {
  // 隐藏点赞功能
}
```

### 4. 防抖处理

点赞按钮应该有防抖处理，避免用户快速点击导致重复请求。

---

## 📞 技术支持

### 遇到问题？

1. 查看 **[06-错误处理与常见问题.md](./06-错误处理与常见问题.md)**
2. 检查浏览器 Network 面板的请求详情
3. 查看 Swagger 文档测试 API
4. 联系后端开发人员

### 错误排查步骤

```
1. 检查 Token 是否存在且有效
   ↓
2. 检查请求头是否正确（Authorization 和 X-Tenant-ID）
   ↓
3. 检查用户类型是否为 Member
   ↓
4. 检查文章 ID 是否正确
   ↓
5. 查看错误响应中的 error_code 和 message
```

---

## 📝 更新日志

### v1.0 (2024-11-19)
- ✅ 初始版本发布
- ✅ 完整的 API 实现
- ✅ React 和 Vue 集成示例
- ✅ 完整的错误处理文档
- ✅ TypeScript 类型定义

---

## 📖 推荐阅读顺序

### 对于新手

1. **01-文章点赞功能概述.md** - 了解功能和权限
2. **02-API接口详细说明.md** - 学习 API 使用
3. **04-前端集成指南-React.md** 或 **05-前端集成指南-Vue.md** - 选择您使用的框架
4. **06-错误处理与常见问题.md** - 了解如何处理错误

### 对于有经验的开发者

1. **03-数据结构说明.md** - 快速了解数据结构
2. **02-API接口详细说明.md** - 查看 API 文档
3. 根据需要查看框架相关的集成指南

---

## 🎯 集成检查清单

完成以下步骤确保正确集成：

- [ ] 获取并保存 access_token 和 tenant_id
- [ ] 配置请求拦截器添加认证头
- [ ] 实现点赞按钮组件
- [ ] 实现点赞状态检查
- [ ] 添加错误处理
- [ ] 处理 Token 过期情况
- [ ] 测试所有功能（点赞、取消、列表）
- [ ] 添加防抖处理
- [ ] 检查用户类型权限
- [ ] 测试租户隔离

---

**文档版本**: v1.0  
**最后更新**: 2024-11-19  
**维护者**: 后端开发团队

如有任何问题或建议，请及时反馈！
