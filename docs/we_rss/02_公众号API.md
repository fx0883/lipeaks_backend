# we_rss 公众号 API

这份文档覆盖公众号搜索、公众号记录管理和公众号文章同步接口。前端通常
在“公众号管理页”或者“新增公众号弹窗”里使用这些接口。

这里的“公众号”指 `WechatFeed`。它代表当前 tenant 保存的一条
微信公众号记录，可以绑定凭证，也可以被标记为 `featured`。

## 数据结构说明

公众号对象的字段如下。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 公众号记录 ID |
| `credential_id` | `number \| null` | 绑定的微信凭证 ID |
| `source_id` | `string` | 微信侧来源 ID |
| `faker_id` | `string` | 微信侧 faker_id |
| `biz` | `string` | 微信公众号 `biz` |
| `mp_name` | `string` | 公众号名称 |
| `mp_cover` | `string` | 公众号头像 URL |
| `mp_intro` | `string` | 公众号简介 |
| `status` | `string` | 当前状态，默认是 `active` |
| `sync_time` | `string \| null` | 最近一次同步时间 |
| `update_time` | `string \| null` | 最近一次更新时间 |
| `last_synced_at` | `string \| null` | 最近一次同步完成时间 |
| `is_featured` | `boolean` | 是否是 featured feed |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

## 通用请求头

这组接口都要求带成员 token 和租户头。

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 1. 获取公众号列表

这个接口返回当前 tenant 下已经保存的公众号记录，当前不分页。

### 请求信息

```http
GET /api/v1/we-rss/feeds/
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
      "credential_id": 1,
      "source_id": "gh_abcdef123456",
      "faker_id": "MzA5NzQ1Mjg2NA==",
      "biz": "MzA5NzQ1Mjg2NA==",
      "mp_name": "AI Daily",
      "mp_cover": "https://example.com/feed-cover.png",
      "mp_intro": "Daily updates from the AI team.",
      "status": "active",
      "sync_time": "2026-03-21T09:20:00Z",
      "update_time": "2026-03-21T09:20:00Z",
      "last_synced_at": "2026-03-21T09:20:00Z",
      "is_featured": false,
      "created_at": "2026-03-20T11:00:00Z",
      "updated_at": "2026-03-21T09:20:00Z"
    }
  ]
}
```

### 前端调用示例

```ts
const res = await weRssRequest<Array<any>>("/feeds/");
const feeds = res.data;
```

## 2. 创建公众号记录

这个接口用于把公众号保存到当前 tenant。可以来自“搜索结果选择后保存”，
也可以来自“手工录入”。

### 请求信息

```http
POST /api/v1/we-rss/feeds/
Content-Type: application/json
```

### 请求体

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

