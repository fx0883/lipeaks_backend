# we_rss 前端完整 API 文档

这份文档是给前端直接使用的单文件汇总版，覆盖当前 `we_rss` 已提供的
全部接口。你可以只看这一份，就完成凭证管理、扫码登录、公众号管理、
文章管理、任务轮询，以及 RSS / HTML 输出的接入。

如果你后续想按模块深入看细节，可以再回到拆分文档：
[README.md](./README.md)。

## 1. 接口范围

`we_rss` 是当前 Django 项目中的独立 app，只负责下面这类能力：

- 微信抓取凭证
- 微信扫码登录会话
- 微信公众号管理
- 微信公众号文章管理
- 后台异步同步任务
- 需要鉴权的 RSS / 正文输出

这里的文章是 `WechatArticle`，和项目现有 `cms.Article` 完全分离，前端
不要混用接口和字段。

## 2. 基础地址

```text
/api/v1/we-rss/
```

本地开发环境通常类似：

```text
http://localhost:8000/api/v1/we-rss/
```

## 3. 鉴权与租户头

所有 `we_rss` 接口都必须使用当前项目已有的 `Member JWT`，并且每个请求
都必须带 `X-Tenant-ID`。

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

### 3.1 `X-Tenant-ID` 规则

- 必填，所有 `we_rss` 接口都要传
- 必须等于当前登录成员绑定的 `member.tenant.id`
- 不能跨租户访问
- `member` 没有 tenant 时，后端会直接拒绝访问

### 3.2 数据隔离规则

`we_rss` 数据是 tenant 共享，不是 member 私有。

也就是说：

- A 成员创建的微信凭证
- 只要 B 成员属于同一个 tenant
- B 也能看到并使用这份数据

前端 UI 建议使用“当前租户的凭证 / 当前租户的公众号 / 当前租户的文章”
这样的语义，不要写成“我的凭证 / 我的文章”。

## 4. 标准返回格式

### 4.1 JSON 接口成功格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {}
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `success` | `boolean` | 是否成功 |
| `code` | `number` | 业务码，成功通常为 `2000` |
| `message` | `string` | 结果说明 |
| `data` | `object \| array \| null` | 真实业务数据 |

### 4.2 常见错误格式

```json
{
  "success": false,
  "code": 4003,
  "message": "没有权限执行该操作",
  "data": null
}
```

常见状态码：

| HTTP 状态码 | 含义 | 常见原因 |
| --- | --- | --- |
| `400` | 参数错误 | 缺字段、字段类型错误、URL 非法 |
| `401` | 未认证 | 没带 token、token 过期 |
| `403` | 无权限 | `X-Tenant-ID` 不匹配、member 无 tenant |
| `404` | 资源不存在 | 当前 tenant 内找不到该资源 |
| `500` | 服务端异常 | 微信抓取链路异常、未知错误 |

### 4.3 非 JSON 接口

| 接口类型 | 返回类型 | 前端读取方式 |
| --- | --- | --- |
| 普通业务接口 | `application/json` | `response.json()` |
| RSS 输出 | `application/xml` | `response.text()` |
| 正文 HTML 输出 | `text/html` | `response.text()` |

## 5. 推荐前端请求封装

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
```

如果是 RSS / HTML 接口：

```ts
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

