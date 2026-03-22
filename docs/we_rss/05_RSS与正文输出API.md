# we_rss RSS 与正文输出 API

这份文档覆盖 `we_rss` 的 3 个非普通 JSON 接口。它们分别用于输出
tenant 级 RSS、单个公众号 RSS，以及单篇文章正文 HTML。

虽然它们输出的是 XML 或 HTML，但它们仍然不是公开接口。前端调用时，
依然必须带 `Member JWT` 和 `X-Tenant-ID`。

## 通用请求头

这 3 个接口都要求下面两个请求头。

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 返回类型说明

这组接口最重要的特点是：它们不是 JSON。

| 接口 | 返回类型 | 前端解析方式 |
| --- | --- | --- |
| tenant RSS | `application/xml` | `await response.text()` |
| feed RSS | `application/xml` | `await response.text()` |
| article HTML | `text/html` | `await response.text()` |

## 1. 获取当前 tenant 的聚合 RSS

这个接口返回当前 tenant 下全部公众号文章的聚合 RSS。适合做“当前租户
所有微信文章的统一订阅源”。

### 请求信息

```http
GET /api/v1/we-rss/rss/
```

### 成功响应示例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tenant A We RSS</title>
    <link>https://example.com/api/v1/we-rss/rss/</link>
    <description>Tenant scoped WeChat article feed.</description>
    <item>
      <title>Imported Article</title>
      <link>https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&amp;mid=1&amp;idx=1&amp;sn=abc</link>
      <description>Imported description</description>
    </item>
  </channel>
</rss>
```

### 前端调用示例

```ts
const xmlText = await weRssTextRequest("/rss/");
console.log(xmlText);
```

## 2. 获取单个公众号的 RSS

这个接口只返回某个公众号下的 RSS。适合做“单公众号订阅页”或
“导出某个公众号的 RSS 地址”。

### 请求信息

```http
GET /api/v1/we-rss/rss/{feed_id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `feed_id` | `number` | 是 | 公众号 ID |

### 成功响应示例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI Daily</title>
    <link>https://example.com/api/v1/we-rss/rss/1/</link>
    <description>RSS feed for a single WeChat public account.</description>
    <item>
      <title>Imported Article</title>
      <link>https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&amp;mid=1&amp;idx=1&amp;sn=abc</link>
      <description>Imported description</description>
    </item>
  </channel>
</rss>
```

### 前端调用示例

```ts
const feedId = 1;
const xmlText = await weRssTextRequest(`/rss/${feedId}/`);
```

## 3. 获取文章正文 HTML

这个接口返回某篇文章的正文 HTML，适合嵌入前端阅读页，或者提供给
RSS 阅读器、导出页使用。

### 请求信息

```http
GET /api/v1/we-rss/rss/content/{article_id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `article_id` | `number` | 是 | 文章 ID |

### 成功响应示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>Imported Article</title>
  </head>
  <body>
    <article>
      <h1>Imported Article</h1>
      <p>Imported description</p>
      <div><p>Imported content</p></div>
    </article>
  </body>
</html>
```

### 前端调用示例

```ts
const html = await weRssTextRequest("/rss/content/1/");
document.getElementById("article-container")!.innerHTML = html;
```

## 浏览器内打开时的注意事项

如果你不是用 `fetch`，而是直接在浏览器里打开这些地址，仍然要考虑鉴权。
这意味着前端通常不能把它们当纯公开 URL 直接发给匿名用户。

推荐做法如下。

| 场景 | 推荐做法 |
| --- | --- |
| 前端内部阅读页 | 通过 `fetch` 拉文本，再自行渲染 |
| 导出 RSS 内容 | 通过后端代理或前端鉴权后获取文本 |
| 外部阅读器订阅 | 先确认是否需要额外的鉴权代理方案 |

## XML / HTML 渲染建议

这类接口前端实现时，建议注意下面几点。

1. 不要调用 `response.json()`。
2. 统一调用 `response.text()`。
3. XML 场景可以再交给 XML parser 处理。
4. HTML 场景如果要插入 DOM，要结合你的前端安全策略处理。

## 典型前端示例

下面这个函数可以统一处理 RSS 和正文输出请求。

```ts
async function loadWeRssText(path: string) {
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

## 下一步

如果你已经看完这份文档，整个 `we_rss` 前端接入链路就可以串起来了。
建议回到索引页，按模块逐项实现。

- [README.md](./README.md)
- [00_总览与对接说明.md](./00_%E6%80%BB%E8%A7%88%E4%B8%8E%E5%AF%B9%E6%8E%A5%E8%AF%B4%E6%98%8E.md)
