# we_rss 公众号文章 API

这份文档覆盖 `WechatArticle` 相关接口，也就是当前 tenant 下的公众号文章列表、
文章详情、按 URL 导入、单篇刷新、已读、收藏和删除能力。

这里的文章是 `WechatArticle`，与项目中的 `cms.Article` 不是同一个概念。前端
页面、类型定义、状态管理都不要直接复用 `cms.Article` 的字段假设。

## 通用请求头

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 数据结构说明

### 1. WechatArticle 模型字段

`WechatArticle` 继承 `BaseModel` 后，模型层字段如下：

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
| `url` | 业务字段 | 归一化后的公开文章 URL，不保存抓取跳转过程里的 `token` |
| `pic_url` | 业务字段 | 封面图 URL |
| `publish_time` | 业务字段 | 发布时间 |
| `status` | 业务字段 | 文章状态，常见为 `active` 或 `deleted` |
| `is_read` | 业务字段 | 是否已读 |
| `is_favorite` | 业务字段 | 是否收藏 |
| `last_refreshed_at` | 业务字段 | 最近刷新时间 |
| `read_num` | 业务字段 | 阅读数 |
| `like_num` | 业务字段 | 点赞数 |
| `old_like_num` | 业务字段 | 在看数 |
| `share_num` | 业务字段 | 分享数 |
| `collect_num` | 业务字段 | 收藏数 |
| `comment_count` | 业务字段 | 评论数 |
| `comment_reply_count` | 业务字段 | 评论回复数 |
| `comment_total_count` | 业务字段 | 评论总数 |

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
| `url` | `string` | 归一化后的公开文章 URL，不保存抓取跳转过程里的 `token` |
| `pic_url` | `string` | 封面 URL |
| `publish_time` | `string \| null` | 发布时间 |
| `status` | `string` | 文章状态 |
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

不会直接返回给前端的字段包括：

- `tenant`
- `feed` 原对象
- `is_deleted`

### 3. 文章接口可写字段

文章当前没有一个“任意字段编辑接口”。前端只能通过下面三类动作修改文章状态。

#### 按 URL 导入

```json
{
  "url": "https://mp.weixin.qq.com/s/..."
}
```

#### 更新已读状态

