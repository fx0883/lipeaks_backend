# lipeaks_backend

多租户用户管理系统后端

## 项目配置

...

## 租户验证配置

系统使用配置化的方式来确定哪些路径需要租户验证：

1. 在 `settings.py` 中通过 `TENANT_REQUIRED_PATHS` 配置需要租户验证的路径关键字:

```python
# 租户验证设置
# 只有URL路径中包含这些关键字的请求才会被租户中间件处理
TENANT_REQUIRED_PATHS = [
    'cms',  # CMS相关API
    'admin',  # 管理员API
    # 可以添加其他需要租户验证的关键字...
]
```

2. 租户中间件 (`TenantMiddleware`) 会检查请求路径中是否包含这些关键字，只有包含才会进行租户验证
3. 静态文件、媒体文件和API文档路径会自动排除，不需要进行租户验证

这种配置方式使得系统更加灵活，添加新的需要租户验证的路径时只需在 `settings.py` 中修改配置即可。

### 配置示例

以下是一些配置示例：

**只对CMS路径进行租户验证**：
```python
TENANT_REQUIRED_PATHS = ['cms']
```

**对管理员和图表路径进行租户验证**：
```python
TENANT_REQUIRED_PATHS = ['admin', 'charts']
```

**对多种资源进行租户验证**：
```python
TENANT_REQUIRED_PATHS = ['cms', 'admin', 'charts', 'orders']
```

## 媒体文件访问说明

对于 `/media/` 路径的访问，系统做了以下处理：

1. 在 TenantMiddleware 中添加了对 `/media/` 路径的排除逻辑，允许直接访问媒体文件而无需租户验证
2. 在 APIAuthMiddleware 中添加了对 `/media/` 路径的排除逻辑，确保媒体文件可以不受 JWT 认证影响
3. 其他中间件（ResponseStandardizationMiddleware、EnhancedAPILoggingMiddleware 等）已默认排除对 `/media/` 路径的处理

确保媒体文件可以正常访问，例如用户头像：`/media/avatars/{uuid}.png`

## API 文档访问

对于 API 文档路径，系统做了以下处理：

1. 在 TenantMiddleware 中添加了对 `/api/v1/schema/`, `/api/v1/docs/`, `/api/v1/redoc/` 路径的排除逻辑
2. 在 APIAuthMiddleware 中添加了对 API 文档路径的排除逻辑
3. 其他中间件已默认排除对 API 文档路径的处理

这样确保 API 文档可以正常访问，无需租户验证和认证：
- Swagger UI: `/api/v1/docs/`
- ReDoc: `/api/v1/redoc/`
- OpenAPI Schema: `/api/v1/schema/`

## 常见问题

### 问题：为什么访问某些路径会返回 400 错误？

**解决方案**：
- 检查路径是否包含在 `TENANT_REQUIRED_PATHS` 中配置的关键字
- 如果不需要租户验证，确保路径中不包含配置的关键字
- 如果需要租户验证，确保请求中包含有效的租户ID（通过X-Tenant-ID请求头或用户关联的租户）

### 问题：如何为新功能模块添加租户验证？

**解决方案**：
在 `settings.py` 中的 `TENANT_REQUIRED_PATHS` 列表中添加新模块的路径关键字。例如，如果新模块的路径是 `/api/v1/newmodule/`，只需要添加 `'newmodule'` 到列表中。

## 联系方式

