# we_rss 前端完整 API 文档

这是一份给前端直接使用的单文件总文档。它基于当前仓库里的 `we_rss` 真实代
码整理，重点补齐了 feed 订阅、文章收藏、member 私有标签和文章标题搜索的
接口口径。

## 1. 模块范围

`we_rss` 当前覆盖下面几类能力：

- 微信凭证管理
- 微信扫码登录
- 公众号搜索
- member 订阅公众号和取消订阅
- member 私有标签管理
- feed 和 article 标签绑定
- 公众号同步
- 文章列表、详情、标题搜索、收藏、导入、刷新、删除
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
- member 必须绑定 tenant。
- `X-Tenant-ID` 必须等于当前 member 绑定的 tenant。
- feed 和 article 主数据是 tenant 共享。
- `is_subscribed` 和 `is_favorite` 是当前 member 的状态。
- 标签是当前 member 的私有资产，不存在 tenant 公共标签。
- 当前没有 `is_read`。

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
| `GET` | `/api/v1/we-rss/tags/` | 获取当前 member 标签列表 |
| `POST` | `/api/v1/we-rss/tags/` | 创建当前 member 私有标签 |
| `GET` | `/api/v1/we-rss/tags/{id}/` | 获取标签详情 |
| `PUT` | `/api/v1/we-rss/tags/{id}/` | 更新标签 |
| `DELETE` | `/api/v1/we-rss/tags/{id}/` | 硬删除标签 |
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
| `GET` | `/api/v1/we-rss/articles/` | 获取文章列表 |
| `GET` | `/api/v1/we-rss/articles/{id}/` | 获取文章详情 |
| `DELETE` | `/api/v1/we-rss/articles/{id}/` | 软删除文章 |
| `POST` | `/api/v1/we-rss/articles/import-by-url/` | 按 URL 导入文章 |
| `POST` | `/api/v1/we-rss/articles/{id}/refresh/` | 刷新文章 |
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

### 6.1 凭证对象

返回字段如下：

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

### 6.2 登录会话对象

返回字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | `string` | 会话 ID |
| `status` | `string` | `pending / scanned / confirmed / success / failed / expired` |
| `qr_code_url` | `string` | 二维码地址 |
| `qr_code_image` | `string` | Data URL 图片 |
| `scan_status` | `string` | 当前扫码阶段 |
| `error_message` | `string` | 失败信息 |
| `expired_at` | `string \| null` | 过期时间 |
| `credential_id` | `number \| null` | 成功后的凭证 ID |
| `task_id` | `number \| null` | 关联任务 ID |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

### 6.3 公众号对象

返回字段如下：

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

### 6.4 文章对象

返回字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 文章 ID |
| `feed_id` | `number \| null` | 所属公众号 ID |
| `source_id` | `string` | 文章来源 ID |
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

### 6.5 任务对象

返回字段如下：

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
| `result_payload` | `object \| null` | 结果负载 |
| `celery_task_id` | `string` | Celery 任务 ID |
| `started_at` | `string \| null` | 开始时间 |
| `finished_at` | `string \| null` | 结束时间 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

### 6.6 标签对象

返回字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 标签 ID |
| `name` | `string` | 标签名，同一 member 下大小写不敏感唯一 |
| `color` | `string` | 标签颜色 |
| `description` | `string` | 标签描述 |
| `sort_order` | `number` | 排序值 |
| `is_pinned` | `boolean` | 是否置顶 |
| `feed_count` | `number` | 当前 member 使用该标签的 feed 数量 |
| `article_count` | `number` | 当前 member 使用该标签的 article 数量 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

标签对象的补充规则如下：

- 标签是当前 member 私有资产，不存在 tenant 公共标签。
- 同一个标签可以同时绑定到 feed 和 article。
- 标签列表默认按 `is_pinned desc, sort_order asc, id desc` 排序。
- 删除标签会硬删除，并自动删除所有 feed/article 标签关系。

## 7. 标签接口说明

### 7.1 获取标签列表

```http
GET /api/v1/we-rss/tags/
```

这个接口返回当前 member 的私有标签库。

### 7.2 创建标签

```http
POST /api/v1/we-rss/tags/
Content-Type: application/json
```

请求体示例如下：

```json
{
  "name": "AI",
  "color": "#008000",
  "description": "Interesting reads",
  "sort_order": 10,
  "is_pinned": true
}
```

