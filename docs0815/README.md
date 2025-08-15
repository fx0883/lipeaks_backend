# 多租户后端系统 - Docker 部署文档

## 📚 文档概览

本目录包含多租户后端系统的完整 Docker 部署文档，特别是新增的数据库快照导入功能。

## 📋 文档列表

### 📚 核心文档
- **[README](./README.md)** - 文档索引和概览
- **[快速开始指南](./quick_start_guide.md)** - 一键部署，快速上手
- **[完整部署指南](./docker_deployment_guide.md)** - 详细的部署说明

### 🚀 快速开始
- **[快速开始指南](./quick_start_guide.md)** - 一键部署，快速上手
  - 标准部署模式
  - 数据库快照导入模式
  - 常用命令和故障排除

### 📖 详细指南
- **[完整部署指南](./docker_deployment_guide.md)** - 详细的部署说明
  - 系统要求和文件结构
  - 环境变量配置
  - 部署步骤详解
  - 高级配置和优化
  - 故障排除和维护

### ⚙️ 配置参考
- **[环境变量参考](./environment_variables_reference.md)** - 完整的环境变量说明
  - 数据库配置
  - Django 配置
  - 超级用户配置
  - 数据库快照导入配置
  - 安全建议和最佳实践

### 🚀 部署与发布
- **[Docker Hub 推送指南](./docker_hub_push_guide.md)** - 镜像构建与推送
  - 镜像构建和标记
  - 推送到 Docker Hub
  - 版本管理和最佳实践
  - 自动化脚本和故障排除

## 🎯 功能特性

### ✨ 新增功能
- **数据库快照导入** - 自动导入预设的数据库快照
- **智能迁移检测** - 自动检测数据库状态，智能跳过迁移
- **环境变量控制** - 通过 `IMPORT_DB_SNAPSHOT` 控制快照导入
- **详细日志输出** - 完整的启动过程日志
- **错误处理机制** - 完善的错误处理和回滚

### 🔧 核心功能
- **多租户架构** - 支持多租户数据隔离
- **RESTful API** - 完整的 API 接口
- **权限管理** - RBAC 权限系统
- **内容管理** - CMS 文章管理
- **用户管理** - 用户和成员管理
- **订单系统** - 订单和客户管理

## 🚀 快速部署

### 标准部署（推荐首次使用）

```bash
# 1. 克隆项目
git clone <your-repository-url>
cd lipeaks_backend

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f web
```

### 数据库快照导入部署

```bash
# 1. 克隆项目
git clone <your-repository-url>
cd lipeaks_backend

# 2. 设置环境变量并启动
export IMPORT_DB_SNAPSHOT=true
docker-compose up -d

# 3. 查看日志
docker-compose logs -f web
```

## 🔧 环境变量配置

### 关键环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `IMPORT_DB_SNAPSHOT` | `false` | **数据库快照导入开关** |
| `CREATE_SUPERUSER` | `true` | 是否创建超级用户 |
| `DB_NAME` | `multi_tenant_db_dev` | 数据库名称 |
| `DEBUG` | `True` | 调试模式 |

### 配置示例

```yaml
# docker-compose.yml
environment:
  - IMPORT_DB_SNAPSHOT=true  # 启用数据库快照导入
  - CREATE_SUPERUSER=true     # 创建超级用户
  - SUPERUSER_USERNAME=admin  # 超级用户名
  - SUPERUSER_PASSWORD=admin_main  # 超级用户密码
```

## 📊 部署模式对比

| 特性 | 标准部署 | 快照导入部署 |
|------|----------|--------------|
| 数据库初始化 | 执行迁移 | 导入快照 |
| 启动速度 | 较慢 | 快速 |
| 数据内容 | 空数据库 | 包含预设数据 |
| 适用场景 | 首次部署 | 快速恢复/测试 |

## 🔍 验证部署

### 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看启动日志
docker-compose logs web | grep -E "(数据库|SQL|迁移|错误)"
```

### 访问应用

- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/schema/swagger-ui/
- **管理后台**: http://localhost:8000/admin/
- **默认超级用户**: admin / admin_main

## 🛠️ 常用操作

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f web
```

### 数据库操作

```bash
# 备份数据库
docker-compose exec db mysqldump -u root -ppassword multi_tenant_db_dev > backup.sql

# 恢复数据库
docker-compose exec -T db mysql -u root -ppassword multi_tenant_db_dev < backup.sql

# 连接数据库
docker-compose exec db mysql -u django -pdjango_password multi_tenant_db_dev
```

### 故障排除

```bash
# 清理数据重新开始
docker-compose down -v
docker-compose up -d

# 重新构建镜像
docker-compose build --no-cache

# 检查环境变量
docker-compose exec web env | grep IMPORT_DB_SNAPSHOT
```

## 📝 更新日志

### v1.0 (2025-08-15)
- ✅ 新增数据库快照导入功能
- ✅ 智能迁移检测和跳过
- ✅ 环境变量控制开关
- ✅ 详细的日志输出
- ✅ 完善的错误处理
- ✅ 完整的部署文档

## 🤝 技术支持

如果在部署过程中遇到问题：

1. **查看文档** - 先查看本文档的故障排除部分
2. **检查日志** - 使用 `docker-compose logs web` 查看详细日志
3. **验证配置** - 确认环境变量和配置文件正确
4. **联系支持** - 提供详细的错误日志和环境信息

## 📞 联系方式

- **项目仓库**: [GitHub Repository]
- **问题反馈**: [GitHub Issues]
- **文档更新**: 本文档会随项目更新

---

**文档版本**: 1.0  
**最后更新**: 2025-08-15  
**适用版本**: Django 5.2, Docker 20.10+
