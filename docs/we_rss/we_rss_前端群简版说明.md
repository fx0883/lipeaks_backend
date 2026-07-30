# we_rss 前端群简版说明

这份说明适合直接转给前端群里同步现状。内容已经按当前 `we_rss` 真实实现更新，
重点是统一“tenant 共享主数据 + member 个性化状态”的口径，并补上文章统计刷新。

## 这次前端要接什么

当前 `we_rss` 已开放的核心能力如下：

- 微信凭证管理
- 微信扫码登录
- 公众号搜索
- member 订阅公众号和取消订阅
- 公众号同步文章
- 文章列表、标题搜索、收藏、详情、正文刷新、统计刷新、删除
- 异步任务轮询
- tenant RSS、单 feed RSS、正文 HTML 输出

## 这次最重要的结构变化

当前必须统一下面几条认知：

- `we_rss` 主数据仍然是 tenant 共享，不是 member 私有。
- `WechatFeed` 和 `WechatArticle` 是 tenant 共享主数据。
- `is_subscribed` 是当前 member 对 feed 的订阅状态。
- `is_favorite` 是当前 member 对 article 的收藏状态。
- 当前没有 `is_read`，也没有 `PUT /articles/{id}/read/`。
- 文章列表已支持服务端标题搜索，只搜 `title`。
- 文章“正文刷新”和“统计刷新”是两套独立能力：
  - `POST /api/v1/we-rss/articles/{id}/refresh/` 是正文刷新，返回任务。
  - `POST /api/v1/we-rss/article-stats/refresh-by-url/` 是单篇统计同步刷新，直接返回文章。
  - `POST /api/v1/we-rss/article-stats/refresh/` 是批量统计异步刷新，返回 `article_stats_refresh` 任务。

## 所有接口共同约束

所有 `we_rss` 请求都必须带：

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

另外要注意：

- RSS / HTML 接口也需要鉴权，不是公开链接。
- `DELETE` 默认按软删除理解，只有清空 feed 文章是物理删除。

## 当前核心接口

### 凭证与扫码登录

- `GET /api/v1/we-rss/credentials/`
- `GET /api/v1/we-rss/credentials/{id}/`
- `PUT /api/v1/we-rss/credentials/{id}/`
- `DELETE /api/v1/we-rss/credentials/{id}/`
- `POST /api/v1/we-rss/credentials/{id}/check/`
- `POST /api/v1/we-rss/credentials/{id}/set-default/`
- `POST /api/v1/we-rss/credentials/login-sessions/`
- `GET /api/v1/we-rss/credentials/login-sessions/{session_id}/`

### 公众号

- `GET /api/v1/we-rss/feeds/`
- `GET /api/v1/we-rss/feeds/?subscribed_only=true`
- `GET /api/v1/we-rss/feeds/search/?keyword=...`
- `POST /api/v1/we-rss/feeds/subscribe/`
- `GET /api/v1/we-rss/feeds/{id}/`
- `PUT /api/v1/we-rss/feeds/{id}/`
- `DELETE /api/v1/we-rss/feeds/{id}/`
- `DELETE /api/v1/we-rss/feeds/{id}/subscribe/`
- `DELETE /api/v1/we-rss/feeds/{id}/articles/`
- `POST /api/v1/we-rss/feeds/{id}/sync/`

### 文章

- `GET /api/v1/we-rss/articles/`
- `GET /api/v1/we-rss/articles/?article_type=newspic`
- `GET /api/v1/we-rss/articles/?search=AI`
- `GET /api/v1/we-rss/articles/?favorite_only=true`
- `GET /api/v1/we-rss/articles/{id}/`
- `DELETE /api/v1/we-rss/articles/{id}/`
- `POST /api/v1/we-rss/articles/import-by-url/`
- `POST /api/v1/we-rss/article-stats/refresh-by-url/`
- `POST /api/v1/we-rss/article-stats/refresh/`
- `POST /api/v1/we-rss/articles/{id}/refresh/`
- `PUT /api/v1/we-rss/articles/{id}/favorite/`

### 任务

- `GET /api/v1/we-rss/tasks/`
- `GET /api/v1/we-rss/tasks/{task_id}/`

公众号同步时，前端只轮询父任务 `feed_sync_run`。当前约定是每 5 秒轮询
一次 `GET /api/v1/we-rss/tasks/{task_id}/`。如果
`result_payload.latest_completed_batch.batch_no` 变了，就说明后端又产出了一批
新文章，前端这时刷新一次文章列表，或者只追加这一批一次；如果 `batch_no`
没变，就不要重复刷新。

### RSS / 正文输出

- `GET /api/v1/we-rss/rss/`
- `GET /api/v1/we-rss/rss/{feed_id}/`
- `GET /api/v1/we-rss/rss/content/{article_id}/`

## 当前标准链路

前端建议按这条链路做：

1. 扫码登录，拿到有效凭证。
2. 搜索公众号。
3. 用搜索结果调用 `POST /feeds/subscribe/`。
4. 对已订阅 feed 调 `POST /feeds/{id}/sync/`。
5. 在文章列表里用 `search`、`article_type`、`favorite_only` 做筛选。
6. 用 `PUT /articles/{id}/favorite/` 做收藏切换。
7. 对单篇文章需要更新统计时，调 `POST /article-stats/refresh-by-url/`。
8. 对批量文章需要更新统计时，调 `POST /article-stats/refresh/` 并轮询任务。

## 当前不要按旧习惯去做的事

下面这些口径已经过期了，不要继续沿用：

- 不要再接 `PUT /articles/{id}/read/`。
- 不要再把 `is_read` 当返回字段。
- 不要再把“搜索结果保存 feed”的标准流程写成 `POST /feeds/`。
- 不要再写“文章列表不支持服务端搜索”。
- 不要把 `/articles/{id}/refresh/` 当成统计刷新接口。

## 下一步

如果你需要一份完整对接文档，直接看
[we_rss_前端完整API文档.md](./we_rss_前端完整API文档.md)。如果你现在在联调，
直接看 [we_rss_前端联调清单版.md](./we_rss_前端联调清单版.md)。