## 6. 接口总表

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/we-rss/credentials/` | 获取凭证列表 |
| `GET` | `/api/v1/we-rss/credentials/{id}/` | 获取凭证详情 |
| `PUT` | `/api/v1/we-rss/credentials/{id}/` | 更新凭证名称 |
| `DELETE` | `/api/v1/we-rss/credentials/{id}/` | 删除凭证 |
| `POST` | `/api/v1/we-rss/credentials/{id}/check/` | 校验凭证可用性 |
| `POST` | `/api/v1/we-rss/credentials/{id}/set-default/` | 设置默认凭证 |
| `POST` | `/api/v1/we-rss/credentials/login-sessions/` | 创建扫码登录会话 |
| `GET` | `/api/v1/we-rss/credentials/login-sessions/{session_id}/` | 查询扫码登录会话 |
| `GET` | `/api/v1/we-rss/feeds/` | 获取公众号列表 |
| `POST` | `/api/v1/we-rss/feeds/` | 创建公众号 |
| `GET` | `/api/v1/we-rss/feeds/{id}/` | 获取公众号详情 |
| `PUT` | `/api/v1/we-rss/feeds/{id}/` | 更新公众号 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/` | 删除公众号 |
| `GET` | `/api/v1/we-rss/feeds/search/?keyword=关键词` | 搜索公众号 |
| `POST` | `/api/v1/we-rss/feeds/{id}/sync/` | 触发公众号文章同步 |
| `GET` | `/api/v1/we-rss/articles/` | 获取文章列表 |
| `POST` | `/api/v1/we-rss/articles/import-by-url/` | 按 URL 导入文章 |
| `GET` | `/api/v1/we-rss/articles/{id}/` | 获取文章详情 |
| `DELETE` | `/api/v1/we-rss/articles/{id}/` | 删除文章 |
| `POST` | `/api/v1/we-rss/articles/{id}/refresh/` | 刷新文章 |
| `PUT` | `/api/v1/we-rss/articles/{id}/read/` | 更新已读状态 |
| `PUT` | `/api/v1/we-rss/articles/{id}/favorite/` | 更新收藏状态 |
| `GET` | `/api/v1/we-rss/tasks/` | 获取任务列表 |
| `GET` | `/api/v1/we-rss/tasks/{task_id}/` | 获取任务详情 |
| `GET` | `/api/v1/we-rss/rss/` | 获取 tenant RSS |
| `GET` | `/api/v1/we-rss/rss/{feed_id}/` | 获取单公众号 RSS |
| `GET` | `/api/v1/we-rss/rss/content/{article_id}/` | 获取文章正文 HTML |

## 7. 对象结构

### 7.1 微信凭证对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 凭证主键 |
| `name` | `string` | 凭证名称 |
| `status` | `string` | `pending / active / expired / invalid / disabled` |
| `expires_at` | `string \| null` | 过期时间 |
| `last_login_at` | `string \| null` | 最近登录时间 |
| `last_check_at` | `string \| null` | 最近检查时间 |
| `last_error` | `string` | 最近一次错误 |
| `is_default` | `boolean` | 是否默认凭证 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

### 7.2 登录会话对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | `string` | 会话 ID |
| `status` | `string` | `pending / scanned / confirmed / success / failed / expired` |
| `qr_code_url` | `string` | 二维码 URL |
| `qr_code_image` | `string` | 二维码 Base64 图片 |
| `scan_status` | `string` | 扫码阶段状态，比如 `waiting / scanned / confirmed / expired` |
| `error_message` | `string` | 错误信息 |
| `expired_at` | `string \| null` | 过期时间 |
| `credential_id` | `number \| null` | 登录成功后生成的凭证 ID |
| `task_id` | `number \| null` | 对应后台任务 ID |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

### 7.3 公众号对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 公众号 ID |
| `credential_id` | `number \| null` | 绑定凭证 ID |
| `source_id` | `string` | 微信来源 ID |
| `faker_id` | `string` | 微信 faker_id |
| `biz` | `string` | 微信 biz |
| `mp_name` | `string` | 公众号名称 |
| `mp_cover` | `string` | 公众号头像 |
| `mp_intro` | `string` | 公众号简介 |
| `status` | `string` | 当前状态，默认 `active` |
| `sync_time` | `string \| null` | 最近同步时间 |
| `update_time` | `string \| null` | 最近更新时间 |
| `last_synced_at` | `string \| null` | 最近同步完成时间 |
| `is_featured` | `boolean` | 是否 featured |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

### 7.4 公众号文章对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 文章 ID |
| `feed_id` | `number \| null` | 所属公众号 ID |
| `source_id` | `string` | 微信文章来源 ID |
| `title` | `string` | 标题 |
| `description` | `string` | 摘要 |
| `content` | `string` | 正文 HTML |
| `url` | `string` | 微信文章 URL |
| `pic_url` | `string` | 封面图 URL |
| `publish_time` | `string \| null` | 发布时间 |
| `status` | `string` | 文章状态，通常为 `active` |
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

