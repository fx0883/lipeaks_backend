# 匿名访问租户过滤修复报告

## 修复时间
2025-11-01

## 问题描述
在CMS模块中，多个允许匿名访问的API端点在查询数据时没有使用 `X-Tenant-ID` 请求头进行租户过滤，导致返回所有租户的数据而不是指定租户的数据。

## 根本原因
虽然 `TenantMiddleware` 已经正确解析 `X-Tenant-ID` 请求头并设置了：
- `request.tenant_id` - 租户ID
- 租户上下文（通过 `set_current_tenant()`）

但在视图层的 `get_queryset()` 方法中，匿名用户分支的查询没有使用这些已设置的租户信息进行过滤。

## 修复的API端点

### CMS模块（7处修复）

#### 1. CategoryViewSet.get_queryset()
- **文件**: `cms/views.py` 行 1316-1342
- **问题**: 匿名用户只过滤 `is_active=True`，未使用租户过滤
- **修复**: 添加 `tenant=current_tenant` 过滤条件

#### 2. CategoryViewSet.get_category_tree()
- **文件**: `cms/views.py` 行 1507-1560
- **问题**: 匿名分支未使用租户过滤，返回所有激活的分类树
- **修复**: 在根分类和子分类查询中都添加租户过滤

#### 3. TagGroupViewSet.get_queryset()
- **文件**: `cms/views.py` 行 1681-1707
- **问题**: 匿名用户只过滤 `is_active=True`，未使用租户过滤
- **修复**: 添加 `tenant=current_tenant` 过滤条件

#### 4. TagViewSet.get_queryset()
- **文件**: `cms/views.py` 行 1927-1953
- **问题**: 匿名用户只过滤 `is_active=True`，未使用租户过滤
- **修复**: 添加 `tenant=current_tenant` 过滤条件

#### 5. TagViewSet.get_usage_stats()
- **文件**: `cms/views.py` 行 2073-2105
- **问题**: 匿名分支只过滤 `is_active=True`，统计所有租户的标签使用
- **修复**: 添加 `tenant=current_tenant` 过滤条件

#### 6. CommentViewSet.get_queryset()
- **文件**: `cms/views.py` 行 2235-2291
- **问题**: 匿名用户只过滤 `status='approved'`，未使用租户过滤
- **修复**: 添加 `tenant=current_tenant` 过滤条件

#### 7. CommentViewSet.replies()
- **文件**: `cms/views.py` 行 2472-2494
- **问题**: 匿名分支只过滤 `status='approved'`，未使用租户过滤
- **修复**: 添加 `tenant=current_tenant` 过滤条件

## 修复方案

### 统一的修复模式

```python
from common.utils.tenant_context import get_current_tenant

# 匿名用户分支
if not user.is_authenticated:
    # 从中间件设置的租户上下文获取租户
    current_tenant = get_current_tenant()
    if current_tenant:
        # 使用租户进行过滤
        return queryset.filter(is_active=True, tenant=current_tenant)
    else:
        # 如果没有租户ID，返回空查询集
        return queryset.none()
```

### 关键点

1. **使用租户上下文**: 通过 `get_current_tenant()` 获取中间件已设置的租户
2. **空值处理**: 如果没有租户上下文，返回空查询集而不是所有数据
3. **一致性**: 所有匿名访问端点使用相同的过滤逻辑

## 其他模块检查结果

### Feedbacks模块
- `FeedbackViewSet.get_queryset()` 不允许匿名访问（返回 `queryset.none()`）
- **无需修复**

### Customers模块
- 未发现允许匿名访问的视图
- **无需修复**

## 验证测试

### 测试场景
```bash
# 测试1: 匿名用户带 X-Tenant-ID 请求分类树
curl --location 'https://backend.compressx.online/api/v1/cms/categories/tree/' \
  --header 'X-Tenant-ID: 1'
# 预期: 只返回租户1的分类树

# 测试2: 匿名用户带 X-Tenant-ID 请求标签列表
curl --location 'https://backend.compressx.online/api/v1/cms/tags/' \
  --header 'X-Tenant-ID: 2'
# 预期: 只返回租户2的激活标签

# 测试3: 匿名用户不带 X-Tenant-ID 请求
curl --location 'https://backend.compressx.online/api/v1/cms/categories/'
# 预期: 返回错误或空结果（根据权限检查器配置）
```

## 影响范围

### 功能影响
- **正面**: 确保数据隔离，匿名用户只能看到指定租户的数据
- **兼容性**: 对已认证用户无影响，仅影响匿名访问

### 性能影响
- **可忽略**: 只是添加了一个额外的过滤条件
- **优化**: 减少返回的数据量，提高查询效率

## 代码审查通过

- ✅ 无 Lint 错误
- ✅ 逻辑一致性
- ✅ 错误处理完善
- ✅ 注释清晰

## 部署建议

1. **测试环境验证**: 在测试环境中验证所有修复的端点
2. **日志监控**: 部署后监控租户过滤相关的日志
3. **回滚准备**: 保留当前版本以便必要时回滚

## 相关文档

- 租户中间件文档: `docs/multi_tenant/tenant_middleware_refactor.md`
- 租户过滤实现: `docs/tenant_filter_implementation.md`
- API 权限说明: `docs/cms/permissions.md`

