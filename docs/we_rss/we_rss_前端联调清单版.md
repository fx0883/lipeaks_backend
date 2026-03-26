# we_rss 前端联调清单版

这份文档按“实际联调顺序”整理，适合作为 checklist 使用。内容已经按当前实现
更新，重点修正了 member 订阅、member 收藏和文章标题搜索这三块。

## 0. 联调前总检查

在正式联调前，先确认下面这些基础前提都满足：

- [ ] 当前账号是 member 账号，不是管理员口径。
- [ ] member 已绑定 tenant。
- [ ] 请求层会自动带 `Authorization: Bearer <member_access_token>`。
- [ ] 请求层会自动带 `X-Tenant-ID`。
- [ ] `X-Tenant-ID` 与当前 member 真实 tenant 一致。
- [ ] JSON 请求和文本请求已经拆成两个读取入口。
- [ ] 前端知道 RSS / HTML 接口也需要鉴权。

## 1. 请求层联调

这一部分虽然不是业务页面，但一定要先通过。

- [ ] `GET /api/v1/we-rss/credentials/` 能正常返回。
- [ ] 漏传 `X-Tenant-ID` 时，前端能识别并提示。
- [ ] 文本接口不会误用 `response.json()`。
- [ ] 统一请求层能处理 `204 No Content`。

## 2. 凭证与扫码登录联调

先把登录态链路跑通，因为后面公众号搜索和文章导入都依赖有效凭证。

- [ ] `GET /credentials/` 能返回当前 tenant 的凭证数组。
- [ ] 列表能展示 `name`、`status`、`is_default`、`last_check_at`。
- [ ] `POST /credentials/login-sessions/` 能返回 `session_id`。
- [ ] 页面能展示 `qr_code_image`。
- [ ] 前端能轮询 `GET /credentials/login-sessions/{session_id}/`。
- [ ] 轮询成功时能拿到 `credential_id`。
- [ ] `POST /credentials/{id}/set-default/` 可用。
- [ ] `POST /credentials/{id}/check/` 可用。
- [ ] `PUT /credentials/{id}/` 只传 `name` 时可成功。
- [ ] `DELETE /credentials/{id}/` 返回 `204`。

## 3. 公众号联调

### 3.1 搜索微信公众号

- [ ] `GET /feeds/search/?keyword=...` 可返回搜索结果。
- [ ] 没有有效凭证时，前端能识别搜索失败原因。
- [ ] 搜索结果页能展示 `mp_name`、`mp_cover`、`mp_intro`。
- [ ] 前端知道搜索返回的是搜索结果对象，不是本地已保存 feed。

### 3.2 订阅公众号

- [ ] `POST /feeds/subscribe/` 可用。
- [ ] 能直接把搜索结果负载提交给订阅接口。
- [ ] 订阅成功后返回对象里 `is_subscribed = true`。
- [ ] 同一个 feed 被重复订阅时，前端能接受“复用已存在关系”的行为。

### 3.3 公众号列表与详情

- [ ] `GET /feeds/` 可用。
- [ ] `GET /feeds/?subscribed_only=true` 可用。
- [ ] 列表能展示 `mp_name`、`mp_intro`、`last_synced_at`、`is_subscribed`。
- [ ] `GET /feeds/{id}/` 可用。
- [ ] `PUT /feeds/{id}/` 可用。
- [ ] `DELETE /feeds/{id}/` 返回 `204`。
- [ ] `DELETE /feeds/{id}/subscribe/` 返回 `204`。
- [ ] 前端知道取消订阅不会删除 feed 主数据。

### 3.4 同步公众号

- [ ] `POST /feeds/{id}/sync/` 返回任务对象。
- [ ] 前端不会把它当成“文章列表立即返回”接口。
- [ ] 同步后能进入任务轮询。
- [ ] 同步成功后文章列表能刷新。
- [ ] 重复点击同步时，前端能接受“复用运行中任务”的行为。

### 3.5 清空公众号文章

- [ ] `DELETE /feeds/{id}/articles/` 可用。
- [ ] 前端知道这是永久删除当前 feed 下文章记录，不是软删除。
- [ ] 前端能展示 `deleted_count`。

## 4. 任务轮询联调

这一部分最好抽成统一模块。

