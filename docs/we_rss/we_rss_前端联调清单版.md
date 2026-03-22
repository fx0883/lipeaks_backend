# we_rss 前端联调清单版

这份文档面向前端联调阶段，不再按后端模块拆分，而是按页面开发顺序来排。
你可以把它理解成“页面施工清单 + 对应接口清单 + 联调完成标准”。

这份整理参考了旧项目 `we-mp-rss-main` 的前端页面流，尤其是下面这些页面
的交互思路：

- 微信扫码授权弹窗
- 添加订阅页
- 公众号管理页
- 文章列表页
- 文章阅读抽屉

不过这份文档使用的是**新项目业务命名**，并且只保留当前 `we_rss` 真正已
实现的能力，不会把旧项目里已经废弃或本次不迁移的能力混进来。

## 使用方式

这份文档最适合前端按任务拆工时使用。你可以从上往下接，每完成一页，就用
这一页下面的“完成标准”做自测。

如果你需要看字段细节、完整响应示例和所有 API 的逐项说明，再配合阅读：

- [we_rss_前端完整API文档.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%AE%8C%E6%95%B4API%E6%96%87%E6%A1%A3.md)
- [README.md](./README.md)

## 总体开发顺序

建议前端按下面顺序推进，这个顺序基本就是可联调的最短路径。

1. 先完成统一请求层和鉴权头注入。
2. 再完成“微信凭证与扫码登录”页面。
3. 再完成“新增公众号 / 导入文章”页面。
4. 然后完成“公众号管理”页面。
5. 再完成“文章列表”页面。
6. 然后完成“文章详情阅读”页面。
7. 抽出统一的“任务轮询能力”。
8. 最后再做 RSS / HTML 输出页或阅读器集成。

## 页面 0：统一请求层

这一页不是业务页面，但它必须最先完成。旧项目里前端请求层分散在
`auth.ts`、`subscription.ts`、`article.ts` 等文件里；新项目建议先统一做
一个 `weRssApiClient`，后面所有页面都复用它。

### 你要完成什么

- 注入 `Authorization: Bearer <member_access_token>`
- 注入 `X-Tenant-ID`
- 统一解析项目标准 JSON 包裹
- 能区分 JSON、XML、HTML 三种响应

### 必须接的接口

- 所有 `we_rss` JSON 接口
- `GET /api/v1/we-rss/rss/`
- `GET /api/v1/we-rss/rss/{feed_id}/`
- `GET /api/v1/we-rss/rss/content/{article_id}/`

### 前端实现建议

你可以直接封装两个基础函数，一个处理 JSON，一个处理文本。

```ts
type ApiEnvelope<T> = {
  success: boolean;
  code: number;
  message: string;
  data: T;
};

async function weRssRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiEnvelope<T>> {
  const token = localStorage.getItem("member_access_token");
  const tenantId = localStorage.getItem("member_tenant_id");

  const response = await fetch(`/api/v1/we-rss${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": String(tenantId),
      ...(options.headers || {}),
    },
  });

  return response.json();
}

