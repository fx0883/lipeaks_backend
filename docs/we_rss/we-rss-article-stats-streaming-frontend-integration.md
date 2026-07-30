# We RSS 文章统计刷新流式接口前端接入说明

## 结论

`POST /api/v1/we-rss/article-stats/refresh/` 已改为流式接口。

前端不要再把它当普通 JSON 接口调用，也不要再拿返回的 task 去轮询
`GET /api/v1/we-rss/tasks/{task_id}/`。

现在前端应该：

1. 点击刷新统计时进入 loading。
2. `fetch` 调用 `POST /api/v1/we-rss/article-stats/refresh/`。
3. 用 `response.body.getReader()` 持续读取后端返回的 `text/event-stream`。
4. 每收到一条 `progress` 事件，就 `console.log` 当前刷新的文章数据。
5. 收到 `done` 事件后退出 loading，并按需刷新文章列表。

## 请求

### 刷新某个 feed 下的全部文章统计

```http
POST /api/v1/we-rss/article-stats/refresh/
Accept: text/event-stream
Content-Type: application/json
Authorization: Bearer <member_jwt>
X-Tenant-ID: <tenant_id>

{
  "feed_id": 20
}
```

### 刷新指定文章

```json
{
  "article_ids": [101, 102, 103]
}
```

### 刷新某个 member 订阅范围内的文章

```json
{
  "member_id": 12
}
```

三个选择器只能传一个：`feed_id`、`article_ids`、`member_id`。

## 响应格式

响应不是 JSON envelope，不会是：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {}
}
```

响应是：

```http
Content-Type: text/event-stream; charset=utf-8
```

流里按 SSE 格式返回：

```text
event: start
data: {"selector_type":"feed_id","feed_id":20,"total":5,"status":"running"}

event: progress
data: {"index":1,"total":5,"progress":20,"status":"success","article_id":123,"title":"..."}

event: done
data: {"total":5,"success_count":5,"failed_count":0,"status":"done","articles":[...],"failed_articles":[]}
```

## 事件说明

### `start`

表示后端已经开始刷新。

常用字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `selector_type` | string | `feed_id`、`article_ids` 或 `member_id` |
| `feed_id` | number/null | 本次刷新 feed ID |
| `member_id` | number/null | 本次刷新 member ID |
| `article_ids` | number[] | 后端实际解析出来要刷新的文章 ID |
| `total` | number | 总文章数 |
| `success_count` | number | 当前成功数，开始时为 0 |
| `failed_count` | number | 当前失败数，开始时为 0 |
| `progress` | number | 当前进度，开始时为 0 |
| `status` | string | `running` |

### `progress`

每刷完一篇文章返回一次。成功和失败都会返回，不会因为某篇失败中断整个 feed。

常用字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `index` | number | 当前第几篇，从 1 开始 |
| `total` | number | 总文章数 |
| `progress` | number | 百分比进度 |
| `status` | string | `success` 或 `failed` |
| `article_id` | number | 文章 ID |
| `source_id` | string | 微信文章 source ID |
| `title` | string | 文章标题 |
| `url` | string | 文章 URL |
| `read_num` | number | 阅读数 |
| `like_num` | number | 点赞数 |
| `old_like_num` | number | 在看/旧点赞字段 |
| `share_num` | number | 分享数 |
| `collect_num` | number | 收藏数 |
| `comment_count` | number | 评论数 |
| `comment_reply_count` | number | 回复数 |
| `comment_total_count` | number | 评论总数 |
| `last_refreshed_at` | string/null | 统计刷新时间 |
| `success_count` | number | 当前累计成功数 |
| `failed_count` | number | 当前累计失败数 |
| `error` | string | 失败原因；成功时为空字符串 |

### `done`

表示本次刷新全部结束。

常用字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `total` | number | 总文章数 |
| `success_count` | number | 成功数 |
| `failed_count` | number | 失败数 |
| `progress` | number | 100 |
| `status` | string | `done` |
| `articles` | object[] | 成功刷新的文章进度数据 |
| `failed_articles` | object[] | 失败文章进度数据 |

## 前端接入代码

下面代码可以直接放进前端 API client 里。

```ts
type ArticleStatsRefreshSelector =
  | { feed_id: number }
  | { article_ids: number[] }
  | { member_id: number };

type ArticleStatsStreamEventName = "start" | "progress" | "done" | "error";

type ArticleStatsStreamPayload = {
  selector_type?: "feed_id" | "article_ids" | "member_id";
  feed_id?: number | null;
  member_id?: number | null;
  article_ids?: number[];
  index?: number;
  total?: number;
  progress?: number;
  status?: "running" | "success" | "failed" | "done";
  article_id?: number;
  source_id?: string;
  title?: string;
  url?: string;
  read_num?: number;
  like_num?: number;
  old_like_num?: number;
  share_num?: number;
  collect_num?: number;
  comment_count?: number;
  comment_reply_count?: number;
  comment_total_count?: number;
  last_refreshed_at?: string | null;
  success_count?: number;
  failed_count?: number;
  error?: string;
  articles?: ArticleStatsStreamPayload[];
  failed_articles?: ArticleStatsStreamPayload[];
};

type RefreshArticleStatsStreamOptions = {
  token: string;
  tenantId: number | string;
  selector: ArticleStatsRefreshSelector;
  signal?: AbortSignal;
  onEvent?: (eventName: ArticleStatsStreamEventName, payload: ArticleStatsStreamPayload) => void;
};

