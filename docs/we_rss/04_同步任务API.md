# we_rss 同步任务 API

这份文档专门讲 `we_rss` 的异步任务接口。前端如果要把扫码登录、
公众号同步、文章导入和文章刷新接完整，任务接口几乎一定会用到。

`we_rss` 的任务模型是 `WechatSyncTask`。前端需要把它理解成统一的
后台工作单，而不是某个具体业务接口的附属字段。

## 数据结构说明

任务对象字段如下。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 任务 ID |
| `task_type` | `string` | 任务类型 |
| `status` | `string` | 任务状态 |
| `task_key` | `string` | 去重键 |
| `target_type` | `string` | 目标对象类型 |
| `target_id` | `number \| null` | 目标对象 ID |
| `message` | `string` | 当前任务消息 |
| `request_payload` | `object \| null` | 创建任务时的请求载荷 |
| `result_payload` | `object \| null` | 执行结果载荷 |
| `celery_task_id` | `string` | Celery 任务 ID |
| `started_at` | `string \| null` | 开始执行时间 |
| `finished_at` | `string \| null` | 执行结束时间 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

## task_type 枚举

当前任务类型只有下面 4 类。

| 值 | 含义 |
| --- | --- |
| `credential_login` | 扫码登录后台轮询任务 |
| `feed_sync` | 公众号文章同步任务 |
| `article_import` | 按 URL 导入文章任务 |
| `article_refresh` | 刷新文章正文和统计任务 |

## status 枚举

任务状态当前只有下面 4 类。

| 值 | 含义 |
| --- | --- |
| `pending` | 已创建，等待执行 |
| `running` | 正在执行 |
| `success` | 成功完成 |
| `failed` | 执行失败 |

## target_type 常见值

`target_type` 不是严格枚举字段，但目前常见值如下。

| 值 | 含义 |
| --- | --- |
| `login_session` | 登录会话 |
| `feed` | 公众号 |
| `article` | 文章 |

## 1. 获取任务列表

这个接口返回当前 tenant 下的任务列表，支持按任务类型、状态和目标过滤。
前端适合做“任务中心”页，也适合做轻量轮询列表。

### 请求信息

```http
GET /api/v1/we-rss/tasks/
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_type` | `string` | 否 | 按任务类型过滤 |
| `status` | `string` | 否 | 按状态过滤 |
| `target_type` | `string` | 否 | 按目标类型过滤 |
| `target_id` | `number` | 否 | 按目标对象 ID 过滤 |

### 请求示例

```http
GET /api/v1/we-rss/tasks/?task_type=feed_sync&status=success
```

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
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
        "errors": []
      },
      "celery_task_id": "6ec3c8a2-e570-4bd8-9031-53d5976fb415",
      "started_at": "2026-03-21T09:20:00Z",
      "finished_at": "2026-03-21T09:20:08Z",
      "created_at": "2026-03-21T09:20:00Z",
      "updated_at": "2026-03-21T09:20:08Z"
    }
  ]
}
```

### 前端调用示例

```ts
const params = new URLSearchParams({
  task_type: "feed_sync",
  status: "success",
});

const res = await weRssRequest<Array<any>>(`/tasks/?${params.toString()}`);
const tasks = res.data;
```

## 2. 获取任务详情

这个接口是前端轮询任务的核心接口。通常在发起异步动作后，用这个接口
持续刷新进度和结果。

### 请求信息

```http
GET /api/v1/we-rss/tasks/{task_id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_id` | `number` | 是 | 任务 ID |

### 成功响应示例：公众号同步成功

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

### 成功响应示例：任务失败

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 106,
    "task_type": "article_import",
    "status": "failed",
    "task_key": "article_import:https://mp.weixin.qq.com/s/import-fail",
    "target_type": "article",
    "target_id": null,
    "message": "Article import failed: WeChat import blocked by anti-bot",
    "request_payload": {
      "url": "https://mp.weixin.qq.com/s/import-fail"
    },
    "result_payload": {
      "task_type": "article_import",
      "url": "https://mp.weixin.qq.com/s/import-fail",
      "error": "WeChat import blocked by anti-bot"
    },
    "celery_task_id": "8617396d-8d65-4fe9-94ef-0d7f1803e688",
    "started_at": "2026-03-21T09:45:00Z",
    "finished_at": "2026-03-21T09:45:01Z",
    "created_at": "2026-03-21T09:45:00Z",
    "updated_at": "2026-03-21T09:45:01Z"
  }
}
```

### result_payload 的理解方式

`result_payload` 的结构会随任务类型变化，前端不能按一个固定结构硬编码。
建议按 `task_type` 分支解析。

| task_type | 常见 result_payload 字段 |
| --- | --- |
| `credential_login` | `session_id`、`status`、`error` |
| `feed_sync` | `fetched_count`、`detail_success_count`、`detail_failed_count`、`errors` |
| `article_import` | `article_id`、`feed_id`、`message` 或 `error` |
| `article_refresh` | `article_id`、`read_num`、`comment_total_count` 或 `error` |

### 前端轮询示例

```ts
async function pollTask(taskId: number) {
  const timer = window.setInterval(async () => {
    const res = await weRssRequest<any>(`/tasks/${taskId}/`);
    const task = res.data;

    if (task.status === "success") {
      clearInterval(timer);
      console.log("task done", task.result_payload);
    }

    if (task.status === "failed") {
      clearInterval(timer);
      console.error("task failed", task.result_payload?.error);
    }
  }, 2000);
}
```

## 常见前端场景

前端通常会在下面这些场景使用任务接口。

1. 扫码登录弹窗里轮询登录任务结果。
2. 公众号同步后轮询同步状态。
3. 按 URL 导入文章后轮询导入状态。
4. 刷新文章后轮询刷新状态。
5. 单独做一个“最近任务”面板或任务中心页。

## UI 展示建议

任务的 UI 最好把“任务状态”和“业务结果”分开显示。

| 展示区块 | 建议显示内容 |
| --- | --- |
| 基础状态 | `task_type`、`status`、`message` |
| 时间信息 | `created_at`、`started_at`、`finished_at` |
| 请求上下文 | `request_payload` |
| 执行结果 | `result_payload` |
| 失败原因 | `result_payload.error` 或 `message` |

## 下一步

如果你的任务已经能跑通，下一步通常是根据任务结果刷新文章列表，或者接
RSS 和正文输出能力。

- [03_公众号文章API.md](./03_%E5%85%AC%E4%BC%97%E5%8F%B7%E6%96%87%E7%AB%A0API.md)
- [05_RSS与正文输出API.md](./05_RSS%E4%B8%8E%E6%AD%A3%E6%96%87%E8%BE%93%E5%87%BAAPI.md)