async function weRssTextRequest(path: string): Promise<string> {
  const token = localStorage.getItem("member_access_token");
  const tenantId = localStorage.getItem("member_tenant_id");

  const response = await fetch(`/api/v1/we-rss${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": String(tenantId),
    },
  });

  return response.text();
}
```

### 完成标准

- 任意一个 `GET /credentials/` 能正常拿到数据
- 漏传 `X-Tenant-ID` 时，前端能识别并提示
- RSS / HTML 接口不会误用 `response.json()`

## 页面 1：微信凭证与扫码登录页

这一页对应旧前端的“微信授权二维码弹窗”能力，但新项目建议把它做成一个更
明确的“凭证管理 + 扫码登录”页或弹窗。

### 页面目标

用户在这里完成两件事：

1. 查看当前 tenant 下有哪些微信凭证
2. 通过扫码生成或刷新可用凭证

### 推荐 UI 模块

- 凭证列表区
- 默认凭证标记区
- “检查凭证状态”按钮
- “设置为默认”按钮
- “扫码登录”弹窗

### 必须接的接口

- `GET /api/v1/we-rss/credentials/`
- `GET /api/v1/we-rss/credentials/{id}/`
- `PUT /api/v1/we-rss/credentials/{id}/`
- `POST /api/v1/we-rss/credentials/{id}/check/`
- `POST /api/v1/we-rss/credentials/{id}/set-default/`
- `DELETE /api/v1/we-rss/credentials/{id}/`
- `POST /api/v1/we-rss/credentials/login-sessions/`
- `GET /api/v1/we-rss/credentials/login-sessions/{session_id}/`

### 页面联调顺序

1. 先接凭证列表。
2. 再接“扫码登录”按钮，创建登录会话。
3. 二维码弹窗展示 `qr_code_image`。
4. 前端每 2 到 3 秒轮询登录会话详情。
5. 成功后关闭弹窗并刷新凭证列表。
6. 再接“检查凭证”和“设为默认”。

### 关键交互

- 登录成功条件：`status === "success"`
- 登录失败条件：`status === "failed"`
- 二维码失效条件：`status === "expired"`
- 登录成功后，用 `credential_id` 刷新列表并高亮新凭证

### 典型调用链

```ts
const sessionRes = await weRssRequest<any>("/credentials/login-sessions/", {
  method: "POST",
  body: JSON.stringify({}),
});

const sessionId = sessionRes.data.session_id;
const qrCodeImage = sessionRes.data.qr_code_image;

async function pollLogin() {
  const res = await weRssRequest<any>(
    `/credentials/login-sessions/${sessionId}/`,
  );
  return res.data;
}
```

### 完成标准

- 能看到当前 tenant 的凭证列表
- 能发起扫码登录并展示二维码
- 登录成功后列表自动刷新
- 能把某个凭证设成默认
- 默认凭证变更后，后续公众号搜索能直接复用它

## 页面 2：新增公众号 / 导入文章页

这一页对应旧前端的 `AddSubscription.vue`。旧前端把“搜索公众号”和“通过文章
链接识别公众号”放在一个页面里；新项目建议继续保留这种页面组合，但要改成
新的业务语言。

### 页面目标

用户在这里可以做两件事：

1. 搜索微信平台上的公众号并保存
2. 粘贴单篇微信文章链接，把文章直接导入系统

### 推荐 UI 模块

- 搜索公众号输入框
- 搜索结果列表
- 公众号创建表单
- “通过文章链接导入”区域
- 导入任务状态提示区

### 必须接的接口

- `GET /api/v1/we-rss/feeds/search/?keyword=...`
- `POST /api/v1/we-rss/feeds/`
- `POST /api/v1/we-rss/articles/import-by-url/`
- `GET /api/v1/we-rss/tasks/{task_id}/`

### 页面联调顺序

1. 先接公众号搜索。
2. 用户选中搜索结果后，填充创建表单。
3. 调用 `POST /feeds/` 保存公众号。
4. 再接“按文章 URL 导入”。
5. 导入接口返回任务对象后，进入统一任务轮询。

### 特别说明

这一页和旧项目有一个重要差异：

- 旧项目支持“通过文章链接先识别公众号，再补齐订阅信息”
- 当前 `we_rss` 没有单独的“通过文章链接识别公众号信息”接口

所以新前端这页要这样改：

- 搜索公众号，走 `/feeds/search/`
- 导入单篇文章，走 `/articles/import-by-url/`
- 这两个动作不要混成一个接口

### 导入文章后的页面跳转建议

当任务成功时，优先读取：

- `result_payload.article_id`
- `result_payload.feed_id`

然后你可以：

- 跳文章详情页
- 或者跳文章列表页并高亮新文章

### 完成标准

- 有默认有效凭证时，能搜到公众号结果
- 能把搜索结果保存为公众号记录
- 能输入一篇微信文章 URL 并创建导入任务
- 导入成功后能定位到文章详情或文章列表

## 页面 3：公众号管理页

这一页对应旧前端的 `WeChatMpManagement.vue`，但新项目不再沿用旧的
`订阅`、`mp_id` 这些命名，而是统一使用“公众号 / feed / feed_id”。

### 页面目标

用户在这里维护当前 tenant 下已经保存的公众号。

### 推荐 UI 模块

- 公众号列表
- 公众号详情侧栏或编辑弹窗
- 删除按钮
- 修改基础信息按钮
- “同步文章”按钮
- featured 标记开关

### 必须接的接口

- `GET /api/v1/we-rss/feeds/`
- `GET /api/v1/we-rss/feeds/{id}/`
- `PUT /api/v1/we-rss/feeds/{id}/`
- `DELETE /api/v1/we-rss/feeds/{id}/`
- `POST /api/v1/we-rss/feeds/{id}/sync/`
- `GET /api/v1/we-rss/tasks/{task_id}/`

### 页面联调顺序

1. 先接公众号列表。
2. 再接编辑弹窗和保存。
3. 再接删除。
4. 最后接“同步文章”按钮和任务轮询。

### 建议前端字段展示

- `mp_name`
- `mp_cover`
- `mp_intro`
- `status`
- `last_synced_at`
- `credential_id`
- `is_featured`

### 特别说明

旧前端有下面这些行为：

- 分页加载公众号
- 启用 / 停用切换
- 导入 / 导出公众号
- OPML 导出

当前 `we_rss` 后端**没有**这些对应能力，所以这版页面不要直接照搬旧前端。

当前后端明确支持的只有：

- 列表
- 新建
- 编辑
- 删除
- 同步

### 完成标准

- 能列出当前 tenant 的全部公众号
- 能编辑并保存公众号
- 能删除公众号
- 能发起同步并看到任务结果
- 同步成功后刷新文章列表页能看到新文章

## 页面 4：文章列表页

这一页对应旧前端的 `ArticleList.vue`、`ArticleListDesktop.vue` 和
`ArticleListMobile.vue`。旧项目前端把它做成首页；新项目也建议这样做。

### 页面目标

用户在这里浏览当前 tenant 下的公众号文章，并能对文章做基础操作。

### 推荐 UI 模块

- 文章列表
- 当前公众号过滤区
- 已读 / 收藏状态按钮
- 刷新文章按钮
- 删除文章按钮
- 跳转详情按钮

### 必须接的接口

- `GET /api/v1/we-rss/articles/`
- `PUT /api/v1/we-rss/articles/{id}/read/`
- `PUT /api/v1/we-rss/articles/{id}/favorite/`
- `POST /api/v1/we-rss/articles/{id}/refresh/`
- `DELETE /api/v1/we-rss/articles/{id}/`
- `GET /api/v1/we-rss/tasks/{task_id}/`
- `GET /api/v1/we-rss/feeds/`

### 页面联调顺序

1. 先接文章列表。
2. 再接公众号列表，做前端侧过滤。
3. 再接已读状态切换。
4. 再接收藏状态切换。
5. 再接单篇刷新。
6. 最后接删除。

### 一个很重要的当前限制

旧前端文章首页支持很多服务端筛选能力，比如：

- 按公众号过滤
- 按标题搜索
- 仅显示收藏
- 分页

当前 `we_rss` 后端的 `GET /articles/` 还没有这些查询参数能力，当前是：

- 返回当前 tenant 下全部文章
- 不分页
- 不带服务端过滤

所以这一版前端页面建议这么处理：

- 先把全量文章拉下来
- 用前端本地状态做关键词过滤
- 用前端本地状态做按公众号过滤
- 用前端本地状态做仅收藏过滤

如果后续后端补了过滤参数，这一页再升级成服务端过滤。

### 刷新文章的处理方式

刷新单篇文章时：

1. 调用 `POST /articles/{id}/refresh/`
2. 拿到 `article_refresh` 任务
3. 进入任务轮询
4. 任务成功后刷新当前文章列表

### 完成标准

- 能看到文章列表
- 能本地过滤文章标题、公众号、收藏状态
- 能切换已读 / 收藏
- 能单篇刷新并在成功后更新列表
- 能删除文章

## 页面 5：文章详情阅读页

这一页对应旧前端的“文章阅读抽屉 / 阅读器”能力。新项目建议优先做成一个
详情页或抽屉，而不是公开地址。

### 页面目标

用户点击文章后，可以看到文章正文 HTML，并保留跳原文能力。

### 推荐 UI 模块

- 标题
- 发布时间
- 原文链接
- 正文容器
- 可选的上一篇 / 下一篇占位区

### 必须接的接口

- `GET /api/v1/we-rss/articles/{id}/`
- 或 `GET /api/v1/we-rss/rss/content/{article_id}/`

### 两种实现方式

这里有两种可用实现，你可以选一个。

#### 方案 A：直接用文章详情里的 `content`

优点：

- 少一次请求
- 列表跳详情更简单

缺点：

- 你要自己决定如何包裹 HTML 外壳

#### 方案 B：使用正文 HTML 输出接口

优点：

- 后端直接返回可渲染 HTML
- 更适合做阅读器页或嵌入页

缺点：

- 需要额外一次请求

我更推荐前端详情页先使用**方案 A**，如果后续要接 RSS 阅读器，再补
**方案 B**。

### 当前和旧项目的差异

旧前端支持：

- 上一篇 / 下一篇
- 阅读器模式
- 更复杂的正文渲染隔离

当前 `we_rss` 后端**没有**上一篇 / 下一篇接口，所以新前端这里不要先做
强依赖。可以先留占位，不要写死调用。

### 完成标准

- 能进入文章详情
- 能展示标题、摘要、正文
- 能跳转到原文链接
- 正文渲染不会把 XML / HTML 当 JSON 解析

## 页面 6：任务轮询能力

这一块不一定做成单独页面，但前端最好抽成单独模块。旧前端里“扫码授权”
“刷新文章”“添加精选文章”都各自写了一套轮询，新项目建议统一。

### 模块目标

把下面四类异步任务统一成一个轮询器：

- `credential_login`
- `feed_sync`
- `article_import`
- `article_refresh`

### 必须接的接口

- `GET /api/v1/we-rss/tasks/`
- `GET /api/v1/we-rss/tasks/{task_id}/`

### 推荐封装

```ts
async function pollWeRssTask(
  taskId: number,
  {
    interval = 2000,
    maxAttempts = 30,
  }: { interval?: number; maxAttempts?: number } = {},
) {
  for (let i = 0; i < maxAttempts; i += 1) {
    const res = await weRssRequest<any>(`/tasks/${taskId}/`);
    const task = res.data;

    if (task.status === "success") {
      return task;
    }

    if (task.status === "failed") {
      throw new Error(task.result_payload?.error || task.message);
    }

    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  throw new Error("任务轮询超时");
}
```

### 任务结果解析建议

前端按 `task_type` 分支解析 `result_payload`。

| `task_type` | 成功时重点字段 |
| --- | --- |
| `credential_login` | `session_id`、`status` |
| `feed_sync` | `fetched_count`、`detail_success_count`、`detail_failed_count` |
| `article_import` | `article_id`、`feed_id` |
| `article_refresh` | `article_id`、`read_num`、`comment_total_count` |

### 完成标准

- 登录轮询、公众号同步、文章导入、文章刷新都复用同一套任务轮询逻辑
- 页面不会各自维护不同的轮询实现
- 失败时能正确展示 `task.message` 或 `result_payload.error`

## 页面 7：RSS 输出与正文输出页

这一页是可选页面，更偏阅读器集成或外部订阅能力。旧项目有 RSS / Atom /
JSON / Markdown 等更多格式；当前 `we_rss` 先只对接当前实际存在的 3 个
接口。

### 页面目标

用户或前端内部工具可以：

1. 查看当前 tenant 的 RSS XML
2. 查看单公众号的 RSS XML
3. 获取单篇正文 HTML

### 必须接的接口

- `GET /api/v1/we-rss/rss/`
- `GET /api/v1/we-rss/rss/{feed_id}/`
- `GET /api/v1/we-rss/rss/content/{article_id}/`

### 一个关键约束

这些接口虽然返回 XML / HTML，但仍然必须带：

- `Authorization`
- `X-Tenant-ID`

所以它们不是匿名公开地址，不能直接照抄旧项目里“公开订阅地址”的思路。

### 前端接法建议

- 内部阅读页：用 `fetch` 拉文本，再自己渲染
- RSS 调试页：直接展示原始 XML 文本
- 订阅器集成：优先走前端代理或业务后端代理

### 完成标准

- 能获取 tenant RSS 文本
- 能获取单公众号 RSS 文本
- 能获取单篇正文 HTML
- 页面不会误以为这些是公开链接

## 当前后端未提供的旧前端能力

这一节很重要。下面这些旧前端里出现过的能力，当前 `we_rss` 后端还没有，
前端不要直接按旧接口实现。

### 当前未提供

- 文章列表服务端分页
- 文章列表服务端搜索
- 文章列表服务端按公众号过滤
- 文章列表仅收藏服务端过滤
- 上一篇 / 下一篇文章接口
- 公众号启用 / 停用专用接口
- 公众号导入 / 导出
- OPML 导出
- 通过文章链接识别公众号信息的专用接口
- 多格式 RSS 输出，如 Atom / JSON / Markdown / Text

### 前端建议处理方式

- 先用本地过滤代替服务端过滤
- 对未实现能力保留 UI 占位，但不要接假接口
- 如果某个页面必须依赖这些能力，再单独提后端需求

## 前端最终联调验收顺序

当你准备联调收口时，建议按下面顺序走一遍完整链路。

1. 登录前端系统，确认请求层能自动带 `Member JWT` 和 `X-Tenant-ID`
2. 打开“微信凭证与扫码登录页”，创建扫码登录会话
3. 扫码成功后，确认凭证列表出现新凭证
4. 把凭证设为默认
5. 打开“新增公众号 / 导入文章页”，搜索并保存一个公众号
6. 在“公众号管理页”触发同步
7. 确认任务成功
8. 打开“文章列表页”，确认看到同步下来的文章
9. 对一篇文章做已读、收藏、刷新
10. 打开“文章详情页”，确认正文可读
11. 调试 RSS / HTML 输出页

## 下一步

如果前端已经开始分工，我建议把任务拆成下面几包：

1. 一个人负责请求层 + 任务轮询 + 凭证扫码页
2. 一个人负责公众号新增页 + 公众号管理页
3. 一个人负责文章列表页 + 文章详情页 + RSS 页

需要字段级接口说明时，再回看：
[we_rss_前端完整API文档.md](./we_rss_%E5%89%8D%E7%AB%AF%E5%AE%8C%E6%95%B4API%E6%96%87%E6%A1%A3.md)。
