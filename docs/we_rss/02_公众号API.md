# we_rss 公众号 API

这份文档覆盖 `WechatFeed` 相关接口，也就是当前系统中“公众号记录”的接口。
前端在做公众号搜索、保存、编辑、删除、同步时，都会使用这一组能力。

这里的“公众号”是当前 tenant 下保存的一条 `WechatFeed` 记录。它既可以来自
微信平台搜索结果，也可以由前端手动录入。后续公众号同步任务，会基于这条
记录继续抓取文章并 upsert 到 `WechatArticle`。

## 通用请求头

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 数据结构说明

这部分同样按“模型字段”“接口返回字段”“接口可写字段”拆开说明。

### 1. WechatFeed 模型字段

`WechatFeed` 当前继承 `BaseModel`。模型层真实字段如下：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `tenant` | `BaseModel` | 所属租户 |
| `created_at` | `BaseModel` | 创建时间 |
| `updated_at` | `BaseModel` | 更新时间 |
| `is_deleted` | `BaseModel` | 软删除标记 |
| `credential` | 业务字段 | 绑定微信凭证，可为空 |
| `source_id` | 业务字段 | 微信侧来源 ID |
| `faker_id` | 业务字段 | 微信 fakeid / faker_id |
| `biz` | 业务字段 | 微信 biz |
| `mp_name` | 业务字段 | 公众号名称 |
| `mp_cover` | 业务字段 | 公众号头像 |
| `mp_intro` | 业务字段 | 公众号简介 |
| `status` | 业务字段 | 当前状态，默认 `active` |
| `sync_time` | 业务字段 | 最近同步时间 |
| `update_time` | 业务字段 | 最近更新文章元数据时间 |
| `last_synced_at` | 业务字段 | 最近一次同步完成时间 |
| `is_featured` | 业务字段 | 是否为精选 feed |
| `created_by` | 业务字段 | 创建成员 |
| `updated_by` | 业务字段 | 更新成员 |

### 2. 公众号接口返回字段

列表、详情、创建成功响应、更新成功响应都返回下面这些字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 公众号记录 ID |
| `credential_id` | `number \| null` | 绑定的凭证 ID |
| `source_id` | `string` | 微信侧来源 ID |
| `faker_id` | `string` | fakeid / faker_id |
| `biz` | `string` | 微信 biz |
| `mp_name` | `string` | 公众号名称 |
| `mp_cover` | `string` | 公众号头像 URL |
| `mp_intro` | `string` | 公众号简介 |
| `status` | `string` | 当前状态 |
| `sync_time` | `string \| null` | 最近同步时间 |
| `update_time` | `string \| null` | 最近更新时间 |
| `last_synced_at` | `string \| null` | 最近同步完成时间 |
| `is_featured` | `boolean` | 是否精选 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

不会返回给前端的字段包括：

- `tenant`
- `is_deleted`
- `credential` 原对象
- `created_by`
- `updated_by`

### 3. 创建 / 更新可写字段

`FeedWriteSerializer` 当前允许提交的字段如下：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `credential_id` | `number \| null` | 否 | 绑定凭证 ID |
| `source_id` | `string` | 否 | 微信来源 ID |
| `faker_id` | `string` | 否 | fakeid / faker_id |
| `biz` | `string` | 否 | 微信 biz |
| `mp_name` | `string` | 是 | 公众号名称 |
| `mp_cover` | `string` | 否 | 头像 URL |
| `mp_intro` | `string` | 否 | 简介 |
| `status` | `string` | 否 | 默认 `active` |
| `is_featured` | `boolean` | 否 | 默认 `false` |

### 4. 搜索结果字段

`GET /feeds/search/` 返回的是搜索结果对象，不是已保存的 `WechatFeed` 对象。
当前字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source_id` | `string` | 微信来源 ID |
| `faker_id` | `string` | fakeid / faker_id |
| `biz` | `string` | 微信 biz |
| `mp_name` | `string` | 公众号名称 |
| `mp_cover` | `string` | 头像 URL |
| `mp_intro` | `string` | 简介 |

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/we-rss/feeds/` | 获取公众号列表 |
| `POST` | `/api/v1/we-rss/feeds/` | 创建公众号记录 |
| `GET` | `/api/v1/we-rss/feeds/search/?keyword=...` | 搜索微信平台公众号 |
| `GET` | `/api/v1/we-rss/feeds/{id}/` | 获取公众号详情 |
| `PUT` | `/api/v1/we-rss/feeds/{id}/` | 更新公众号记录 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/` | 软删除公众号 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/articles/` | 永久清空该公众号下全部文章记录 |
| `POST` | `/api/v1/we-rss/feeds/{id}/sync/` | 触发公众号同步任务 |

## 1. 获取公众号列表

这个接口返回当前 tenant 下全部未软删除的公众号记录，不分页。

```http
GET /api/v1/we-rss/feeds/
```

接口当前没有服务端过滤参数。也就是说：

- 没有分页。
- 没有按 `credential_id` 过滤。
- 没有按 `is_featured` 过滤。
- 没有按关键字搜索已保存公众号。

如果前端页面需要这些交互，当前版本建议先做本地过滤。

## 2. 创建公众号记录

这个接口把一条公众号信息保存到当前 tenant。

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

当前创建规则有几个需要注意：

- `mp_name` 是唯一必填业务字段。
- `credential_id` 可以不传。
- 如果传了 `credential_id`，后端只会绑定“属于当前 tenant 的凭证”。
- 如果传入的 `credential_id` 不存在，或者不属于当前 tenant，当前实现不会报错，
  最终会以 `credential = null` 保存。

因此，前端最好让用户从当前 tenant 的凭证列表中选，而不要手填 ID。

