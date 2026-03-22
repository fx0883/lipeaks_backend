# we_rss 凭证与扫码登录 API

这份文档覆盖微信抓取凭证和扫码登录相关的全部接口。前端接入时，通常会
先从这里开始，因为没有有效微信凭证时，后面的公众号搜索和同步能力很难
完整工作。

凭证相关接口全部属于 tenant 共享资源。也就是说，某个成员创建成功的
微信凭证，当前 tenant 下的其他成员也能看到和使用。

## 数据结构说明

这一部分先讲清楚前端最常会用到的两个对象：微信凭证和登录会话。

### 微信凭证对象

凭证对象由下面这些字段组成。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 凭证主键 |
| `name` | `string` | 凭证显示名称 |
| `status` | `string` | 凭证状态 |
| `expires_at` | `string \| null` | 过期时间，ISO 8601 |
| `last_login_at` | `string \| null` | 最近登录时间 |
| `last_check_at` | `string \| null` | 最近检查时间 |
| `last_error` | `string` | 最近一次错误信息 |
| `is_default` | `boolean` | 是否是当前 tenant 默认凭证 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

`status` 当前可能取这些值。

| 值 | 含义 |
| --- | --- |
| `pending` | 刚创建或还没完成初始化 |
| `active` | 可正常使用 |
| `expired` | 已过期 |
| `invalid` | 无效 |
| `disabled` | 被停用 |

### 登录会话对象

登录会话对象用于扫码登录流程。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | `string` | 登录会话唯一 ID |
| `status` | `string` | 会话状态 |
| `qr_code_url` | `string` | 微信二维码地址 |
| `qr_code_image` | `string` | 二维码图片 Base64 Data URL |
| `scan_status` | `string` | 扫码阶段状态 |
| `error_message` | `string` | 失败或过期时的错误说明 |
| `expired_at` | `string \| null` | 会话过期时间 |
| `credential_id` | `number \| null` | 登录成功后关联的凭证 ID |
| `task_id` | `number \| null` | 对应的后台登录任务 ID |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

`status` 和 `scan_status` 常见值如下。

| 值 | 含义 |
| --- | --- |
| `pending` | 等待扫码 |
| `scanned` | 已扫码，但还没确认 |
| `confirmed` | 已确认登录 |
| `success` | 登录成功并已落库凭证 |
| `failed` | 登录失败 |
| `expired` | 二维码过期 |

## 通用请求头

这组接口的每个请求都要带下面两个请求头。

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 1. 获取凭证列表

这个接口返回当前 tenant 下全部微信凭证。前端通常在凭证管理页、
公众号搜索页初始化时调用。

### 请求信息

```http
GET /api/v1/we-rss/credentials/
```

### 请求参数

这个接口没有路径参数、查询参数，也没有请求体。

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "Default Credential",
      "status": "active",
      "expires_at": "2026-03-31T12:00:00Z",
      "last_login_at": "2026-03-21T08:30:00Z",
      "last_check_at": "2026-03-21T08:35:00Z",
      "last_error": "",
      "is_default": true,
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-21T08:35:00Z"
    }
  ]
}
```

### 前端调用示例

```ts
const res = await weRssRequest<Array<any>>("/credentials/");
const credentials = res.data;
```

## 2. 获取单个凭证详情

这个接口适合在“凭证详情弹窗”或“编辑凭证名称”前读取当前值。

### 请求信息

```http
GET /api/v1/we-rss/credentials/{id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 微信抓取凭证 ID |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "Default Credential",
    "status": "active",
    "expires_at": "2026-03-31T12:00:00Z",
    "last_login_at": "2026-03-21T08:30:00Z",
    "last_check_at": "2026-03-21T08:35:00Z",
    "last_error": "",
    "is_default": true,
    "created_at": "2026-03-20T10:00:00Z",
    "updated_at": "2026-03-21T08:35:00Z"
  }
}
```

### 前端调用示例

```ts
const credentialId = 1;
const res = await weRssRequest<any>(`/credentials/${credentialId}/`);
const credential = res.data;
```

## 3. 更新凭证名称

这个接口只允许更新凭证名称，不允许前端直接改 `token` 或 `cookie`。
如果前端传了这两个字段，后端会返回校验错误。

### 请求信息

```http
PUT /api/v1/we-rss/credentials/{id}/
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 微信抓取凭证 ID |

### 请求体

```json
{
  "name": "Default Credential"
}
```

