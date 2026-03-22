# we_rss 前端 API 文档索引

这组文档面向前端开发，覆盖 `we_rss` 当前已经提供的全部 API。内容包含
认证方式、`X-Tenant-ID` 约束、标准响应格式、每个接口的请求参数、
响应结构，以及可直接参考的调用示例。

`we_rss` 的能力范围包括微信抓取凭证、扫码登录、公众号管理、公众号
文章管理、同步任务查询，以及需要鉴权的 RSS 和正文输出接口。

如果你希望直接把一份文档发给前端，不想拆模块阅读，建议优先使用
[we_rss_前端完整API文档.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%AE%8C%E6%95%B4API%E6%96%87%E6%A1%A3.md)。
如果你希望前端按页面开发顺序逐步联调，建议优先使用
[we_rss_前端联调清单版.md](./we_rss_%E5%89%8D%E7%AB%AF%E8%81%94%E8%B0%83%E6%B8%85%E5%8D%95%E7%89%88.md)。
如果你要给前端负责人拆开发阶段和人力分工，建议优先使用
[we_rss_前端开发排期版.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%BC%80%E5%8F%91%E6%8E%92%E6%9C%9F%E7%89%88.md)。
如果你要直接发到前端群里，建议优先使用
[we_rss_前端群简版说明.md](./we_rss_%E5%89%8D%E7%AB%AF%E7%BE%A4%E7%AE%80%E7%89%88%E8%AF%B4%E6%98%8E.md)。

## 文档目录

- [00_总览与对接说明.md](./00_%E6%80%BB%E8%A7%88%E4%B8%8E%E5%AF%B9%E6%8E%A5%E8%AF%B4%E6%98%8E.md)
- [01_凭证与扫码登录API.md](./01_%E5%87%AD%E8%AF%81%E4%B8%8E%E6%89%AB%E7%A0%81%E7%99%BB%E5%BD%95API.md)
- [02_公众号API.md](./02_%E5%85%AC%E4%BC%97%E5%8F%B7API.md)
- [03_公众号文章API.md](./03_%E5%85%AC%E4%BC%97%E5%8F%B7%E6%96%87%E7%AB%A0API.md)
- [04_同步任务API.md](./04_%E5%90%8C%E6%AD%A5%E4%BB%BB%E5%8A%A1API.md)
- [05_RSS与正文输出API.md](./05_RSS%E4%B8%8E%E6%AD%A3%E6%96%87%E8%BE%93%E5%87%BAAPI.md)
- [we_rss_前端完整API文档.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%AE%8C%E6%95%B4API%E6%96%87%E6%A1%A3.md)
- [we_rss_前端联调清单版.md](./we_rss_%E5%89%8D%E7%AB%AF%E8%81%94%E8%B0%83%E6%B8%85%E5%8D%95%E7%89%88.md)
- [we_rss_前端开发排期版.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%BC%80%E5%8F%91%E6%8E%92%E6%9C%9F%E7%89%88.md)
- [we_rss_前端群简版说明.md](./we_rss_%E5%89%8D%E7%AB%AF%E7%BE%A4%E7%AE%80%E7%89%88%E8%AF%B4%E6%98%8E.md)

## API 模块概览

这套 API 一共分为 5 个业务模块，推荐前端按下面的顺序接入。

| 模块 | 文档 | 主要用途 |
| --- | --- | --- |
| 总览 | `00_总览与对接说明.md` | 看认证、租户隔离、标准响应、整体调用链 |
| 凭证与扫码登录 | `01_凭证与扫码登录API.md` | 创建微信扫码登录会话、轮询登录结果、管理凭证 |
| 公众号 | `02_公众号API.md` | 搜索公众号、创建公众号记录、同步公众号文章 |
| 公众号文章 | `03_公众号文章API.md` | 列表、详情、按 URL 导入、刷新、已读、收藏 |
| 同步任务 | `04_同步任务API.md` | 查询后台异步任务执行状态和结果 |
| RSS 与正文输出 | `05_RSS与正文输出API.md` | 获取 tenant RSS、单公众号 RSS、文章 HTML |

## 推荐阅读顺序

如果你是第一次接这套能力，建议按下面顺序阅读。

1. 先看 `00_总览与对接说明.md`。
2. 再看 `01_凭证与扫码登录API.md`，完成微信登录。
3. 然后看 `02_公众号API.md`，完成公众号搜索、创建和同步。
4. 再看 `04_同步任务API.md`，实现任务轮询。
5. 最后看 `03_公众号文章API.md` 和 `05_RSS与正文输出API.md`。

## 完整接口清单

下面这张表把当前 `we_rss` 的全部接口方法都列出来了，方便前端快速定位。

