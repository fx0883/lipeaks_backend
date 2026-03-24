# we_rss 前端群简版说明

这份说明是给前端群里直接转发用的短版同步说明，内容已经按当前 `we_rss`
真实实现更新过，尤其补充了最新数据结构变化。

## 这次前端要接什么

当前 `we_rss` 已开放的核心能力只有这些：

- 微信凭证管理
- 微信扫码登录
- 公众号搜索、创建、编辑、删除
- 公众号同步文章
- 文章列表、详情、已读、收藏、刷新、删除
- 异步任务轮询
- tenant RSS、feed RSS、正文 HTML 输出

这里的文章是 `WechatArticle`，和 `cms.Article` 没关系，不要混用。

## 这次结构变化最重要的点

`we_rss` 下面的核心模型现在都继承了 `BaseModel`，所以数据库层统一有：

- `tenant`
- `created_at`
- `updated_at`
- `is_deleted`

但是前端接口返回字段仍然以 serializer 为准，不是模型里有就会返回。请务必按
文档里的“接口字段”来建类型，不要直接按 model 猜字段。

文章这里再额外注意一件事：`WechatArticle` 现在返回官方字段名
`article_type`，取值为 `news` 或 `newspic`，前端不要再按 `type` 建字段。

## 所有接口共同约束

所有 `we_rss` 接口都必须带：

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

另外要注意：

- `we_rss` 数据是 tenant 共享，不是 member 私有
- `DELETE` 现在按软删除理解
- RSS / HTML 接口也需要鉴权，不是公开链接

## 建议开发顺序

建议前端按下面顺序推进：

1. 先做统一请求层，自动带 token 和 `X-Tenant-ID`
2. 再做凭证与扫码登录
3. 再做公众号搜索、保存、同步
4. 再做统一任务轮询
5. 再做文章列表和详情
6. 最后做 RSS / HTML 调试页

## 当前已经有的核心接口

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
- `POST /api/v1/we-rss/feeds/`
- `GET /api/v1/we-rss/feeds/search/?keyword=...`
- `GET /api/v1/we-rss/feeds/{id}/`
- `PUT /api/v1/we-rss/feeds/{id}/`
- `DELETE /api/v1/we-rss/feeds/{id}/`
- `DELETE /api/v1/we-rss/feeds/{id}/articles/`
- `POST /api/v1/we-rss/feeds/{id}/sync/`

### 文章

- `GET /api/v1/we-rss/articles/`
- `GET /api/v1/we-rss/articles/?article_type=newspic`
- `GET /api/v1/we-rss/articles/{id}/`
- `DELETE /api/v1/we-rss/articles/{id}/`
- `POST /api/v1/we-rss/articles/import-by-url/`
- `POST /api/v1/we-rss/articles/{id}/refresh/`
- `PUT /api/v1/we-rss/articles/{id}/read/`
- `PUT /api/v1/we-rss/articles/{id}/favorite/`

### 任务

- `GET /api/v1/we-rss/tasks/`
- `GET /api/v1/we-rss/tasks/{task_id}/`

### RSS / 正文输出

- `GET /api/v1/we-rss/rss/`
- `GET /api/v1/we-rss/rss/{feed_id}/`
- `GET /api/v1/we-rss/rss/content/{article_id}/`

## 当前不要按旧前端直接照搬的能力

下面这些当前后端还没有，不要先按旧前端写死：

- 文章服务端分页
- 文章服务端搜索
- 文章服务端按公众号过滤
- 文章服务端仅收藏过滤
- 上一篇 / 下一篇文章
- OPML 导出
- Atom / JSON / Markdown / Text 等多格式输出
- 通过文章链接先识别公众号的专用接口

## 群里建议优先看的文档

如果是开发同学，先看：

1. [we_rss_前端联调清单版.md](./we_rss_前端联调清单版.md)
2. [we_rss_前端完整API文档.md](./we_rss_前端完整API文档.md)

如果是负责人，再补看：

3. [we_rss_前端开发排期版.md](./we_rss_前端开发排期版.md)
