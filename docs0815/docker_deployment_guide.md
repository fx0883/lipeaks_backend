# Docker 部署指南 - 数据库快照导入功能

## 概述

本指南详细说明如何使用 Docker 部署多租户后端系统，特别是新增的数据库快照导入功能。该功能允许在容器启动时自动导入预设的数据库快照，快速初始化系统。

## 功能特性

- ✅ 自动检测数据库状态
- ✅ 条件导入数据库快照
- ✅ 智能跳过迁移步骤
- ✅ 环境变量控制开关
- ✅ 详细的日志输出
- ✅ 错误处理和回滚机制

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 10GB 可用磁盘空间

## 文件结构

```
lipeaks_backend/
├── docker-compose.yml          # Docker Compose 配置
├── Dockerfile                  # Docker 镜像构建文件
├── docker-entrypoint.sh        # 容器启动脚本（已更新）
├── docs/init_sql/
│   └── multi_tenant_db_dev.sql # 数据库快照文件
├── media/                      # 媒体文件目录
│   ├── uploads/               # 上传文件
│   └── avatars/               # 头像文件
└── requirements.txt           # Python 依赖
```

## 环境变量配置

### 必需环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_NAME` | `multi_tenant_db_dev` | 数据库名称 |
| `DB_USER` | `django` | 数据库用户名 |
| `DB_PASSWORD` | `django_password` | 数据库密码 |
| `DB_HOST` | `db` | 数据库主机 |
| `DB_PORT` | `3306` | 数据库端口 |

### 可选环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEBUG` | `True` | 调试模式 |
| `SECRET_KEY` | `your_production_secret_key_here` | Django 密钥 |
| `LOG_TO_CONSOLE` | `True` | 日志输出到控制台 |
| `CREATE_SUPERUSER` | `true` | 是否创建超级用户 |
| `SUPERUSER_USERNAME` | `admin` | 超级用户名 |
| `SUPERUSER_EMAIL` | `admin@example.com` | 超级用户邮箱 |
| `SUPERUSER_PASSWORD` | `admin_main` | 超级用户密码 |
| `IMPORT_DB_SNAPSHOT` | `false` | **数据库快照导入开关** |

## 部署步骤

### 步骤 1: 准备环境

1. **克隆项目**
   ```bash
   git clone <your-repository-url>
   cd lipeaks_backend
   ```

2. **确认文件存在**
   ```bash
   # 检查关键文件
   ls -la docker-compose.yml
   ls -la Dockerfile
   ls -la docker-entrypoint.sh
   ls -la docs/init_sql/multi_tenant_db_dev.sql
   ```

### 步骤 2: 配置环境变量

1. **创建环境变量文件（可选）**
   ```bash
   # 创建 .env 文件
   cat > .env << EOF
   DEBUG=True
   SECRET_KEY=your_production_secret_key_here
   DB_NAME=multi_tenant_db_dev
   DB_USER=django
   DB_PASSWORD=django_password
   DB_HOST=db
   DB_PORT=3306
   LOG_TO_CONSOLE=True
   CREATE_SUPERUSER=true
   SUPERUSER_USERNAME=admin
   SUPERUSER_EMAIL=admin@example.com
   SUPERUSER_PASSWORD=admin_main
   IMPORT_DB_SNAPSHOT=false
   EOF
   ```

2. **或直接在 docker-compose.yml 中设置**
   ```yaml
   environment:
     - DEBUG=True
     - SECRET_KEY=your_production_secret_key_here
     - DB_NAME=multi_tenant_db_dev
     - DB_USER=django
     - DB_PASSWORD=django_password
     - DB_HOST=db
     - DB_PORT=3306
     - LOG_TO_CONSOLE=True
     - CREATE_SUPERUSER=true
     - SUPERUSER_USERNAME=admin
     - SUPERUSER_EMAIL=admin@example.com
     - SUPERUSER_PASSWORD=admin_main
     - IMPORT_DB_SNAPSHOT=false  # 关键配置
   ```

### 步骤 3: 选择部署模式

#### 模式 A: 标准部署（推荐首次使用）

```bash
# 使用默认配置启动
docker-compose up -d
```

**特点：**
- 自动创建数据库表结构
- 执行 Django 迁移
- 创建超级用户
- 导入基础配置数据

#### 模式 B: 数据库快照导入部署

```bash
# 设置环境变量启用快照导入
export IMPORT_DB_SNAPSHOT=true

# 启动服务
docker-compose up -d
```

**特点：**
- 自动检测数据库状态
- 如果数据库为空，导入完整快照
- 跳过迁移步骤
- 包含预设的数据和配置

### 步骤 4: 监控启动过程

```bash
# 查看容器启动日志
docker-compose logs -f web

# 查看数据库容器日志
docker-compose logs -f db
```

**预期日志输出：**

**标准部署模式：**
```
等待数据库...
数据库已准备就绪!
等待数据库完全初始化...
检查是否需要导入数据库快照...
IMPORT_DB_SNAPSHOT 不为 true，跳过数据库快照导入
检查数据库是否已初始化...
× 数据库未初始化，缺少关键表
数据库未初始化，执行迁移步骤
创建迁移文件...
应用所有迁移...
...
```

