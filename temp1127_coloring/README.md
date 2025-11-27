# Lipeaks Coloring API 文档

> 本文档适用于 Lipeaks Coloring 移动应用的后端 API 对接
> 测试环境: `http://localhost:8000`
> 测试租户ID: `3`
> 测试应用ID: `6`

---

## 文档索引

| 文档 | 说明 | 接口数量 |
|------|------|----------|
| [01_AUTH_API.md](./01_AUTH_API.md) | 认证相关（登录/注册/Token刷新） | 3 |
| [02_MEMBER_API.md](./02_MEMBER_API.md) | 会员管理和子账号管理 | 9 |
| [03_INTERACTION_API.md](./03_INTERACTION_API.md) | 用户互动（点赞/关注/收藏/文章点赞） | 25 |
| [04_CMS_API.md](./04_CMS_API.md) | 内容管理（分类/文章/标签/评论） | 44 |
| [05_FILE_UPLOAD_API.md](./05_FILE_UPLOAD_API.md) | 文件上传 | 2 |
| **总计** | | **83** |

---

## 通用规范

### 基础URL
- 开发环境: `http://localhost:8000`
- 生产环境: `https://api.yourdomain.com`

### 请求Headers

#### 必须Headers
| Header | 说明 | 示例 |
|--------|------|------|
| X-Tenant-ID | 租户ID（Member用户必须） | `3` |
| Content-Type | 请求体类型 | `application/json` |

#### 认证Header
| Header | 说明 | 示例 |
|--------|------|------|
| Authorization | JWT Token | `Bearer eyJhbG...` |

### 响应格式

所有API响应格式统一:

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": { ... }
}
```

#### 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| code | integer | 业务状态码 |
| message | string | 响应消息（可国际化） |
| data | object/array/null | 响应数据 |
| error_code | string | 错误代码（失败时） |

### 业务状态码

| code | 说明 |
|------|------|
| 2000 | 成功 |
| 4000 | 请求参数错误/验证失败 |
| 4001 | 缺少必要参数 |
| 4002 | 认证失败（用户名或密码错误） |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 4005 | 方法不允许 |
| 4100 | 租户操作失败 |
| 5000 | 服务器内部错误 |

### 分页格式

分页接口响应格式:

```json
{
  "success": true,
  "code": 2000,
  "data": {
    "pagination": {
      "count": 100,
      "next": "http://localhost:8000/api/xxx/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 10
    },
    "results": [ ... ]
  }
}
```

---

## 快速开始

### 1. 登录获取Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "7548155@qq.com",
    "password": "Fengxuan_0027337"
  }'
```

### 2. 使用Token调用API

```bash
# 将返回的token保存为环境变量
TOKEN="eyJhbG..."

# 调用需要认证的API
curl -X GET "http://localhost:8000/api/v1/members/me/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 3"
```

### 3. Token刷新

当access token过期时，使用refresh token获取新token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "refresh_token": "eyJhbG..."
  }'
```

---

## Token有效期

| Token类型 | 有效期 |
|-----------|--------|
| Access Token | 24小时 |
| Refresh Token | 7天 |

---

## 注意事项

1. **租户隔离**: 所有数据都按租户隔离，必须携带 `X-Tenant-ID` Header
2. **认证要求**: 除登录/注册/刷新Token外，其他API都需要 `Authorization` Header
3. **收藏功能**: 目前收藏API仅支持管理员用户，Member用户请使用文章点赞API替代
4. **方法限制**: 部分更新接口不支持PATCH，请使用PUT方法
5. **分页默认值**: 默认 `page_size=10`，可通过参数调整

---

## 测试账号

| 字段 | 值 |
|------|-----|
| 租户ID | 3 |
| 用户名 | 7548155@qq.com |
| 密码 | Fengxuan_0027337 |
| 应用ID | 6 |

---

## 更新日志

### 2025-11-27
- 初始版本，包含83个API接口文档
- 修复了interactions模块的tenant设置bug
