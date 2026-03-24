# we_rss 同步任务 API

这份文档专门讲 `WechatSyncTask`，也就是 `we_rss` 当前所有异步动作共用的任务
模型。前端只要接扫码登录、公众号同步、按 URL 导入文章、刷新文章中的任意一项，
就几乎一定会用到这一组接口。

你可以把任务模型理解成统一的“后台工作单”。触发某个异步动作后，前端先拿到
一个任务对象，再用任务详情接口持续轮询，直到进入终态。

## 通用请求头

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 数据结构说明

### 1. WechatSyncTask 模型字段

`WechatSyncTask` 已继承 `BaseModel`，模型层字段包括：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `tenant` | `BaseModel` | 所属租户 |
| `created_at` | `BaseModel` | 创建时间 |
| `updated_at` | `BaseModel` | 更新时间 |
| `is_deleted` | `BaseModel` | 软删除标记 |
| `task_type` | 业务字段 | 任务类型 |
| `status` | 业务字段 | 任务状态 |
| `task_key` | 业务字段 | 去重键 |
| `target_type` | 业务字段 | 目标对象类型 |
| `target_id` | 业务字段 | 目标对象 ID |
| `message` | 业务字段 | 当前任务消息 |
| `request_payload` | 业务字段 | 任务请求快照 |
| `result_payload` | 业务字段 | 任务结果快照 |
| `celery_task_id` | 业务字段 | Celery 任务 ID |
| `started_at` | 业务字段 | 开始执行时间 |
| `finished_at` | 业务字段 | 完成时间 |
| `created_by` | 业务字段 | 触发成员 |

### 2. 任务接口返回字段

列表和详情接口当前返回下面这些字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 任务 ID |
| `task_type` | `string` | 任务类型 |
| `status` | `string` | 任务状态 |
| `task_key` | `string` | 去重键 |
| `target_type` | `string` | 目标对象类型 |
| `target_id` | `number \| null` | 目标对象 ID |
| `message` | `string` | 当前任务消息 |
| `request_payload` | `object \| null` | 请求快照 |
| `result_payload` | `object \| null` | 结果快照 |
| `celery_task_id` | `string` | Celery 任务 ID |
| `started_at` | `string \| null` | 开始时间 |
| `finished_at` | `string \| null` | 完成时间 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

不会返回给前端的字段包括：

- `tenant`
- `is_deleted`
- `created_by`

## 枚举值说明

### task_type

当前代码里已经固定的任务类型如下：

| 值 | 含义 |
| --- | --- |
| `credential_login` | 扫码登录任务 |
| `feed_sync` | 公众号同步任务 |
| `article_refresh` | 单篇文章刷新任务 |
| `article_import` | 按 URL 导入文章任务 |

### status

当前任务状态只有四种：

| 值 | 含义 |
| --- | --- |
| `pending` | 已创建，等待执行 |
| `running` | 正在执行 |
| `success` | 执行成功 |
| `failed` | 执行失败 |

### target_type

`target_type` 不是严格枚举字段，但当前实现里常见值如下：

