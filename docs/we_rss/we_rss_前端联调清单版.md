# we_rss 前端联调清单版

这份文档按“实际联调顺序”整理，不按后端模块拆，而是按前端页面和链路一步一步
打勾。你可以把它当成联调 checklist 使用。

本文已经按当前真实实现更新，重点补充了三类高风险点：

- `we_rss` 数据是 tenant 共享
- 所有核心模型都对齐 `BaseModel`
- 删除行为是软删除，不是物理删除

## 0. 联调前总检查

在正式联调前，先确认下面这些基础前提都满足。

- [ ] 当前账号是成员账号，不是管理员账号口径
- [ ] 成员账号已绑定 tenant
- [ ] 请求层会自动带 `Authorization: Bearer <member_access_token>`
- [ ] 请求层会自动带 `X-Tenant-ID`
- [ ] `X-Tenant-ID` 与当前成员真实 tenant 一致
- [ ] JSON 请求和文本请求已经拆成两个读取入口
- [ ] 前端知道 RSS / HTML 接口也需要鉴权

## 1. 请求层联调

这一部分虽然不是业务页面，但一定要先通过。

- [ ] `GET /api/v1/we-rss/credentials/` 能正常返回
- [ ] 漏传 `X-Tenant-ID` 时，前端能识别并提示
- [ ] 文本接口不会误用 `response.json()`
- [ ] 统一请求层能处理 `204 No Content`

建议自测接口：

- `GET /api/v1/we-rss/credentials/`
- `GET /api/v1/we-rss/rss/`

## 2. 凭证与扫码登录联调

先把登录态链路跑通，因为后面公众号搜索和文章导入都依赖有效凭证。

### 2.1 凭证列表

- [ ] `GET /credentials/` 能返回当前 tenant 的凭证数组
- [ ] 列表能展示 `name`、`status`、`is_default`、`last_check_at`
- [ ] 前端没有错误假设 `token`、`cookie` 会出现在响应中

### 2.2 扫码登录

- [ ] `POST /credentials/login-sessions/` 能返回 `session_id`
- [ ] 页面能展示 `qr_code_image`
- [ ] 前端能保存 `session_id`
- [ ] 前端能轮询 `GET /credentials/login-sessions/{session_id}/`
- [ ] 轮询成功时能拿到 `credential_id`
- [ ] `failed` 和 `expired` 状态能正确处理

### 2.3 默认凭证与检查

- [ ] `POST /credentials/{id}/set-default/` 可用
- [ ] 默认凭证切换后列表展示正确
- [ ] `POST /credentials/{id}/check/` 可用
- [ ] 检查后能看到最新 `status` 和 `last_error`

### 2.4 凭证更新与删除

- [ ] `PUT /credentials/{id}/` 只传 `name` 时可成功
- [ ] 传 `token` 或 `cookie` 时前端知道这是错误调用
- [ ] `DELETE /credentials/{id}/` 返回 `204`
- [ ] 前端知道凭证删除是软删除

## 3. 公众号联调

### 3.1 微信平台搜索

- [ ] `GET /feeds/search/?keyword=...` 可返回搜索结果
- [ ] 没有有效凭证时，前端能识别搜索失败原因
- [ ] 搜索结果页展示 `mp_name`、`mp_cover`、`mp_intro`
- [ ] 前端知道搜索返回的是结果对象，不是本地已保存 feed

### 3.2 创建公众号

- [ ] `POST /feeds/` 能保存搜索结果为本地公众号
- [ ] 前端只从当前 tenant 凭证列表中选择 `credential_id`
- [ ] 前端知道传错 tenant 的 `credential_id` 可能不会报错，但会绑定失败
- [ ] 创建成功后列表可见

### 3.3 编辑与删除公众号

- [ ] `GET /feeds/{id}/` 可用
- [ ] `PUT /feeds/{id}/` 可用
- [ ] `DELETE /feeds/{id}/` 返回 `204`
- [ ] 前端知道删除公众号是软删除

### 3.4 同步公众号

- [ ] `POST /feeds/{id}/sync/` 返回任务对象
- [ ] 前端不会把它当成“文章列表立即返回”接口
- [ ] 同步后能进入任务轮询
- [ ] 同步成功后文章列表能刷新
- [ ] 重复点击同步时，前端能接受“返回已有运行中任务”的行为

### 3.5 清空公众号文章

- [ ] `DELETE /feeds/{id}/articles/` 可用
- [ ] 前端知道这是永久删除当前 feed 下文章记录，不是软删除
- [ ] 前端能展示 `deleted_count`

## 4. 任务轮询联调

这部分最好抽成统一模块，别让每个页面各写一套。

