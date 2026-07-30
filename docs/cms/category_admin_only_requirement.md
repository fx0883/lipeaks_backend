# 需求规格：分类级管理员专属文章控制

> 状态：✅ 已完成需求澄清，待进入设计/开发阶段
> 创建日期：2026-06-29
> 模块：`cms`
> 类型：增量功能需求

---

## 1. 需求概述（TL;DR）

每个租户可以在分类维度配置"管理员专属分类"。该分类下的文章：
- ✅ **所有人（含游客）可以观看**
- ❌ **Member（普通成员）不能创建 / 编辑 / 删除**
- ✅ **管理员（User：租户管理员 + 超级管理员）可以增删改查**

---

## 2. 背景

当前 CMS 系统的权限控制是**文章作者级别**的：
- Member 通过 `/api/v1/cms/member/articles/` 走 `MemberArticleViewSet`，只能增删改自己创建的文章
- 管理员通过 `/api/v1/cms/articles/` 走 `ArticleViewSet`，可以管理租户内所有文章
- **没有**任何分类级别的写权限控制

**业务痛点**：租户希望某些"官方分类"（如「公告」「官方资讯」「精选专题」）下的内容只由管理员维护，避免 Member 在这些分类下发布内容，但又要保证 Member 在其他分类下可以正常创作。

---

## 3. 用户故事

| # | 角色 | 故事 |
|---|------|------|
| US-1 | 租户管理员 | 作为租户管理员，我希望能把某个分类标记为"管理员专属"，这样该分类下的文章只有我和其他管理员能维护 |
| US-2 | 租户管理员 | 作为租户管理员，我希望能取消"管理员专属"标记，恢复 Member 的创作权限 |
| US-3 | Member | 作为 Member，我希望在创建文章时如果选择了管理员专属分类，能收到清晰的错误提示，告诉我哪些分类不可用 |
| US-4 | Member | 作为 Member，我希望在编辑/删除自己的文章时，如果文章关联了管理员专属分类，能被拒绝并给出原因 |
| US-5 | 游客/任意用户 | 作为访客，我希望可以正常浏览管理员专属分类下的文章，不受影响 |

---

## 4. 已确认的设计决策

| # | 决策项 | 选定方案 | 理由 |
|---|--------|---------|------|
| D-1 | 字段粒度 | **单一布尔字段 `is_admin_only`** | 场景简单，无需拆分 create/edit/delete |
| D-2 | 子分类继承 | **不继承，各自独立配置** | 行为可预测，实现简单 |
| D-3 | 多分类冲突 | **任一受限即拒绝** | 保守策略，避免越权 |
| D-4 | 历史数据 | **严格模式：配置立即生效** | 老文章 Member 也不能改，管理员接手维护 |
| D-5 | 管理员范围 | **租户管理员 + 超级管理员**（即所有 `User` 类型） | 与现有 `CMSBasePermission` 行为一致 |
| D-6 | 配置权限 | **仅管理员可修改 `is_admin_only` 字段** | Member 本来就不能改分类，沿用现状 |

---

## 5. 功能需求详述

### 5.1 数据模型变更

在 `cms.Category` 模型新增字段：

```python
is_admin_only = models.BooleanField(
    _("管理员专属"),
    default=False,
    db_index=True,
    help_text="标记为True时，该分类下的文章仅管理员可创建/编辑/删除，Member不可操作"
)
```

**迁移要求**：
- 新建 migration，default=False（不影响现有数据）
- 加索引 `Index(fields=['tenant', 'is_admin_only'])` 优化查询

### 5.2 API 行为变更

#### 5.2.1 分类 API（`/api/v1/cms/categories/`）

| 接口 | 变更 |
|------|------|
| `GET /categories/` | 响应中包含 `is_admin_only` 字段，所有人可读 |
| `GET /categories/{id}/` | 同上 |
| `POST /categories/` | 请求可传 `is_admin_only`，仅管理员可设置 |
| `PUT/PATCH /categories/{id}/` | 仅管理员可修改 `is_admin_only` |
| `GET /categories/tree/` | 树结构响应中包含 `is_admin_only` |

#### 5.2.2 Member 文章 API（`/api/v1/cms/member/articles/`）

**创建文章 `POST`**：
- 在 `MemberArticleCreateUpdateSerializer.validate()` 中校验 `category_ids`
- 如果任一 `category_id` 对应的分类 `is_admin_only=True`，抛出 400 错误
- 错误消息示例：`"分类 [公告] 是管理员专属分类，您无法在此分类下创建文章"`

**更新文章 `PUT/PATCH`**：
- 在 `MemberArticleViewSet.perform_update()` 中：
  1. 如果请求体包含 `category_ids`，校验新分类列表中是否有管理员专属分类
  2. 如果请求体不含 `category_ids`，校验文章**当前关联的分类**是否含管理员专属
- 任一命中即抛出 403 错误

**删除文章 `DELETE`**：
- 在 `MemberArticleViewSet.perform_destroy()` 中校验文章当前关联分类
- 含管理员专属分类 → 抛出 403 错误

**自定义动作 `publish_article`**：
- 同样校验，含管理员专属分类的草稿 Member 不能发布

#### 5.2.3 管理员文章 API（`/api/v1/cms/articles/`）

**不变**。管理员可以正常在管理员专属分类下创建/编辑/删除文章。

#### 5.2.4 观看 API

**所有 GET 接口不变**。管理员专属分类下的文章，对游客、Member、管理员都可见（前提是文章状态为 `published` + `visibility=public`）。

### 5.3 权限规则矩阵

