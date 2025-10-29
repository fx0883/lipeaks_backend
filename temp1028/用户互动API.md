# 用户互动 API

Base: `/api/v1/interactions/`

## 通用要求
- **Headers（必须）**：
  - `X-Tenant-ID: <tenant_id>`
  - `Authorization: Bearer <token>`（所有接口都需要认证）
  - `Content-Type: application/json`
- **权限模型**：
  - 所有互动API都需要认证（登录）
  - 用户只能管理自己的互动记录
  - 支持租户隔离

## 1. 获取我的收藏列表 GET /favorites/

获取当前用户收藏的文章列表，按收藏时间倒序排列。

### 请求参数
- `page` - 页码（可选，默认1）
- `page_size` - 每页数量（可选，默认10）

### 权限要求
- **需要认证**：必须登录
- **返回内容**：仅返回当前用户的收藏

### 示例
```bash
curl -X GET "http://your-domain.com/api/v1/interactions/favorites/" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

**成功响应 (200)**
```json
{
  "count": 15,
  "next": "http://your-domain.com/api/v1/interactions/favorites/?page=2",
  "previous": null,
  "results": [
    {
      "id": 23,
      "user": 5,
      "article": 42,
      "article_detail": {
        "id": 42,
        "title": "深入理解Python装饰器",
        "slug": "python-decorators",
        "excerpt": "本文详细介绍Python装饰器的原理和应用...",
        "cover_image": "https://example.com/python.jpg",
        "author_info": {
          "id": 3,
          "username": "author"
        },
        "status": "published",
        "views_count": 1250,
        "likes_count": 42
      },
      "user_info": {
        "id": 5,
        "username": "member_user"
      },
      "tenant": 1,
      "created_at": "2024-01-20T10:30:00Z"
    }
  ]
}
```

---

## 2. 收藏文章 POST /favorites/

将指定文章添加到收藏列表。

### 权限要求
- **需要认证**：必须登录
- **租户限制**：只能收藏本租户内的文章
- **唯一性**：同一文章不能重复收藏

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| article | integer | 是 | 要收藏的文章ID |

### 业务规则
- 每个用户对每篇文章只能收藏一次
- 收藏时自动记录租户和当前时间
- 文章必须属于当前租户
- 文章必须存在且状态为published（建议）

### 示例
```bash
curl -X POST http://your-domain.com/api/v1/interactions/favorites/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 42
  }'
```

### 响应示例

**成功响应 (201)**
```json
{
  "id": 23,
  "user": 5,
  "article": 42,
  "article_detail": {
    "id": 42,
    "title": "深入理解Python装饰器",
    "slug": "python-decorators",
    "excerpt": "本文详细介绍Python装饰器的原理和应用...",
    "cover_image": "https://example.com/python.jpg",
    "author_info": {
      "id": 3,
      "username": "author"
    },
    "status": "published"
  },
  "user_info": {
    "id": 5,
    "username": "member_user"
  },
  "tenant": 1,
  "created_at": "2024-01-20T10:30:00Z"
}
```

**错误响应 (400) - 已收藏**
```json
{
  "article": ["您已经收藏过这篇文章"]
}
```

**错误响应 (400) - 文章不存在**
```json
{
  "article": ["Invalid pk \"999\" - object does not exist."]
}
```

**错误响应 (403) - 跨租户收藏**
```json
{
  "article": ["您无法收藏其他租户的文章"]
}
```

---

## 3. 取消收藏 DELETE /favorites/{id}/

从收藏列表中移除指定的收藏记录。

### 权限要求
- **需要认证**：必须登录
- **所有权验证**：只能删除自己的收藏记录

### 参数

| 参数 | 类型 | 位置 | 说明 |
|---|---|---|---|
| id | integer | path | 收藏记录ID（不是文章ID） |

### 示例
```bash
curl -X DELETE http://your-domain.com/api/v1/interactions/favorites/23/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

**成功响应 (204)**
```
无响应体
```

**错误响应 (403) - 尝试删除别人的收藏**
```json
{
  "detail": "您没有权限执行此操作。"
}
```

**错误响应 (404) - 收藏记录不存在**
```json
{
  "detail": "未找到。"
}
```

---

## 4. 通过文章ID取消收藏 DELETE /favorites/by-article/{article_id}/

根据文章ID取消收藏（便捷方法）。适用于文章详情页等已知文章ID但不知道收藏记录ID的场景。

### 权限要求
- **需要认证**：必须登录
- **所有权验证**：只能取消自己的收藏

### 参数

| 参数 | 类型 | 位置 | 说明 |
|---|---|---|---|
| article_id | integer | path | 文章ID |

### 业务规则
- 如果该文章未被收藏，返回404
- 操作是幂等的（重复操作不会报错）

### 示例
```bash
curl -X DELETE http://your-domain.com/api/v1/interactions/favorites/by-article/42/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

**成功响应 (204)**
```json
{
  "message": "已取消收藏"
}
```

**错误响应 (404) - 未收藏该文章**
```json
{
  "detail": "未找到。"
}
```

---

## 5. 检查文章是否已收藏 GET /favorites/check/{article_id}/

检查当前用户是否已收藏指定文章。

### 权限要求
- **需要认证**：必须登录

### 参数

| 参数 | 类型 | 位置 | 说明 |
|---|---|---|---|
| article_id | integer | path | 文章ID |

### 返回内容
- `is_favorited` - 是否已收藏（boolean）
- `favorite_id` - 收藏记录ID（如已收藏）
- `created_at` - 收藏时间（如已收藏）

### 使用场景
前端显示文章详情时，判断是否显示"已收藏"状态和收藏按钮样式。

### 示例
```bash
curl -X GET http://your-domain.com/api/v1/interactions/favorites/check/42/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