| 方法 | 路径 | 说明 | 文档 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/we-rss/credentials/` | 获取凭证列表 | `01_凭证与扫码登录API.md` |
| `GET` | `/api/v1/we-rss/credentials/{id}/` | 获取凭证详情 | `01_凭证与扫码登录API.md` |
| `PUT` | `/api/v1/we-rss/credentials/{id}/` | 更新凭证名称 | `01_凭证与扫码登录API.md` |
| `DELETE` | `/api/v1/we-rss/credentials/{id}/` | 删除凭证 | `01_凭证与扫码登录API.md` |
| `POST` | `/api/v1/we-rss/credentials/{id}/check/` | 校验凭证可用性 | `01_凭证与扫码登录API.md` |
| `POST` | `/api/v1/we-rss/credentials/{id}/set-default/` | 设置默认凭证 | `01_凭证与扫码登录API.md` |
| `POST` | `/api/v1/we-rss/credentials/login-sessions/` | 创建扫码登录会话 | `01_凭证与扫码登录API.md` |
| `GET` | `/api/v1/we-rss/credentials/login-sessions/{session_id}/` | 查询扫码登录会话 | `01_凭证与扫码登录API.md` |
| `GET` | `/api/v1/we-rss/feeds/` | 获取公众号列表 | `02_公众号API.md` |
| `POST` | `/api/v1/we-rss/feeds/` | 创建公众号记录 | `02_公众号API.md` |
| `GET` | `/api/v1/we-rss/feeds/{id}/` | 获取公众号详情 | `02_公众号API.md` |
| `PUT` | `/api/v1/we-rss/feeds/{id}/` | 更新公众号记录 | `02_公众号API.md` |
| `DELETE` | `/api/v1/we-rss/feeds/{id}/` | 删除公众号记录 | `02_公众号API.md` |
| `GET` | `/api/v1/we-rss/feeds/search/` | 搜索公众号 | `02_公众号API.md` |
| `POST` | `/api/v1/we-rss/feeds/{id}/sync/` | 触发公众号同步 | `02_公众号API.md` |
| `GET` | `/api/v1/we-rss/articles/` | 获取文章列表 | `03_公众号文章API.md` |
| `POST` | `/api/v1/we-rss/articles/import-by-url/` | 按 URL 导入文章 | `03_公众号文章API.md` |
| `GET` | `/api/v1/we-rss/articles/{id}/` | 获取文章详情 | `03_公众号文章API.md` |
| `DELETE` | `/api/v1/we-rss/articles/{id}/` | 删除文章 | `03_公众号文章API.md` |
| `POST` | `/api/v1/we-rss/articles/{id}/refresh/` | 刷新文章 | `03_公众号文章API.md` |
| `PUT` | `/api/v1/we-rss/articles/{id}/read/` | 更新已读状态 | `03_公众号文章API.md` |
| `PUT` | `/api/v1/we-rss/articles/{id}/favorite/` | 更新收藏状态 | `03_公众号文章API.md` |
| `GET` | `/api/v1/we-rss/tasks/` | 获取任务列表 | `04_同步任务API.md` |
| `GET` | `/api/v1/we-rss/tasks/{task_id}/` | 获取任务详情 | `04_同步任务API.md` |
| `GET` | `/api/v1/we-rss/rss/` | 获取 tenant RSS | `05_RSS与正文输出API.md` |
| `GET` | `/api/v1/we-rss/rss/{feed_id}/` | 获取单公众号 RSS | `05_RSS与正文输出API.md` |
| `GET` | `/api/v1/we-rss/rss/content/{article_id}/` | 获取文章正文 HTML | `05_RSS与正文输出API.md` |

## 典型接入链路

前端接入时，通常会按下面的链路调用。

1. 创建扫码登录会话。
2. 轮询登录会话详情，直到拿到 `credential_id` 或状态失败。
3. 获取凭证列表，必要时把某个凭证设为默认。
4. 搜索公众号，或者手动创建公众号记录。
5. 对公众号发起同步任务。
6. 轮询同步任务详情，拿到同步结果。
7. 拉取文章列表和文章详情。
8. 按需要执行文章刷新、已读、收藏。
9. 如果需要 RSS 阅读器或内嵌正文，再调用 RSS / HTML 输出接口。

## 注意事项

这套 API 有几个前端接入时必须注意的约束。

- 所有 `we_rss` 接口都必须带 `Member JWT`。
- 所有 `we_rss` 接口都必须带 `X-Tenant-ID`。
- `X-Tenant-ID` 必须等于当前登录 `member` 绑定的租户 ID。
- `we_rss` 数据是 tenant 共享的，不是 member 私有的。
- 所有列表接口当前都不分页。
- 所有任务接口都是异步任务状态查询，不会阻塞到微信抓取完成。
- RSS 和文章 HTML 接口也需要鉴权，不能当公开链接处理。

## 下一步

你可以先从
[00_总览与对接说明.md](./00_%E6%80%BB%E8%A7%88%E4%B8%8E%E5%AF%B9%E6%8E%A5%E8%AF%B4%E6%98%8E.md)
开始，再按模块逐步接入。