### 请求字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | `string` | 是 | 凭证显示名称 |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "Default Credential",
    "status": "active",
    "expires_at": "2026-03-31T12:00:00Z",
    "last_login_at": "2026-03-21T08:30:00Z",
    "last_check_at": "2026-03-21T08:35:00Z",
    "last_error": "",
    "is_default": true,
    "created_at": "2026-03-20T10:00:00Z",
    "updated_at": "2026-03-21T08:35:00Z"
  }
}
```

### 前端调用示例

```ts
await weRssRequest(`/credentials/1/`, {
  method: "PUT",
  body: JSON.stringify({
    name: "业务线默认凭证",
  }),
});
```

## 4. 删除凭证

这个接口会直接删除当前 tenant 下的某个微信凭证。前端调用前建议二次确认。

### 请求信息

```http
DELETE /api/v1/we-rss/credentials/{id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 微信抓取凭证 ID |

### 成功响应

这个接口成功时返回 `204 No Content`，没有 JSON 包裹体。

### 前端调用示例

```ts
await fetch("/api/v1/we-rss/credentials/1/", {
  method: "DELETE",
  headers: {
    Authorization: `Bearer ${token}`,
    "X-Tenant-ID": String(tenantId),
  },
});
```

## 5. 校验凭证是否可用

这个接口会让后端拿当前凭证去访问微信网关，更新凭证状态。前端适合在
用户点击“检查凭证状态”按钮时调用。

### 请求信息

```http
POST /api/v1/we-rss/credentials/{id}/check/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 微信抓取凭证 ID |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "valid": true,
    "status": "active",
    "message": ""
  }
}
```

### 前端调用示例

```ts
const res = await weRssRequest<any>("/credentials/1/check/", {
  method: "POST",
});

if (!res.data.valid) {
  console.warn(res.data.message);
}
```

## 6. 设置默认凭证

这个接口会把指定凭证设置为当前 tenant 的默认凭证，并自动取消其他默认项。
公众号搜索和某些抓取动作会优先使用默认凭证。

### 请求信息

```http
POST /api/v1/we-rss/credentials/{id}/set-default/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `number` | 是 | 微信抓取凭证 ID |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "Default Credential",
    "status": "active",
    "expires_at": "2026-03-31T12:00:00Z",
    "last_login_at": "2026-03-21T08:30:00Z",
    "last_check_at": "2026-03-21T08:35:00Z",
    "last_error": "",
    "is_default": true,
    "created_at": "2026-03-20T10:00:00Z",
    "updated_at": "2026-03-21T08:35:00Z"
  }
}
```

### 前端调用示例

```ts
await weRssRequest("/credentials/1/set-default/", {
  method: "POST",
});
```

## 7. 创建扫码登录会话

这个接口会创建一个新的微信扫码登录会话，同时自动触发后台
`credential_login` 任务。前端拿到二维码后，不需要自己访问微信网关，
只需要展示二维码并轮询会话详情。

### 请求信息

```http
POST /api/v1/we-rss/credentials/login-sessions/
Content-Type: application/json
```

### 请求体

这个接口当前不需要业务字段，请传空对象。

```json
{}
```

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "session_id": "session-123",
    "status": "pending",
    "qr_code_url": "https://mp.weixin.qq.com/cgi-bin/scanloginqrcode?action=getqrcode&uuid=session-123",
    "qr_code_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "scan_status": "waiting",
    "error_message": "",
    "expired_at": "2026-03-21T09:00:00Z",
    "credential_id": null,
    "task_id": 301,
    "created_at": "2026-03-21T08:40:00Z",
    "updated_at": "2026-03-21T08:40:00Z"
  }
}
```

### 前端使用说明

这个接口返回的两个二维码字段作用不同。

| 字段 | 作用 |
| --- | --- |
| `qr_code_url` | 可作为二维码原始地址使用 |
| `qr_code_image` | 可直接赋给 `<img src>` 展示 |

### 前端调用示例

```ts
const res = await weRssRequest<any>("/credentials/login-sessions/", {
  method: "POST",
  body: JSON.stringify({}),
});

const session = res.data;
setQrCodeSrc(session.qr_code_image);
setCurrentSessionId(session.session_id);
```

## 8. 查询扫码登录会话详情

这个接口用于轮询扫码登录状态。前端通常在调用“创建扫码登录会话”后，
每 2 到 3 秒轮询一次，直到会话进入结束状态。

### 请求信息

```http
GET /api/v1/we-rss/credentials/login-sessions/{session_id}/
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `session_id` | `string` | 是 | 扫码登录会话 ID |

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "session_id": "session-123",
    "status": "success",
    "qr_code_url": "https://mp.weixin.qq.com/cgi-bin/scanloginqrcode?action=getqrcode&uuid=session-123",
    "qr_code_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "scan_status": "confirmed",
    "error_message": "",
    "expired_at": "2026-03-21T09:00:00Z",
    "credential_id": 1,
    "task_id": 301,
    "created_at": "2026-03-21T08:40:00Z",
    "updated_at": "2026-03-21T08:40:10Z"
  }
}
```

### 轮询终止条件

前端可以按下面规则结束轮询。

| 条件 | 处理方式 |
| --- | --- |
| `status === "success"` | 登录完成，刷新凭证列表 |
| `status === "failed"` | 提示失败原因 |
| `status === "expired"` | 提示二维码过期，重新创建会话 |

### 前端轮询示例

```ts
async function pollLoginSession(sessionId: string) {
  const timer = window.setInterval(async () => {
    const res = await weRssRequest<any>(
      `/credentials/login-sessions/${sessionId}/`,
    );

    const session = res.data;

    if (session.status === "success") {
      clearInterval(timer);
      console.log("credential id:", session.credential_id);
    }

    if (session.status === "failed" || session.status === "expired") {
      clearInterval(timer);
      console.error(session.error_message);
    }
  }, 3000);
}
```

## 常见前端处理建议

这组接口接入时，前端可以用下面的交互策略。

1. 打开登录弹窗时创建扫码会话。
2. 先展示 `qr_code_image`。
3. 页面上实时显示 `scan_status`，比如“等待扫码”“已扫码”“已确认”。
4. 成功后自动关闭弹窗并刷新凭证列表。
5. 失败或过期后展示 `error_message` 并提供“重新生成二维码”按钮。

## 下一步

完成扫码登录和凭证管理后，你可以继续接公众号相关接口。

- [02_公众号API.md](./02_%E5%85%AC%E4%BC%97%E5%8F%B7API.md)
- [04_同步任务API.md](./04_%E5%90%8C%E6%AD%A5%E4%BB%BB%E5%8A%A1API.md)