function parseSseChunk(buffer: string) {
  const events: Array<{ eventName: ArticleStatsStreamEventName; payload: ArticleStatsStreamPayload }> = [];
  const blocks = buffer.split("\n\n");
  const rest = blocks.pop() ?? "";

  for (const block of blocks) {
    const lines = block.split("\n");
    let eventName: ArticleStatsStreamEventName = "progress";
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice("event:".length).trim() as ArticleStatsStreamEventName;
      }
      if (line.startsWith("data:")) {
        dataLines.push(line.slice("data:".length).trim());
      }
    }

    if (!dataLines.length) continue;

    events.push({
      eventName,
      payload: JSON.parse(dataLines.join("\n")),
    });
  }

  return { events, rest };
}

export async function refreshArticleStatsStream(options: RefreshArticleStatsStreamOptions) {
  const response = await fetch("/api/v1/we-rss/article-stats/refresh/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${options.token}`,
      "X-Tenant-ID": String(options.tenantId),
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(options.selector),
    signal: options.signal,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`刷新文章统计失败: HTTP ${response.status} ${text}`);
  }

  if (!response.body) {
    throw new Error("浏览器不支持读取流式响应。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let donePayload: ArticleStatsStreamPayload | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSseChunk(buffer);
    buffer = parsed.rest;

    for (const item of parsed.events) {
      options.onEvent?.(item.eventName, item.payload);

      if (item.eventName === "progress") {
        console.log("[article-stats:progress]", item.payload);
      }

      if (item.eventName === "done") {
        donePayload = item.payload;
        console.log("[article-stats:done]", item.payload);
      }
    }
  }

  return donePayload;
}
```

## React 使用示例

```tsx
import { useState } from "react";
import { refreshArticleStatsStream } from "./api/refreshArticleStatsStream";

export function RefreshFeedStatsButton({
  feedId,
  token,
  tenantId,
  onFinished,
}: {
  feedId: number;
  token: string;
  tenantId: number | string;
  onFinished?: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [progressText, setProgressText] = useState("");

  async function handleClick() {
    setLoading(true);
    setProgressText("准备刷新文章统计...");

    try {
      const donePayload = await refreshArticleStatsStream({
        token,
        tenantId,
        selector: { feed_id: feedId },
        onEvent(eventName, payload) {
          if (eventName === "start") {
            setProgressText(`开始刷新，共 ${payload.total ?? 0} 篇文章`);
            console.log("[article-stats:start]", payload);
          }

          if (eventName === "progress") {
            setProgressText(
              `刷新中 ${payload.index}/${payload.total}: ${payload.title ?? ""}`
            );
            console.log("[article-stats:article]", payload);
          }

          if (eventName === "done") {
            setProgressText(
              `刷新完成：成功 ${payload.success_count ?? 0}，失败 ${payload.failed_count ?? 0}`
            );
          }
        },
      });

      console.log("[article-stats:summary]", donePayload);
      onFinished?.();
    } catch (error) {
      console.error("[article-stats:error]", error);
      setProgressText(error instanceof Error ? error.message : "刷新失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <button type="button" onClick={handleClick} disabled={loading}>
      {loading ? progressText || "刷新中..." : "刷新统计"}
    </button>
  );
}
```

## AbortController 取消刷新

如果前端需要用户手动取消，可以这样做：

```ts
const controller = new AbortController();

refreshArticleStatsStream({
  token,
  tenantId,
  selector: { feed_id: 20 },
  signal: controller.signal,
  onEvent(eventName, payload) {
    console.log(eventName, payload);
  },
});

// 用户点击取消
controller.abort();
```

取消只表示浏览器断开连接。已经在后端处理完成的文章不会回滚。

## curl 调试

用 `curl -N` 可以看到服务端一条条吐出来的事件。

```bash
curl -N 'http://localhost:8000/api/v1/we-rss/article-stats/refresh/' \
  -H 'Authorization: Bearer <member_jwt>' \
  -H 'X-Tenant-ID: <tenant_id>' \
  -H 'Accept: text/event-stream' \
  -H 'Content-Type: application/json' \
  --data '{"feed_id":20}'
```

## 前端注意事项

1. 不要用 `response.json()`。
2. 不要用浏览器原生 `EventSource`，它不支持 POST JSON body。
3. 不要再轮询 `/api/v1/we-rss/tasks/{task_id}/`。
4. loading 状态从发起请求开始，到收到 `done` 或 catch 到错误结束。
5. 每条 `progress` 都可以直接 `console.log`，也可以追加到页面日志面板。
6. 某一篇失败不会终止整个刷新；失败数据在 `progress.status === "failed"` 和最终 `done.failed_articles` 里。
7. 反向代理如果有 buffering，需要关掉。后端已设置 `X-Accel-Buffering: no`，Nginx 侧也要避免把流攒到最后才吐。

## 推荐页面行为

刷新按钮点击后：

1. 按钮 disabled。
2. 显示 loading 文案：`刷新统计中...`
3. 收到 `start` 后显示总数。
4. 收到 `progress` 后更新当前文章标题和进度。
5. 同时 `console.log("[article-stats:article]", payload)`。
6. 收到 `done` 后显示成功/失败数量。
7. 重新请求文章列表，刷新页面上的统计字段。

