# 租户过滤实现说明

## 概述

本系统实现了灵活的租户过滤机制，支持两种API查询方式，既保持了向后兼容性，又提供了更符合REST规范的查询参数方式。

## 支持的API查询方式

### 方式1：查询参数（推荐）
```bash
# 获取特定租户的文章
GET /api/v1/cms/articles/?tenant_id=1

# 获取特定租户的分类
GET /api/v1/cms/categories/?tenant_id=2

# 获取特定租户的标签
GET /api/v1/cms/tags/?tenant_id=3
```

### 方式2：请求头（向后兼容）
```bash
# 通过请求头指定租户
GET /api/v1/cms/articles/
# 请求头：X-Tenant-ID: 1

GET /api/v1/cms/categories/
# 请求头：X-Tenant-ID: 2
```

## 租户ID优先级

系统按照以下优先级确定最终使用的租户ID：

1. **查询参数** (`?tenant_id=1`) - 最高优先级
2. **请求头** (`X-Tenant-ID: 1`) - 中等优先级  
3. **用户关联租户** - 最低优先级

## 用户权限处理

### 超级管理员
- **可以访问所有租户的数据**：不提供租户ID时，返回所有租户数据
- **可以过滤特定租户**：通过查询参数或请求头指定租户ID
- **跨租户操作**：可以在任何租户中创建、修改、删除数据

```bash
# 查看所有租户的文章
GET /api/v1/cms/articles/

# 查看租户1的文章
GET /api/v1/cms/articles/?tenant_id=1

# 查看租户2的文章
GET /api/v1/cms/articles/?tenant_id=2
```

### 普通用户
- **只能访问自己租户的数据**：自动按用户关联的租户过滤
- **不能跨租户操作**：无法访问其他租户的资源
- **必须提供租户ID**：如果没有租户ID，返回空结果

```bash
# 普通用户只能看到自己租户的数据
GET /api/v1/cms/articles/  # 自动过滤为当前用户租户
```

### 租户管理员
- **可以访问自己租户的所有数据**：自动使用关联的租户ID
- **可以通过参数指定其他租户**：但只能在自己的权限范围内操作

## 技术实现

### 中间件层 (`TenantMiddleware`)
- **收集租户信息**：从查询参数、请求头、用户关联获取租户ID
- **设置租户上下文**：为当前线程设置租户上下文
- **传递租户信息**：将租户信息设置到request对象，供视图层使用

### 视图层 (`TenantModelViewSet`)
- **自动租户过滤**：所有继承自`TenantModelViewSet`的视图自动获得租户过滤功能
- **智能权限控制**：根据用户类型和租户信息实现不同的过滤逻辑
- **无需修改具体视图**：利用继承架构，所有子类自动获得新功能

## 使用示例

### 前端实现

#### 使用查询参数（推荐）
```javascript
// 获取所有租户的文章（超级管理员）
const response = await fetch('/api/v1/cms/articles/');

// 获取特定租户的文章
const response = await fetch('/api/v1/cms/articles/?tenant_id=1');

// 动态切换租户
function switchTenant(tenantId) {
    const url = `/api/v1/cms/articles/?tenant_id=${tenantId}`;
    // 更新页面内容
}
```

#### 使用请求头（向后兼容）
```javascript
// 设置请求头
const headers = {
    'X-Tenant-ID': '1',
    'Authorization': 'Bearer ' + token
};

const response = await fetch('/api/v1/cms/articles/', { headers });
```

### 后端视图

```python
# 不需要修改任何代码！
class ArticleViewSet(TenantModelViewSet):
    # 自动继承租户过滤功能
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

class CategoryViewSet(TenantModelViewSet):
    # 自动继承租户过滤功能
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
```

## 配置说明

### 中间件配置
确保在 `settings.py` 中启用了租户中间件：

```python
MIDDLEWARE = [
    'common.middleware.tenant_middleware.TenantMiddleware',
    # ... 其他中间件
]
```

### 视图继承
所有需要租户过滤的视图都应该继承自 `TenantModelViewSet`：

```python
from common.viewsets import TenantModelViewSet

class MyViewSet(TenantModelViewSet):
    # 自动获得租户过滤功能
    pass
```

## 调试和监控

### 日志记录
系统会记录详细的租户过滤日志，包括：
- 租户ID来源（查询参数、请求头、用户关联）
- 用户权限类型（超级管理员、普通用户、租户管理员）
- 过滤结果和操作结果

### 调试模式
可以通过设置请求头 `X-Debug-Log: true` 来获取更详细的调试信息：

```bash
GET /api/v1/cms/articles/?tenant_id=1
X-Debug-Log: true
```

## 注意事项

1. **查询参数优先级更高**：如果同时提供查询参数和请求头，系统会优先使用查询参数
2. **超级管理员权限**：超级管理员可以访问所有租户数据，但建议通过参数明确指定租户
3. **性能考虑**：查询参数方式更符合REST规范，也更容易被缓存和代理服务器处理
4. **向后兼容**：现有的 `X-Tenant-ID` 请求头方式仍然支持，不会影响现有代码

## 故障排除

### 常见问题

1. **租户ID无效**
   - 检查租户ID是否为有效整数
   - 确认租户在系统中存在且状态正常

2. **权限不足**
   - 普通用户无法访问其他租户的数据
   - 确认用户已正确关联租户

3. **查询结果为空**
   - 检查是否提供了正确的租户ID
   - 确认该租户下确实存在数据

### 调试步骤

1. 检查请求日志中的租户信息
2. 确认中间件是否正确设置了租户上下文
3. 验证视图层的过滤逻辑是否正常工作
4. 检查数据库中的租户数据是否正确

## 总结

新的租户过滤实现提供了：
- **灵活性**：支持两种API查询方式
- **易用性**：查询参数方式更符合REST规范
- **兼容性**：保持现有请求头方式的向后兼容
- **可维护性**：利用继承架构，无需修改具体视图
- **安全性**：保持现有的权限控制和安全机制

这种设计既解决了超级管理员访问系统级资源的问题，又提供了更灵活和标准的API使用方式。
