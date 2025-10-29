# CMS API 文档

## 概述
- **Base URL**: `/api/v1/cms/`
- **认证**: JWT（`Authorization: Bearer <token>`，未携带时视为匿名用户）
- **多租户隔离**: 所有CMS接口都要求在Header中携带 `X-Tenant-ID: <tenant_id>`（GET也需要）。服务器侧由中间件/权限层校验并将其注入 `request.tenant_id`。
- **内容类型**: `application/json`

## 文档索引
1. [文章管理API](./文章管理API.md)
2. [分类管理API](./分类管理API.md)
3. [标签管理API](./标签管理API.md)
4. [评论管理API](./评论管理API.md)

## 通用请求头（必须）
```http
Authorization: Bearer <token>        # 非GET可选但强烈建议；匿名访问则可不带
X-Tenant-ID: 1                       # 必须，所有CMS路径均需要
Content-Type: application/json
```

## 权限与角色
- **匿名用户(Anonymous)**: 仅可GET公开已发布资源（例如公开文章、激活分类/标签等），仍需 `X-Tenant-ID`。
- **普通成员(Member)**: 登录后，可以：
  - 创建文章（作者自动为当前用户）
  - 更新/删除自己的文章
  - **发布/取消发布/归档自己的文章**
  - 创建/管理自己的评论
  - **收藏/取消收藏文章**（用户互动功能）
- **租户管理员(Admin)**: 可管理本租户所有CMS资源。
- **超级管理员(Super Admin)**: 需要在Header中显式带 `X-Tenant-ID` 来指定目标租户，方可操作该租户资源。

权限判定要点（来自 `cms/permissions.py` 与各视图集）：
- GET请求：允许匿名，但若访问非公开内容，需要认证与权限；并且必须提供 `X-Tenant-ID`。
- 非GET请求：需要认证；Member通常仅能操作自己资源，Admin可操作本租户所有资源，Super Admin 可指定租户操作。
- 文章读取：匿名仅能读取 `status=published && visibility=public` 的文章。
- 特例：`POST /articles/{id}/view/` 视为记录阅读接口，允许匿名，但由于获取文章对象依赖租户过滤，仍建议携带 `X-Tenant-ID`。

## 常用状态码
- 200 OK
- 201 Created
- 204 No Content
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found

## 分页与搜索
- `page`, `page_size`
- `search`（具体字段见各模块）
- 排序：`sort` + `sort_direction`（或个别视图支持 `ordering`）

## 快速开始
- 登录获取Token：`POST /api/v1/auth/login/`
- 访问Swagger：`/api/v1/docs/` ；OpenAPI：`/api/v1/schema/`
