# we_rss 前端完整 API 文档

这是一份给前端直接使用的单文件总文档。它基于当前仓库中 `we_rss` 的真实代码
重新整理，覆盖了全部已开放接口、最新数据结构变化、字段说明、任务行为和
联调建议。你如果只想保留一份文档给前端，优先发这一份就可以。

这次文档更新最重要的一点不是多了哪些接口，而是 `we_rss` 下全部核心模型都已
经继承 `BaseModel`。这使得数据库模型层字段、接口层返回字段、接口层可写字段
之间出现了明显差异。前端如果继续沿用“model 有什么字段，接口就会返回什么”
的思路，很容易踩坑。

## 1. 模块范围

`we_rss` 当前覆盖下面几类能力：

- 微信凭证管理
- 微信扫码登录
- 公众号搜索、保存、编辑、删除
- 公众号同步
- 公众号文章列表、详情、导入、刷新、已读、收藏、删除
- 异步同步任务查询
- tenant RSS、feed RSS、正文 HTML 输出

这里的文章模型是 `WechatArticle`，不是项目中的 `cms.Article`。

## 2. 基础地址

```text
/api/v1/we-rss/
```

本地开发通常是：

```text
http://localhost:8000/api/v1/we-rss/
```

## 3. 鉴权与 tenant 规则

所有 `we_rss` 接口都要求成员鉴权，并且必须带租户头。

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

必须牢记下面几条规则：

- 只有成员可以访问 `we_rss`。
- 成员必须有 tenant。
- `X-Tenant-ID` 必须等于当前成员绑定的 tenant。
- 所有数据都是 tenant 共享，不是 member 私有。
- RSS / HTML 接口也要求鉴权，不是公开链接。

## 4. 标准返回格式

普通 JSON 接口统一使用包装结构：

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

## 5. 最新数据结构变化

### 5.1 所有核心模型都继承 BaseModel

当前五个核心模型都已经继承 `BaseModel`：

- `WechatCredential`
- `WechatCredentialLoginSession`
- `WechatFeed`
- `WechatArticle`
- `WechatSyncTask`

统一新增或统一对齐的模型能力如下：

| 字段或能力 | 说明 |
| --- | --- |
| `tenant` | 归属租户 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |
| `is_deleted` | 软删除标记 |
| `objects` | 默认只查当前 tenant 且过滤已软删数据 |
| `original_objects` | 原始 manager |
| `soft_delete()` | 软删除方法 |

### 5.2 接口字段不等于模型字段

这次变化里，前端最需要注意的是：

- 模型层现在字段更多。
- serializer 仍然只暴露部分字段。
- 某些字段虽然在 serializer 中出现，但作用是显式拒绝写入。

比如：

- `WechatCredential` 模型里有 `token`、`cookie`、`tenant`、`is_deleted`。
- 但凭证 API 根本不会把 `token` 和 `cookie` 返回给前端。
- 更新凭证接口里即便出现了 `token` 和 `cookie`，传入也会直接报错。

### 5.3 DELETE 统一按软删除理解

由于这些模型都继承了 `BaseModel`，并且删除流程优先调用 `soft_delete()`，
所以 `we_rss` 下的 `DELETE` 接口现在都应该按“软删除”理解：

- 成功返回 `204 No Content`
- 记录被标记为 `is_deleted = true`
- 后续默认列表中消失

## 6. 接口总表

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
| `POST` | `/api/v1/we-rss/feeds/` | 创建公众号记录 |
| `GET` | `/api/v1/we-rss/feeds/search/?keyword=...` | 搜索微信平台公众号 |
| `GET` | `/api/v1/we-rss/feeds/{id}/` | 获取公众号详情 |
| `PUT` | `/api/v1/we-rss/feeds/{id}/` | 更新公众号 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/` | 软删除公众号 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/articles/` | 永久清空该公众号下全部文章记录 |
| `POST` | `/api/v1/we-rss/feeds/{id}/sync/` | 触发公众号同步 |
| `GET` | `/api/v1/we-rss/articles/` | 获取文章列表 |
| `GET` | `/api/v1/we-rss/articles/{id}/` | 获取文章详情 |
| `DELETE` | `/api/v1/we-rss/articles/{id}/` | 软删除文章 |
| `POST` | `/api/v1/we-rss/articles/import-by-url/` | 按 URL 导入文章 |
| `POST` | `/api/v1/we-rss/articles/{id}/refresh/` | 刷新文章 |
| `PUT` | `/api/v1/we-rss/articles/{id}/read/` | 更新已读状态 |
| `PUT` | `/api/v1/we-rss/articles/{id}/favorite/` | 更新收藏状态 |
| `GET` | `/api/v1/we-rss/tasks/` | 获取任务列表 |
| `GET` | `/api/v1/we-rss/tasks/{task_id}/` | 获取任务详情 |
| `GET` | `/api/v1/we-rss/rss/` | 当前 tenant 聚合 RSS |
| `GET` | `/api/v1/we-rss/rss/{feed_id}/` | 单个公众号 RSS |
| `GET` | `/api/v1/we-rss/rss/content/{article_id}/` | 文章正文 HTML |

