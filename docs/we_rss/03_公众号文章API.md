# we_rss 公众号文章 API

这份文档覆盖公众号文章的列表、详情、导入、刷新、已读和收藏接口。前端
接入时，文章模块通常依赖公众号同步任务的结果，也可以独立使用“按 URL
导入文章”能力。

这里的“文章”对应 `WechatArticle`，和项目现有的 `cms.Article`
完全没有关系，前端不要混用字段和接口。

## 数据结构说明

文章对象字段如下。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 文章 ID |
| `feed_id` | `number \| null` | 所属公众号 ID |
| `source_id` | `string` | 微信文章来源 ID |
| `title` | `string` | 标题 |
| `description` | `string` | 摘要 |
| `content` | `string` | 正文 HTML 字符串 |
| `url` | `string` | 原始微信文章 URL |
| `pic_url` | `string` | 封面图 URL |
| `publish_time` | `string \| null` | 发布时间 |
| `status` | `string` | 文章状态 |
| `is_read` | `boolean` | 是否已读 |
| `is_favorite` | `boolean` | 是否收藏 |
| `last_refreshed_at` | `string \| null` | 最近一次刷新时间 |
| `read_num` | `number` | 阅读数 |
| `like_num` | `number` | 点赞数 |
| `old_like_num` | `number` | 在看数 |
| `share_num` | `number` | 分享数 |
| `collect_num` | `number` | 收藏数 |
| `comment_count` | `number` | 评论数 |
| `comment_reply_count` | `number` | 评论回复数 |
| `comment_total_count` | `number` | 评论总数 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

`status` 常见值如下。

| 值 | 含义 |
| --- | --- |
| `active` | 当前可正常使用 |
| `deleted` | 微信侧已删除或不可读 |

## 通用请求头

这组接口都要求带成员 token 和租户头。

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 1. 获取文章列表

这个接口返回当前 tenant 下已经保存的全部公众号文章，当前不分页，
默认按发布时间倒序。

### 请求信息