| 值 | 含义 |
| --- | --- |
| `login_session` | 登录会话 |
| `feed` | 公众号 |
| `article` | 文章 |

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/we-rss/tasks/` | 获取当前 tenant 的任务列表 |
| `GET` | `/api/v1/we-rss/tasks/{task_id}/` | 获取单个任务详情 |

## 1. 获取任务列表

这个接口返回当前 tenant 下的任务列表，并支持简单过滤。

```http
GET /api/v1/we-rss/tasks/
```

当前可用查询参数如下：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `task_type` | `string` | 按任务类型精确过滤 |
| `status` | `string` | 按状态精确过滤 |
| `target_type` | `string` | 按目标类型精确过滤 |
| `target_id` | `number` | 按目标 ID 精确过滤 |

示例：

```http
GET /api/v1/we-rss/tasks/?task_type=feed_sync&status=success
```

这个接口没有分页，返回的是数组。

## 2. 获取任务详情

这个接口是前端轮询后台任务的核心接口。

```http
GET /api/v1/we-rss/tasks/{task_id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `task_id` | `number` | 任务 ID |

前端轮询时建议主要看这几个字段：

- `status`
- `message`
- `result_payload`
- `finished_at`

## result_payload 结构说明

`result_payload` 没有全局统一 schema。它会随任务类型和成功/失败状态而变化，这一
点必须写进前端类型设计里。

### 1. credential_login

登录任务成功时，当前代码会返回：

```json
{
  "credential_id": 12,
  "session_id": "f5d7e6f8e4c34b11"
}
```

登录任务失败时，当前代码会返回：

```json
{
  "session_id": "f5d7e6f8e4c34b11",
  "task_type": "credential_login",
  "status": "failed",
  "error": "WeChat rejected the QR login."
}
```

### 2. feed_sync

公众号同步成功时，当前代码返回的 `result_payload` 常见结构如下：

前端要特别注意两个行为：

- 公众号同步当前会按页抓取文章列表，直到微信返回空页为止。
- 后端会在请求下一页文章列表前，以及请求下一篇文章详情前，各等待 `0.5`
  秒。

```json
{
  "message": "Feed sync complete",
  "feed_id": 3,
  "article_ids": [101, 102],
  "article_count": 2,
  "detail_success_count": 2,
  "detail_failed_count": 1,
  "failed_articles": [
    {
      "source_id": "article-3",
      "url": "https://mp.weixin.qq.com/s/...",
      "error": "detail fetch failed"
    }
  ],
  "result_payload": {
    "fetched_count": 3,
    "detail_success_count": 2,
    "detail_failed_count": 1,
    "errors": [
      {
        "source_id": "article-3",
        "url": "https://mp.weixin.qq.com/s/...",
        "error": "detail fetch failed"
      }
    ]
  }
}
```

`result_payload` 里外两层字段的含义不同：

- 外层 `article_ids`、`article_count` 是最终写入本地 `WechatArticle` 的结果。
- 内层 `result_payload.fetched_count` 是微信网关层本次抓到的文章数汇总。
- `failed_articles` 和 `result_payload.errors` 都表示详情抓取失败明细，前者更适合
  前端直接展示。

同步失败时，当前代码会返回：

```json
{
  "feed_id": 3,
  "task_type": "feed_sync",
  "error": "WeChat rate limit triggered"
}
```

### 3. article_import

文章导入成功时，当前代码返回：

```json
{
  "message": "Article import complete",
  "article_id": 15,
  "feed_id": 9,
  "source_id": "article-source-id"
}
```

补充说明：

- `article_import` 的 `task_key` 使用归一化后的公开文章 URL。
- 同一篇文章如果只是抓取时多了 `token` 这类临时参数，仍会命中同一个导入任务。

文章导入失败时，当前代码返回：

```json
{
  "task_type": "article_import",
  "url": "https://mp.weixin.qq.com/s/import-fail",
  "error": "Wechat article is unavailable or has been deleted."
}
```

### 4. article_refresh

文章刷新成功时，当前代码返回：

```json
{
  "message": "Article refresh complete",
  "article_id": 15,
  "title": "Updated title",
  "updated_by_id": 21
}
```

补充说明：

- 刷新任务重新抓取正文时，会使用微信返回页做解析，但不会把带 `token` 的跳转 URL 写回文章记录。

文章刷新失败时，当前代码返回：

```json
{
  "task_type": "article_refresh",
  "article_id": 15,
  "error": "WeChat refresh blocked by anti-bot"
}
```

## 轮询建议

前端统一任务轮询建议如下：

1. 触发异步动作后先拿到任务 ID。
2. 每 2 秒左右请求一次任务详情。
3. `status === "success"` 时结束轮询并消费 `result_payload`。
4. `status === "failed"` 时结束轮询并优先显示
   `result_payload.error`，没有的话显示 `message`。
5. 到达设定超时后给出“任务超时，请稍后刷新”的提示。

一个通用轮询示例：

```ts
async function pollWeRssTask(taskId: number) {
  const interval = 2000;
  const maxAttempts = 60;

  for (let i = 0; i < maxAttempts; i += 1) {
    const res = await weRssRequest<any>(`/tasks/${taskId}/`);
    const task = res.data;

    if (task.status === "success") {
      return task;
    }

    if (task.status === "failed") {
      throw new Error(task.result_payload?.error || task.message);
    }

    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  throw new Error("we_rss task polling timed out");
}
```

## UI 展示建议

如果你要做任务详情面板或任务中心页，建议至少展示下面几个区块：

| 展示区块 | 建议显示内容 |
| --- | --- |
| 基础信息 | `task_type`、`status`、`message` |
| 目标对象 | `target_type`、`target_id` |
| 请求快照 | `request_payload` |
| 执行结果 | `result_payload` |
| 时间信息 | `created_at`、`started_at`、`finished_at` |

## 容易踩坑的点

- `result_payload` 不是统一结构，必须按 `task_type` 分支处理。
- `task_key` 并不是每个任务都有。只有某些去重任务会显式写入，例如文章导入。
- 某些触发接口会直接复用已有运行中任务，所以“返回旧任务”是正常行为。
- 任务列表当前没有分页。

## 下一步

如果你是按链路联调，建议继续看：

- [02_公众号API.md](./02_公众号API.md)
- [03_公众号文章API.md](./03_公众号文章API.md)