## 3. 搜索微信平台公众号

这个接口不是查本地库，而是拿当前 tenant 的有效微信凭证去请求微信平台。

```http
GET /api/v1/we-rss/feeds/search/?keyword=AI
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | `string` | 是 | 搜索关键字 |

当前业务规则如下：

- 必须提供 `keyword`。
- 当前 tenant 必须存在有效凭证。
- 搜索时优先使用当前 tenant 的默认有效凭证。
- 如果没有默认有效凭证，会回退到当前 tenant 下第一条有效凭证。
- 如果完全没有有效凭证，会报错 `Active credential required.`。

响应的 `data` 是搜索结果数组，不带 `id`，因为这些结果还没保存为本地
`WechatFeed`。

## 4. 获取公众号详情

这个接口返回单条已保存公众号的完整对外字段。

```http
GET /api/v1/we-rss/feeds/{id}/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 公众号记录 ID |

## 5. 更新公众号记录

这个接口可修改公众号元数据、绑定凭证和精选标记。

```http
PUT /api/v1/we-rss/feeds/{id}/
Content-Type: application/json
```

请求体结构与创建接口相同。更新规则和创建规则一致：

- `credential_id` 仍然是可选。
- 传入一个不属于当前 tenant 的 `credential_id` 时，不会报错，最终会被清成空。
- 可以修改 `is_featured`。
- 成功后返回更新后的完整公众号对象。

## 6. 删除公众号

```http
DELETE /api/v1/we-rss/feeds/{id}/
```

当前语义同样是软删除：

- 返回 `204 No Content`。
- 数据会被标记为 `is_deleted = true`。
- 后续不会再出现在默认列表里。

## 7. 清空公众号下全部文章

这个接口用于清空某个公众号在当前 tenant 下的全部文章数据库记录。

```http
DELETE /api/v1/we-rss/feeds/{id}/articles/
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 公众号记录 ID |

返回示例：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "feed_id": 1,
    "deleted_count": 12
  }
}
```

当前行为说明：

- 只删除当前 tenant 下、且 `feed_id = {id}` 的文章。
- 这个操作会永久删除数据库记录，不是软删除。
- 不会删除公众号本身。
- 不会删除其他公众号下的文章。
- 即使这个公众号当前没有文章，也会返回成功，`deleted_count = 0`。

## 8. 触发公众号同步

这个接口不会同步返回文章列表，而是创建或复用一个 `feed_sync` 任务。

```http
POST /api/v1/we-rss/feeds/{id}/sync/
```

当前同步规则非常重要：

- 如果同一个 feed 已经存在 `pending` 或 `running` 的同步任务，会直接返回这条
  现有任务，而不是创建重复任务。
- 同步执行时优先使用 `feed.credential`。
- 如果 `feed.credential` 为空，会回退到当前 tenant 的默认有效凭证或第一条有效
  凭证。
- 如果没有任何有效凭证，同步会失败。
- 微信网关抓取文章列表时，当前默认每页请求 `5` 篇文章。
- 同步不再限制固定页数。后端会持续翻页，直到微信返回空页为止。
- 后端会在两个抓取阶段之间主动限速：
  - 请求下一页文章列表前，会等待 `0.5` 秒。
  - 请求下一篇文章详情前，也会等待 `0.5` 秒。
- 单篇文章详情抓取失败时，不会中断整次同步。当前实现会保留列表页里的基础
  字段，并把失败原因记录到任务结果里。

同步成功后，后端会做下面几件事：

- 按页抓取公众号文章列表，直到微信返回空页。
- 逐篇抓取文章详情，并解析标题、摘要、正文、封面、发布时间和互动统计。
- 按 `tenant + source_id` 对文章执行 upsert。
- 更新 feed 的 `sync_time`、`update_time`、`last_synced_at`。
- 如果抓取到了更准确的 `biz`、`mp_name`、`mp_cover`，会回写 feed。

同步成功时，任务的 `result_payload` 中常见字段包括：

| 字段 | 说明 |
| --- | --- |
| `feed_id` | 当前 feed ID |
| `article_ids` | 这次同步 upsert 的文章 ID 列表 |
| `article_count` | 文章数量 |
| `detail_success_count` | 详情抓取成功数 |
| `detail_failed_count` | 详情抓取失败数 |
| `failed_articles` | 失败明细数组 |
| `result_payload` | 微信网关层的原始汇总结果 |

## 前端接入建议

公众号管理页建议至少支持这些交互：

- 列表展示 `mp_name`、`mp_cover`、`mp_intro`、`credential_id`、
  `last_synced_at`、`is_featured`。
- 从搜索结果一键创建本地 feed。
- 编辑 feed 的名称、简介、凭证绑定和精选状态。
- 一键触发同步。
- 同步后跳到任务详情，或者直接开始轮询任务。

## 容易踩坑的点

这里列一下当前实现中最容易误解的地方。

- `GET /feeds/search/` 搜的是微信平台，不是本地数据库。
- 公众号列表接口当前没有分页和服务端搜索。
- `credential_id` 不一定传了就会真正绑定成功，必须属于当前 tenant。
- `DELETE /feeds/{id}/articles/` 是永久清库动作，不是软删除。
- `POST /feeds/{id}/sync/` 返回的是任务，不是文章列表。
- `POST /feeds/{id}/sync/` 当前会一直翻页抓取，直到微信返回空页，不是只抓固定
  几页。
- 同一个 feed 的同步任务会去重复用。
- 删除公众号是软删除。

## 下一步

公众号同步跑通后，建议继续看：

- [03_公众号文章API.md](./03_公众号文章API.md)
- [04_同步任务API.md](./04_同步任务API.md)