### 请求字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `credential_id` | `number \| null` | 否 | 绑定凭证 ID |
| `source_id` | `string` | 否 | 微信侧来源 ID |
| `faker_id` | `string` | 否 | 微信侧 faker_id |
| `biz` | `string` | 否 | 微信公众号 biz |
| `mp_name` | `string` | 是 | 公众号名称 |
| `mp_cover` | `string` | 否 | 公众号头像 URL |
| `mp_intro` | `string` | 否 | 公众号简介 |
| `status` | `string` | 否 | 默认 `active` |
| `is_featured` | `boolean` | 否 | 是否设为 featured |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "credential_id": 1,
    "source_id": "gh_abcdef123456",
    "faker_id": "MzA5NzQ1Mjg2NA==",
    "biz": "MzA5NzQ1Mjg2NA==",
    "mp_name": "AI Daily",
    "mp_cover": "https://example.com/feed-cover.png",
    "mp_intro": "Daily updates from the AI team.",
    "status": "active",
    "sync_time": null,
    "update_time": null,
    "last_synced_at": null,
    "is_featured": false,
    "created_at": "2026-03-20T11:00:00Z",
    "updated_at": "2026-03-20T11:00:00Z"
  }
}
```

### 前端调用示例

```ts
await weRssRequest("/feeds/", {
  method: "POST",
  body: JSON.stringify({
    credential_id: 1,
    source_id: "gh_abcdef123456",
    faker_id: "MzA5NzQ1Mjg2NA==",
    biz: "MzA5NzQ1Mjg2NA==",
    mp_name: "AI Daily",
    mp_cover: "https://example.com/feed-cover.png",
    mp_intro: "Daily updates from the AI team.",
    status: "active",
    is_featured: false,
  }),
});
```

## 3. 获取公众号详情

这个接口适合公众号详情页或编辑弹窗初始化。

### 请求信息

```http
GET /api/v1/we-rss/feeds/{id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 公众号记录 ID |

### 成功响应

成功响应字段和“创建公众号记录”的响应体一致。

### 前端调用示例

```ts
const res = await weRssRequest<any>("/feeds/1/");
const feed = res.data;
```

## 4. 更新公众号记录

这个接口用于修改公众号元数据，比如名称、简介、绑定凭证和
`is_featured` 状态。

### 请求信息

```http
PUT /api/v1/we-rss/feeds/{id}/
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 公众号记录 ID |

### 请求体示例

```json
{
  "credential_id": 1,
  "source_id": "gh_abcdef123456",
  "faker_id": "MzA5NzQ1Mjg2NA==",
  "biz": "MzA5NzQ1Mjg2NA==",
  "mp_name": "AI Daily Updated",
  "mp_cover": "https://example.com/feed-cover.png",
  "mp_intro": "Updated introduction.",
  "status": "active",
  "is_featured": true
}
```

### 前端调用示例

```ts
await weRssRequest("/feeds/1/", {
  method: "PUT",
  body: JSON.stringify({
    credential_id: 1,
    source_id: "gh_abcdef123456",
    faker_id: "MzA5NzQ1Mjg2NA==",
    biz: "MzA5NzQ1Mjg2NA==",
    mp_name: "AI Daily Updated",
    mp_cover: "https://example.com/feed-cover.png",
    mp_intro: "Updated introduction.",
    status: "active",
    is_featured: true,
  }),
});
```

## 5. 删除公众号记录

这个接口会删除公众号记录本身。删除后它不会再参与同步和 RSS 输出。

### 请求信息

```http
DELETE /api/v1/we-rss/feeds/{id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 公众号记录 ID |

### 成功响应

成功时返回 `204 No Content`，没有 JSON 响应体。

## 6. 搜索微信平台公众号

这个接口会用当前 tenant 的默认有效凭证去搜索微信平台上的公众号结果。
如果当前 tenant 没有可用默认凭证，接口会失败。

### 请求信息

```http
GET /api/v1/we-rss/feeds/search/?keyword=AI
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | `string` | 是 | 搜索关键字，通常是公众号名称或主题词 |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "source_id": "gh_search_1",
      "faker_id": "MzI3NjQ4NTY=",
      "biz": "MzI3NjQ4NTY=",
      "mp_name": "AI Weekly",
      "mp_cover": "https://example.com/search-cover.png",
      "mp_intro": "Weekly insights about AI products."
    }
  ]
}
```

### 失败场景

这个接口常见失败原因如下。

| 场景 | 典型表现 |
| --- | --- |
| 没传 `keyword` | `400` 参数错误 |
| 没有可用默认凭证 | `400` 或业务校验错误 |
| 默认凭证失效 | 后端微信请求失败 |

### 前端调用示例

```ts
const keyword = "AI";
const res = await weRssRequest<Array<any>>(
  `/feeds/search/?keyword=${encodeURIComponent(keyword)}`,
);
const results = res.data;
```

## 7. 触发公众号文章同步

这个接口不会直接返回文章列表，而是返回一个 `feed_sync` 任务。前端要
再去轮询任务详情，直到任务结束。

### 请求信息

```http
POST /api/v1/we-rss/feeds/{id}/sync/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 公众号记录 ID |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 101,
    "task_type": "feed_sync",
    "status": "success",
    "task_key": "feed_sync:1",
    "target_type": "feed",
    "target_id": 1,
    "message": "Feed sync complete",
    "request_payload": {
      "feed_id": 1
    },
    "result_payload": {
      "fetched_count": 3,
      "detail_success_count": 2,
      "detail_failed_count": 1,
      "errors": [
        {
          "source_id": "article-3",
          "url": "https://mp.weixin.qq.com/s/article-3?__biz=Qkl6&mid=1&idx=3&sn=ghi",
          "error": "WeChat article detail fetch failed."
        }
      ]
    },
    "celery_task_id": "6ec3c8a2-e570-4bd8-9031-53d5976fb415",
    "started_at": "2026-03-21T09:20:00Z",
    "finished_at": "2026-03-21T09:20:08Z",
    "created_at": "2026-03-21T09:20:00Z",
    "updated_at": "2026-03-21T09:20:08Z"
  }
}
```

### 接口行为说明

这个接口有两个对前端很重要的特点。

| 特性 | 说明 |
| --- | --- |
| 后台异步执行 | 不要把它当同步接口 |
| 任务排重 | 如果同一个公众号已经有运行中的同步任务，可能直接返回已有任务 |

### 前端调用示例

```ts
const res = await weRssRequest<any>("/feeds/1/sync/", {
  method: "POST",
});

const task = res.data;
router.push(`/we-rss/tasks/${task.id}`);
```

## 典型页面建议

公众号模块通常适合拆成下面几种页面或弹窗。

1. 公众号列表页，调用 `GET /feeds/`。
2. 搜索公众号弹窗，调用 `GET /feeds/search/`。
3. 新建公众号弹窗，调用 `POST /feeds/`。
4. 编辑公众号弹窗，调用 `GET /feeds/{id}/` 和 `PUT /feeds/{id}/`。
5. 同步按钮，调用 `POST /feeds/{id}/sync/` 后跳任务详情或开始轮询。

## 下一步

如果你已经能创建并同步公众号，下一步通常就是接文章接口和任务轮询。

- [03_公众号文章API.md](./03_%E5%85%AC%E4%BC%97%E5%8F%B7%E6%96%87%E7%AB%A0API.md)
- [04_同步任务API.md](./04_%E5%90%8C%E6%AD%A5%E4%BB%BB%E5%8A%A1API.md)