### 7.5 同步任务对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 任务 ID |
| `task_type` | `string` | `credential_login / feed_sync / article_import / article_refresh` |
| `status` | `string` | `pending / running / success / failed` |
| `task_key` | `string` | 任务去重键 |
| `target_type` | `string` | 目标类型，如 `login_session / feed / article` |
| `target_id` | `number \| null` | 目标 ID |
| `message` | `string` | 当前任务描述 |
| `request_payload` | `object \| null` | 请求快照 |
| `result_payload` | `object \| null` | 执行结果 |
| `celery_task_id` | `string` | Celery 任务 ID |
| `started_at` | `string \| null` | 开始时间 |
| `finished_at` | `string \| null` | 结束时间 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

## 8. 凭证与扫码登录 API

### 8.1 获取凭证列表

```http
GET /api/v1/we-rss/credentials/
```

请求参数：无。

返回：当前 tenant 下全部微信凭证数组。

示例：

```ts
const res = await weRssRequest<Array<any>>("/credentials/");
const credentials = res.data;
```

### 8.2 获取凭证详情

```http
GET /api/v1/we-rss/credentials/{id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 凭证 ID |

示例：

```ts
const res = await weRssRequest<any>("/credentials/1/");
```

### 8.3 更新凭证名称

```http
PUT /api/v1/we-rss/credentials/{id}/
Content-Type: application/json
```

请求体：

```json
{
  "name": "业务线默认凭证"
}
```

说明：

- 只允许更新 `name`
- 不支持手动改 `token`
- 不支持手动改 `cookie`

示例：

```ts
await weRssRequest("/credentials/1/", {
  method: "PUT",
  body: JSON.stringify({ name: "业务线默认凭证" }),
});
```

### 8.4 删除凭证

```http
DELETE /api/v1/we-rss/credentials/{id}/
```

成功时返回 `204 No Content`。

### 8.5 校验凭证可用性

```http
POST /api/v1/we-rss/credentials/{id}/check/
```

返回示例：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "valid": true,
    "status": "active",
    "message": ""
  }
}
```

### 8.6 设置默认凭证

```http
POST /api/v1/we-rss/credentials/{id}/set-default/
```

返回：更新后的凭证对象。

### 8.7 创建扫码登录会话

```http
POST /api/v1/we-rss/credentials/login-sessions/
Content-Type: application/json
```

请求体：

```json
{}
```

返回重点字段：

- `session_id`
- `qr_code_url`
- `qr_code_image`
- `task_id`

示例：

```ts
const res = await weRssRequest<any>("/credentials/login-sessions/", {
  method: "POST",
  body: JSON.stringify({}),
});

setQrCodeSrc(res.data.qr_code_image);
setCurrentSessionId(res.data.session_id);
```

### 8.8 查询扫码登录会话

```http
GET /api/v1/we-rss/credentials/login-sessions/{session_id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | `string` | 登录会话 ID |

轮询终止条件：

- `status === "success"`，拿到 `credential_id`
- `status === "failed"`，展示失败原因
- `status === "expired"`，提示重新生成二维码

示例：

```ts
async function pollLoginSession(sessionId: string) {
  const timer = window.setInterval(async () => {
    const res = await weRssRequest<any>(
      `/credentials/login-sessions/${sessionId}/`,
    );

    const session = res.data;

    if (session.status === "success") {
      clearInterval(timer);
    }

    if (session.status === "failed" || session.status === "expired") {
      clearInterval(timer);
    }
  }, 3000);
}
```

## 9. 公众号 API

### 9.1 获取公众号列表

```http
GET /api/v1/we-rss/feeds/
```

返回：当前 tenant 下全部公众号列表，不分页。

### 9.2 创建公众号

```http
POST /api/v1/we-rss/feeds/
Content-Type: application/json
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