| 操作 | 游客 | Member | 租户管理员 | 超级管理员 |
|------|------|--------|------------|------------|
| 观看管理员专属分类本身 | ✅（分类激活时） | ✅ | ✅ | ✅ |
| 观看管理员专属分类下的公开文章 | ✅ | ✅ | ✅ | ✅ |
| 在管理员专属分类下创建文章 | ❌ | ❌ | ✅ | ✅（需指定 X-Tenant-ID） |
| 编辑该分类下的文章 | ❌ | ❌（即使自己是作者） | ✅ | ✅ |
| 删除该分类下的文章 | ❌ | ❌（即使自己是作者） | ✅ | ✅ |
| 修改分类的 `is_admin_only` 标记 | ❌ | ❌ | ✅ | ✅ |
| 在开放分类下创建/编辑/删除文章 | ❌ | ✅（仅自己的） | ✅ | ✅ |

### 5.4 错误响应规范

所有因 `is_admin_only` 触发的拦截，统一返回结构化错误：

```json
{
  "code": "CATEGORY_ADMIN_ONLY",
  "message": "分类 [公告] 是管理员专属分类，您无权操作该分类下的文章",
  "details": {
    "restricted_categories": [
      {"id": 5, "name": "公告", "slug": "announcement"}
    ],
    "action": "create|update|delete|publish"
  }
}
```

HTTP 状态码：
- 创建时拦截：`400 Bad Request`（参数校验失败）
- 更新/删除/发布时拦截：`403 Forbidden`

---

## 6. 边界场景与处理策略

| 场景 | 处理策略 |
|------|---------|
| Member 创建文章时同时关联了 1 个管理员专属 + 2 个开放分类 | 拒绝（任一受限即拒绝） |
| Member 把文章从开放分类移到管理员专属分类 | 拒绝（更新时校验新分类列表） |
| Member 把文章从管理员专属分类移到开放分类 | 拒绝（严格模式，老文章也受限） |
| 管理员标记某分类为"管理员专属"前，Member 已在该分类下有 50 篇文章 | 这 50 篇文章 Member 立即不能再编辑/删除，需管理员接手 |
| 文章未关联任何分类（`category_ids=[]`） | 不受 `is_admin_only` 影响，正常走原有权限 |
| 子分类的父分类是管理员专属，子分类本身未标记 | **不拦截**（D-2 决策：不继承） |
| 管理员取消"管理员专属"标记 | Member 立即恢复对相关文章的操作权限 |

---

## 7. 非功能需求

### 7.1 性能
- `is_admin_only` 字段加索引（`tenant + is_admin_only` 组合索引）
- 校验逻辑避免 N+1 查询：用 `Category.objects.filter(id__in=category_ids, tenant=tenant, is_admin_only=True)` 一次性查询
- 文章关联分类的校验，用 `ArticleCategory.objects.filter(article=article, category__is_admin_only=True).select_related('category')` 一次性查询

### 7.2 国际化
- 所有错误消息通过 `gettext_lazy` 包装，支持 `zh-hans` / `en` 等语言

### 7.3 日志
- 在 `OperationLog` 中记录管理员对 `is_admin_only` 字段的修改（action='update', entity_type='category'）
- Member 被拦截时记录 WARNING 级别日志，含 user_id、article_id、category_ids

### 7.4 兼容性
- 现有无 `is_admin_only` 字段的请求：默认 `False`，行为不变
- 现有数据：migration 默认值 `False`，不破坏现有数据
- Swagger schema 自动更新

---

## 8. 影响文件清单（预估）

| 文件 | 改动类型 |
|------|---------|
| `cms/models.py` | 新增 `is_admin_only` 字段 |
| `cms/migrations/00XX_add_category_is_admin_only.py` | 新建 migration |
| `cms/serializers.py` | `CategorySerializer` 输出新字段；`ArticleCreateUpdateSerializer.validate()` 加校验；`MemberArticleCreateUpdateSerializer` 继承校验 |
| `cms/member_article_views.py` | `perform_create` / `perform_update` / `perform_destroy` / `publish_article` 加分类校验 |
| `cms/permissions.py` | （可选）在 `CategoryPermission` 限制 Member 修改 `is_admin_only` 字段 |
| `cms/tests/test_category_admin_only.py` | 新增测试用例 |

---

## 9. 测试用例覆盖（建议）

| # | 场景 | 期望结果 |
|---|------|---------|
| T-1 | 管理员创建标记 `is_admin_only=True` 的分类 | 成功 |
| T-2 | Member 尝试创建 `is_admin_only=True` 的分类 | 403 |
| T-3 | Member 在管理员专属分类下创建文章 | 400，错误码 `CATEGORY_ADMIN_ONLY` |
| T-4 | Member 在开放分类下创建文章 | 成功 |
| T-5 | Member 创建文章时关联混合分类（1 专属 + 2 开放） | 400 |
| T-6 | Member 编辑关联管理员专属分类的自己文章 | 403 |
| T-7 | Member 删除关联管理员专属分类的自己文章 | 403 |
| T-8 | Member 发布关联管理员专属分类的草稿 | 403 |
| T-9 | 管理员编辑管理员专属分类下的文章 | 成功 |
| T-10 | 游客 GET 管理员专属分类下的公开文章 | 200 |
| T-11 | 管理员取消 `is_admin_only` 标记后，Member 恢复操作权限 | 成功 |
| T-12 | 文章未关联任何分类，Member 正常操作 | 成功 |
| T-13 | 子分类父级是管理员专属，子分类未标记，Member 创建 | 成功（不继承） |

---

## 10. 待办与下一步

- [ ] 用户确认本需求文档
- [ ] 进入架构设计阶段（评估是否需要走标准 SOP，或直接快速模式实现）
- [ ] 开发实现
- [ ] 测试验证
- [ ] 文档更新（更新 `docs/cms/` 下的 API 文档）
