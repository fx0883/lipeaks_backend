# 分级租户管理员与应用级数据范围授权实施方案 (Hierarchical Tenant Admin & App Scoping Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现租户管理员权限分级（租户主管理员 `tenant_owner` 与应用管理员 `app_admin`），支持为应用管理员多选绑定管辖应用；应用管理员严禁管理人事与修改应用配置，在 CMS 中严格隔离非管辖应用与公共分类；前后端全链路打通。

**Architecture:** 
- 后端在 `users.User` 增加 `admin_type` 枚举区分管理层级，在 `applications.UserApplication` 建立多对多关系支持多应用绑定；
- 在人员管理、应用设置、CMS 文章/分类各层注入声明式数据范围拦截；
- 动态路由自动剔除人员/系统菜单；前端在 `lipeaks_admin` 提供管理员类型单选与管辖应用多选交互，类型检查与全量测试闭环。

**Tech Stack:** 
- 后端：Python 3.13 / Django 6.1.2 / DRF 3.18.3 / SQLite (测试) / MySQL (生产) / Pytest
- 前端：Vue 3.5 / TypeScript 6 / Element Plus / Pinia 4 / Vite 8 / vue-pure-admin

---

## Global Constraints

- 存量所有管理员在数据库迁移中默认置为 `tenant_owner`，保持历史行为 100% 兼容。
- 严禁破坏现有 630+ 项单元测试，新加测试必须 100% 通过。
- 应用管理员严禁调用 `users` 和 `members` 的增删改查接口（返回 403 Forbidden）。
- 应用管理员在 CMS 中不可见公共分类（`application is null`），不可创建公共分类，不可在文章中引用公共分类。
- 应用管理员不可修改应用配置（`PUT/PATCH/DELETE /api/applications/{id}/` 阻断）。
- 前端 `lipeaks_admin` 必须通过 `pnpm typecheck` 零报错。

---

### Task 1: 后端数据模型与迁移 (`applications.UserApplication` 与 `users.User.admin_type`)

**Files:**
- Create: `applications/tests/test_user_application_model.py`
- Modify: `applications/models.py`
- Modify: `users/models.py:100-188`
- Generate: `applications/migrations/0002_userapplication.py`
- Generate: `users/migrations/0002_user_admin_type.py` (具体迁移编号由 makemigrations 确定)

**Interfaces:**
- `User.admin_type`: choices `('tenant_owner', '租户主管理员')`, `('app_admin', '应用管理员')`, default `'tenant_owner'`
- `User.is_tenant_owner`: property -> `bool`
- `User.is_app_admin`: property -> `bool`
- `User.get_managed_app_ids()`: method -> `Optional[list[int]]` (None 表示全部应用)
- `UserApplication`: `user`, `application`, `role` (default `'admin'`)

- [ ] **Step 1: 编写数据模型与辅助方法的失败测试**
  在 `applications/tests/test_user_application_model.py` 中编写模型定义、属性与 `get_managed_app_ids()` 的断言测试。
- [ ] **Step 2: 运行测试确保初始失败**
  运行 `pytest applications/tests/test_user_application_model.py` 验证失败。
- [ ] **Step 3: 在 `applications/models.py` 增加 `UserApplication`**
  实现 `UserApplication` 模型，包含唯一约束 `unique_together = [['user', 'application']]`。
- [ ] **Step 4: 在 `users/models.py` 扩展 `admin_type` 与快捷方法**
  增加 `admin_type` 字段、`is_tenant_owner`、`is_app_admin` 与 `get_managed_app_ids()` 方法。
- [ ] **Step 5: 生成并执行 Django 迁移**
  运行 `python manage.py makemigrations` 和 `python manage.py migrate`。
- [ ] **Step 6: 重新运行测试确保通过**
  运行 `pytest applications/tests/test_user_application_model.py` 确保 100% 通过。

---

### Task 2: 用户序列化器与人员管理权限拦截 (`users/serializers.py` & `users/views/`)

**Files:**
- Create: `users/tests/test_app_admin_personnel_restriction.py`
- Modify: `users/serializers.py:20-140`
- Modify: `users/views/admin_user_views.py`
- Modify: `users/views/member_admin_views.py`

**Interfaces:**
- `UserSerializer`: 输出 `admin_type`, `managed_applications` (id, name, code)
- `UserCreateSerializer` / `UserUpdateSerializer`: 接收 `admin_type`, `application_ids`，并在保存时原子更新 `UserApplication` 表。
- 人员管理接口：对 `is_app_admin == True` 的请求抛出 403 `PermissionDenied("应用管理员无权管理租户人员")`。

- [ ] **Step 1: 编写人员管理拦截与应用绑定的失败测试**
  测试包括：主管理员创建应用管理员并绑定应用、应用管理员调用人员列表/创建接口返回 403。
- [ ] **Step 2: 运行测试确认失败**
  运行 `pytest users/tests/test_app_admin_personnel_restriction.py`。
- [ ] **Step 3: 改造 `UserSerializer`**
  增加 `admin_type` 字段，并通过 `SerializerMethodField` 返回 `managed_applications`。
- [ ] **Step 4: 改造 `UserCreateSerializer` 与 `UserUpdateSerializer`**
  支持 `admin_type` 及 `application_ids` 参数校验与原子关联更新。
- [ ] **Step 5: 在 `admin_user_views.py` 与 `member_admin_views.py` 注入拦截**
  检查调用者是否为 `is_tenant_owner` 或 `is_super_admin`，拒绝 `is_app_admin`。