## 7. 对象结构总览

### 7.1 凭证对象

接口返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 凭证 ID |
| `name` | `string` | 名称 |
| `status` | `string` | `pending / active / expired / invalid / disabled` |
| `expires_at` | `string \| null` | 过期时间 |
| `last_login_at` | `string \| null` | 最近登录时间 |
| `last_check_at` | `string \| null` | 最近检查时间 |
| `last_error` | `string` | 最近错误 |
| `is_default` | `boolean` | 是否默认 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

模型存在但不返回的字段：

- `tenant`
- `token`
- `cookie`
- `created_by`
- `updated_by`
- `is_deleted`

更新接口可写字段：

- `name`

更新接口显式拒绝字段：

- `token`
- `cookie`

### 7.2 登录会话对象

接口返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | `string` | 会话 ID |
| `status` | `string` | `pending / scanned / confirmed / success / failed / expired` |
| `qr_code_url` | `string` | 二维码地址 |
| `qr_code_image` | `string` | Data URL 图片 |
| `scan_status` | `string` | 当前扫描阶段 |
| `error_message` | `string` | 失败信息 |
| `expired_at` | `string \| null` | 过期时间 |
| `credential_id` | `number \| null` | 成功后凭证 ID |
| `task_id` | `number \| null` | 后台任务 ID |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

模型存在但不返回的字段：

- `tenant`
- `is_deleted`
- `token_snapshot`
- `cookie_snapshot`
- `created_by`

### 7.3 公众号对象

接口返回字段：

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
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

创建 / 更新可写字段：

- `credential_id`
- `source_id`
- `faker_id`
- `biz`
- `mp_name`
- `mp_cover`
- `mp_intro`
- `status`
- `is_featured`

### 7.4 文章对象

接口返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 文章 ID |
| `feed_id` | `number \| null` | 所属公众号 ID |
| `source_id` | `string` | 文章来源 ID |
| `title` | `string` | 标题 |
| `description` | `string` | 摘要 |
| `content` | `string` | 正文 HTML |
| `url` | `string` | 原始 URL |
| `article_type` | `string` | 文章类型，支持 `news` 和 `newspic` |
| `pic_url` | `string` | 封面 URL |
| `publish_time` | `string \| null` | 发布时间 |
| `status` | `string` | `active` 或 `deleted` 等 |
| `is_read` | `boolean` | 是否已读 |
| `is_favorite` | `boolean` | 是否收藏 |
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

文章可写动作当前只有三类：

- 按 URL 导入：`{ "url": "..." }`
- 已读状态：`{ "is_read": true }`
- 收藏状态：`{ "is_favorite": true }`

### 7.5 任务对象

接口返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 任务 ID |
| `task_type` | `string` | 任务类型 |
| `status` | `string` | `pending / running / success / failed` |
| `task_key` | `string` | 去重键 |
| `target_type` | `string` | 目标类型 |
| `target_id` | `number \| null` | 目标 ID |
| `message` | `string` | 当前消息 |
| `request_payload` | `object \| null` | 请求快照 |
| `result_payload` | `object \| null` | 结果快照 |
| `celery_task_id` | `string` | Celery ID |
| `started_at` | `string \| null` | 开始时间 |
| `finished_at` | `string \| null` | 完成时间 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

## 8. 凭证与扫码登录接口

### 8.1 获取凭证列表

```http
GET /api/v1/we-rss/credentials/
```

返回当前 tenant 全部凭证，不分页。

### 8.2 获取凭证详情

```http
GET /api/v1/we-rss/credentials/{id}/
```

### 8.3 更新凭证

