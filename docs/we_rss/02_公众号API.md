# we_rss 公众号 API

这份文档覆盖 `WechatFeed` 相关接口，也就是当前系统中的“公众号主数据”和
“当前 member 的订阅状态”。你在做公众号搜索、订阅、取消订阅、同步、编辑
、删除和标签管理时，都会用到这一组能力。

这里最重要的口径是：`WechatFeed` 仍然是 tenant 共享主数据，不是某个
member 的私有对象；`is_subscribed` 只是当前 member 对这条 feed 的个人
订阅状态。

标签能力也要分开理解：feed 可以打当前 member 自己的私有标签，但这些标签
不会直接内嵌进 `WechatFeed` 主响应里，而是通过独立对象标签接口查询和维护。

## 通用请求头

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 数据结构说明

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
| `faker_id` | 业务字段 | fakeid / faker_id |
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

列表、详情、创建成功、更新成功、订阅成功响应都会返回下面这些字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 公众号记录 ID |
| `credential_id` | `number \| null` | 绑定的凭证 ID |
| `source_id` | `string` | 微信来源 ID |
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
| `is_subscribed` | `boolean` | 当前 member 是否订阅 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

不会直接返回给前端的字段包括：

- `tenant`
- `is_deleted`
- `credential` 原对象
- `created_by`
- `updated_by`

### 3. 创建和更新可写字段

`POST /feeds/` 和 `PUT /feeds/{id}/` 允许提交的字段如下：

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

`GET /feeds/search/` 返回的是微信平台搜索结果对象，不是已保存的
`WechatFeed` 对象。当前字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source_id` | `string` | 微信来源 ID |
| `faker_id` | `string` | fakeid / faker_id |
| `biz` | `string` | 微信 biz |
| `mp_name` | `string` | 公众号名称 |
| `mp_cover` | `string` | 头像 URL |
| `mp_intro` | `string` | 简介 |

### 5. 订阅请求字段

`POST /feeds/subscribe/` 用搜索结果负载创建或复用 tenant feed，再给当前
member 建立订阅关系。请求体字段如下：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_id` | `string` | 否 | 微信来源 ID |
| `faker_id` | `string` | 否 | fakeid / faker_id |
| `biz` | `string` | 否 | 微信 biz |
| `mp_name` | `string` | 是 | 公众号名称 |
| `mp_cover` | `string` | 否 | 头像 URL |
| `mp_intro` | `string` | 否 | 简介 |

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/we-rss/feeds/` | 获取公众号列表 |
| `POST` | `/api/v1/we-rss/feeds/` | 手动创建公众号记录 |
| `GET` | `/api/v1/we-rss/feeds/search/?keyword=...` | 搜索微信平台公众号 |
| `POST` | `/api/v1/we-rss/feeds/subscribe/` | 订阅公众号 |
| `GET` | `/api/v1/we-rss/feeds/{id}/` | 获取公众号详情 |
| `PUT` | `/api/v1/we-rss/feeds/{id}/` | 更新公众号记录 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/` | 软删除公众号 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/subscribe/` | 取消当前 member 订阅 |
| `GET` | `/api/v1/we-rss/feeds/{id}/tags/` | 获取当前 member 在该 feed 上的标签 |
| `POST` | `/api/v1/we-rss/feeds/{id}/tags/attach/` | 给该 feed 增量绑定标签 |
| `POST` | `/api/v1/we-rss/feeds/{id}/tags/detach/` | 给该 feed 增量解绑标签 |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/articles/` | 永久清空该公众号下全部文章记录 |
| `POST` | `/api/v1/we-rss/feeds/{id}/sync/` | 触发公众号同步任务 |

## 1. 获取公众号列表

这个接口返回当前 tenant 下全部未软删除的 feed 主数据。它支持一个 member
维度过滤参数：

```http
GET /api/v1/we-rss/feeds/
GET /api/v1/we-rss/feeds/?subscribed_only=true
```

