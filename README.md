# lipeaks_backend

多租户用户管理系统后端

## 项目配置

...

## 媒体文件访问说明

对于 `/media/` 路径的访问，系统做了以下处理：

1. 在 TenantMiddleware 中添加了对 `/media/` 路径的排除逻辑，允许直接访问媒体文件而无需租户验证
2. 在 APIAuthMiddleware 中添加了对 `/media/` 路径的排除逻辑，确保媒体文件可以不受 JWT 认证影响
3. 其他中间件（ResponseStandardizationMiddleware、EnhancedAPILoggingMiddleware 等）已默认排除对 `/media/` 路径的处理

确保媒体文件可以正常访问，例如用户头像：`/media/avatars/{uuid}.png`

## 联系方式

