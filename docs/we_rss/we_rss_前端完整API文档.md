# we_rss 前端完整 API 文档

这是一份给前端直接使用的单文件总文档。它基于当前仓库里的 `we_rss` 真实实现
整理，覆盖鉴权、核心对象、接口总表、文章统计刷新和任务轮询口径。

如果你只想快速接入，先看“鉴权规则”“接口总表”“文章接口说明”“同步任务说明”
这四部分就够了。

## 1. 模块范围

`we_rss` 当前覆盖下面几类能力：

- 微信凭证管理
- 微信扫码登录
- 公众号搜索
- member 订阅公众号和取消订阅
- member 私有标签管理
- feed 和 article 标签绑定
- 公众号同步
- 文章列表、详情、收藏、按 URL 导入、正文刷新、统计刷新、删除
- 异步任务查询
- tenant RSS、单 feed RSS、文章正文 HTML 输出

## 2. 基础地址

```text
/api/v1/we-rss/
```

本地开发环境通常是：

```text
http://localhost:8000/api/v1/we-rss/
```

## 3. 鉴权与 tenant 规则

所有 `we_rss` 接口都要求成员鉴权，并且必须带租户头：

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

必须记住下面几条规则：

- 只有 member 可以访问 `we_rss`。
- `X-Tenant-ID` 必须等于当前 member 绑定的 tenant。
- `WechatFeed` 和 `WechatArticle` 是 tenant 共享主数据。
- `is_subscribed` 和 `is_favorite` 是当前 member 的状态。
- 标签是当前 member 的私有资产，不存在 tenant 公共标签。
- 当前没有 `is_read`。

## 4. 标准返回格式

