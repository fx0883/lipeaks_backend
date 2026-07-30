# we_rss 公众号文章 API

这份文档覆盖 `WechatArticle` 相关接口，也就是当前 tenant 下的公众号文章列表、
文章详情、按 URL 导入、正文刷新、文章统计刷新、收藏、标签和删除能力。

这里最重要的口径是：文章主数据仍然 tenant 共享，所有 member 默认都能看到
当前 tenant 的全部文章；但 `is_favorite` 是 member 维度。当前接口没有已读
状态，也没有 `is_read` 字段。

从这次开始，文章“正文刷新”和“统计刷新”是两套独立能力：

- `/api/v1/we-rss/articles/{id}/refresh/` 仍然用于正文、摘要、封面、发布时间等
  内容刷新。
- `/api/v1/we-rss/article-stats/refresh-by-url/` 和
  `/api/v1/we-rss/article-stats/refresh/` 只负责统计字段刷新。

## 通用请求头

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 数据结构说明

### 1. WechatArticle 模型字段

`WechatArticle` 继承 `BaseModel` 后，模型层真实字段如下：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `tenant` | `BaseModel` | 所属租户 |
| `created_at` | `BaseModel` | 创建时间 |
| `updated_at` | `BaseModel` | 更新时间 |
| `is_deleted` | `BaseModel` | 软删除标记 |
| `feed` | 业务字段 | 所属公众号，可为空 |
| `source_id` | 业务字段 | 微信文章来源 ID |
| `article_type` | 业务字段 | 微信文章类型，取值为 `news` 或 `newspic` |
| `title` | 业务字段 | 标题 |
| `description` | 业务字段 | 摘要 |
| `content` | 业务字段 | 正文 HTML |
| `url` | 业务字段 | 归一化后的公开文章 URL |
| `pic_url` | 业务字段 | 封面图 URL |
| `publish_time` | 业务字段 | 发布时间 |
| `status` | 业务字段 | 文章状态 |
| `last_refreshed_at` | 业务字段 | 最近刷新时间 |
| `read_num` | 业务字段 | 阅读数 |
| `like_num` | 业务字段 | 点赞数 |
| `old_like_num` | 业务字段 | 在看数 |
| `share_num` | 业务字段 | 分享数 |
| `collect_num` | 业务字段 | 收藏数 |
| `comment_count` | 业务字段 | 评论数 |
| `comment_reply_count` | 业务字段 | 评论回复数 |
| `comment_total_count` | 业务字段 | 评论总数 |

模型层已经没有下面两个旧字段：

- `is_read`
- `is_favorite`

### 2. 文章接口返回字段

列表和详情接口当前返回下列字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 文章 ID |
| `feed_id` | `number \| null` | 所属公众号 ID |
| `source_id` | `string` | 微信文章来源 ID |
| `article_type` | `string` | 微信文章类型，取值为 `news` 或 `newspic` |
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

不会直接返回给前端的字段包括：

- `tenant`
- `feed`
- `is_deleted`

### 3. 可写动作字段

文章当前没有通用编辑接口。前端只会通过下面几类动作修改状态：

#### 按 URL 导入

```json
{
  "url": "https://mp.weixin.qq.com/s/..."
}
```

#### 按 URL 同步刷新文章统计

```json
{
  "url": "https://mp.weixin.qq.com/s/..."
}
```

#### 批量刷新文章统计

```json
{
  "article_ids": [11, 12, 13]
}
```

```json
{
  "feed_id": 5
}
```

```json
{
  "member_id": 9
}
```

#### 更新收藏状态