**快照导入模式：**
```
等待数据库...
数据库已准备就绪!
等待数据库完全初始化...
检查是否需要导入数据库快照...
开始导入数据库快照: /app/docs/init_sql/multi_tenant_db_dev.sql
SQL文件大小: 123456 字符
执行SQL快照导入...
√ SQL快照导入成功
数据库快照导入完成
检查数据库是否已初始化...
√ 数据库已初始化，包含基础数据
数据库已初始化，跳过迁移步骤
...
```

### 步骤 5: 验证部署

1. **检查服务状态**
   ```bash
   docker-compose ps
   ```

2. **访问应用**
   - 后端 API: http://localhost:8000
   - API 文档: http://localhost:8000/api/schema/swagger-ui/
   - 管理后台: http://localhost:8000/admin/

3. **验证数据库**
   ```bash
   # 连接到数据库容器
   docker-compose exec db mysql -u django -pdjango_password multi_tenant_db_dev
   
   # 查看表
   SHOW TABLES;
   
   # 查看用户数据
   SELECT COUNT(*) FROM auth_user;
   
   # 查看租户数据
   SELECT COUNT(*) FROM tenant;
   ```

## 高级配置

### 自定义数据库快照

1. **准备新的快照文件**
   ```bash
   # 从现有数据库导出
   docker-compose exec db mysqldump -u root -ppassword multi_tenant_db_dev > docs/init_sql/my_snapshot.sql
   ```

2. **修改启动脚本**
   ```bash
   # 编辑 docker-entrypoint.sh，修改 sql_file 路径
   sql_file="/app/docs/init_sql/my_snapshot.sql"
   ```

### 生产环境配置

1. **安全配置**
   ```yaml
   environment:
     - DEBUG=False
     - SECRET_KEY=your_very_secure_secret_key
     - ALLOWED_HOSTS=your-domain.com
   ```

2. **性能优化**
   ```yaml
   environment:
     - LOG_TO_CONSOLE=False
   ```

3. **禁用快照导入**
   ```yaml
   environment:
     - IMPORT_DB_SNAPSHOT=false
   ```

## 故障排除

### 常见问题

#### 1. 数据库连接失败

**症状：** 容器启动时显示数据库连接错误

**解决方案：**
```bash
# 检查数据库容器状态
docker-compose ps db

# 重启数据库容器
docker-compose restart db

# 检查数据库日志
docker-compose logs db
```

#### 2. SQL 快照导入失败

**症状：** 显示 "SQL快照导入失败" 错误

**解决方案：**
```bash
# 检查 SQL 文件是否存在
docker-compose exec web ls -la /app/docs/init_sql/

# 检查文件权限
docker-compose exec web cat /app/docs/init_sql/multi_tenant_db_dev.sql | head -10

# 手动测试数据库连接
docker-compose exec web python -c "
import pymysql
conn = pymysql.connect(host='db', user='django', password='django_password', db='multi_tenant_db_dev')
print('数据库连接成功')
conn.close()
"
```

#### 3. 迁移冲突

**症状：** 迁移步骤报错，表已存在

**解决方案：**
```bash
# 清理数据库
docker-compose down -v
docker-compose up -d

# 或使用快照导入模式
export IMPORT_DB_SNAPSHOT=true
docker-compose up -d
```

#### 4. 媒体文件访问问题

**症状：** 上传的文件无法访问

**解决方案：**
```bash
# 检查媒体文件目录权限
docker-compose exec web ls -la /app/media/

# 重新设置权限
docker-compose exec web chmod -R 755 /app/media/

# 检查卷挂载
docker-compose exec web mount | grep media
```

### 日志分析

#### 关键日志信息

- `√ 数据库已初始化，包含基础数据` - 快照导入成功
- `× 数据库未初始化，缺少关键表` - 需要执行迁移
- `SQL快照导入成功` - 快照文件导入完成
- `数据库快照导入失败` - 需要检查 SQL 文件或数据库连接

#### 调试命令

```bash
# 查看详细启动日志
docker-compose logs web | grep -E "(数据库|SQL|迁移|错误)"

# 检查环境变量
docker-compose exec web env | grep IMPORT_DB_SNAPSHOT

# 手动执行检测
docker-compose exec web bash -c "source docker-entrypoint.sh && check_database_initialized"
```

## 维护操作

### 备份数据库

```bash
# 创建备份
docker-compose exec db mysqldump -u root -ppassword multi_tenant_db_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
docker-compose exec -T db mysql -u root -ppassword multi_tenant_db_dev < backup_file.sql
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 清理资源

```bash
# 停止所有服务
docker-compose down

# 清理数据卷（谨慎使用）
docker-compose down -v

# 清理镜像
docker-compose down --rmi all
```

## 性能优化建议

1. **数据库优化**
   - 调整 MySQL 配置参数
   - 使用 SSD 存储
   - 配置适当的连接池

2. **应用优化**
   - 启用静态文件缓存
   - 配置 CDN
   - 使用 Redis 缓存

3. **容器优化**
   - 限制资源使用
   - 配置健康检查
   - 使用多阶段构建

## 安全建议

1. **生产环境安全**
   - 使用强密码
   - 启用 HTTPS
   - 配置防火墙
   - 定期更新依赖

2. **数据安全**
   - 定期备份
   - 加密敏感数据
   - 限制数据库访问

3. **容器安全**
   - 使用非 root 用户
   - 扫描镜像漏洞
   - 限制容器权限

## 联系支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目 GitHub Issues
3. 提供详细的错误日志和环境信息

---

**文档版本：** 1.0  
**最后更新：** 2025-08-15  
**适用版本：** Django 5.2, Docker 20.10+