普通 JSON 接口统一使用包裹结构：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {}
}
```

非 JSON 接口如下：

| 接口 | Content-Type | 前端读取方式 |
| --- | --- | --- |
| 普通业务接口 | `application/json` | `response.json()` |
| RSS 接口 | `application/xml` | `response.text()` |
| 正文 HTML 接口 | `text/html` | `response.text()` |

## 5. 接口总表

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/we-rss/credentials/` | 获取凭证列表 |
| `GET` | `/api/v1/we-rss/credentials/{id}/` | 获取凭证详情 |
| `PUT` | `/api/v1/we-rss/credentials/{id}/` | 更新凭证名称 |
| `DELETE` | `/api/v1/we-rss/credentials/{id}/` | 软删除凭证 |
| `POST` | `/api/v1/we-rss/credentials/{id}/check/` | 检查凭证有效性 |
| `POST` | `/api/v1/we-rss/credentials/{id}/set-default/` | 设置默认凭证 |
| `POST` | `/api/v1/we-rss/credentials/login-sessions/` | 创建扫码登录会话 |
| `GET` | `/api/v1/we-rss/credentials/login-sessions/{session_id}/` | 查询扫码登录会话 |
| `GET` | `/api/v1/we-rss/feeds/` | 获取公众号列表 |
| `POST` | `/api/v1/we-rss/feeds/` | 手动创建公众号记录 |
| `GET` | `/api/v1/we-rss/feeds/search/?keyword=...` | 搜索微信平台公众号 |
| `POST` | `/api/v1/we-rss/feeds/subscribe/` | 订阅公众号 |
| `GET` | `/api/v1/we-rss/feeds/{id}/` | 获取公众号详情 |
| `PUT` | `/api/v1/we-rss/feeds/{id}/` | 更新公众号 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/` | 软删除公众号 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/subscribe/` | 取消当前 member 订阅 |
| `GET` | `/api/v1/we-rss/feeds/{id}/tags/` | 获取当前 member 在该 feed 上的标签 |
| `POST` | `/api/v1/we-rss/feeds/{id}/tags/attach/` | 给 feed 增量绑定标签 |
| `POST` | `/api/v1/we-rss/feeds/{id}/tags/detach/` | 给 feed 增量解绑标签 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/articles/` | 永久清空该公众号下全部文章记录 |
| `POST` | `/api/v1/we-rss/feeds/{id}/sync/` | 触发公众号同步 |
| `GET` | `/api/v1/we-rss/tags/` | 获取当前 member 标签列表 |
| `POST` | `/api/v1/we-rss/tags/` | 创建当前 member 私有标签 |
| `GET` | `/api/v1/we-rss/tags/{id}/` | 获取标签详情 |
| `PUT` | `/api/v1/we-rss/tags/{id}/` | 更新标签 |
| `DELETE` | `/api/v1/we-rss/tags/{id}/` | 删除标签 |
| `GET` | `/api/v1/we-rss/articles/` | 获取文章列表 |
| `GET` | `/api/v1/we-rss/articles/{id}/` | 获取文章详情 |
| `DELETE` | `/api/v1/we-rss/articles/{id}/` | 软删除文章 |
| `POST` | `/api/v1/we-rss/article-stats/refresh-by-url/` | 按 URL 同步刷新文章统计并返回完整文章 |
| `POST` | `/api/v1/we-rss/article-stats/refresh/` | 批量异步刷新文章统计 |
| `POST` | `/api/v1/we-rss/articles/import-by-url/` | 按 URL 导入文章 |
| `POST` | `/api/v1/we-rss/articles/{id}/refresh/` | 刷新文章正文 |
| `PUT` | `/api/v1/we-rss/articles/{id}/favorite/` | 更新收藏状态 |
| `GET` | `/api/v1/we-rss/articles/{id}/tags/` | 获取当前 member 在该文章上的标签 |
| `POST` | `/api/v1/we-rss/articles/{id}/tags/attach/` | 给文章增量绑定标签 |
| `POST` | `/api/v1/we-rss/articles/{id}/tags/detach/` | 给文章增量解绑标签 |
| `GET` | `/api/v1/we-rss/tasks/` | 获取任务列表 |
| `GET` | `/api/v1/we-rss/tasks/{task_id}/` | 获取任务详情 |
| `GET` | `/api/v1/we-rss/rss/` | 当前 tenant 聚合 RSS |
| `GET` | `/api/v1/we-rss/rss/{feed_id}/` | 单个公众号 RSS |
| `GET` | `/api/v1/we-rss/rss/content/{article_id}/` | 文章正文 HTML |

## 6. 对象结构总览

### 6.1 公众号对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 公众号 ID |
| `credential_id` | `number \| null` | 绑定凭证 ID |
| `source_id` | `string` | 微信来源 ID |
| `faker_id` | `string` | fakeid / faker_id |
| `biz` | `string` | 微信 biz |
| `mp_name` | `string` | 名称 |
| `mp_cover` | `string` | 头像 |
| `mp_intro` | `string` | 简介 |
| `status` | `string` | 当前状态 |
| `sync_time` | `string \| null` | 最近同步时间 |
| `update_time` | `string \| null` | 最近更新时间 |
| `last_synced_at` | `string \| null` | 最近同步完成时间 |
| `is_featured` | `boolean` | 是否精选 |
| `is_subscribed` | `boolean` | 当前 member 是否订阅 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

### 6.2 文章对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 文章 ID |
| `feed_id` | `number \| null` | 所属公众号 ID |
| `source_id` | `string` | 微信文章来源 ID |
| `article_type` | `string` | 文章类型，支持 `news` 和 `newspic` |
| `title` | `string` | 标题 |
| `description` | `string` | 摘要 |
| `content` | `string` | 正文 HTML |
| `url` | `string` | 归一化后的公开文章 URL |
| `pic_url` | `string` | 封面 URL |
| `publish_time` | `string \| null` | 发布时间 |
| `status` | `string` | 文章状态 |
| `is_favorite` | `boolean` | 当前 member 是否收藏 |
| `last_refreshed_at` | `string \| null` | 最近刷新时间 |
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

### 6.3 任务对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 任务 ID |
| `task_type` | `string` | 任务类型 |
| `status` | `string` | `pending / running / success / failed` |
| `task_key` | `string` | 去重键 |
| `target_type` | `string` | 目标类型 |
| `target_id` | `number \| null` | 目标 ID |
| `message` | `string` | 任务说明 |
| `request_payload` | `object \| null` | 请求参数快照 |
| `result_payload` | `object \| null` | 结果快照 |
| `celery_task_id` | `string` | Celery 任务 ID |
| `started_at` | `string \| null` | 开始时间 |
| `finished_at` | `string \| null` | 结束时间 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

## 7. 公众号接口说明

### 7.1 获取公众号列表

```http
GET /api/v1/we-rss/feeds/
GET /api/v1/we-rss/feeds/?subscribed_only=true
GET /api/v1/we-rss/feeds/?tag_ids=1,2,3
```

### 7.2 搜索微信平台公众号

```http
GET /api/v1/we-rss/feeds/search/?keyword=AI
```

这里搜的是微信平台，不是本地数据库。

### 7.3 订阅公众号

```http
POST /api/v1/we-rss/feeds/subscribe/
Content-Type: application/json
```

标准流程是：先搜索，再订阅。

### 7.4 触发公众号同步

```http
POST /api/v1/we-rss/feeds/{id}/sync/
```

返回的是父任务 `feed_sync_run`，不是文章列表。

前端拿到这个任务后，必须轮询：

```http
GET /api/v1/we-rss/tasks/{task_id}/
```

公众号同步的前端处理规则如下：

- 每 5 秒轮询一次父任务。
- 如果 `result_payload.latest_completed_batch` 不存在，说明当前还没有一批可消费数据。
- 如果 `result_payload.latest_completed_batch.batch_no` 比前端上一次处理过的批次号大，前端就刷新一次文章列表，或者只把这一批文章追加一次。
- 如果 `result_payload.latest_completed_batch.batch_no` 没变化，前端不要重复刷新，避免同一批数据重复渲染。
- 如果再次点击同步，而后端返回的是同一个运行中的父任务，前端继续轮询这个父任务即可。

## 8. 标签接口说明

### 8.1 当前 member 标签

```http
GET /api/v1/we-rss/tags/
POST /api/v1/we-rss/tags/
GET /api/v1/we-rss/tags/{id}/
PUT /api/v1/we-rss/tags/{id}/
DELETE /api/v1/we-rss/tags/{id}/
```

### 8.2 feed 标签

```http
GET /api/v1/we-rss/feeds/{id}/tags/
POST /api/v1/we-rss/feeds/{id}/tags/attach/
POST /api/v1/we-rss/feeds/{id}/tags/detach/
```

### 8.3 article 标签

```http
GET /api/v1/we-rss/articles/{id}/tags/
POST /api/v1/we-rss/articles/{id}/tags/attach/
POST /api/v1/we-rss/articles/{id}/tags/detach/
```

## 9. 文章接口说明

### 9.1 获取文章列表

```http
GET /api/v1/we-rss/articles/
GET /api/v1/we-rss/articles/?article_type=newspic
GET /api/v1/we-rss/articles/?search=AI
GET /api/v1/we-rss/articles/?favorite_only=true
GET /api/v1/we-rss/articles/?tag_ids=1,2,3
```

支持参数如下：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `article_type` | `string` | 可选，支持 `news` 或 `newspic` |
| `search` | `string` | 可选，只按 `title` 搜索 |
| `favorite_only` | `boolean` | 可选，只返回当前 member 收藏文章 |
| `tag_ids` | `string` | 可选，逗号分隔标签 ID，多个标签使用 AND 语义 |

### 9.2 按 URL 导入文章

```http
POST /api/v1/we-rss/articles/import-by-url/
Content-Type: application/json
```

请求体如下：

```json
{
  "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
}
```

返回的是 `article_import` 任务。

### 9.3 按 URL 同步刷新文章统计

```http
POST /api/v1/we-rss/article-stats/refresh-by-url/
Content-Type: application/json
```

请求体如下：

```json
{
  "url": "https://mp.weixin.qq.com/s/article-1?token=123456"
}
```

这里要记住下面几条规则：

- 这是同步接口，不返回任务对象。
- URL 只能命中当前 tenant 下已经存在的文章，不会创建新文章。
- 后端会先更新数据库，再返回完整的 `WechatArticle` 对象。
- 只会刷新统计字段和 `last_refreshed_at`，不会刷新正文、标题、摘要、封面和发布时间。
- 如果当前 tenant 下找不到对应文章，返回 `404`。

### 9.4 批量异步刷新文章统计

```http
POST /api/v1/we-rss/article-stats/refresh/
Content-Type: application/json
```

请求体三选一：

```json
{
  "article_ids": [11, 12, 13]
}
```

```json
{
  "feed_id": 5
}
```

```json
{
  "member_id": 9
}
```

这里要记住下面几条规则：

- 这是异步接口，只返回 `article_stats_refresh` 任务。
- `article_ids`、`feed_id`、`member_id` 只能传一种。
- `article_ids` 会去重，但只要有任意一篇文章不属于当前 tenant 或不存在，就会直接返回 `400`。
- 任务完成后需要看 `result_payload.success_count`、`failed_count` 和 `failed_articles`。
- 即使有部分文章失败，只要整批执行完，任务状态仍然会是 `success`。

### 9.5 刷新文章正文

```http
POST /api/v1/we-rss/articles/{id}/refresh/
```

返回的是 `article_refresh` 任务。

这个接口和文章统计刷新接口的区别如下：

- `/articles/{id}/refresh/` 负责正文、摘要、封面、发布时间等内容刷新。
- `/article-stats/refresh-by-url/` 和 `/article-stats/refresh/` 只负责统计字段刷新。

### 9.6 更新收藏状态

```http
PUT /api/v1/we-rss/articles/{id}/favorite/
Content-Type: application/json
```

请求体如下：

```json
{
  "is_favorite": true
}
```

### 9.7 文章标签接口

```http
GET /api/v1/we-rss/articles/{id}/tags/
POST /api/v1/we-rss/articles/{id}/tags/attach/
POST /api/v1/we-rss/articles/{id}/tags/detach/
```

请求体如下：

```json
{
  "tag_ids": [1, 2, 3]
}
```

## 10. 同步任务说明

`we_rss` 当前常见的任务类型如下：

| task_type | 用途 |
| --- | --- |
| `credential_login` | 扫码登录 |
| `feed_sync_run` | 公众号同步父任务，前端轮询这个任务 |
| `feed_sync_batch` | 公众号同步子批次任务，前端一般不用直接消费 |
| `article_import` | 按 URL 导入文章 |
| `article_refresh` | 单篇文章正文刷新 |
| `article_stats_refresh` | 批量文章统计刷新 |

公众号同步父任务的 `result_payload` 常见结构如下：

```json
{
  "run_status": "running",
  "feed_id": 1,
  "batch_size": 20,
  "poll_after_seconds": 5,
  "has_more": true,
  "next_begin": 20,
  "batches_completed": 1,
  "batches_failed": 0,
  "articles_synced": 20,
  "articles_failed": 0,
  "article_ids": [11, 12, 13],
  "current_batch_task_id": 202,
  "latest_completed_batch": {
    "batch_no": 1,
    "begin": 0,
    "end": 20,
    "has_more": true,
    "article_count": 20,
    "article_ids": [11, 12, 13],
    "articles": [
      {
        "id": 11,
        "source_id": "article-1",
        "title": "Imported Article 1",
        "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
        "publish_time": "2026-03-20T12:00:00Z",
        "pic_url": "https://example.com/article-cover-1.png",
        "status": "active"
      }
    ],
    "failed_articles": [],
    "started_at": "2026-03-21T09:20:00Z",
    "finished_at": "2026-03-21T09:20:08Z"
  },
  "last_progress_at": "2026-03-21T09:20:08Z",
  "timeout_reason": ""
}
```

公众号同步任务最重要的语义是：

- 前端轮询的是 `feed_sync_run`，不是 `feed_sync_batch`。
- `poll_after_seconds` 当前固定是 `5`，前端按 5 秒轮询。
- 只要 `latest_completed_batch.batch_no` 发生变化，就表示后端又产出了一批新数据，前端应当刷新一次。
- 同一个 `batch_no` 只能消费一次，否则会重复插入同一批文章。
- `status` 可能是 `pending`、`running`、`success`、`partial_success`、
  `timed_out`、`failed`。
- `partial_success` 表示前面已经同步出部分批次，后面某一批失败或超时。
- `timed_out` 表示任务超时结束，前端要停止轮询，并按终态展示。

批量文章统计刷新任务完成时，`result_payload` 常见结构如下：

```json
{
  "task_type": "article_stats_refresh",
  "selector_type": "feed_id",
  "requested_count": 3,
  "success_count": 2,
  "failed_count": 1,
  "article_ids": [11, 12, 13],
  "failed_articles": [
    {
      "article_id": 13,
      "url": "https://mp.weixin.qq.com/s/article-13",
      "error": "stats blocked"
    }
  ]
}
```

这里最重要的语义是：

- `status === "success"` 只表示整批任务执行完。
- 是否存在单篇失败，要看 `failed_count` 和 `failed_articles`。

## 11. 前端封装示例

```ts
type ApiEnvelope<T> = {
  success: boolean;
  code: number;
  message: string;
  data: T;
};

