# 租户管理员 API 文档索引

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 租户管理员是具有 `is_admin=True` 且关联到特定租户的用户
- 所有API都需要在Header中携带 `Authorization: Bearer <access_token>`

## 认证方式
- 所有API都需要JWT认证
- Header: `Authorization: Bearer <access_token>`
- 租户管理员登录时**禁止**携带 `X-Tenant-ID` 请求头

## 重要说明：tenant_id 参数

**对于超级管理员(super_admin)访问租户级别API，必须携带 `tenant_id` 参数：**

```bash
# Query参数方式
curl -X GET "http://localhost:8000/api/v1/cms/articles/?tenant_id=1" \
  -H "Authorization: Bearer <token>"
```

**涉及的API包括：**
- CMS文章: `/api/v1/cms/articles/?tenant_id=1`
- CMS分类: `/api/v1/cms/categories/?tenant_id=1`
- CMS标签: `/api/v1/cms/tags/?tenant_id=1`
- 应用管理: `/api/v1/applications/?tenant_id=1`
- 菜单管理: `/api/v1/menus/?tenant_id=1`
- 订单管理: `/api/v1/orders/?tenant_id=1`
- 客户管理: `/api/v1/customers/?tenant_id=1`

**以下API不需要tenant_id（由系统自动判断）：**
- Member管理: `/api/v1/admin/members/`
- 租户信息: `/api/v1/tenants/{id}/`

## 统一返回结构
所有API遵循统一响应格式：
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": { ... }
}
```

分页返回结构：
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 100,
      "next": "http://localhost:8000/api/v1/xxx/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 10
    },
    "results": [ ... ]
  }
}
```

## API文档目录

### 1. Member管理 API
- 文档：`01_租户管理员Member管理API文档.md`
- 路径前缀：`/api/v1/admin/members/`
- 功能：
  - Member列表查询
  - 创建新Member
  - 获取Member详情
  - 更新Member信息
  - 删除Member
  - 子账号管理
  - 头像上传

### 2. CMS文章管理 API
- 文档：`02_租户管理员CMS文章API文档.md`
- 路径前缀：`/api/v1/cms/articles/`
- 功能：
  - 文章列表查询
  - 创建新文章
  - 获取文章详情
  - 更新文章
  - 删除文章
  - 发布/取消发布
  - 归档文章
  - 批量删除
  - 版本历史
  - 统计数据

### 3. CMS分类管理 API
- 文档：`03_租户管理员CMS分类API文档.md`
- 路径前缀：`/api/v1/cms/categories/`
- 功能：
  - 分类列表查询
  - 创建新分类
  - 获取分类详情
  - 更新分类
  - 删除分类
  - 获取分类树

### 4. CMS标签管理 API
- 文档：`04_租户管理员CMS标签API文档.md`
- 路径前缀：`/api/v1/cms/tags/` 和 `/api/v1/cms/tag-groups/`
- 功能：
  - 标签列表查询
  - 创建新标签
  - 获取标签详情
  - 更新标签
  - 删除标签
  - 标签组管理

### 5. 应用管理 API
- 文档：`05_租户管理员应用管理API文档.md`
- 路径前缀：`/api/v1/applications/`
- 功能：
  - 应用列表查询
  - 创建新应用
  - 获取应用详情
  - 更新应用
  - 删除应用
  - 应用统计

### 6. 菜单管理 API
- 文档：`06_租户管理员菜单管理API文档.md`
- 路径前缀：`/api/v1/menus/`
- 功能：
  - 菜单列表查询
  - 创建新菜单
  - 获取菜单详情
  - 更新菜单
  - 删除菜单
  - 用户菜单获取

### 7. 订单管理 API
- 文档：`07_租户管理员订单管理API文档.md`
- 路径前缀：`/api/v1/orders/`
- 功能：
  - 订单列表查询
  - 获取订单详情
  - 订单状态管理
  - 订单历史记录

### 8. 客户管理 API
- 文档：`08_租户管理员客户管理API文档.md`
- 路径前缀：`/api/v1/customers/`
- 功能：
  - 客户列表查询
  - 创建新客户
  - 获取客户详情
  - 更新客户信息
  - 删除客户
  - 客户关系管理

### 9. 租户信息 API
- 文档：`09_租户管理员租户信息API文档.md`
- 路径前缀：`/api/v1/tenants/`
- 功能：
  - 获取租户完整信息
  - 查看配额使用情况
  - 获取租户用户列表

## 权限说明

### 租户管理员权限范围
1. **数据隔离**：租户管理员只能访问和管理自己租户下的数据
2. **读写权限**：对本租户的资源拥有完整的增删改查权限
3. **用户管理**：可以管理本租户下的所有Member用户
4. **内容管理**：可以管理本租户下的文章、分类、标签等内容

### 权限限制
1. 不能访问其他租户的数据
2. 不能创建或管理其他租户管理员
3. 不能修改租户配额设置（只能查看）
4. 不能暂停或激活租户

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| 2000 | 操作成功 |
| 2001 | 创建成功 |
| 4000 | 参数错误/验证失败 |
| 4001 | 认证失败 |
| 4002 | 凭据无效 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 4030 | 无权限访问 |
| 4040 | 租户不存在 |
| 5000 | 服务器内部错误 |

## 通用请求头

| 请求头 | 必填 | 说明 |
|-------|------|------|
| Authorization | 是 | Bearer Token认证，格式：`Bearer <access_token>` |
| Content-Type | 是 | 请求内容类型，通常为 `application/json` |
| Accept | 否 | 响应内容类型，通常为 `application/json` |

## 基础URL
```
生产环境: https://your-domain.com/api/v1/
开发环境: http://localhost:8000/api/v1/
```
