# we_rss 前端群简版说明

这份说明是给前端群直接转发用的短版本。你可以把它理解成“现在能做什么、
先看哪份文档、按什么顺序开发”的速读说明。

## 这次前端要接什么

当前 `we_rss` 已经整理好的能力范围只有这几块：

- 微信凭证管理
- 微信扫码登录
- 公众号搜索与创建
- 公众号同步文章
- 公众号文章列表、详情、已读、收藏、刷新、删除
- 异步任务轮询
- RSS XML 和文章正文 HTML 输出

这里的文章是 `WechatArticle`，和现有 `cms.Article` 没关系，不要混用。

## 所有接口的公共约束

前端调用所有 `we_rss` 接口时都必须带：

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

要注意两点：

- `we_rss` 数据是 tenant 共享，不是 member 私有
- RSS 和正文 HTML 接口也必须鉴权，不是公开链接

## 建议前端先看哪几份文档

如果你是前端开发同学，建议按下面顺序阅读。

1. [we_rss_前端联调清单版.md](./we_rss_%E5%89%8D%E7%AB%AF%E8%81%94%E8%B0%83%E6%B8%85%E5%8D%95%E7%89%88.md)
2. [we_rss_前端完整API文档.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%AE%8C%E6%95%B4API%E6%96%87%E6%A1%A3.md)

如果你是前端负责人，建议加看：

3. [we_rss_前端开发排期版.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%BC%80%E5%8F%91%E6%8E%92%E6%9C%9F%E7%89%88.md)

## 建议开发顺序

前端建议按下面顺序推进：

1. 先做统一请求层，自动带 token 和 `X-Tenant-ID`
2. 再做微信凭证与扫码登录页
3. 再做新增公众号 / 导入文章页
4. 再做公众号管理页
5. 再做文章列表页
6. 再做文章详情阅读页
7. 最后做 RSS / HTML 调试页

## 本期最小可用链路

本期前端只要跑通下面这条链路，就算主目标完成：

1. 扫码登录，生成微信凭证
2. 把某个凭证设为默认
3. 搜索公众号并保存
4. 触发公众号同步
5. 在文章列表里看到同步下来的文章
6. 对文章做已读、收藏、刷新
7. 打开文章详情查看正文

## 当前后端已经有的核心接口

### 凭证与扫码登录

- `GET /api/v1/we-rss/credentials/`
- `POST /api/v1/we-rss/credentials/login-sessions/`
- `GET /api/v1/we-rss/credentials/login-sessions/{session_id}/`
- `POST /api/v1/we-rss/credentials/{id}/set-default/`
- `POST /api/v1/we-rss/credentials/{id}/check/`

### 公众号

- `GET /api/v1/we-rss/feeds/`
- `GET /api/v1/we-rss/feeds/search/?keyword=...`
- `POST /api/v1/we-rss/feeds/`
- `PUT /api/v1/we-rss/feeds/{id}/`
- `DELETE /api/v1/we-rss/feeds/{id}/`
- `POST /api/v1/we-rss/feeds/{id}/sync/`

### 文章

- `GET /api/v1/we-rss/articles/`
- `GET /api/v1/we-rss/articles/{id}/`
- `POST /api/v1/we-rss/articles/import-by-url/`
- `POST /api/v1/we-rss/articles/{id}/refresh/`
- `PUT /api/v1/we-rss/articles/{id}/read/`
- `PUT /api/v1/we-rss/articles/{id}/favorite/`
- `DELETE /api/v1/we-rss/articles/{id}/`

### 任务

- `GET /api/v1/we-rss/tasks/`
- `GET /api/v1/we-rss/tasks/{task_id}/`

### RSS / 正文输出

- `GET /api/v1/we-rss/rss/`
- `GET /api/v1/we-rss/rss/{feed_id}/`
- `GET /api/v1/we-rss/rss/content/{article_id}/`

## 当前不要按旧前端直接照搬的能力

旧项目 `we-mp-rss-main` 前端里有一些能力，这次后端还没提供，前端不要先按
旧接口写死。

- 文章服务端分页
- 文章服务端搜索
- 文章服务端按公众号过滤
- 仅收藏服务端过滤
- 上一篇 / 下一篇文章
- 公众号导入 / 导出
- OPML 导出
- 多格式 RSS，比如 Atom / JSON / Markdown / Text
- 通过文章链接识别公众号信息的专用接口

这些能力如果页面上需要，本期建议先做：

- 本地过滤
- UI 占位
- 后续单独提后端需求

## 推荐分工

如果前端有 3 个人，建议这样拆：

1. A 负责请求层 + 任务轮询 + 扫码登录页
2. B 负责新增公众号页 + 公众号管理页
3. C 负责文章列表页 + 文章详情页 + RSS 页

如果只有 1 到 2 个人，优先级顺序是：

1. 请求层
2. 扫码登录
3. 公众号搜索与同步
4. 文章列表与详情

## 最后一句给前端同学

先不要被旧前端页面带偏，当前请以前面几份 `docs/we_rss` 文档和
`/api/v1/we-rss/` 真实接口为准。
