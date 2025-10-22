# 软件管理 API 使用文档

## 📦 模块概述

软件管理模块提供对软件分类、软件产品、软件版本的完整管理功能。

**API 数量**: 18 个  
**权限要求**: 大部分需要租户管理员权限  
**主要用途**: 管理反馈系统中的软件产品及其版本信息

## 📑 API 列表

### 软件分类管理 (6个API)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/software-categories/` | 获取分类列表 | 已认证用户 |
| POST | `/software-categories/` | 创建分类 | 管理员 |
| GET | `/software-categories/{id}/` | 获取分类详情 | 已认证用户 |
| PUT | `/software-categories/{id}/` | 完整更新分类 | 管理员 |
| PATCH | `/software-categories/{id}/` | 部分更新分类 | 管理员 |
| DELETE | `/software-categories/{id}/` | 删除分类 | 管理员 |

### 软件产品管理 (8个API)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/software/` | 获取软件列表 | 已认证用户 |
| POST | `/software/` | 创建软件 | 管理员 |
| GET | `/software/{id}/` | 获取软件详情 | 已认证用户 |
| PUT | `/software/{id}/` | 完整更新软件 | 管理员 |
| PATCH | `/software/{id}/` | 部分更新软件 | 管理员 |
| DELETE | `/software/{id}/` | 删除软件 | 管理员 |
| POST | `/software/{id}/versions/` | 为软件添加版本 | 管理员 |
| GET | `/software/{id}/versions/` | 获取软件的所有版本 | 已认证用户 |

### 软件版本管理 (4个API)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/software-versions/` | 获取所有版本列表 | 已认证用户 |
| GET | `/software-versions/{id}/` | 获取版本详情 | 已认证用户 |
| PATCH | `/software-versions/{id}/` | 更新版本 | 管理员 |
| DELETE | `/software-versions/{id}/` | 删除版本 | 管理员 |

---

## 软件分类管理

### 1. 获取软件分类列表

**接口**: `GET /software-categories/`

**用途**: 获取系统中所有的软件分类，用于下拉选择或分类导航。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 否 | 筛选激活状态 |
| search | string | 否 | 搜索分类名称和描述 |
| ordering | string | 否 | 排序：sort_order, name, created_at |

**返回数据字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 分类ID |
| name | string | 分类名称 |
| code | string | 分类代码（唯一） |
| description | string | 分类描述 |
| icon | string | 图标名称 |
| sort_order | integer | 排序顺序 |
| is_active | boolean | 是否激活 |
| software_count | integer | 该分类下的软件数量 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**使用场景**:
- 在反馈提交表单中显示软件分类下拉框
- 在管理后台显示分类列表
- 在首页展示不同分类的软件

---

### 2. 创建软件分类

**接口**: `POST /software-categories/`

**用途**: 创建新的软件分类（仅管理员）

**请求字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 分类名称（最多100字符） |
| code | string | ✅ | 分类代码（唯一，英文） |
| description | string | ❌ | 分类描述 |
| icon | string | ❌ | 图标名称 |
| sort_order | integer | ❌ | 排序（默认0） |
| is_active | boolean | ❌ | 是否激活（默认true） |

**注意事项**:
- `code` 字段在租户内必须唯一
- 建议使用英文小写+下划线格式，如 `web_app`
- `sort_order` 越小越靠前

---

### 3-6. 其他分类操作

**获取详情** (`GET /software-categories/{id}/`)
- 返回单个分类的完整信息
- 包含该分类下的软件数量统计

**更新分类** (`PUT` 或 `PATCH /software-categories/{id}/`)
- `PUT`: 需要提供所有字段
- `PATCH`: 只需提供要修改的字段
- 常用于修改分类名称、描述、排序

**删除分类** (`DELETE /software-categories/{id}/`)
- 软删除，数据仍保留
- 删除前需确保该分类下没有软件
- 返回 204 状态码

---

## 软件产品管理

### 7. 获取软件产品列表

**接口**: `GET /software/`