### 7.3 获取、更新、删除标签

```http
GET /api/v1/we-rss/tags/{id}/
PUT /api/v1/we-rss/tags/{id}/
DELETE /api/v1/we-rss/tags/{id}/
```

这里需要记住下面几条规则：

- 同一个 member 下，标签名全局唯一，且大小写不敏感。
- attach 和 detach 不会自动创建标签，必须先创建再绑定。
- 删除标签是硬删除，不带恢复语义。

## 8. 公众号接口说明

### 8.1 获取公众号列表

```http
GET /api/v1/we-rss/feeds/
GET /api/v1/we-rss/feeds/?subscribed_only=true
GET /api/v1/we-rss/feeds/?tag_ids=1,2,3
```

支持参数如下：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `subscribed_only` | `boolean` | 为 `true` 时，只返回当前 member 已订阅 feed |
| `tag_ids` | `string` | 逗号分隔标签 ID，多个标签使用 AND 语义 |

### 8.2 搜索微信公众号

```http
GET /api/v1/we-rss/feeds/search/?keyword=AI
```

这里搜索的是微信平台，不是本地数据库。

### 8.3 订阅公众号

```http
POST /api/v1/we-rss/feeds/subscribe/
Content-Type: application/json
```

请求体示例如下：

```json
{
  "source_id": "gh_search_1",
  "faker_id": "MzI3NjQ4NTY=",
  "biz": "MzI3NjQ4NTY=",
  "mp_name": "AI Weekly",
  "mp_cover": "https://example.com/search-cover.png",
  "mp_intro": "Weekly insights about AI products."
}
```

补充说明如下：

- 这是当前 member 正常订阅公众号的标准入口。
- 后端会先复用或创建 tenant 共享 `WechatFeed` 主数据。
- 然后为当前 member 创建或复用订阅关系。

### 8.4 手动创建公众号记录

```http
POST /api/v1/we-rss/feeds/
Content-Type: application/json
```

这个接口仍然可用，但更适合后台手动录入场景。前端正常订阅流程，推荐优先使用
`POST /feeds/subscribe/`。

### 8.5 取消订阅公众号

```http
DELETE /api/v1/we-rss/feeds/{id}/subscribe/
```

这个动作只删除当前 member 的订阅关系，不删除 feed 主数据。

取消订阅时，也会自动清理当前 member 在这个 feed 上的所有标签关系。

### 8.6 feed 标签接口

```http
GET /api/v1/we-rss/feeds/{id}/tags/
POST /api/v1/we-rss/feeds/{id}/tags/attach/
POST /api/v1/we-rss/feeds/{id}/tags/detach/
```

对象标签接口请求体如下：

```json
{
  "tag_ids": [1, 2, 3]
}
```

这里的关键规则如下：

- 只能绑定当前 member 自己的标签。
- feed 打标签前，当前 member 必须已订阅该 feed。
- 绑定和解绑都是增量操作，不是全量覆盖。
- 已存在绑定关系会被忽略，不会重复创建。

### 8.7 触发公众号同步

```http
POST /api/v1/we-rss/feeds/{id}/sync/
```

返回的是 `feed_sync` 任务，不是文章列表。

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

`search` 的规则如下：

- 只搜 `title`
- 会先把 `-` 和 `|` 替换为空格
- 再按空格拆词
- 多个词按 OR 匹配

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

### 9.3 刷新文章

```http
POST /api/v1/we-rss/articles/{id}/refresh/
```

返回的是 `article_refresh` 任务。

### 9.4 更新收藏状态

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

### 9.5 文章标签接口

```http
GET /api/v1/we-rss/articles/{id}/tags/
POST /api/v1/we-rss/articles/{id}/tags/attach/
POST /api/v1/we-rss/articles/{id}/tags/detach/
```

对象标签接口请求体如下：

```json
{
  "tag_ids": [1, 2, 3]
}
```

这里的关键规则如下：

- 只能绑定当前 member 自己的标签。
- 文章打标签不要求当前 member 已订阅对应 feed。
- 只要文章在当前 tenant 中存在，就允许绑定。
- 绑定和解绑都是增量操作，不是全量覆盖。

## 10. 前端封装示例

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

## 11. 最容易踩坑的点

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
  `POST /articles/{id}/refresh/` 返回的都是任务对象。