```http
PUT /api/v1/we-rss/credentials/{id}/
```

请求体只推荐传：

```json
{
  "name": "运营默认凭证"
}
```

当前行为说明：

- 只允许更新 `name`
- 传 `token` 会报错
- 传 `cookie` 会报错

### 8.4 删除凭证

```http
DELETE /api/v1/we-rss/credentials/{id}/
```

当前是软删除。

### 8.5 检查凭证状态

```http
POST /api/v1/we-rss/credentials/{id}/check/
```

返回结构：

```json
{
  "valid": true,
  "status": "active",
  "message": ""
}
```

同时会回写 `status`、`last_error`、`last_check_at`。

### 8.6 设置默认凭证

```http
POST /api/v1/we-rss/credentials/{id}/set-default/
```

当前 tenant 内最终只会保留一个默认凭证。

### 8.7 创建扫码登录会话

```http
POST /api/v1/we-rss/credentials/login-sessions/
```

请求体：

```json
{}
```

会自动创建一个 `credential_login` 任务。

### 8.8 查询扫码登录会话

```http
GET /api/v1/we-rss/credentials/login-sessions/{session_id}/
```

终态判断建议：

- `success`：刷新凭证列表
- `failed`：展示 `error_message`
- `expired`：提示重新生成二维码

## 9. 公众号接口

### 9.1 获取公众号列表

```http
GET /api/v1/we-rss/feeds/
```

当前没有分页和服务端过滤。

### 9.2 创建公众号

```http
POST /api/v1/we-rss/feeds/
```

请求体示例：

```json
{
  "credential_id": 1,
  "source_id": "gh_abcdef123456",
  "faker_id": "MzA5NzQ1Mjg2NA==",
  "biz": "MzA5NzQ1Mjg2NA==",
  "mp_name": "AI Daily",
  "mp_cover": "https://example.com/feed-cover.png",
  "mp_intro": "Daily updates from the AI team.",
  "status": "active",
  "is_featured": false
}
```

关键规则：

- `mp_name` 必填
- `credential_id` 可为空
- `credential_id` 如果不属于当前 tenant，最终不会绑定成功

### 9.3 搜索公众号

```http
GET /api/v1/we-rss/feeds/search/?keyword=AI
```

关键规则：

- 搜索微信平台，不是查本地库
- 需要有效凭证
- 优先使用默认有效凭证，否则回退到第一条有效凭证

### 9.4 获取公众号详情

```http
GET /api/v1/we-rss/feeds/{id}/
```

### 9.5 更新公众号

```http
PUT /api/v1/we-rss/feeds/{id}/
```

请求体结构和创建相同。

### 9.6 删除公众号

```http
DELETE /api/v1/we-rss/feeds/{id}/
```

当前是软删除。

### 9.7 同步公众号

```http
POST /api/v1/we-rss/feeds/{id}/sync/
```

关键规则：

- 返回的是 `feed_sync` 任务
- 同一 feed 的运行中任务会去重复用
- 微信网关默认每页抓取 `5` 篇文章
- 同步会持续翻页，直到微信返回空页
- 请求下一页文章列表前会等待 `0.5` 秒
- 请求下一篇文章详情前也会等待 `0.5` 秒
- 同步按 `tenant + source_id` upsert 文章
- 单篇文章详情抓取失败不会中断整次同步，会记录到任务结果里
- 同步会回写 feed 的 `biz`、`mp_name`、`mp_cover`、同步时间字段

### 9.8 清空某个公众号下全部文章

```http
DELETE /api/v1/we-rss/feeds/{id}/articles/
```

这个接口会永久删除当前 tenant 下该公众号关联的全部文章数据库记录，并返回：

```json
{
  "feed_id": 1,
  "deleted_count": 12
}
```

关键规则：

- 只影响当前 `feed_id`
- 是永久删除，不是软删除
- 不删除 feed 本身
- 没有文章时也会成功返回，`deleted_count` 为 `0`

## 10. 文章接口

### 10.1 获取文章列表

```http
GET /api/v1/we-rss/articles/
```

当前接口支持一个服务端过滤参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `article_type` | `string` | 可选，支持 `news` 或 `newspic` |

例如：

```http
GET /api/v1/we-rss/articles/?article_type=newspic
```

除 `article_type` 之外，当前还没有分页、关键字搜索、按 `feed_id` 过滤、
仅收藏过滤等服务端能力。