- [ ] `GET /tasks/{task_id}/` 能稳定轮询
- [ ] `pending / running / success / failed` 四态处理正确
- [ ] 超时机制已实现
- [ ] 失败时优先显示 `result_payload.error`
- [ ] 前端知道 `result_payload` 会随 `task_type` 变化

建议分别验证这四类任务：

- [ ] `credential_login`
- [ ] `feed_sync`
- [ ] `article_import`
- [ ] `article_refresh`

## 5. 文章联调

### 5.1 文章列表

- [ ] `GET /articles/` 能返回当前 tenant 文章
- [ ] 页面能展示 `title`、`feed_id`、`publish_time`、`article_type`、`is_read`、`is_favorite`
- [ ] 前端知道当前没有服务端分页
- [ ] 前端知道当前支持 `article_type` 服务端过滤
- [ ] 前端知道当前没有服务端搜索和其它文章服务端过滤

### 5.2 按 URL 导入文章

- [ ] `POST /articles/import-by-url/` 返回任务对象
- [ ] 前端知道导入是异步流程
- [ ] 导入成功后能从 `result_payload.article_id` 定位文章
- [ ] 前端知道导入会自动创建或复用精选 feed
- [ ] 相同 URL 的运行中导入任务会去重复用

### 5.3 已读与收藏

- [ ] `PUT /articles/{id}/read/` 可更新 `is_read`
- [ ] `PUT /articles/{id}/favorite/` 可更新 `is_favorite`
- [ ] 成功后页面条目状态同步更新

### 5.4 刷新文章

- [ ] `POST /articles/{id}/refresh/` 返回任务对象
- [ ] 刷新成功后 `last_refreshed_at` 发生变化
- [ ] 前端知道刷新优先使用 feed 绑定凭证
- [ ] 同一文章运行中刷新任务会去重复用

### 5.5 删除文章

- [ ] `DELETE /articles/{id}/` 返回 `204`
- [ ] 前端知道删除文章是软删除
- [ ] 删除后列表状态处理正确

## 6. 文章详情联调

- [ ] `GET /articles/{id}/` 可返回完整文章对象
- [ ] 页面能展示 `title`、`description`、`publish_time`
- [ ] 页面能渲染 `content`
- [ ] 页面能跳转 `url`
- [ ] 前端没有依赖“上一篇 / 下一篇”接口

## 7. RSS 与正文输出联调

### 7.1 RSS

- [ ] `GET /rss/` 能返回 XML 文本
- [ ] `GET /rss/{feed_id}/` 能返回 XML 文本
- [ ] 前端用 `response.text()` 读取
- [ ] 前端知道这不是匿名公开链接

### 7.2 正文 HTML

- [ ] `GET /rss/content/{article_id}/` 能返回 HTML 文本
- [ ] 前端用 `response.text()` 读取
- [ ] HTML 注入页面前已按项目安全策略处理

## 8. 字段口径核对

这部分非常重要，建议联调时逐项确认。

- [ ] 凭证接口不返回 `token`
- [ ] 凭证接口不返回 `cookie`
- [ ] 登录会话接口不返回 `token_snapshot`
- [ ] 登录会话接口不返回 `cookie_snapshot`
- [ ] 公众号接口返回的是 `credential_id`，不是完整 `credential` 对象
- [ ] 文章接口返回的是 `feed_id`，不是完整 `feed` 对象
- [ ] 任务接口的 `result_payload` 没有被前端写死成固定结构

## 9. 当前不要误接的旧能力

联调时如果发现页面有这些需求，先不要误以为后端已经支持。

- [ ] 文章服务端分页
- [ ] 文章服务端搜索
- [ ] 文章服务端按公众号过滤
- [ ] 文章服务端仅收藏过滤
- [ ] 上一篇 / 下一篇文章
- [ ] OPML 导出
- [ ] Atom / JSON / Markdown / Text 多格式输出
- [ ] 通过文章链接先识别公众号的专用接口

## 10. 最终联调通过口径

如果下面 10 条都通过，可以认为本期联调完成：

- [ ] 请求层统一正常
- [ ] 扫码登录成功生成凭证
- [ ] 默认凭证设置成功
- [ ] 公众号搜索可用
- [ ] 公众号创建可用
- [ ] 公众号同步可用
- [ ] 文章列表可见
- [ ] 文章已读 / 收藏 / 刷新 / 删除可用
- [ ] 文章详情可读
- [ ] RSS / HTML 输出可读

## 配套文档

需要更详细字段说明时，请继续看：

- [we_rss_前端完整API文档.md](./we_rss_前端完整API文档.md)
- [01_凭证与扫码登录API.md](./01_凭证与扫码登录API.md)
- [02_公众号API.md](./02_公众号API.md)
- [03_公众号文章API.md](./03_公众号文章API.md)
