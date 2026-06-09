# we_rss 文章统计刷新接口设计

本文档描述 `we_rss` 中一组新的文章统计刷新接口。目标是把
`scripts/lipeaks_viral_articles` 里的 URL-first 微信文章统计能力接入到
`we_rss`，并且与现有的文章导入、文章内容刷新接口彻底解耦。

这组接口只负责刷新文章统计数据，不负责导入新文章，也不负责刷新正文、
标题、封面、发布时间等内容字段。

## 目标

这次设计要解决两个使用场景：

1. 前端传入单个文章 URL，同步刷新该文章的统计字段，更新数据库后返回完整
   文章数据。
2. 前端选择多篇文章、某个公众号下全部文章，或者某个成员订阅下全部文章，
   以异步任务方式批量刷新统计字段。

接口必须满足下面这些要求：

- 单个 URL 刷新走同步调用。
- 批量刷新走异步任务。
- 单个刷新和批量刷新都只处理当前租户下已存在的文章。
- 单个刷新和批量刷新都复用同一套底层统计抓取能力。
- 新接口不复用现有 `/articles/import-by-url/` 和 `/articles/{id}/refresh/`。

## 非目标

本文档也明确排除下面这些范围，避免和现有能力混在一起：

- 不通过新接口创建文章记录。
- 不通过新接口导入公众号或文章正文。
- 不通过新接口刷新 `title`、`description`、`content`、`pic_url`、
  `publish_time`、`article_type`。
- 不把新接口并入现有 `ArticleService.refresh_article()` 语义。

## 现状与约束

当前 `we_rss` 已经有文章导入和文章刷新链路，但它们依赖公众号后台凭证，
主要用途是抓取文章详情和正文。当前 POC 提供的是另一条能力链路：输入文章
URL，结合本地 `session.json` 与 `proxy-live.log` 回放微信接口，得到文章
统计结果。

当前仓库中的真实可导入路径不是 POC 文档示例里的
`scripts.wechat_replay_getappmsgext`，而是：

```python
from scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext import collect_stats
```

这意味着 `we_rss` 接入时必须显式依赖当前仓库中的 POC 路径，不能直接照搬
POC 文档示例中的 import。

此外，这套能力依赖下面两个运行时文件：

- `scripts/lipeaks_viral_articles/output/wechat-stats/session.json`
- `scripts/lipeaks_viral_articles/output/wechat-stats/proxy-live.log`

如果这两个文件不存在、内容已失效，或者没有被最新代理流量刷新，那么接口
即使拿到了正确 URL，也可能抓取失败。

## 总体方案

推荐在 `we_rss` 中新增一套独立的“文章统计刷新”边界，而不是把统计刷新并入
现有文章导入或正文刷新逻辑。

这一层包含四个组成部分：

1. 新的服务层，负责 URL 归一化、文章定位、POC 调用、字段过滤和数据库更新。
2. 新的序列化层，负责同步刷新请求与批量刷新请求的校验。
3. 新的视图动作，负责暴露同步接口和批量异步接口。
4. 新的异步任务类型和执行函数，负责批量刷新。

这种拆分可以让“正文刷新”和“统计刷新”分别拥有稳定边界，避免后续出现同一
个接口同时承担内容抓取、正文转换、统计回放等职责。

## 接口设计

本设计新增两类接口。它们共用同一套底层统计刷新逻辑，但对外行为不同。

### 单个 URL 同步刷新

这个接口用于前端基于一个已存在文章的 URL 立即刷新统计并拿到更新后的完整
文章对象。

推荐接口：

```text
POST /api/v1/we-rss/article-stats/refresh-by-url/
```

请求体：

```json
{
  "url": "https://mp.weixin.qq.com/s/dQh_Q7XYYn9P8HmBEYOiWg"
}
```

处理流程：

1. 校验 URL 是否为微信文章 URL。
2. 按现有 `we_rss` 规则归一化 URL，移除临时查询参数。
3. 在当前租户内用归一化后的 URL 查找已存在文章。
4. 找到文章后调用 POC 的 `collect_stats()`。
5. 将返回的统计字段更新到数据库。
6. 刷新 `last_refreshed_at`。
7. 返回更新后的完整 `WechatArticle` 序列化结果。