```http
GET /api/v1/we-rss/articles/
```

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "feed_id": 1,
      "source_id": "article-1",
      "title": "Imported Article",
      "description": "Imported description",
      "content": "<p>Imported content</p>",
      "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
      "pic_url": "https://example.com/article-cover.png",
      "publish_time": "2026-03-20T12:00:00Z",
      "status": "active",
      "is_read": false,
      "is_favorite": false,
      "last_refreshed_at": "2026-03-21T09:30:00Z",
      "read_num": 101,
      "like_num": 51,
      "old_like_num": 21,
      "share_num": 11,
      "collect_num": 9,
      "comment_count": 7,
      "comment_reply_count": 8,
      "comment_total_count": 15,
      "created_at": "2026-03-20T12:00:00Z",
      "updated_at": "2026-03-21T09:30:00Z"
    }
  ]
}
```

### 前端调用示例

```ts
const res = await weRssRequest<Array<any>>("/articles/");
const articles = res.data;
```

## 2. 获取文章详情

这个接口适合文章详情页。返回字段和文章列表中的单项一致，但更适合
按单篇读取。

### 请求信息

```http
GET /api/v1/we-rss/articles/{id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 文章 ID |

### 前端调用示例

```ts
const res = await weRssRequest<any>("/articles/1/");
const article = res.data;
```

## 3. 删除文章

这个接口会删除本地文章记录。它不会去删除微信平台上的原始文章。

### 请求信息

```http
DELETE /api/v1/we-rss/articles/{id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 文章 ID |

### 成功响应

成功时返回 `204 No Content`。

## 4. 按微信文章 URL 导入文章

这个接口会创建一个后台 `article_import` 任务。前端不应该期待它马上把
文章内容直接返回，而是应该去轮询任务详情。

### 请求信息

```http
POST /api/v1/we-rss/articles/import-by-url/
Content-Type: application/json
```

### 请求体

```json
{
  "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
}
```

### 请求字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `url` | `string` | 是 | 微信文章 URL |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 103,
    "task_type": "article_import",
    "status": "success",
    "task_key": "article_import:https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
    "target_type": "article",
    "target_id": 1,
    "message": "Article import complete",
    "request_payload": {
      "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
    },
    "result_payload": {
      "article_id": 1,
      "feed_id": 1,
      "message": "Article import complete"
    },
    "celery_task_id": "52f577bc-1be3-423f-a79f-f48db2d938df",
    "started_at": "2026-03-21T09:30:00Z",
    "finished_at": "2026-03-21T09:30:03Z",
    "created_at": "2026-03-21T09:30:00Z",
    "updated_at": "2026-03-21T09:30:03Z"
  }
}
```

### 行为说明

这个接口有几个前端需要提前知道的行为。

| 行为 | 说明 |
| --- | --- |
| 自动绑定 featured feed | 后端会把导入结果绑定到当前 tenant 的 featured feed |
| 异步执行 | 需要轮询任务 |
| URL 去重 | 同 URL 的运行中任务可能直接复用已有任务 |

### 前端调用示例

```ts
const res = await weRssRequest<any>("/articles/import-by-url/", {
  method: "POST",
  body: JSON.stringify({
    url: articleUrl,
  }),
});

const task = res.data;
```

## 5. 刷新文章正文和统计

这个接口会创建 `article_refresh` 任务，用于重新抓取正文、发布时间和
统计字段。

### 请求信息

```http
POST /api/v1/we-rss/articles/{id}/refresh/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 文章 ID |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 104,
    "task_type": "article_refresh",
    "status": "success",
    "task_key": "article_refresh:1",
    "target_type": "article",
    "target_id": 1,
    "message": "Article refresh complete",
    "request_payload": {
      "article_id": 1
    },
    "result_payload": {
      "article_id": 1,
      "message": "Article refresh complete",
      "read_num": 101,
      "comment_total_count": 15
    },
    "celery_task_id": "23173654-7d9a-4b62-a916-251c17f7ff7b",
    "started_at": "2026-03-21T09:35:00Z",
    "finished_at": "2026-03-21T09:35:04Z",
    "created_at": "2026-03-21T09:35:00Z",
    "updated_at": "2026-03-21T09:35:04Z"
  }
}
```

### 前端调用示例

```ts
const res = await weRssRequest<any>("/articles/1/refresh/", {
  method: "POST",
});

const task = res.data;
```

## 6. 更新文章已读状态

这个接口是同步接口，不会返回任务对象，而是直接返回更新后的文章对象。

### 请求信息

```http
PUT /api/v1/we-rss/articles/{id}/read/
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 文章 ID |

### 请求体

```json
{
  "is_read": true
}
```

### 请求字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `is_read` | `boolean` | 是 | 是否标记为已读 |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "feed_id": 1,
    "source_id": "article-1",
    "title": "Imported Article",
    "description": "Imported description",
    "content": "<p>Imported content</p>",
    "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
    "pic_url": "https://example.com/article-cover.png",
    "publish_time": "2026-03-20T12:00:00Z",
    "status": "active",
    "is_read": true,
    "is_favorite": false,
    "last_refreshed_at": "2026-03-21T09:30:00Z",
    "read_num": 101,
    "like_num": 51,
    "old_like_num": 21,
    "share_num": 11,
    "collect_num": 9,
    "comment_count": 7,
    "comment_reply_count": 8,
    "comment_total_count": 15,
    "created_at": "2026-03-20T12:00:00Z",
    "updated_at": "2026-03-21T09:30:00Z"
  }
}
```

### 前端调用示例

```ts
const res = await weRssRequest<any>("/articles/1/read/", {
  method: "PUT",
  body: JSON.stringify({
    is_read: true,
  }),
});

const article = res.data;
```

## 7. 更新文章收藏状态

这个接口和“更新已读状态”类似，也是同步接口。

### 请求信息

```http
PUT /api/v1/we-rss/articles/{id}/favorite/
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 文章 ID |

### 请求体

```json
{
  "is_favorite": true
}
```

### 请求字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `is_favorite` | `boolean` | 是 | 是否标记为收藏 |

### 前端调用示例

```ts
const res = await weRssRequest<any>("/articles/1/favorite/", {
  method: "PUT",
  body: JSON.stringify({
    is_favorite: true,
  }),
});

const article = res.data;
```

## 页面建议

文章模块通常适合按下面方式实现页面。

1. 文章列表页，调用 `GET /articles/`。
2. 文章详情页，调用 `GET /articles/{id}/`。
3. 粘贴 URL 导入弹窗，调用 `POST /articles/import-by-url/`。
4. 刷新按钮，调用 `POST /articles/{id}/refresh/`。
5. 已读和收藏按钮，调用 `PUT /articles/{id}/read/` 和
   `PUT /articles/{id}/favorite/`。

## 下一步

如果你要处理导入和刷新后的任务轮询，请继续看任务文档。

- [04_同步任务API.md](./04_%E5%90%8C%E6%AD%A5%E4%BB%BB%E5%8A%A1API.md)
- [05_RSS与正文输出API.md](./05_RSS%E4%B8%8E%E6%AD%A3%E6%96%87%E8%BE%93%E5%87%BAAPI.md)