**文章已收藏 (200)**
```json
{
  "is_favorited": true,
  "favorite_id": 23,
  "created_at": "2024-01-20T10:30:00Z"
}
```

**文章未收藏 (200)**
```json
{
  "is_favorited": false,
  "favorite_id": null,
  "created_at": null
}
```

**错误响应 (404) - 文章不存在**
```json
{
  "detail": "未找到。"
}
```

---

## 完整使用流程示例

### 场景1：Member浏览文章并收藏

```bash
# 1. 查看文章详情（获取文章ID）
curl -X GET http://your-domain.com/api/v1/cms/articles/42/ \
  -H "X-Tenant-ID: 1"

# 2. 检查是否已收藏
curl -X GET http://your-domain.com/api/v1/interactions/favorites/check/42/ \
  -H "Authorization: Bearer <member_token>" \
  -H "X-Tenant-ID: 1"

# 3. 收藏文章
curl -X POST http://your-domain.com/api/v1/interactions/favorites/ \
  -H "Authorization: Bearer <member_token>" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"article": 42}'
```

### 场景2：Member查看和管理收藏列表

```bash
# 1. 获取收藏列表
curl -X GET "http://your-domain.com/api/v1/interactions/favorites/?page=1&page_size=20" \
  -H "Authorization: Bearer <member_token>" \
  -H "X-Tenant-ID: 1"

# 2. 取消收藏（方式1：使用收藏记录ID）
curl -X DELETE http://your-domain.com/api/v1/interactions/favorites/23/ \
  -H "Authorization: Bearer <member_token>" \
  -H "X-Tenant-ID: 1"

# 2. 取消收藏（方式2：使用文章ID）
curl -X DELETE http://your-domain.com/api/v1/interactions/favorites/by-article/42/ \
  -H "Authorization: Bearer <member_token>" \
  -H "X-Tenant-ID: 1"
```

---

## 前端集成建议

### TypeScript 类型定义

```typescript
interface ArticleFavorite {
  id: number;
  user: number;
  article: number;
  article_detail: {
    id: number;
    title: string;
    slug: string;
    excerpt: string;
    cover_image: string;
    author_info: {
      id: number;
      username: string;
    };
    status: string;
    views_count: number;
  };
  user_info: {
    id: number;
    username: string;
  };
  tenant: number;
  created_at: string;
}

interface FavoriteCheckResponse {
  is_favorited: boolean;
  favorite_id: number | null;
  created_at: string | null;
}
```

### React 示例

```typescript
// 收藏按钮组件
const FavoriteButton: React.FC<{ articleId: number }> = ({ articleId }) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const [favoriteId, setFavoriteId] = useState<number | null>(null);

  useEffect(() => {
    // 检查收藏状态
    fetch(`/api/v1/interactions/favorites/check/${articleId}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
      }
    })
    .then(res => res.json())
    .then(data => {
      setIsFavorited(data.is_favorited);
      setFavoriteId(data.favorite_id);
    });
  }, [articleId]);

  const toggleFavorite = async () => {
    if (isFavorited) {
      // 取消收藏
      await fetch(`/api/v1/interactions/favorites/by-article/${articleId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        }
      });
      setIsFavorited(false);
      setFavoriteId(null);
    } else {
      // 添加收藏
      const res = await fetch('/api/v1/interactions/favorites/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article: articleId })
      });
      const data = await res.json();
      setIsFavorited(true);
      setFavoriteId(data.id);
    }
  };

  return (
    <button onClick={toggleFavorite}>
      {isFavorited ? '❤️ 已收藏' : '🤍 收藏'}
    </button>
  );
};
```

---

## 常见错误处理

### 400 Bad Request
- **原因**: 文章已收藏、文章不存在、参数格式错误
- **处理**: 检查请求参数，向用户提示具体错误信息

### 401 Unauthorized
- **原因**: Token过期或无效
- **处理**: 重定向到登录页，提示用户重新登录

### 403 Forbidden
- **原因**: 尝试操作其他用户的收藏、收藏其他租户的文章
- **处理**: 提示用户权限不足

### 404 Not Found
- **原因**: 收藏记录不存在、文章不存在
- **处理**: 刷新页面或返回列表页

---

## 性能优化建议

1. **批量检查收藏状态**: 如果需要在列表页显示多个文章的收藏状态，考虑后端提供批量查询接口
2. **缓存收藏状态**: 前端可以缓存收藏状态，减少API调用
3. **乐观更新**: 点击收藏按钮时立即更新UI，失败后再回滚
4. **分页加载**: 收藏列表使用分页或无限滚动

---

## 数据库索引说明

为保证查询性能，`ArticleFavorite` 模型已创建以下索引：

- `user_id + created_at` - 用于用户收藏列表查询
- `article_id` - 用于查询文章被收藏次数
- `tenant_id + user_id` - 用于租户隔离和用户过滤
- `tenant_id + article_id` - 用于租户隔离和文章过滤
- `unique(user_id, article_id)` - 唯一约束，防止重复收藏