必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `mp_name` | `string` | 公众号名称 |

### 9.3 获取公众号详情

```http
GET /api/v1/we-rss/feeds/{id}/
```

### 9.4 更新公众号

```http
PUT /api/v1/we-rss/feeds/{id}/
Content-Type: application/json
```

请求体格式与创建接口一致。

### 9.5 删除公众号

```http
DELETE /api/v1/we-rss/feeds/{id}/
```

成功返回 `204 No Content`。

### 9.6 搜索公众号

```http
GET /api/v1/we-rss/feeds/search/?keyword=AI
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | `string` | 是 | 搜索关键词 |

返回结果字段：

- `source_id`
- `faker_id`
- `biz`
- `mp_name`
- `mp_cover`
- `mp_intro`

说明：

- 依赖当前 tenant 的默认有效凭证
- 没有默认凭证时，接口会失败

### 9.7 同步公众号文章

```http
POST /api/v1/we-rss/feeds/{id}/sync/
```

说明：

- 这是异步接口
- 返回的是 `feed_sync` 任务对象
- 如果已有同类运行中任务，可能会直接复用已有任务

示例：

```ts
const res = await weRssRequest<any>("/feeds/1/sync/", {
  method: "POST",
});

const task = res.data;
await pollTask(task.id);
```

## 10. 公众号文章 API

### 10.1 获取文章列表

```http
GET /api/v1/we-rss/articles/
```

返回：当前 tenant 下全部文章列表，不分页，默认按发布时间倒序。

### 10.2 获取文章详情

```http
GET /api/v1/we-rss/articles/{id}/
```

### 10.3 删除文章

```http
DELETE /api/v1/we-rss/articles/{id}/
```

成功返回 `204 No Content`。

### 10.4 按 URL 导入文章

```http
POST /api/v1/we-rss/articles/import-by-url/
Content-Type: application/json
```

请求体：

```json
{
  "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
}
```

说明：

- 这是异步接口
- 返回 `article_import` 任务对象
- 后端会自动绑定到当前 tenant 的 featured feed
- 相同 URL 的运行中任务可能会直接复用

### 10.5 刷新文章

```http
POST /api/v1/we-rss/articles/{id}/refresh/
```

说明：

- 这是异步接口
- 返回 `article_refresh` 任务对象
- 后台会重新抓取正文和统计字段

### 10.6 更新已读状态

```http
PUT /api/v1/we-rss/articles/{id}/read/
Content-Type: application/json
```

请求体：

```json
{
  "is_read": true
}
```

返回：更新后的文章对象。

### 10.7 更新收藏状态

```http
PUT /api/v1/we-rss/articles/{id}/favorite/
Content-Type: application/json
```

请求体：

```json
{
  "is_favorite": true
}
```

返回：更新后的文章对象。

## 11. 同步任务 API

### 11.1 获取任务列表

```http
GET /api/v1/we-rss/tasks/
```

可选查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `task_type` | `string` | 按任务类型过滤 |
| `status` | `string` | 按任务状态过滤 |
| `target_type` | `string` | 按目标类型过滤 |
| `target_id` | `number` | 按目标 ID 过滤 |

示例：

```http
GET /api/v1/we-rss/tasks/?task_type=feed_sync&status=success
```

### 11.2 获取任务详情

```http
GET /api/v1/we-rss/tasks/{task_id}/
```

这是前端轮询任务的核心接口。

`result_payload` 会随 `task_type` 不同而变化，前端不要按固定结构硬编码。

建议按下面方式解析：

| `task_type` | 常见结果字段 |
| --- | --- |
| `credential_login` | `session_id`、`status`、`error` |
| `feed_sync` | `fetched_count`、`detail_success_count`、`detail_failed_count`、`errors` |
| `article_import` | `article_id`、`feed_id`、`message` 或 `error` |
| `article_refresh` | `article_id`、`read_num`、`comment_total_count` 或 `error` |

通用轮询示例：

```ts
async function pollTask(taskId: number) {
  const timer = window.setInterval(async () => {
    const res = await weRssRequest<any>(`/tasks/${taskId}/`);
    const task = res.data;

    if (task.status === "success") {
      clearInterval(timer);
      console.log(task.result_payload);
    }

    if (task.status === "failed") {
      clearInterval(timer);
      console.error(task.result_payload?.error || task.message);
    }
  }, 2000);
}
```

## 12. RSS 与正文输出 API

### 12.1 获取当前 tenant 聚合 RSS

```http
GET /api/v1/we-rss/rss/
```

返回类型：`application/xml`

前端示例：

```ts
const xml = await weRssTextRequest("/rss/");
```

### 12.2 获取单公众号 RSS

```http
GET /api/v1/we-rss/rss/{feed_id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `feed_id` | `number` | 公众号 ID |

返回类型：`application/xml`

### 12.3 获取文章正文 HTML

```http
GET /api/v1/we-rss/rss/content/{article_id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `article_id` | `number` | 文章 ID |

返回类型：`text/html`

前端示例：

```ts
const html = await weRssTextRequest("/rss/content/1/");
document.getElementById("article-container")!.innerHTML = html;
```

注意：

- 这不是公开接口，仍然必须带 token 和 `X-Tenant-ID`
- 不要调用 `response.json()`
- 如果要插入 DOM，要结合前端安全策略处理

## 13. 推荐接入顺序

如果前端要从零开始接完整链路，建议按下面顺序做：

1. 先接通 `Member JWT` 和 `X-Tenant-ID`
2. 接“创建扫码登录会话”和“查询扫码登录会话”
3. 接凭证列表和默认凭证设置
4. 接公众号搜索、创建、同步
5. 接任务轮询
6. 接文章列表、详情、已读、收藏、刷新
7. 最后接 RSS 和正文 HTML 输出

## 14. 典型完整调用链路

### 14.1 扫码登录链路

1. 调用 `POST /credentials/login-sessions/`
2. 显示二维码
3. 轮询 `GET /credentials/login-sessions/{session_id}/`
4. 成功后拿到 `credential_id`
5. 刷新凭证列表

### 14.2 搜索公众号并同步文章

1. 调用 `GET /feeds/search/?keyword=...`
2. 用户选中结果
3. 调用 `POST /feeds/`
4. 调用 `POST /feeds/{id}/sync/`
5. 轮询 `GET /tasks/{task_id}/`
6. 成功后刷新文章列表

### 14.3 按 URL 导入文章

1. 调用 `POST /articles/import-by-url/`
2. 拿到任务 ID
3. 轮询 `GET /tasks/{task_id}/`
4. 从 `result_payload.article_id` 进入文章详情页

## 15. 交付建议

如果你是发给前端开发同学，建议这样使用这套文档：

- 日常开发先看本文件
- 需要拆模块细看时，再跳到 `docs/we_rss` 下的分模块文档
- 联调时同时打开 OpenAPI 页面和这份文档，对照字段和示例

## 16. 相关文档

- [README.md](./README.md)
- [00_总览与对接说明.md](./00_%E6%80%BB%E8%A7%88%E4%B8%8E%E5%AF%B9%E6%8E%A5%E8%AF%B4%E6%98%8E.md)
- [01_凭证与扫码登录API.md](./01_%E5%87%AD%E8%AF%81%E4%B8%8E%E6%89%AB%E7%A0%81%E7%99%BB%E5%BD%95API.md)
- [02_公众号API.md](./02_%E5%85%AC%E4%BC%97%E5%8F%B7API.md)
- [03_公众号文章API.md](./03_%E5%85%AC%E4%BC%97%E5%8F%B7%E6%96%87%E7%AB%A0API.md)
- [04_同步任务API.md](./04_%E5%90%8C%E6%AD%A5%E4%BB%BB%E5%8A%A1API.md)
- [05_RSS与正文输出API.md](./05_RSS%E4%B8%8E%E6%AD%A3%E6%96%87%E8%BE%93%E5%87%BAAPI.md)
