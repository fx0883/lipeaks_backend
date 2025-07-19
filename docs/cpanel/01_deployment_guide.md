# Django项目部署到cPanel指南

## 目录

1. [部署概述](01_deployment_guide.md)
2. [准备cPanel环境](02_cpanel_preparation.md)
3. [上传和配置项目代码](03_code_upload.md)
4. [配置Python环境](04_python_setup.md)
5. [数据库配置与迁移](05_database_setup.md)
6. [静态文件与媒体文件配置](06_static_media_files.md)
7. [域名配置与应用启动](07_domain_launch.md)
8. [性能优化与安全配置](08_optimization_security.md)
9. [常见问题排查](09_troubleshooting.md)
10. [维护与更新指南](10_maintenance.md)

## 部署概述

本文档系列提供了将多租户Django项目部署到cPanel托管环境的详细指南。cPanel是一个流行的Web主机控制面板，虽然它主要针对PHP应用程序，但通过适当的配置，也可以有效地部署Django应用。

### 为什么选择cPanel？

- **易于管理**：提供图形化界面，简化服务器管理
- **广泛可用**：许多共享和VPS主机提供cPanel
- **成本效益**：比专用服务器或云平台成本更低
- **一站式服务**：集成了文件管理、数据库、邮件等功能

### 部署架构

在cPanel环境中，Django项目的部署架构如下：

```
[用户请求] → [Apache/LiteSpeed] → [Passenger WSGI] → [Django应用] → [MySQL数据库]
```

- **Web服务器**：Apache或LiteSpeed（由cPanel提供）
- **WSGI接口**：Passenger（cPanel的Python应用支持）
- **应用服务器**：Django
- **数据库**：MySQL/MariaDB（由cPanel提供）

## 前提条件

在开始部署之前，请确保您具备以下条件：

### 必要条件

1. **cPanel主机账号**：
   - 支持Python应用程序功能
   - Python版本 3.9+ (推荐3.12或更高版本)
   - SSH访问权限（可选但推荐）

2. **项目准备**：
   - 完整的Django项目源代码
   - 项目已在本地或其他环境测试通过
   - 所有依赖已在requirements.txt中列出

3. **域名**：
   - 已注册的域名（或子域名）
   - DNS记录已正确配置，指向cPanel服务器

4. **技术知识**：
   - 基本的命令行操作能力
   - 了解Django项目结构
   - 基本的Git使用知识（如果使用Git部署）

### 推荐条件

1. **SSH访问**：
   - 能够通过SSH连接到服务器
   - 了解基本的Linux命令

2. **版本控制**：
   - Git仓库存储项目代码
   - cPanel Git版本控制功能访问

3. **数据库备份**：
   - 如果是迁移现有项目，准备好数据库备份

## 部署流程概述

1. **准备cPanel环境**
   - 创建数据库和数据库用户
   - 配置Python应用设置

2. **上传项目代码**
   - 通过Git或文件管理器上传代码
   - 配置项目设置和环境变量

3. **配置Python环境**
   - 创建并激活虚拟环境
   - 安装项目依赖

4. **数据库配置与迁移**
   - 配置数据库连接
   - 执行数据库迁移
   - 解决可能的字符集问题

5. **静态文件与媒体文件配置**
   - 收集静态文件
   - 配置媒体文件目录

6. **域名配置与应用启动**
   - 配置域名指向项目目录
   - 启动应用程序

7. **性能优化与安全配置**
   - 配置缓存
   - 设置HTTPS
   - 优化静态文件服务

8. **测试与验证**
   - 验证应用功能
   - 检查错误日志

在接下来的文档中，我们将详细介绍每个步骤的具体操作方法。

请继续阅读[准备cPanel环境](02_cpanel_preparation.md)以开始部署流程。 