查询参数如下：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `subscribed_only` | `boolean` | 可选。为 `true` 时，只返回当前 member 已订阅的 feed。 |
| `tag_ids` | `string` | 可选。逗号分隔的标签 ID，例如 `1,2,3`，多个标签使用 AND 语义。 |

补充说明如下：

- 列表里的 `is_subscribed` 是当前 member 的状态，不是全局字段。
- 不传 `subscribed_only` 时，返回当前 tenant 下全部 feed 主数据。
- 传 `tag_ids` 时，只会匹配当前 member 自己在 feed 上的标签关系。
- 当前没有服务端分页和关键字搜索本地 feed 的能力。

## 2. 手动创建公众号记录

这个接口会直接在当前 tenant 下创建一条本地 `WechatFeed` 记录：

```http
POST /api/v1/we-rss/feeds/
Content-Type: application/json
```

这个接口仍然可用，但对 member 正常订阅流程来说，推荐优先使用
`POST /feeds/subscribe/`。`POST /feeds/` 更适合后台手动录入或补录场景。

## 3. 搜索微信公众号

这个接口不是查本地库，而是拿当前 tenant 的有效微信凭证去请求微信平台：

```http
GET /api/v1/we-rss/feeds/search/?keyword=AI
```

查询参数如下：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | `string` | 是 | 搜索关键字 |

当前业务规则如下：

- 必须提供 `keyword`。
- 当前 tenant 必须存在有效凭证。
- 搜索时优先使用当前 tenant 的默认有效凭证。
- 如果没有默认有效凭证，会回退到当前 tenant 第一条有效凭证。
- 如果完全没有有效凭证，会报错 `Active credential required.`。

## 4. 订阅公众号

这个接口是 member 订阅公众号的标准入口：

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

当前订阅规则如下：

- 后端会先在当前 tenant 中查找是否已有同一公众号主数据。
- 如果已有，会复用已有 `WechatFeed`。
- 如果没有，会按搜索结果负载创建一条新的 `WechatFeed`。
- 然后后端会为当前 member 创建或复用订阅关系。
- 同一 tenant 内，同一公众号可以被多个 member 同时订阅。

## 5. 获取公众号详情

这个接口返回单条已保存 feed 的完整对外字段：

```http
GET /api/v1/we-rss/feeds/{id}/
```

## 6. 更新公众号记录

这个接口可修改 feed 元数据、凭证绑定和精选标记：

```http
PUT /api/v1/we-rss/feeds/{id}/
Content-Type: application/json
```

请求体结构与创建接口相同。补充规则如下：

- `credential_id` 仍然是可选。
- 传入不属于当前 tenant 的 `credential_id` 时，不会报错，但最终会被清空。
- 可以修改 `is_featured`。
- 成功后返回更新后的完整 feed 对象。

## 7. 删除公众号

```http
DELETE /api/v1/we-rss/feeds/{id}/
```

这里的语义是软删除：

- 返回 `204 No Content`。
- 数据会被标记为 `is_deleted = true`。
- 后续不会再出现在默认列表里。

## 8. 取消订阅公众号

```http
DELETE /api/v1/we-rss/feeds/{id}/subscribe/
```

这里删除的是“当前 member 和当前 feed 的订阅关系”，不是删除 feed 主数据。

补充说明如下：

- 返回 `204 No Content`。
- 只影响当前 member。
- 其他 member 对同一 feed 的订阅不受影响。
- feed 主数据仍然保留在 tenant 中。
- 该 member 在这个 feed 上的所有标签关系也会被自动清理。

## 9. feed 标签接口

feed 标签接口只处理“当前 member 对当前 feed 的私有标签关系”。标签本身需
要先在 `/tags/` 下创建，这里不会自动创建新标签。

### 9.1 获取当前 feed 标签

这个接口返回当前 member 绑定到指定 feed 的标签列表：

```http
GET /api/v1/we-rss/feeds/{id}/tags/
```

返回字段沿用标签对象结构，包括：