- [ ] **Step 6: 运行测试确保全部通过**
  运行 `pytest users/tests/test_app_admin_personnel_restriction.py`。

---

### Task 3: CMS 分类与文章应用级数据范围隔离 (`cms/views/base_views.py`)

**Files:**
- Create: `cms/tests/test_app_admin_cms_scoping.py`
- Modify: `cms/views/base_views.py:279-450` (ArticleViewSet)
- Modify: `cms/views/base_views.py:1410-1500` (CategoryViewSet)
- Modify: `applications/views.py:20-60` (ApplicationViewSet)

**Interfaces:**
- `CategoryViewSet.get_queryset()`: 当用户为应用管理员时，强制过滤 `application_id__in=user.get_managed_app_ids()`，排除公共分类。
- `CategoryViewSet.perform_create()`: 应用管理员必须指定管辖内的 `application_id`，禁止创建公共分类。
- `ArticleViewSet.get_queryset()`: 强制过滤文章关联的应用必须属于管辖列表。
- `ArticleViewSet.perform_create/update()`: 校验文章的 application_id 和所有 category_ids 均受限于管辖列表。
- `ApplicationViewSet.get_queryset()`: 应用管理员仅能查看被分配的应用列表；禁止写操作。

- [ ] **Step 1: 编写 CMS 分类与文章应用范围隔离的失败测试**
  测试包括：应用管理员查不到公共分类、创建分类不可留空应用、文章只能关联授权应用、无法访问其它应用文章。
- [ ] **Step 2: 运行测试确认失败**
  运行 `pytest cms/tests/test_app_admin_cms_scoping.py`。
- [ ] **Step 3: 改造 `CategoryViewSet` 数据范围与创建校验**
  注入 `get_managed_app_ids()` 过滤与空 application 拦截。
- [ ] **Step 4: 改造 `ArticleViewSet` 数据范围与分类归属校验**
  注入文章关联应用检查和分类属于管辖应用的二次校验。
- [ ] **Step 5: 改造 `ApplicationViewSet` 数据范围与修改拦截**
  应用管理员仅返回管辖应用，写操作拦截 403。
- [ ] **Step 6: 运行测试验证全量通过**
  运行 `pytest cms/tests/test_app_admin_cms_scoping.py`。

---

### Task 4: 动态路由与菜单自适应 (`menus/views/routes_views.py`)

**Files:**
- Create: `menus/tests/test_app_admin_routes.py`
- Modify: `menus/views/routes_views.py:158-196`

**Interfaces:**
- `GET /api/v1/menus/admin/routes/`: 若当前用户为 `is_app_admin`，自动过滤掉非 CMS、非控制台的系统/人事/应用配置路由。

- [ ] **Step 1: 编写应用管理员动态路由过滤测试**
- [ ] **Step 2: 改造 `routes_views.py`**
  对于应用管理员，剔除人员、租户与系统路由节点。
- [ ] **Step 3: 运行测试确保通过**

---

### Task 5: 前端 `lipeaks_admin` 类型与 Store 扩展

**Files:**
- Modify: `/Volumes/MOVESPEED/Github/lipeaks_admin/src/types/adminUser.ts`
- Modify: `/Volumes/MOVESPEED/Github/lipeaks_admin/src/store/modules/adminUser.ts`

- [ ] **Step 1: 扩展 `adminUser.ts` 接口类型**
  增加 `admin_type: 'tenant_owner' | 'app_admin'`、`managed_applications` 及 `application_ids` 字段。
- [ ] **Step 2: 检查并适配 `adminUser.ts` Store**
  确保创建和更新 action 能够将 `admin_type` 和 `application_ids` 完整提交至后端。

---

### Task 6: 前端 `lipeaks_admin` 管理员管理表单与列表改造

**Files:**
- Modify: `/Volumes/MOVESPEED/Github/lipeaks_admin/src/components/AdminUserManagement/AdminUserForm.vue`
- Modify: `/Volumes/MOVESPEED/Github/lipeaks_admin/src/views/admin-user/index.vue`

- [ ] **Step 1: 改造 `AdminUserForm.vue`**
  - 新增【管理员类型】单选按钮组（`tenant_owner` / `app_admin`）；
  - 当选为 `app_admin` 时，条件渲染【管辖应用】多选下拉框（`el-select multiple`）；
  - 组件挂载时调用 `applicationStore.fetchApplicationList` 获取当前租户下的所有可用应用；
  - 增加校验规则：应用管理员模式下，管辖应用不能为空。
- [ ] **Step 2: 改造 `admin-user/index.vue` 列表页**
  - 在角色与类型列中，针对应用管理员展示 Warning 标签及管辖应用的 Tag 列表；主管理员展示 Primary 标签。

---

### Task 7: 前端 `lipeaks_admin` 编译检查与全量回归验收

**Files:**
- Run commands in `/Volumes/MOVESPEED/Github/lipeaks_admin` and `/Volumes/MOVESPEED/Github/lipeaks_backend`

- [ ] **Step 1: 运行前端 TypeScript 类型检查**
  在 `lipeaks_admin` 目录下运行 `pnpm typecheck`，确保 0 错误。
- [ ] **Step 2: 运行后端全量测试套件**
  在 `lipeaks_backend` 目录下运行 `pytest`，确保 630+ 历史用例与全部新增测试 100% 绿色通过。
