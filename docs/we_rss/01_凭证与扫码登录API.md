# we_rss 凭证与扫码登录 API

这份文档覆盖 `we_rss` 中和微信凭证、扫码登录相关的全部接口。你可以把这组
接口理解为“公众号搜索、同步、文章导入”之前的前置能力，因为没有有效的微信
凭证，后面的绝大多数抓取动作都无法正常工作。

当前这一组资源是 tenant 共享资源。某个成员在当前 tenant 下完成扫码登录后，
生成的凭证会被其他同 tenant 成员共同看到和使用。

## 通用请求头

这组接口都要求携带成员 token 和租户头。

```http
Authorization: Bearer <member_access_token>
X-Tenant-ID: <current_member_tenant_id>
```

## 数据结构说明

这部分先把“模型字段”“接口返回字段”“接口可写字段”彻底分开。

### 1. WechatCredential 模型字段

`WechatCredential` 现在继承 `BaseModel`，所以模型层字段实际如下：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `tenant` | `BaseModel` | 所属租户 |
| `created_at` | `BaseModel` | 创建时间 |
| `updated_at` | `BaseModel` | 更新时间 |
| `is_deleted` | `BaseModel` | 软删除标记 |
| `name` | 业务字段 | 凭证显示名 |
| `status` | 业务字段 | `pending / active / expired / invalid / disabled` |
| `token` | 业务字段 | 微信后台 token，模型存在但不返回给前端 |
| `cookie` | 业务字段 | 微信 cookie，模型存在但不返回给前端 |
| `expires_at` | 业务字段 | 过期时间 |
| `last_login_at` | 业务字段 | 最近登录时间 |
| `last_check_at` | 业务字段 | 最近检查时间 |
| `last_error` | 业务字段 | 最近错误信息 |
| `is_default` | 业务字段 | 是否是当前 tenant 默认凭证 |
| `created_by` | 业务字段 | 创建人 |
| `updated_by` | 业务字段 | 更新人 |

### 2. 凭证接口返回字段

凭证列表和详情接口当前只返回下面这些字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 凭证 ID |
| `name` | `string` | 凭证显示名 |
| `status` | `string` | 当前状态 |
| `expires_at` | `string \| null` | 过期时间 |
| `last_login_at` | `string \| null` | 最近登录时间 |
| `last_check_at` | `string \| null` | 最近检查时间 |
| `last_error` | `string` | 最近一次错误信息 |
| `is_default` | `boolean` | 是否默认凭证 |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

不会返回给前端的字段包括：

- `tenant`
- `token`
- `cookie`
- `created_by`
- `updated_by`
- `is_deleted`

### 3. 凭证可写字段

当前更新凭证的接口只允许前端改下面这个字段：

| 字段 | 类型 | 是否可写 |
| --- | --- | --- |
| `name` | `string` | 可写 |

下面两个字段虽然出现在更新 serializer 里，但设计目的是显式拒绝前端手动修改：

| 字段 | 行为 |
| --- | --- |
| `token` | 传入就会报校验错误，提示不支持手动更新 |
| `cookie` | 传入就会报校验错误，提示不支持手动更新 |

### 4. WechatCredentialLoginSession 模型字段

扫码登录会话模型同样继承 `BaseModel`。模型层字段包括：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `tenant` | `BaseModel` | 所属租户 |
| `created_at` | `BaseModel` | 创建时间 |
| `updated_at` | `BaseModel` | 更新时间 |
| `is_deleted` | `BaseModel` | 软删除标记 |
| `session_id` | 业务字段 | 登录会话唯一 ID |
| `status` | 业务字段 | `pending / scanned / confirmed / success / failed / expired` |
| `qr_code_url` | 业务字段 | 微信二维码地址 |
| `qr_code_image` | 业务字段 | Base64 二维码图片 |
| `scan_status` | 业务字段 | 当前扫码阶段 |
| `token_snapshot` | 业务字段 | 登录过程快照，不返回给前端 |
| `cookie_snapshot` | 业务字段 | 登录过程快照，不返回给前端 |
| `error_message` | 业务字段 | 登录失败原因 |
| `expired_at` | 业务字段 | 二维码过期时间 |
| `credential` | 业务字段 | 登录成功后关联的凭证 |
| `created_by` | 业务字段 | 创建成员 |

