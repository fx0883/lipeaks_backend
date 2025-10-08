# Member管理API文档索引

**最后更新**: 2025-10-06  
**版本**: v2.0 (API重构版本)

---

## 📚 文档导航

### 🔥 优先阅读（前端开发必读）

| 序号 | 文档 | 说明 | 重要程度 |
|------|------|------|---------|
| 1 | **FRONTEND_MIGRATION_GUIDE.md** | 前端迁移指南 | ⭐⭐⭐⭐⭐ |
| 2 | **README.md** | API总览和快速开始 | ⭐⭐⭐⭐⭐ |
| 3 | **member_common.md** | 通用规范和数据模型 | ⭐⭐⭐⭐ |

### 📖 功能API文档

| 序号 | 文档 | 涵盖的API | 目标读者 |
|------|------|-----------|---------|
| 4 | **member_list_create_api.md** | 列表查询、创建Member | 管理后台开发 |
| 5 | **member_detail_api.md** | 详情查询、更新、删除 | 管理后台开发 |
| 6 | **member_subaccount_api.md** | 子账号管理 | 管理后台+个人中心开发 |
| 7 | **member_avatar_api.md** | 头像上传 | 管理后台+个人中心开发 |

### 📑 技术文档

| 序号 | 文档 | 说明 | 目标读者 |
|------|------|------|---------|
| 8 | **API_REFACTOR_COMPLETED.md** | API重构完成说明 | 技术负责人 |
| 9 | **API_RESTRUCTURE_PROPOSAL.md** | API重构方案详解 | 架构师/技术负责人 |
| 10 | **URL_PATH_CORRECTION.md** | URL路径演变历史 | 参考 |

---

## 🎯 根据角色选择文档

### 前端开发人员（管理后台）

**推荐阅读顺序**：

1. 📌 **FRONTEND_MIGRATION_GUIDE.md** - 了解API变更
2. 📘 **README.md** - 快速上手
3. 📗 **member_common.md** - 理解认证和权限
4. 📙 **member_list_create_api.md** - 实现列表和创建功能
5. 📕 **member_detail_api.md** - 实现编辑和删除功能
6. 📔 **member_avatar_api.md** - 实现头像上传

**核心关注点**：
- ✅ 使用 `/api/v1/admin/members/` 作为基础路径
- ✅ 理解管理员权限（超级管理员 vs 租户管理员）
- ✅ 实现租户隔离逻辑

### 前端开发人员（Member个人中心）

**推荐阅读顺序**：

1. 📘 **README.md** - 快速上手
2. 📗 **member_common.md** - 理解数据模型
3. 📙 **member_subaccount_api.md** - Member端子账号管理
4. 📔 **member_avatar_api.md** - Member端头像上传

**核心关注点**：
- ✅ 使用 `/api/v1/members/` 作为基础路径
- ✅ Member只能操作自己的数据
- ✅ 子账号创建和管理

### 技术负责人/架构师

**推荐阅读顺序**：

1. 📌 **API_REFACTOR_COMPLETED.md** - 重构概览
2. 📘 **API_RESTRUCTURE_PROPOSAL.md** - 重构方案
3. 📗 **README.md** - API总览

---

## 🔍 快速查找

### 按功能查找

| 功能 | 管理员端 | Member端 | 文档 |
|------|---------|---------|------|
| **列表查询** | `/api/v1/admin/members/` | `/api/v1/members/me/` | member_list_create_api.md |
| **创建Member** | `/api/v1/admin/members/` | - | member_list_create_api.md |
| **查看详情** | `/api/v1/admin/members/{id}/` | `/api/v1/members/me/` | member_detail_api.md |
| **编辑信息** | `/api/v1/admin/members/{id}/` | `/api/v1/members/me/` | member_detail_api.md |
| **删除Member** | `/api/v1/admin/members/{id}/` | - | member_detail_api.md |
| **上传头像** | `/api/v1/admin/members/{id}/avatar/upload/` | `/api/v1/members/avatar/upload/` | member_avatar_api.md |
| **子账号列表** | `/api/v1/admin/members/sub-accounts/` | `/api/v1/members/sub-accounts/` | member_subaccount_api.md |
| **创建子账号** | - | `/api/v1/members/sub-accounts/` | member_subaccount_api.md |
| **管理子账号** | `/api/v1/admin/members/sub-accounts/{id}/` | `/api/v1/members/sub-accounts/{id}/` | member_subaccount_api.md |
| **修改密码** | - | `/api/v1/members/me/password/` | member_common.md |