### 10.2 获取文章详情

```http
GET /api/v1/we-rss/articles/{id}/
```

### 10.3 删除文章

```http
DELETE /api/v1/we-rss/articles/{id}/
```

当前是软删除。

### 10.4 按 URL 导入文章

```http
POST /api/v1/we-rss/articles/import-by-url/
```

请求体：

```json
{
  "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
}
```

关键规则：

- 返回的是 `article_import` 任务
- 同一 URL 的运行中任务会按 `task_key` 去重复用
- 导入会自动绑定到精选 feed
- 没有精选 feed 时自动创建 `Imported Articles`
- 文章被删除或正文为空时会失败
- 最终按 `tenant + source_id` 做 upsert
- 文章类型字段名和微信官方文档保持一致，返回字段是 `article_type`，
  取值为 `news` 或 `newspic`

### 10.5 刷新文章

```http
POST /api/v1/we-rss/articles/{id}/refresh/
```

关键规则：

- 返回的是 `article_refresh` 任务
- 同一文章运行中任务会去重复用
- 优先使用 `article.feed.credential`
- 没有 feed 凭证时回退到 tenant 有效凭证

### 10.6 更新已读状态

```http
PUT /api/v1/we-rss/articles/{id}/read/
```

请求体：

```json
{
  "is_read": true
}
```

### 10.7 更新收藏状态

```http
PUT /api/v1/we-rss/articles/{id}/favorite/
```

请求体：

```json
{
  "is_favorite": true
}
```

## 11. 任务接口

### 11.1 获取任务列表

```http
GET /api/v1/we-rss/tasks/
```

支持过滤参数：

- `task_type`
- `status`
- `target_type`
- `target_id`

### 11.2 获取任务详情

```http
GET /api/v1/we-rss/tasks/{task_id}/
```

`result_payload` 的结构会随任务类型变化：

| `task_type` | 成功时常见字段 | 失败时常见字段 |
| --- | --- | --- |
| `credential_login` | `credential_id`、`session_id` | `task_type`、`session_id`、`status`、`error` |
| `feed_sync` | `feed_id`、`article_ids`、`article_count`、`detail_success_count`、`detail_failed_count`、`failed_articles`、`result_payload.fetched_count` | `task_type`、`feed_id`、`error` |
| `article_import` | `article_id`、`feed_id`、`source_id` | `task_type`、`url`、`error` |
| `article_refresh` | `article_id`、`title`、`updated_by_id` | `task_type`、`article_id`、`error` |

## 12. RSS 与正文输出接口

### 12.1 当前 tenant 聚合 RSS

```http
GET /api/v1/we-rss/rss/
```

返回 `application/xml`。

### 12.2 单个公众号 RSS

```http
GET /api/v1/we-rss/rss/{feed_id}/
```

返回 `application/xml`。

### 12.3 单篇文章正文 HTML

```http
GET /api/v1/we-rss/rss/content/{article_id}/
```

返回 `text/html`。

这三个接口都要用 `response.text()` 读取，而且仍然需要带鉴权头。

## 13. 推荐前端封装

推荐至少拆成两个请求方法：

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

## 14. 推荐接入顺序

1. 先完成统一请求层。
2. 再接扫码登录和凭证管理。
3. 再接公众号搜索、创建、编辑和同步。
4. 再接统一任务轮询。
5. 再接文章列表、详情、已读、收藏、刷新。
6. 最后接 RSS 和正文 HTML。

## 15. 最容易踩坑的点

- `we_rss` 是 tenant 共享，不是 member 私有。
- 模型字段不等于接口字段。
- `DELETE` 统一按软删除理解。
- `result_payload` 不能用一个固定类型覆盖全部任务。
- RSS / HTML 接口不是匿名公共 URL。
- 公众号列表当前没有分页和服务端过滤。
- 文章列表支持 `article_type` 过滤，但还没有分页、搜索和其它服务端过滤。

## 16. 关联文档

- [README.md](./README.md)
- [00_总览与对接说明.md](./00_总览与对接说明.md)
- [01_凭证与扫码登录API.md](./01_凭证与扫码登录API.md)
- [02_公众号API.md](./02_公众号API.md)
- [03_公众号文章API.md](./03_公众号文章API.md)
- [04_同步任务API.md](./04_同步任务API.md)
- [05_RSS与正文输出API.md](./05_RSS与正文输出API.md)