- `id`
- `name`
- `color`
- `description`
- `sort_order`
- `is_pinned`
- `feed_count`
- `article_count`
- `created_at`
- `updated_at`

### 9.2 增量绑定 feed 标签

这个接口把已有标签增量绑定到当前 feed：

```http
POST /api/v1/we-rss/feeds/{id}/tags/attach/
Content-Type: application/json
```

请求体如下：

```json
{
  "tag_ids": [1, 2, 3]
}
```

绑定规则如下：

- 一次可以传多个 `tag_ids`。
- 这是增量操作，不是全量覆盖。
- 当前 member 必须已经订阅这个 feed，才允许打标签。
- 只能使用当前 member 自己的标签。
- 已存在的绑定关系会被自动忽略，不会重复创建。

### 9.3 增量解绑 feed 标签

这个接口从当前 feed 上解绑已有标签：

```http
POST /api/v1/we-rss/feeds/{id}/tags/detach/
Content-Type: application/json
```

请求体同样是：

```json
{
  "tag_ids": [1, 2, 3]
}
```

解绑规则如下：

- 一次可以传多个 `tag_ids`。
- 这是增量解绑，不是全量覆盖。
- 不存在的绑定关系会被直接忽略。
- 成功后返回解绑后的当前 feed 标签列表。

## 10. 清空公众号下全部文章

这个接口用于清空某个 feed 在当前 tenant 下的全部文章数据库记录：

```http
DELETE /api/v1/we-rss/feeds/{id}/articles/
```

返回示例如下：

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

当前行为说明如下：

- 只删除当前 tenant 下、且 `feed_id = {id}` 的文章。
- 这是永久删除文章记录，不是软删除。
- 不会删除 feed 本身。
- 即使当前没有文章，也会返回成功，`deleted_count = 0`。

## 11. 触发公众号同步

这个接口不会同步返回文章列表，而是创建或复用一个 `feed_sync` 任务：

```http
POST /api/v1/we-rss/feeds/{id}/sync/
```

当前同步规则如下：

- 如果同一个 feed 已经存在 `pending` 或 `running` 的同步任务，会直接返回
  这条现有任务。
- 同步时优先使用 `feed.credential`。
- 如果 `feed.credential` 为空，会回退到当前 tenant 的默认有效凭证或第一条
  有效凭证。
- 如果没有任何有效凭证，同步会失败。
- 后端会持续翻页抓取，直到微信返回空页。

## 前端接入建议

公众号管理页建议至少支持这些交互：

- 搜索微信平台公众号。
- 用搜索结果调用 `POST /feeds/subscribe/` 完成订阅。
- 展示当前 member 的 `is_subscribed`。
- 支持 `subscribed_only=true` 过滤。
- 编辑 feed 的名称、简介、凭证绑定和精选状态。
- 一键触发同步，并跳到任务轮询。

## 容易踩坑的点

- `GET /feeds/search/` 搜的是微信平台，不是本地数据库。
- `POST /feeds/subscribe/` 才是 member 正常订阅流程。
- `POST /feeds/` 仍然可用，但更像手动创建本地 feed，不是订阅动作。
- `DELETE /feeds/{id}/subscribe/` 删除的是订阅关系，不是删除 feed。
- 列表里的 `is_subscribed` 是当前 member 的状态，不是全局字段。
- feed 标签不会内嵌到 `GET /feeds/` 或 `GET /feeds/{id}/` 响应里。
- `POST /feeds/{id}/tags/attach/` 只能给当前 member 已订阅的 feed 打标签。
- `tag_ids` 是逗号分隔字符串查询参数，不是重复 query key。
- `DELETE /feeds/{id}/articles/` 是永久清库动作，不是软删除。
- `POST /feeds/{id}/sync/` 返回的是任务，不是文章列表。

## 下一步

公众号同步跑通后，建议继续看：

- [03_公众号文章API.md](./03_公众号文章API.md)
- [04_同步任务API.md](./04_同步任务API.md)