```json
{
  "is_favorite": true
}
```

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/we-rss/articles/` | 获取文章列表 |
| `GET` | `/api/v1/we-rss/articles/{id}/` | 获取文章详情 |
| `DELETE` | `/api/v1/we-rss/articles/{id}/` | 软删除文章 |
| `POST` | `/api/v1/we-rss/article-stats/refresh-by-url/` | 按 URL 同步刷新文章统计并返回完整文章 |
| `POST` | `/api/v1/we-rss/article-stats/refresh/` | 批量异步刷新文章统计 |
| `POST` | `/api/v1/we-rss/articles/import-by-url/` | 按微信文章 URL 导入文章 |
| `POST` | `/api/v1/we-rss/articles/{id}/refresh/` | 刷新单篇文章正文 |
| `PUT` | `/api/v1/we-rss/articles/{id}/favorite/` | 更新当前 member 收藏状态 |
| `GET` | `/api/v1/we-rss/articles/{id}/tags/` | 获取当前 member 在该文章上的标签 |
| `POST` | `/api/v1/we-rss/articles/{id}/tags/attach/` | 给文章增量绑定标签 |
| `POST` | `/api/v1/we-rss/articles/{id}/tags/detach/` | 给文章增量解绑标签 |

## 1. 获取文章列表

这个接口返回当前 tenant 下全部未软删除文章，不分页。

```http
GET /api/v1/we-rss/articles/
```

当前支持的服务端过滤参数如下：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `article_type` | `string` | 可选，支持 `news` 或 `newspic` |
| `search` | `string` | 可选，只按标题搜索 |
| `favorite_only` | `boolean` | 可选。为 `true` 时，只返回当前 member 已收藏文章 |
| `tag_ids` | `string` | 可选。逗号分隔的标签 ID，例如 `1,2,3`，多个标签使用 AND 语义 |

示例如下：

```http
GET /api/v1/we-rss/articles/?article_type=newspic
GET /api/v1/we-rss/articles/?search=AI
GET /api/v1/we-rss/articles/?favorite_only=true
GET /api/v1/we-rss/articles/?tag_ids=1,2,3
```

`search` 的关键词拆分规则：

- 只搜 `title`
- 会先把 `-` 和 `|` 替换为空格
- 再按空格拆词
- 多个词按 OR 匹配

补充说明如下：

- 返回里的 `is_favorite` 是当前 member 的状态，不是全局字段。
- 当前没有 `is_read`，也没有只看未读的过滤。
- 传 `tag_ids` 时，只会匹配当前 member 自己在文章上的标签关系。
- 当前没有分页、按 `feed_id` 过滤等其他服务端能力。

## 2. 获取文章详情

这个接口返回单篇文章完整对外字段，适合详情页或阅读抽屉。

```http
GET /api/v1/we-rss/articles/{id}/
```

## 3. 删除文章

```http
DELETE /api/v1/we-rss/articles/{id}/
```

当前删除语义是软删除：

- 返回 `204 No Content`
- 数据标记为 `is_deleted = true`
- 后续默认列表里不再出现
- 当前文章上的标签关系会随删除自动清理

## 4. 按 URL 导入文章

这个接口根据微信文章 URL 创建一个后台 `article_import` 任务。

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

补充说明如下：

- 后端会先把文章 URL 归一化，再用于任务去重和最终入库。
- `WechatArticle.url` 保存的是稳定公开链接，不保留抓取过程里的临时
  `token` 参数。
- 这是异步接口，返回的是任务对象，不是最终文章对象。
- 任务去重键是 `article_import:<normalized_url>`。
- 导入会自动绑定到当前 tenant 的精选 feed。
- 如果当前 tenant 还没有任何 `is_featured = true` 的 feed，会自动创建
  `mp_name = "Imported Articles"` 的 feed。

## 5. 按 URL 同步刷新文章统计

这个接口用于“只刷新统计数据”。它要求前端传入当前 tenant 内已经存在的文章 URL，
后端会先更新数据库，再返回完整文章对象。

```http
POST /api/v1/we-rss/article-stats/refresh-by-url/
Content-Type: application/json
```

请求体如下：

```json
{
  "url": "https://mp.weixin.qq.com/s/article-1?token=123456"
}
```

处理规则如下：

- 这是同步接口，不创建后台任务。
- URL 只用于定位当前 tenant 下已存在的文章，不会自动创建新文章。
- 后端会先归一化 URL，再匹配已有文章记录。
- 成功后会更新这些字段：
  `read_num`、`like_num`、`old_like_num`、`share_num`、`collect_num`、
  `comment_count`、`comment_reply_count`、`comment_total_count`、
  `last_refreshed_at`。
- 成功后直接返回更新落库后的完整 `WechatArticle` 对象。
- 如果当前 tenant 下找不到对应文章，返回 `404`。
- 如果统计运行时未就绪，例如缺少 `session.json` 或 `proxy-live.log`，
  返回 `400`。

这个接口和旧接口的区别如下：

- 它不导入文章，因此和 `/articles/import-by-url/` 无关。
- 它不刷新正文、标题、摘要、封面、发布时间，因此和
  `/articles/{id}/refresh/` 无关。

## 6. 批量异步刷新文章统计

这个接口用于批量刷新文章统计。它只创建任务，不在响应里返回每篇文章数据。

```http
POST /api/v1/we-rss/article-stats/refresh/
Content-Type: application/json
```

请求体三选一：

```json
{
  "article_ids": [11, 12, 13]
}
```

```json
{
  "feed_id": 5
}
```

```json
{
  "member_id": 9
}
```

处理规则如下：

- 这是异步接口，返回的是任务对象，不是文章数组。
- `article_ids`、`feed_id`、`member_id` 只能传一种。
- `article_ids` 会先去重，但如果其中任意一篇文章不属于当前 tenant 或不存在，
  会直接返回 `400`。
- `feed_id` 表示刷新该公众号下全部文章。
- `member_id` 表示刷新该成员订阅的所有公众号下全部文章。
- 成功创建后返回的任务类型是 `article_stats_refresh`。
- 后台任务逐篇更新文章统计字段，并把结果写回 `WechatArticle`。
- 即使部分文章刷新失败，只要任务整体跑完，任务状态仍然会是 `success`。

任务完成后，`result_payload` 重点字段如下：

- `selector_type`
- `requested_count`
- `success_count`
- `failed_count`
- `article_ids`
- `failed_articles`

`failed_articles` 中每一项都包含：

- `article_id`
- `url`
- `error`

## 7. 刷新单篇文章正文

这个接口创建一个 `article_refresh` 任务，用于重新抓取当前文章内容与统计字段。

```http
POST /api/v1/we-rss/articles/{id}/refresh/
```

当前刷新规则如下：

- 同一篇文章如果已经存在 `pending` 或 `running` 的刷新任务，会直接返回现有任务。
- 刷新时优先使用 `article.feed.credential`。
- 如果文章所属 feed 没有绑定凭证，会回退到当前 tenant 的默认有效凭证或第一条
  有效凭证。
- 成功后会更新正文、摘要、封面、发布时间、统计字段和 `last_refreshed_at`。

这个接口适合“内容级刷新”。如果前端只是想更新统计数字，优先使用
`/api/v1/we-rss/article-stats/refresh-by-url/` 或
`/api/v1/we-rss/article-stats/refresh/`。

## 8. 更新收藏状态

这个接口是同步接口，不走后台任务。

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

补充说明如下：

- 这里更新的是“当前 member 对这篇文章的收藏关系”。
- 成功后直接返回更新后的文章对象。
- 同一篇文章可以被同一 tenant 下多个 member 分别收藏。
- 其他 member 的收藏状态不会受影响。

## 9. 文章标签接口

文章标签接口处理的是“当前 member 对当前 article 的私有标签关系”。标签本身
必须先在 `/tags/` 下创建，这里不会自动创建标签。

### 9.1 获取当前文章标签

```http
GET /api/v1/we-rss/articles/{id}/tags/
```

### 9.2 增量绑定文章标签

```http
POST /api/v1/we-rss/articles/{id}/tags/attach/
Content-Type: application/json
```

请求体如下：

```json
{
  "tag_ids": [1, 2, 3]
}
```

绑定规则如下：

- 一次可以传多个 `tag_ids`
- 这是增量操作，不是全量覆盖
- 只能使用当前 member 自己的标签
- 只要文章在当前 tenant 中存在，就允许绑定，不要求当前 member 已订阅对应 feed
- 已存在的绑定关系会被自动忽略，不会重复创建

### 9.3 增量解绑文章标签

```http
POST /api/v1/we-rss/articles/{id}/tags/detach/
Content-Type: application/json
```

请求体同样是：

```json
{
  "tag_ids": [1, 2, 3]
}
```

解绑规则如下：

- 一次可以传多个 `tag_ids`
- 这是增量解绑，不是全量覆盖
- 不存在的绑定关系会被直接忽略
- 成功后返回解绑后的当前文章标签列表

## 前端接入建议

文章列表和详情页建议按下面方式组织：

- 列表页直接使用 `GET /articles/` 全量拉取。
- 如果要做标题搜索，直接使用服务端 `search`。
- 如果要只看收藏，直接使用 `favorite_only=true`。
- 如果要按标签筛选，使用 `tag_ids=1,2,3`，多个标签是 AND 语义。
- 如果要区分图文消息和图片消息，读取 `article_type`，或者使用
  `GET /articles/?article_type=newspic`。
- 收藏操作直接调用 `PUT /articles/{id}/favorite/` 并就地刷新当前条目。
- 如果只是刷新统计数字，优先调用
  `POST /api/v1/we-rss/article-stats/refresh-by-url/` 或
  `POST /api/v1/we-rss/article-stats/refresh/`。
- 如果要刷新正文、摘要、封面和发布时间，继续走
  `POST /api/v1/we-rss/articles/{id}/refresh/` 并轮询任务。
- 文章标签操作走独立 `/articles/{id}/tags/*` 接口，不要改造主文章响应结构。

## 容易踩坑的点

- 当前没有文章 `read` 接口，也没有 `is_read` 字段。
- `is_favorite` 是当前 member 的状态，不是全局字段。
- 文章标签不会内嵌到 `GET /articles/` 或 `GET /articles/{id}/` 响应里。
- 文章列表已经支持服务端标题搜索，不要再写成“只做前端本地搜索”。
- `search` 只搜 `title`，不要误搜摘要或正文。
- 文章标签不要求先订阅对应 feed，只要求文章在当前 tenant 中存在。
- `import-by-url` 返回的是任务，不是文章详情。
- `article-stats/refresh-by-url/` 返回的是已经更新落库后的完整文章，不是任务。
- `article-stats/refresh/` 返回的是 `article_stats_refresh` 任务，不是文章数组。
- `articles/{id}/refresh/` 是正文刷新任务，不要和统计刷新接口混用。
- 导入文章会自动创建或复用精选 feed，这不是前端自己完成的。
- 删除文章是软删除。

## 下一步

建议继续看：

- [04_同步任务API.md](./04_同步任务API.md)
- [05_RSS与正文输出API.md](./05_RSS与正文输出API.md)