### 5. 登录会话接口返回字段

登录会话 create / retrieve 接口当前返回下面这些字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | `string` | 会话 ID |
| `status` | `string` | 会话状态 |
| `qr_code_url` | `string` | 原始二维码地址 |
| `qr_code_image` | `string` | 可直接用于 `<img src>` 的 Data URL |
| `scan_status` | `string` | 扫码阶段状态 |
| `error_message` | `string` | 失败信息 |
| `expired_at` | `string \| null` | 过期时间 |
| `credential_id` | `number \| null` | 登录成功后生成的凭证 ID |
| `task_id` | `number \| null` | 后端 `credential_login` 任务 ID |
| `created_at` | `string` | 创建时间 |
| `updated_at` | `string` | 更新时间 |

不会返回给前端的字段包括：

- `tenant`
- `is_deleted`
- `token_snapshot`
- `cookie_snapshot`
- `created_by`
- `credential` 原对象

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/we-rss/credentials/` | 获取当前 tenant 的凭证列表 |
| `GET` | `/api/v1/we-rss/credentials/{id}/` | 获取单个凭证详情 |
| `PUT` | `/api/v1/we-rss/credentials/{id}/` | 仅更新凭证名称 |
| `DELETE` | `/api/v1/we-rss/credentials/{id}/` | 软删除凭证 |
| `POST` | `/api/v1/we-rss/credentials/{id}/check/` | 检查当前凭证是否仍然有效 |
| `POST` | `/api/v1/we-rss/credentials/{id}/set-default/` | 设置默认凭证 |
| `POST` | `/api/v1/we-rss/credentials/login-sessions/` | 创建扫码登录会话 |
| `GET` | `/api/v1/we-rss/credentials/login-sessions/{session_id}/` | 查询扫码登录会话详情 |

## 1. 获取凭证列表

这个接口返回当前 tenant 下全部未软删除的微信凭证，列表不分页。

```http
GET /api/v1/we-rss/credentials/
```

成功响应中的 `data` 是数组。示例如下：

```json
[
  {
    "id": 1,
    "name": "Default Credential",
    "status": "active",
    "expires_at": null,
    "last_login_at": "2026-03-23T10:00:00Z",
    "last_check_at": "2026-03-23T10:05:00Z",
    "last_error": "",
    "is_default": true,
    "created_at": "2026-03-23T10:00:00Z",
    "updated_at": "2026-03-23T10:05:00Z"
  }
]
```

## 2. 获取单个凭证详情

这个接口按 `id` 返回单个凭证详情，返回字段与列表单项一致。

```http
GET /api/v1/we-rss/credentials/{id}/
```

路径参数说明：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `number` | 凭证 ID |

## 3. 更新凭证

这个接口当前只支持更新 `name`。它不是“凭证内容编辑接口”，前端不能用它去
覆盖微信 token 或 cookie。

```http
PUT /api/v1/we-rss/credentials/{id}/
Content-Type: application/json
```

请求体：

```json
{
  "name": "运营默认凭证"
}
```

当前写入规则如下：

- 只推荐传 `name`。
- 如果传 `token`，后端会直接抛校验错误。
- 如果传 `cookie`，后端会直接抛校验错误。
- 成功后返回更新后的凭证对象。

## 4. 删除凭证

这个接口返回 `204 No Content`。当前语义是软删除，不是物理删除。

```http
DELETE /api/v1/we-rss/credentials/{id}/
```

删除后的实际行为是：

- 该记录会被标记 `is_deleted = true`。
- 之后不会再出现在默认列表中。
- 当前没有恢复接口。

## 5. 检查凭证有效性

这个接口会让后端拿当前保存的微信 token + cookie 去访问微信后台，并把检查
结果回写到凭证本身。

```http
POST /api/v1/we-rss/credentials/{id}/check/
```

返回结构：

```json
{
  "valid": true,
  "status": "active",
  "message": ""
}
```

这个接口除了返回检查结果，还会顺带更新：

- `status`
- `last_error`
- `last_check_at`
- `updated_at`

如果检查失败，前端建议马上刷新凭证列表，让用户看到最新状态。

## 6. 设置默认凭证

这个接口把目标凭证设为当前 tenant 的默认凭证。

```http
POST /api/v1/we-rss/credentials/{id}/set-default/
```

当前业务规则如下：

- 一个 tenant 最终只会保留一个默认凭证。
- 设置某个凭证为默认后，其他默认项会自动取消。
- 成功后返回最新凭证对象。
- 公众号搜索、文章导入、部分刷新逻辑会优先用默认凭证。

## 7. 创建扫码登录会话

这个接口会创建一个新的扫码登录会话，同时自动创建一个
`credential_login` 后台任务。

```http
POST /api/v1/we-rss/credentials/login-sessions/
Content-Type: application/json
```

当前请求体不需要业务字段，传空对象即可：

```json
{}
```

响应重点字段如下：

| 字段 | 用法 |
| --- | --- |
| `session_id` | 后续轮询登录状态时要用 |
| `qr_code_url` | 原始二维码地址 |
| `qr_code_image` | 适合直接展示在前端页面 |
| `task_id` | 对应后台 `credential_login` 任务 |
| `status` | 初始一般为 `pending` |
| `scan_status` | 初始一般为 `waiting` |

建议前端优先直接使用 `qr_code_image` 来显示二维码。

## 8. 查询扫码登录会话

这个接口是扫码登录轮询的核心接口。

```http
GET /api/v1/we-rss/credentials/login-sessions/{session_id}/
```

路径参数说明：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | `string` | 登录会话 ID |

前端建议每 2 到 3 秒轮询一次，直到进入终态。常见终态如下：

| 条件 | 含义 | 前端建议 |
| --- | --- | --- |
| `status === "success"` | 登录完成，凭证已落库 | 刷新凭证列表，并高亮 `credential_id` |
| `status === "failed"` | 登录失败 | 展示 `error_message` |
| `status === "expired"` | 二维码失效 | 提示重新生成二维码 |

一个典型的成功响应示例如下：

```json
{
  "session_id": "f5d7e6f8e4c34b11",
  "status": "success",
  "qr_code_url": "https://mp.weixin.qq.com/cgi-bin/scanloginqrcode?...",
  "qr_code_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "scan_status": "confirmed",
  "error_message": "",
  "expired_at": "2026-03-23T10:10:00Z",
  "credential_id": 12,
  "task_id": 301,
  "created_at": "2026-03-23T10:00:00Z",
  "updated_at": "2026-03-23T10:00:09Z"
}
```

## 前端接入建议

扫码登录页或弹窗建议按下面节奏实现：

1. 点击“扫码登录”时调用创建会话接口。
2. 页面直接展示 `qr_code_image`。
3. 保存 `session_id` 和 `task_id`。
4. 轮询登录会话详情，不要直接轮询微信侧。
5. 状态成功后刷新凭证列表。
6. 失败或过期后允许用户一键重新创建会话。

## 容易踩坑的点

这里列几个当前实现里最容易误解的点。

- 凭证更新接口不是“凭证编辑器”，只允许改名称。
- 默认凭证是 tenant 级唯一，不是当前成员唯一。
- 删除凭证是软删除。
- 登录会话返回的 `task_id` 是附加信息，前端登录流程本身仍然建议优先轮询
  `login-sessions/{session_id}`。
- 当前没有“手动录入 token/cookie”入口，也不建议前端做这种能力。

## 下一步

把凭证链路跑通后，建议继续看：

- [02_公众号API.md](./02_公众号API.md)
- [04_同步任务API.md](./04_同步任务API.md)