**用途**: 获取所有软件产品，支持多条件筛选。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| category | integer | 按分类ID筛选 |
| status | string | development\|testing\|released\|maintenance\|deprecated |
| is_active | boolean | 筛选激活状态 |
| search | string | 搜索名称、代码、描述 |
| ordering | string | 排序：name, created_at, total_feedbacks |

**返回字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 软件ID |
| name | string | 软件名称 |
| code | string | 软件代码 |
| description | string | 软件描述 |
| category | integer | 分类ID |
| category_name | string | 分类名称 |
| logo | string/null | Logo URL |
| current_version | string/null | 当前版本号 |
| status | string | 开发状态 |
| is_active | boolean | 是否激活 |
| total_feedbacks | integer | 总反馈数 |
| open_feedbacks | integer | 未解决反馈数 |
| version_count | integer | 版本数量 |

**使用场景**:
- 反馈表单中的软件选择器
- 软件列表展示页面
- 管理后台软件管理

---

### 8. 创建软件产品

**接口**: `POST /software/`

**用途**: 创建新的软件产品

**请求字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 软件名称 |
| code | string | ✅ | 软件代码（唯一） |
| description | string | ❌ | 软件描述 |
| category_id | integer | ✅ | 所属分类ID |
| website | string | ❌ | 官方网站 |
| owner | string | ❌ | 负责人 |
| team | string | ❌ | 团队名称 |
| contact_email | string | ❌ | 联系邮箱 |
| tags | array | ❌ | 标签数组 |
| status | string | ❌ | 状态（默认development） |
| is_active | boolean | ❌ | 是否激活（默认true） |

**软件状态说明**:

| 状态 | 说明 | 适用场景 |
|------|------|---------|
| development | 开发中 | 内部测试阶段 |
| testing | 测试中 | Beta 测试 |
| released | 已发布 | 正式版本 |
| maintenance | 维护中 | 仅修复bug |
| deprecated | 已弃用 | 不再维护 |

---

### 9-14. 其他软件操作

**获取软件详情** (`GET /software/{id}/`)
- 返回完整的软件信息
- 包含所有版本列表
- 包含统计数据（反馈数、版本数等）

**更新软件** (`PATCH /software/{id}/`)
- 常用于更新状态、负责人、描述等
- 可以修改所属分类

**删除软件** (`DELETE /software/{id}/`)
- 软删除
- 删除前需确保没有关联的反馈

**添加版本** (`POST /software/{id}/versions/`)
- 为指定软件添加新版本
- 自动更新软件的 `current_version`

**获取版本列表** (`GET /software/{id}/versions/`)
- 获取指定软件的所有版本
- 按版本号降序排列

---

## 软件版本管理

### 15. 获取所有版本列表

**接口**: `GET /software-versions/`

**用途**: 获取系统中所有的软件版本（跨软件）

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| software | integer | 按软件ID筛选 |
| is_stable | boolean | 筛选稳定版本 |
| is_active | boolean | 筛选激活状态 |
| ordering | string | 排序：-version_code, release_date |

**返回字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 版本ID |
| software | integer | 软件ID |
| software_name | string | 软件名称 |
| version | string | 版本号（如 v2.1.0） |
| version_code | integer | 版本代码（用于比较大小） |
| release_date | date | 发布日期 |
| release_notes | string | 发布说明 |
| is_stable | boolean | 是否稳定版 |
| is_active | boolean | 是否激活 |
| download_url | string/null | 下载链接 |

**版本号规范**:
- 格式：`v主版本.次版本.修订版本`
- 示例：`v2.1.0`, `v3.0.1`
- version_code 建议：主*100 + 次*10 + 修订

---

### 16-18. 版本其他操作

**获取版本详情** (`GET /software-versions/{id}/`)
- 返回单个版本的详细信息

**更新版本** (`PATCH /software-versions/{id}/`)
- 常用于修改发布说明、稳定性标记
- 不建议修改版本号

**删除版本** (`DELETE /software-versions/{id}/`)
- 软删除
- 谨慎操作，可能影响关联的反馈记录

---