### 按HTTP方法查找

#### GET请求

- 列表查询：`member_list_create_api.md`
- 详情查询：`member_detail_api.md`
- 子账号查询：`member_subaccount_api.md`

#### POST请求

- 创建Member：`member_list_create_api.md`
- 上传头像：`member_avatar_api.md`
- 修改密码：`member_common.md`

#### PUT/PATCH请求

- 更新信息：`member_detail_api.md`
- 更新子账号：`member_subaccount_api.md`

#### DELETE请求

- 删除Member：`member_detail_api.md`
- 删除子账号：`member_subaccount_api.md`

---

## 📊 API统计

### 管理员端API（10个）

```
GET    /api/v1/admin/members/                      # 列表
POST   /api/v1/admin/members/                      # 创建
GET    /api/v1/admin/members/{id}/                 # 详情
PUT    /api/v1/admin/members/{id}/                 # 完整更新
PATCH  /api/v1/admin/members/{id}/                 # 部分更新
DELETE /api/v1/admin/members/{id}/                 # 删除
POST   /api/v1/admin/members/{id}/avatar/upload/   # 上传头像
GET    /api/v1/admin/members/sub-accounts/         # 子账号列表
GET    /api/v1/admin/members/sub-accounts/{id}/    # 子账号详情
PUT    /api/v1/admin/members/sub-accounts/{id}/    # 更新子账号
PATCH  /api/v1/admin/members/sub-accounts/{id}/    # 部分更新子账号
DELETE /api/v1/admin/members/sub-accounts/{id}/    # 删除子账号
```

### Member端API（9个）

```
GET    /api/v1/members/me/                         # 自己信息
PUT    /api/v1/members/me/                         # 更新自己
POST   /api/v1/members/me/password/                # 修改密码
POST   /api/v1/members/avatar/upload/              # 上传头像
GET    /api/v1/members/sub-accounts/               # 子账号列表
POST   /api/v1/members/sub-accounts/               # 创建子账号
GET    /api/v1/members/sub-accounts/{id}/          # 子账号详情
PUT    /api/v1/members/sub-accounts/{id}/          # 更新子账号
PATCH  /api/v1/members/sub-accounts/{id}/          # 部分更新子账号
DELETE /api/v1/members/sub-accounts/{id}/          # 删除子账号
```

---

## 🚀 开始使用

### 步骤1：了解变更

👉 **必读**：FRONTEND_MIGRATION_GUIDE.md

### 步骤2：选择API文档

**如果你在开发管理后台**：
- 阅读管理员端API文档
- 使用 `/api/v1/admin/members/` 路径

**如果你在开发Member个人中心**：
- 阅读Member端API文档
- 使用 `/api/v1/members/` 路径

### 步骤3：集成API

参考各API文档中的代码示例，直接复制使用。

---

## 📌 快速参考

### API Base URL对照

```javascript
// 根据用户角色选择
const getAPIBaseURL = (user) => {
  if (user.is_admin || user.is_super_admin) {
    return 'http://localhost:8000/api/v1/admin/members';
  }
  return 'http://localhost:8000/api/v1/members';
};
```

### 权限对照表

| 操作 | 超级管理员 | 租户管理员 | Member |
|------|-----------|-----------|--------|
| 查看所有Member | ✅ | ✅ (本租户) | ❌ |
| 创建Member | ✅ | ✅ (本租户) | ❌ |
| 编辑Member | ✅ | ✅ (本租户) | ✅ (自己) |
| 删除Member | ✅ | ✅ (本租户) | ❌ |
| 查看自己 | ✅ | ✅ | ✅ |
| 管理子账号 | ✅ | ✅ (本租户) | ✅ (自己的) |

---

## 💡 提示

- 📘 所有API都需要JWT认证
- 🔒 严格的租户隔离机制
- 🎯 管理员和Member使用不同的API路径
- ✅ Member端API完全向后兼容

---

**祝开发顺利！** 🎉