这个接口不返回单独的“统计快照 DTO”。它返回的是已经更新入库后的完整文章
对象，这样前端可以直接用返回值覆盖当前文章详情或列表数据。

### 批量异步刷新

这个接口用于批量刷新文章统计，不在创建任务时返回每篇文章数据。

推荐接口：

```text
POST /api/v1/we-rss/article-stats/refresh/
```

请求体支持三种选择器：

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

批量接口的行为如下：

1. 校验选择器，只允许三种模式中的一种生效。
2. 根据选择器在当前租户内解析出目标文章集合。
3. 创建新的异步任务。
4. 立即返回任务对象。
5. 后台任务逐篇调用同一套统计刷新逻辑。
6. 任务完成后在任务详情里呈现成功数、失败数和失败明细。

因为批量接口本身是异步接口，所以创建任务时不返回每篇文章的统计数据或文章
详情。

## 请求选择器规则

批量接口需要支持三种选择器，它们底层都会解析成文章集合。

### `article_ids`

当请求体包含 `article_ids` 时，接口只刷新显式传入的文章 ID。这个模式优先级
最高，适合前端从列表中勾选多篇文章后批量刷新。

规则：

- 需要去重。
- 所有文章必须属于当前租户。
- 如果存在任意不存在或不属于当前租户的文章 ID，接口直接返回校验错误。

### `feed_id`

当请求体包含 `feed_id` 时，接口刷新该公众号下的全部文章。

规则：

- `feed_id` 必须属于当前租户。
- 查询结果按当前服务中的稳定排序返回给后台任务处理。

### `member_id`

当请求体包含 `member_id` 时，接口刷新该成员订阅的所有公众号下的全部文章。

规则：

- `member_id` 必须属于当前租户。
- 目标文章集合来自该成员订阅的 feed 集合。
- 如果一个成员没有订阅任何 feed，接口仍可创建任务，但任务结果中的请求数为
  `0`。

## 数据更新边界

这组新接口只更新统计相关字段和刷新时间，不修改文章内容字段。

允许更新的字段如下：

- `read_num`
- `like_num`
- `old_like_num`
- `share_num`
- `collect_num`
- `comment_count`
- `comment_reply_count`
- `comment_total_count`
- `last_refreshed_at`

明确不更新的字段如下：

- `title`
- `description`
- `content`
- `pic_url`
- `publish_time`
- `article_type`
- `status`

这样做的原因是统计刷新和正文刷新有不同的依赖、失败模式和调用成本。把两者
拆开后，统计刷新可以稳定地围绕 `article_url -> stats -> update article`
这条契约工作。

## 底层服务边界

推荐在 `we_rss` 中新增一个独立服务，例如 `article_stats_service.py`。这个服务
负责承接新的统计刷新能力，不让现有 `ArticleService` 承担额外语义。

建议保留两个核心入口：

```python
def refresh_article_stats_by_url(*, tenant, article_url: str) -> WechatArticle:
    ...


def refresh_article_stats_for_article(*, article: WechatArticle) -> WechatArticle:
    ...
```

其中：

- `refresh_article_stats_by_url()` 用于同步接口。
- `refresh_article_stats_for_article()` 用于同步接口和批量任务内部复用。

服务层内部需要负责下面这些动作：

1. 归一化文章 URL。
2. 根据 URL 在当前租户定位已存在文章。
3. 检查 POC 依赖文件是否存在。
4. 调用 `collect_stats()`。
5. 使用白名单字段更新文章统计字段。
6. 写入 `last_refreshed_at`。
7. 返回更新后的文章对象。

## POC 集成边界

POC 仍然是统计抓取的来源，但 `we_rss` 不应该直接向上层暴露 POC 的全部内部
细节。

`we_rss` 需要从 POC 结果中只提取下面这些字段：

- `read_num`
- `like_num`
- `old_like_num`
- `share_num`
- `collect_num`
- `comment_count`
- `comment_reply_count`
- `comment_total_count`

这些字段已经是 POC 文档中定义好的稳定输出。`we_rss` 不应该把下面这些底层
字段泄漏到接口契约中：

- `mid`
- `idx`
- `sn`
- `__biz`
- `key`
- `uin`
- `pass_ticket`
- `appmsg_token`
- `session.json` 内部结构