## 数据关系图

```
软件分类 (SoftwareCategory)
    ↓ 一对多
软件产品 (Software)
    ↓ 一对多
软件版本 (SoftwareVersion)
    ↓ 一对多
用户反馈 (Feedback)
```

## 完整业务流程

### 软件管理流程

```
1. 创建软件分类
   ↓
2. 在分类下创建软件产品
   ↓
3. 为软件添加版本
   ↓
4. 用户可以针对特定软件和版本提交反馈
```

### 前端集成建议

**软件选择器组件设计**:

1. **两级联动**:
   - 第一级：选择软件分类（category）
   - 第二级：选择该分类下的软件（software）
   - 第三级（可选）：选择软件版本（version）

2. **数据加载顺序**:
   ```
   加载所有分类 → 用户选择分类 
       ↓
   加载该分类下的软件 → 用户选择软件
       ↓
   加载该软件的版本列表 → 用户选择版本（可选）
   ```

3. **缓存策略**:
   - 分类列表：首次加载后缓存
   - 软件列表：按分类缓存
   - 版本列表：按软件缓存

---

## 常见业务场景

### 场景1: 反馈提交页面的软件选择

**步骤**:
1. 页面加载时获取所有软件分类
2. 用户选择分类后，获取该分类下的软件
3. 用户选择软件后，获取该软件的版本列表
4. 用户选择版本（可选）
5. 提交反馈时携带 `software` 和 `software_version` 字段

**接口调用顺序**:
```
GET /software-categories/?is_active=true
    ↓
GET /software/?category={id}&is_active=true&status=released
    ↓
GET /software/{id}/versions/?is_active=true
```

---

### 场景2: 管理后台软件管理

**功能需求**:
- 软件列表展示（分页、搜索、筛选）
- 添加/编辑软件
- 软件状态管理
- 版本管理

**关键接口**:
- 列表：`GET /software/`
- 创建：`POST /software/`
- 编辑：`PATCH /software/{id}/`
- 添加版本：`POST /software/{id}/versions/`

---

### 场景3: 软件详情页面

**展示内容**:
- 软件基本信息
- 所属分类
- 当前版本
- 版本历史列表
- 相关反馈统计

**接口调用**:
```
GET /software/{id}/  # 获取软件详情（已包含版本列表）
```

---

## 字段验证规则

### 软件分类

| 字段 | 规则 |
|------|------|
| name | 必填，最多100字符 |
| code | 必填，最多50字符，租户内唯一 |
| description | 可选，最多500字符 |
| icon | 可选，最多50字符 |
| sort_order | 整数，默认0 |

### 软件产品

| 字段 | 规则 |
|------|------|
| name | 必填，最多200字符 |
| code | 必填，最多100字符，租户内唯一 |
| description | 可选，文本 |
| category_id | 必填，必须是有效的分类ID |
| website | 可选，URL格式 |
| contact_email | 可选，邮箱格式 |
| tags | 可选，JSON数组 |

### 软件版本

| 字段 | 规则 |
|------|------|
| version | 必填，最多50字符 |
| version_code | 必填，整数 |
| release_date | 可选，日期格式 |
| release_notes | 可选，文本 |
| download_url | 可选，URL格式 |

---

## 注意事项

### 1. 数据约束
- `code` 字段在租户内必须唯一
- 删除分类前需先删除该分类下的所有软件
- 删除软件前需先删除相关反馈
- 版本号建议使用语义化版本规范

### 2. 性能优化
- 软件列表数量较多时使用分页
- 缓存常用的分类和软件列表
- 使用 `ordering` 参数进行排序而非前端排序

### 3. 用户体验
- 分类和软件选择使用级联组件
- 显示软件的反馈统计数（帮助用户判断软件活跃度）
- 版本列表按发布时间倒序排列

### 4. 权限控制
- 普通用户只读
- 只有管理员可以创建、修改、删除
- API 会自动检查权限，前端需要隐藏无权操作的按钮

---

**下一步**: [02_反馈管理API.md](02_反馈管理API.md)
