# 分类级管理员专属文章控制 — API 文档

> 功能上线日期：2026-06-29
> 模块：CMS
> 关联需求：[category_admin_only_requirement.md](../category_admin_only_requirement.md)

## 功能概述

每个租户可在分类维度配置"管理员专属分类"（`is_admin_only=True`）。该分类下的文章：

- ✅ 所有人（含游客）可观看
- ❌ Member 不能创建 / 编辑 / 删除 / 发布
- ✅ 管理员（租户管理员 + 超级管理员）可正常增删改查

## 受影响的 API 清单

本次需求共影响以下 5 个 API，详细文档见同目录独立文件：

| # | API | 文件 | 变更类型 |
|---|-----|------|---------|
| 1 | 创建分类 | [01_create_category.md](01_create_category.md) | 新增 `is_admin_only` 字段，Member 设置该字段会被 403 拒绝 |
| 2 | 更新分类 | [02_update_category.md](02_update_category.md) | 支持修改 `is_admin_only` 字段，仅管理员可改 |
| 3 | 分类列表/详情 | [03_list_retrieve_category.md](03_list_retrieve_category.md) | 响应新增 `is_admin_only` 字段 |
| 4 | Member 创建文章 | [04_member_create_article.md](04_member_create_article.md) | 若 `category_ids` 含管理员专属分类，返回 400 |
| 5 | Member 更新/删除/发布文章 | [05_member_update_delete_publish_article.md](05_member_update_delete_publish_article.md) | 文章关联管理员专属分类时，返回 403 |

## 权限规则矩阵

| 操作 | 游客 | Member | 租户管理员 | 超级管理员 |
|------|------|--------|------------|------------|
| 观看管理员专属分类本身 | ✅（分类激活时） | ✅ | ✅ | ✅ |
| 观看管理员专属分类下的公开文章 | ✅ | ✅ | ✅ | ✅ |
| 在管理员专属分类下创建文章 | ❌ | ❌ | ✅ | ✅（需 X-Tenant-ID） |
| 编辑该分类下的文章 | ❌ | ❌（即使自己是作者） | ✅ | ✅ |
| 删除该分类下的文章 | ❌ | ❌（即使自己是作者） | ✅ | ✅ |
| 发布该分类下的草稿 | ❌ | ❌ | ✅ | ✅ |
| 修改分类的 `is_admin_only` 标记 | ❌ | ❌ | ✅ | ✅ |
| 创建/修改 `is_admin_only=True` 的分类 | ❌ | ❌ | ✅ | ✅ |

## 错误响应规范

### 创建文章时拦截（400 Bad Request）

```json
{
  "code": 400,
  "message": "分类 [公告] 是管理员专属分类，您无法在此分类下创建文章"
}
```

### 更新/删除/发布文章时拦截（403 Forbidden）

```json
{
  "detail": "分类 [公告] 是管理员专属分类，您无权编辑该分类下的文章"
}
```

动作文案映射：
- update → 编辑
- delete → 删除
- publish → 发布

### Member 创建/修改管理员专属分类时拦截（403 Forbidden）

```json
{
  "detail": "只有管理员可以创建管理员专属分类"
}
```

## 关键设计决策

| 决策 | 方案 |
|------|------|
| 字段粒度 | 单一布尔 `is_admin_only` |
| 子分类继承 | 不继承，各自独立配置 |
| 多分类冲突 | 任一受限即拒绝 |
| 历史数据 | 严格模式，配置立即生效 |
| 管理员范围 | 租户管理员 + 超级管理员（所有 `User` 类型） |

## 数据模型变更

`cms.Category` 新增字段：

```python
is_admin_only = models.BooleanField(
    _("管理员专属"),
    default=False,
    db_index=True,
    help_text="标记为True时，该分类下的文章仅管理员可创建/编辑/删除，Member不可操作"
)
```

Migration：`cms/migrations/0014_add_category_is_admin_only.py`