## 同步接口响应

同步接口完成数据库更新后，返回完整文章对象，而不是只返回统计结果。

推荐直接复用现有 `WechatArticleSerializer` 的输出结构。这样前端不需要额外兼容
一套新的文章详情响应格式。

同步接口响应语义：

- 返回对象必须已经反映数据库中的最新统计值。
- `last_refreshed_at` 必须是本次同步刷新写入后的值。
- 其他非统计字段保持文章原值。

## 异步任务设计

批量刷新需要新的任务类型，避免与现有 `article_refresh` 语义混淆。

推荐新增任务类型：

```text
article_stats_refresh
```

这个任务类型只表示“刷新统计数据”，不表示“刷新正文和文章元数据”。

推荐任务目标：

- `target_type` 固定为 `article_stats`
- `target_id` 对于批量任务可为空
- `task_key` 可按选择器生成，例如：
  - `article_stats_refresh:article_ids:<hash>`
  - `article_stats_refresh:feed:<id>`
  - `article_stats_refresh:member:<id>`

## 异步任务结果语义

批量任务的整体状态规则如下：

- 只要任务完整执行完毕，即使其中部分文章刷新失败，任务整体状态仍记为
  `success`。
- 只有任务本身未能启动、选择器解析异常、或执行器级别异常时，任务才记为
  `failed`。

`result_payload` 推荐包含下面这些字段：

- `selector_type`
- `requested_count`
- `success_count`
- `failed_count`
- `article_ids`
- `failed_articles`

`failed_articles` 例子：

```json
[
  {
    "article_id": 3,
    "url": "https://mp.weixin.qq.com/s/example",
    "error": "session.json or proxy-live.log not ready"
  }
]
```

这样前端既能知道任务完成了，也能知道哪些文章没有刷新成功。

## 错误处理

错误处理需要区分同步接口错误和批量任务内部错误。

### 同步接口

同步接口推荐遵循下面这些规则：

- 如果 `url` 不是合法微信文章 URL，返回 `400`。
- 如果根据 URL 在当前租户找不到文章，返回 `404`。
- 如果 `session.json` 或 `proxy-live.log` 不存在，返回 `400`。
- 如果 POC 调用失败，返回 `400`，并保留明确错误信息。
- 如果 POC 返回字段不完整，仍然更新拿到的字段，缺失字段按 `null` 或现有
  规则处理。

### 批量接口

批量接口推荐遵循下面这些规则：

- 如果选择器缺失或同时提供多个冲突选择器，返回 `400`。
- 如果 `article_ids` 中存在当前租户外的文章，返回 `400`。
- 如果 `feed_id` 或 `member_id` 不存在，返回 `400`。
- 如果任务创建成功，单篇文章刷新失败不打断整批执行，只记录到
  `failed_articles`。

## 测试范围

测试需要覆盖同步接口、批量接口和服务层边界。

最小测试集合包括：

- URL 同步刷新可以定位当前租户内已有文章。
- URL 同步刷新在数据库更新后返回完整文章对象。
- URL 同步刷新在文章不存在时返回 `404`。
- URL 同步刷新在 POC 环境未就绪时返回明确错误。
- 批量接口支持 `article_ids`、`feed_id`、`member_id` 三种模式。
- 批量任务在部分文章失败时整体任务状态为 `success`。
- 批量任务会写入 `failed_articles` 失败明细。
- 批量任务不会更新非统计字段。

如果服务层内部增加了 POC 适配器，还需要单独测试：

- POC 输出字段白名单过滤。
- URL 归一化后的文章匹配。
- 缺失依赖文件时的错误分支。

## 实施建议

为了减少风险，实现时建议按下面顺序推进：

1. 先落独立 service 和 POC 适配层。
2. 再补同步接口与对应测试。
3. 最后新增批量接口、任务类型、任务执行器和任务结果测试。

这样可以先把“单个 URL 同步刷新并返回完整文章”的主链路走通，再把批量任务
建立在已经验证过的同步刷新逻辑上。

## 下一步

这份设计确认后，下一步是写实现计划。实现计划会拆出模型变更、服务实现、
视图接口、任务执行器、Schema 文档和测试改造等具体步骤。