```json
{
  "is_read": true
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
| `POST` | `/api/v1/we-rss/articles/import-by-url/` | 按微信文章 URL 导入文章 |
| `POST` | `/api/v1/we-rss/articles/{id}/refresh/` | 刷新单篇文章 |
| `PUT` | `/api/v1/we-rss/articles/{id}/read/` | 更新已读状态 |
| `PUT` | `/api/v1/we-rss/articles/{id}/favorite/` | 更新收藏状态 |

## 1. 获取文章列表

这个接口返回当前 tenant 下全部未软删除文章，不分页。

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

除 `article_type` 之外，当前接口还没有下面这些服务端能力：

- 分页
- 关键字搜索
- 按 `feed_id` 过滤
- 仅收藏过滤
- 仅未读过滤

所以如果页面需要这些筛选，当前版本建议在前端本地完成。

## 2. 获取文章详情

这个接口返回单篇文章完整对外字段，适合详情页或阅读抽屉。

```http
GET /api/v1/we-rss/articles/{id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 文章 ID |

## 3. 删除文章

```http
DELETE /api/v1/we-rss/articles/{id}/
```

当前删除语义是软删除：

- 返回 `204 No Content`
- 数据标记为 `is_deleted = true`
- 后续默认列表中不再出现

它不会去删除微信原始文章，只会删除本地记录。

## 4. 按 URL 导入文章

这个接口根据微信文章 URL 创建一个后台 `article_import` 任务。

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

补充说明：

- 后端会先把文章 URL 归一化，再用于任务去重与最终入库。
- 归一化后的 URL 会保留公开访问所需的稳定参数，例如 `__biz`、`mid`、`idx`、`sn`、`chksm`。
- 抓取过程中微信跳转 URL 里出现的 `token` 等临时参数不会写入 `WechatArticle.url`。

官方参考：
- 微信订阅号草稿接口 `api_draft_add` 使用字段名 `article_type`
- 文章类型支持 `news` 和 `newspic`
- 文档地址：
  `https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html`

当前导入规则非常关键：

- 这是异步接口，返回的是任务对象，不是最终文章对象。
- 任务去重键是 `article_import:<normalized_url>`。
- 如果同一 URL 已经存在 `pending` 或 `running` 任务，会直接返回现有任务。
- 导入时会使用当前 tenant 的有效凭证。如果当前 tenant 没有有效凭证，会失败。
- 导入结果会自动绑定到当前 tenant 的精选 feed。
- 如果当前 tenant 还没有任何 `is_featured = true` 的 feed，会自动创建一条
  `mp_name = "Imported Articles"` 的 feed。
- 如果精选 feed 已存在但没有凭证，会自动补上当前导入所用凭证。
- 如果文章被删除、不可用，或者抓到的正文为空，会直接失败。
- 导入最终会按 `tenant + source_id` 执行 `update_or_create`，所以重复导入同一篇
  文章通常是更新现有记录，不是无限新增重复记录。

任务成功时，`result_payload` 常见字段如下：

| 字段 | 说明 |
| --- | --- |
| `article_id` | 导入后的文章 ID |
| `feed_id` | 自动绑定的 feed ID |
| `source_id` | 文章来源 ID |
| `message` | 结果说明 |

## 5. 刷新单篇文章

这个接口创建一个 `article_refresh` 任务，用于重新抓取当前文章内容与统计字段。

```http
POST /api/v1/we-rss/articles/{id}/refresh/
```

补充说明：

- 刷新后的 `url` 仍然保持归一化后的公开文章 URL，不会被带 `token` 的跳转地址覆盖。

当前刷新规则如下：

- 同一篇文章如果已经存在 `pending` 或 `running` 的刷新任务，会直接返回现有任务。
- 刷新时优先使用 `article.feed.credential`。
- 如果文章所属 feed 没绑定凭证，会回退到当前 tenant 的默认有效凭证或第一条
  有效凭证。
- 成功后会更新文章正文、摘要、封面、发布时间、统计字段，并刷新
  `last_refreshed_at`。

刷新成功时，`result_payload` 常见字段如下：

| 字段 | 说明 |
| --- | --- |
| `article_id` | 当前文章 ID |
| `title` | 刷新后的标题 |
| `updated_by_id` | 触发该刷新的成员 ID |
| `message` | 结果说明 |

## 6. 更新已读状态

这个接口是同步接口，不走后台任务。

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

成功后直接返回更新后的文章对象。当前只有一个可写字段：`is_read`。

## 7. 更新收藏状态

这个接口同样是同步接口。

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

成功后直接返回更新后的文章对象。当前只有一个可写字段：`is_favorite`。

## 前端接入建议

文章列表和详情页建议按下面方式组织：

- 列表页直接使用 `GET /articles/` 全量拉取。
- 如果要区分图文消息和图片消息，直接读取 `article_type`，或者使用
  `GET /articles/?article_type=newspic`。
- 按公众号、按关键字、按收藏这些能力先走前端本地过滤。
- 已读、收藏直接调用同步接口并就地刷新当前条目。
- 刷新正文时走任务轮询。
- 详情页如果只是展示文章内容，通常直接用文章详情里的 `content` 就够了。
- 如果你要做 RSS 阅读器式渲染，再考虑接正文 HTML 输出接口。

## 容易踩坑的点

- 当前没有文章“通用编辑接口”，不要设计成可改标题或正文。
- `import-by-url` 返回的是任务，不是文章详情。
- 导入文章会自动创建或复用精选 feed，这个行为不是前端自己完成的。
- 刷新文章优先走 feed 绑定凭证，不一定总是 tenant 默认凭证。
- 删除文章是软删除。
- 文章列表目前没有后端分页和服务端搜索。

## 下一步

建议继续看：

- [04_同步任务API.md](./04_同步任务API.md)
- [05_RSS与正文输出API.md](./05_RSS与正文输出API.md)