async function weRssRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiEnvelope<T>> {
  const token = localStorage.getItem("member_access_token");
  const tenantId = localStorage.getItem("member_tenant_id");

  const response = await fetch(`/api/v1/we-rss${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": String(tenantId),
      ...(options.headers || {}),
    },
  });

  return response.json();
}

async function weRssTextRequest(path: string): Promise<string> {
  const token = localStorage.getItem("member_access_token");
  const tenantId = localStorage.getItem("member_tenant_id");

  const response = await fetch(`/api/v1/we-rss${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": String(tenantId),
    },
  });

  return response.text();
}
```

## 12. 最容易踩坑的点

- `we_rss` 是 tenant 共享主数据，不是 member 私有资源。
- `is_subscribed` 和 `is_favorite` 是当前 member 的个性化状态。
- 标签是当前 member 私有，不会直接内嵌到 `feeds/` 和 `articles/` 主响应。
- 当前没有 `is_read`，也没有 `PUT /articles/{id}/read/`。
- `GET /feeds/search/` 搜的是微信平台，不是本地库。
- 标准订阅流程是 `GET /feeds/search/` 后接 `POST /feeds/subscribe/`。
- feed 打标签前必须先订阅，article 打标签则不要求订阅 feed。
- `tag_ids` 是逗号分隔查询参数，多个标签使用 AND 语义。
- 文章列表已经支持服务端标题搜索，不要继续只做本地搜索。
- `search` 只搜标题，不搜正文。
- `POST /feeds/{id}/sync/`、`POST /articles/import-by-url/`、
  `POST /articles/{id}/refresh/`、`POST /article-stats/refresh/` 返回的都是任务对象。
- `POST /article-stats/refresh-by-url/` 返回的是更新后的整篇文章，不是任务对象。
- 只刷新统计时，不要误用 `/articles/{id}/refresh/`。