- [ ] `GET /tasks/{task_id}/` 能稳定轮询。
- [ ] `pending / running / success / failed` 四态处理正确。
- [ ] 超时机制已实现。
- [ ] 失败时优先展示 `result_payload.error` 或 `message`。
- [ ] 前端知道 `result_payload` 会随 `task_type` 变化。

## 5. 文章联调

### 5.1 文章列表

- [ ] `GET /articles/` 能返回当前 tenant 文章。
- [ ] 页面能展示 `title`、`feed_id`、`publish_time`、`article_type`、`is_favorite`。
- [ ] `GET /articles/?article_type=newspic` 可用。
- [ ] `GET /articles/?search=AI` 可用。
- [ ] `GET /articles/?favorite_only=true` 可用。
- [ ] 前端知道 `search` 只搜标题，不搜正文。
- [ ] 前端知道当前没有 `is_read` 字段。

### 5.2 按 URL 导入文章

- [ ] `POST /articles/import-by-url/` 返回任务对象。
- [ ] 前端知道导入是异步流程。
- [ ] 导入成功后能从 `result_payload.article_id` 定位文章。
- [ ] 前端知道导入会自动创建或复用精选 feed。

### 5.3 收藏文章

- [ ] `PUT /articles/{id}/favorite/` 可更新 `is_favorite`。
- [ ] 成功后当前条目状态能同步更新。
- [ ] 前端知道这里更新的是“当前 member 的收藏关系”。

### 5.4 刷新文章

- [ ] `POST /articles/{id}/refresh/` 返回任务对象。
- [ ] 刷新成功后 `last_refreshed_at` 发生变化。
- [ ] 前端知道刷新优先使用 feed 绑定凭证。
- [ ] 同一文章运行中刷新任务会复用。

### 5.5 删除文章

- [ ] `DELETE /articles/{id}/` 返回 `204`。
- [ ] 前端知道删除文章是软删除。
- [ ] 删除后列表状态处理正确。

## 6. 文章详情联调

- [ ] `GET /articles/{id}/` 可返回完整文章对象。
- [ ] 页面能展示 `title`、`description`、`publish_time`。
- [ ] 页面能渲染 `content`。
- [ ] 页面能跳转 `url`。
- [ ] 前端没有依赖“上一篇 / 下一篇”接口。

## 7. RSS 与正文输出联调

### 7.1 RSS

- [ ] `GET /rss/` 能返回 XML 文本。
- [ ] `GET /rss/{feed_id}/` 能返回 XML 文本。
- [ ] 前端用 `response.text()` 读取。
- [ ] 前端知道这不是匿名公开链接。

### 7.2 正文 HTML

- [ ] `GET /rss/content/{article_id}/` 能返回 HTML 文本。
- [ ] 前端用 `response.text()` 读取。
- [ ] HTML 注入页面前已按项目安全策略处理。

## 8. 字段口径核对

这一部分非常重要，联调时建议逐项确认。

- [ ] 凭证接口不返回 `token`。
- [ ] 凭证接口不返回 `cookie`。
- [ ] 登录会话接口不返回 `token_snapshot`。
- [ ] 登录会话接口不返回 `cookie_snapshot`。
- [ ] 公众号接口返回的是 `credential_id`，不是完整 `credential` 对象。
- [ ] 文章接口返回的是 `feed_id`，不是完整 `feed` 对象。
- [ ] 文章接口没有 `is_read`。
- [ ] 任务接口的 `result_payload` 没有被前端写死成固定结构。

## 9. 当前不要误接的旧能力

联调时如果发现页面有这些需求，不要误以为后端已经支持：

- [ ] 文章 `read` 接口
- [ ] 文章 `is_read` 字段
- [ ] 文章按 `feed_id` 服务端过滤
- [ ] 文章未读过滤
- [ ] 上一篇 / 下一篇文章接口
- [ ] OPML 导出
- [ ] Atom / JSON / Markdown / Text 多格式输出

## 10. 最终联调通过口径

如果下面这些都通过，可以认为本期联调完成：

- [ ] 请求层统一正常。
- [ ] 扫码登录成功生成凭证。
- [ ] 默认凭证设置成功。
- [ ] 公众号搜索可用。
- [ ] 公众号订阅和取消订阅可用。
- [ ] 公众号同步可用。
- [ ] 文章列表、搜索、收藏可用。
- [ ] 文章详情、刷新、删除可用。
- [ ] RSS / HTML 输出可读。
