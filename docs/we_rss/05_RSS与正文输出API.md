# we_rss RSS 与正文输出 API

这份文档覆盖 `we_rss` 当前三个非 JSON 输出接口。它们分别用于输出当前 tenant 的
聚合 RSS、某个公众号的 RSS，以及单篇文章的正文 HTML。

这组接口最容易被误解的点有两个：第一，它们返回 XML 或 HTML，不是 JSON；
第二，它们虽然不是 JSON，但仍然不是公开匿名接口，必须走成员鉴权和 tenant
隔离。

## 通用请求头

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 接口一览

| 方法 | 路径 | 返回类型 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/we-rss/rss/` | `application/xml` | 当前 tenant 聚合 RSS |
| `GET` | `/api/v1/we-rss/rss/{feed_id}/` | `application/xml` | 单个公众号 RSS |
| `GET` | `/api/v1/we-rss/rss/content/{article_id}/` | `text/html` | 单篇文章正文 HTML |

## 数据范围说明

这组三个接口都遵守 tenant 级隔离：

- `GET /rss/` 只会输出当前 tenant 下可见文章。
- `GET /rss/{feed_id}/` 只会输出当前 tenant 下该公众号的文章。
- `GET /rss/content/{article_id}/` 只会输出当前 tenant 下该文章的正文。

如果 `feed_id` 或 `article_id` 不属于当前 tenant，接口会按权限或不存在处理。

## 1. 获取当前 tenant 的聚合 RSS

这个接口输出当前 tenant 下所有文章组成的聚合 RSS。

```http
GET /api/v1/we-rss/rss/
```

返回 `Content-Type`：

```http
application/xml
```

典型读取方式：

```ts
const xml = await weRssTextRequest("/rss/");
```

适合的前端场景包括：

- 内部调试页展示原始 XML
- 做当前 tenant 的统一订阅源预览
- 提供给后续阅读器集成逻辑使用

## 2. 获取单个公众号 RSS

这个接口输出某一条已保存公众号的 RSS。

```http
GET /api/v1/we-rss/rss/{feed_id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `feed_id` | `number` | 公众号记录 ID |

返回 `Content-Type`：

```http
application/xml
```

典型读取方式：

```ts
const xml = await weRssTextRequest(`/rss/${feedId}/`);
```

## 3. 获取单篇文章正文 HTML

这个接口输出单篇文章的 HTML 文本，适合阅读页、内嵌渲染或 RSS 阅读器正文模式。

```http
GET /api/v1/we-rss/rss/content/{article_id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `article_id` | `number` | 文章 ID |

返回 `Content-Type`：

```http
text/html
```

典型读取方式：

```ts
const html = await weRssTextRequest(`/rss/content/${articleId}/`);
```

## 前端读取方式

这组接口不能用 `response.json()` 读取。推荐统一走文本请求封装。

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

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.text();
}
```

## 前端渲染建议

正文 HTML 接口接入时，建议注意下面几点：

- 如果只是文章详情页，优先考虑直接展示文章详情接口里的 `content`。
- 如果你需要和 RSS 输出共用一套阅读器模式，再接 `rss/content/{article_id}/`。
- HTML 注入 DOM 前，要结合前端自身的安全策略处理。
- 这三个接口都不是公开链接，不要直接照搬旧前端里“公开 RSS 地址”的设计。

## 容易踩坑的点

- 返回的是文本，不是 JSON。
- 仍然需要带 `Authorization` 和 `X-Tenant-ID`。
- 当前没有 Atom、JSON Feed、Markdown、Text 等其它输出格式。
- 当前没有匿名可访问的外链 RSS。

## 下一步

如果你要看全链路总文档，可以回到：

- [we_rss_前端完整API文档.md](./we_rss_前端完整API文档.md)
- [README.md](./README.md)
