# 快速开始指南

## 一键部署

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

#### Linux/macOS 用户
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

#### Windows 用户
```powershell
# 1. 克隆项目
git clone <your-repository-url>
cd lipeaks_backend

# 2. 设置环境变量并启动
$env:IMPORT_DB_SNAPSHOT="true"
docker-compose up -d

# 3. 查看日志
docker-compose logs -f web
```

#### 或者使用 .env 文件（推荐）
```bash
# 1. 克隆项目
git clone <your-repository-url>
cd lipeaks_backend

# 2. 创建 .env 文件
echo IMPORT_DB_SNAPSHOT=true > .env

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f web
```

## 🚀 Docker 更新操作指南

### 更新策略概览

在 Docker 环境中更新应用有多种方式，根据您的需求选择合适的策略：

| 更新类型 | 适用场景 | 影响范围 | 操作复杂度 |
|----------|----------|----------|------------|
| **代码更新** | 修复 Bug、功能增强 | 应用代码 | 低 |
| **镜像更新** | 系统依赖、安全补丁 | 整个容器 | 中 |
| **数据库更新** | 数据结构变更 | 数据库 | 高 |
| **完整重建** | 重大版本升级 | 所有组件 | 高 |

### 🔄 代码更新（推荐日常使用）

#### 方法 1: 热更新（无需重启）
```bash
# 1. 停止 web 服务
docker-compose stop web

# 2. 重新构建并启动
docker-compose up -d --build web

# 3. 查看更新日志
docker-compose logs -f web
```

#### 方法 2: 完整重建
```bash
# 1. 停止所有服务
docker-compose down

# 2. 重新构建并启动
docker-compose up -d --build

# 3. 查看启动日志
docker-compose logs -f web
```

### 🐳 镜像更新

#### 更新 Docker 镜像
```bash
# 1. 拉取最新镜像
docker-compose pull

# 2. 重新构建本地镜像
docker-compose build --no-cache

# 3. 重启服务
docker-compose up -d

# 4. 验证更新
docker-compose ps
```

#### 强制重新构建
```bash
# 1. 清理所有镜像和容器
docker-compose down --rmi all --volumes --remove-orphans

# 2. 重新构建所有镜像
docker-compose build --no-cache

# 3. 启动服务
docker-compose up -d
```

### 🗄️ 数据库更新

#### 安全更新（推荐生产环境）
```bash
# 1. 备份当前数据库
docker-compose exec db mysqldump -u django -pdjango_password multi_tenant_db_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 停止 web 服务
docker-compose stop web

# 3. 应用数据库迁移
docker-compose run --rm web python manage.py migrate

# 4. 重启 web 服务
docker-compose up -d web

# 5. 验证数据库状态
docker-compose exec web python manage.py showmigrations
```

#### 快速更新（开发环境）
```bash
# 1. 应用所有迁移
docker-compose exec web python manage.py migrate

# 2. 检查迁移状态
docker-compose exec web python manage.py showmigrations

# 3. 验证应用状态
docker-compose exec web python manage.py check
```

### 🔧 环境变量更新

#### 更新 .env 文件
```bash
# 1. 编辑 .env 文件
# 修改相关环境变量

# 2. 重启服务以应用新配置
docker-compose restart web

# 3. 验证环境变量
docker-compose exec web env | grep IMPORT_DB_SNAPSHOT
```

#### 更新 docker-compose.yml
```bash
# 1. 修改 docker-compose.yml 文件
# 更新 environment 部分

# 2. 重新构建并启动
docker-compose up -d --build

# 3. 验证配置
docker-compose config
```

### 📦 依赖更新

#### 更新 Python 依赖
```bash
# 1. 更新 requirements.txt 文件
# 修改版本号或添加新依赖

# 2. 重新构建镜像
docker-compose build --no-cache web

# 3. 重启服务
docker-compose up -d web

# 4. 验证依赖
docker-compose exec web pip list
```

#### 更新系统依赖
```bash
# 1. 修改 Dockerfile
# 更新系统包或添加新工具

# 2. 重新构建镜像
docker-compose build --no-cache web

# 3. 重启服务
docker-compose up -d web
```

### 🚨 紧急回滚

#### 快速回滚到上一个版本
```bash
# 1. 查看可用镜像
docker images lipeaks_backend

# 2. 回滚到指定版本
docker-compose down
docker tag lipeaks_backend:previous_version lipeaks_backend:latest
docker-compose up -d

# 3. 验证回滚
docker-compose logs web
```

#### 数据库回滚
```bash
# 1. 停止 web 服务
docker-compose stop web

# 2. 恢复数据库备份
docker-compose exec -T db mysql -u django -pdjango_password multi_tenant_db_dev < backup_file.sql

# 3. 重启 web 服务
docker-compose up -d web
```

### ✅ 更新后验证

#### 基础功能验证

##### Linux/macOS 用户
```bash
# 1. 检查服务状态
docker-compose ps

# 2. 检查应用日志
docker-compose logs web | tail -20

# 3. 测试 API 端点
curl -I http://localhost:8000/api/schema/swagger-ui/

# 4. 验证管理后台
curl -I http://localhost:8000/admin/
```

##### Windows 用户
```powershell
# 1. 检查服务状态
docker-compose ps

# 2. 检查应用日志
docker-compose logs web | Select-Object -Last 20

# 3. 测试 API 端点
Invoke-WebRequest -Uri "http://localhost:8000/api/schema/swagger-ui/" -Method Head

# 4. 验证管理后台
Invoke-WebRequest -Uri "http://localhost:8000/admin/" -Method Head
```

#### 数据库验证

##### Linux/macOS 用户
```bash
# 1. 检查数据库连接
docker-compose exec web python -c "
import pymysql
conn = pymysql.connect(host='db', user='django', password='django_password', db='multi_tenant_db_dev')
print('数据库连接成功')
conn.close()
"

# 2. 检查迁移状态
docker-compose exec web python manage.py showmigrations

# 3. 验证数据完整性
docker-compose exec db mysql -u django -pdjango_password multi_tenant_db_dev -e "SELECT COUNT(*) FROM user;"
```

##### Windows 用户
```powershell
# 1. 检查数据库连接
docker-compose exec web python -c "
import pymysql
conn = pymysql.connect(host='db', user='django', password='django_password', db='multi_tenant_db_dev')
print('数据库连接成功')
conn.close()
"

# 2. 检查迁移状态
docker-compose exec web python manage.py showmigrations

# 3. 验证数据完整性
docker-compose exec db mysql -u django -pdjango_password multi_tenant_db_dev -e "SELECT COUNT(*) FROM user;"
```

### 📋 更新检查清单

#### 更新前检查
- [ ] 备份重要数据
- [ ] 记录当前版本信息
- [ ] 确认更新内容
- [ ] 准备回滚方案

#### 更新中检查
- [ ] 监控构建过程
- [ ] 检查错误日志
- [ ] 验证服务启动
- [ ] 确认功能正常

#### 更新后检查
- [ ] 验证所有功能
- [ ] 检查性能指标
- [ ] 更新文档
- [ ] 通知相关人员

### 🎯 常见更新场景

#### 日常开发更新

##### Linux/macOS 用户
```bash
# 快速代码更新
git pull origin main
docker-compose up -d --build web
```

##### Windows 用户
```powershell
# 快速代码更新
git pull origin main
docker-compose up -d --build web
```

#### 版本发布更新

##### Linux/macOS 用户
```bash
# 完整版本更新
git checkout v1.2.0
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

##### Windows 用户
```powershell
# 完整版本更新
git checkout v1.2.0
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 安全补丁更新

##### Linux/macOS 用户
```bash
# 紧急安全更新
docker-compose pull
docker-compose up -d --build
docker-compose exec web python manage.py check --deploy
```

##### Windows 用户
```powershell
# 紧急安全更新
docker-compose pull
docker-compose up -d --build
docker-compose exec web python manage.py check --deploy
```

### 🔧 高级更新技巧

#### 零停机更新
```bash
# 1. 构建新镜像
docker-compose build web

# 2. 启动新容器（不同端口）
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d web

# 3. 健康检查通过后，切换流量
# 4. 停止旧容器
docker-compose stop web
```

#### 蓝绿部署
```bash
# 1. 创建生产环境副本
cp docker-compose.yml docker-compose.prod.yml

# 2. 在副本中部署新版本
docker-compose -f docker-compose.prod.yml up -d --build

# 3. 验证新版本
# 4. 切换生产流量
# 5. 清理旧版本
```

#### 滚动更新
```bash
# 1. 逐个更新服务实例
docker-compose up -d --no-deps --build web

# 2. 等待服务就绪
docker-compose exec web python manage.py check

# 3. 更新下一个实例
# 4. 重复直到所有实例更新完成
```

### 🚨 故障排除

#### 更新失败处理
```bash
# 1. 查看详细错误日志
docker-compose logs web --tail=100

# 2. 检查容器状态
docker-compose ps -a

# 3. 进入容器调试
docker-compose exec web bash

# 4. 手动执行命令
docker-compose exec web python manage.py check
```

#### 回滚操作
```bash
# 1. 停止当前服务
docker-compose down

# 2. 恢复到上一个版本
git checkout HEAD~1

# 3. 重新构建并启动
docker-compose up -d --build

# 4. 验证回滚成功
docker-compose logs web
```

#### 数据恢复
```bash
# 1. 停止所有服务
docker-compose down

# 2. 恢复数据库备份
docker-compose run --rm db mysql -u django -pdjango_password multi_tenant_db_dev < backup.sql

# 3. 重新启动服务
docker-compose up -d

# 4. 验证数据完整性
docker-compose exec web python manage.py check
```

---

## 环境变量配置

### 🔧 IMPORT_DB_SNAPSHOT 详解

`IMPORT_DB_SNAPSHOT` 是一个关键的环境变量，用于控制数据库快照导入功能：

#### 作用说明
- **`IMPORT_DB_SNAPSHOT=true`**: 启用数据库快照导入
  - 容器启动时自动检测数据库状态
  - 如果数据库为空，自动导入 `docs/init_sql/multi_tenant_db_dev.sql` 文件
  - 导入完成后跳过 Django 迁移步骤
  - 快速初始化包含预设数据的完整系统

- **`IMPORT_DB_SNAPSHOT=false`** (默认): 禁用数据库快照导入
  - 执行标准的 Django 迁移流程
  - 创建空的数据库表结构
  - 需要手动导入数据或通过迁移填充

#### 配置位置

**位置 1: docker-compose.yml 文件（推荐）**
```yaml
version: '3.8'
services:
  web:
    # ... 其他配置
    environment:
      # ... 其他环境变量
      - IMPORT_DB_SNAPSHOT=true  # 启用数据库快照导入
```

**位置 2: .env 文件**
```bash
# 在项目根目录创建 .env 文件
IMPORT_DB_SNAPSHOT=true
```

**位置 3: 命令行环境变量**
```bash
# Linux/macOS
export IMPORT_DB_SNAPSHOT=true

# Windows PowerShell
$env:IMPORT_DB_SNAPSHOT="true"
```

#### 配置优先级（从高到低）
1. 命令行环境变量
2. .env 文件
3. docker-compose.yml 中的 environment 配置
4. 默认值 (false)

### 在 docker-compose.yml 中设置

```yaml
environment:
  - IMPORT_DB_SNAPSHOT=true  # 启用数据库快照导入
  - CREATE_SUPERUSER=true     # 创建超级用户
  - SUPERUSER_USERNAME=admin  # 超级用户名
  - SUPERUSER_PASSWORD=admin_main  # 超级用户密码
```

### 使用 .env 文件

#### Linux/macOS 用户
```bash
# 创建 .env 文件
cat > .env << EOF
IMPORT_DB_SNAPSHOT=true
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=admin_main
EOF

# 启动服务
docker-compose up -d
```

#### Windows 用户
```powershell
# 创建 .env 文件
@"
IMPORT_DB_SNAPSHOT=true
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=admin_main
"@ | Out-File -FilePath .env -Encoding UTF8

# 启动服务
docker-compose up -d
```

#### 或者手动创建
```bash
# 在项目根目录创建 .env 文件，内容如下：
IMPORT_DB_SNAPSHOT=true
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=admin_main
```

### 📋 配置示例对比

#### 示例 1: 启用数据库快照导入（快速部署）
```yaml
# docker-compose.yml
environment:
  - IMPORT_DB_SNAPSHOT=true    # 启用快照导入
  - CREATE_SUPERUSER=true       # 创建超级用户
  - DEBUG=True                  # 调试模式
```

**特点：**
- ✅ 快速启动，包含预设数据
- ✅ 跳过迁移步骤
- ✅ 适合测试和快速部署
- ⚠️ 会覆盖现有数据库

#### 示例 2: 禁用数据库快照导入（标准部署）
```yaml
# docker-compose.yml
environment:
  - IMPORT_DB_SNAPSHOT=false   # 禁用快照导入
  - CREATE_SUPERUSER=true       # 创建超级用户
  - DEBUG=True                  # 调试模式
```

**特点：**
- ✅ 执行标准 Django 迁移
- ✅ 创建干净的数据库结构
- ✅ 适合生产环境
- ⚠️ 启动时间较长

## 🎯 部署模式选择

### 模式 A: 数据库快照导入模式（推荐测试/快速部署）
```bash
# 配置: IMPORT_DB_SNAPSHOT=true
# 特点: 快速启动，包含预设数据，跳过迁移
# 适用: 开发测试、快速演示、数据恢复

# 启动命令
docker-compose up -d

# 预期日志
# 1. 等待数据库准备就绪
# 2. 检查是否需要导入数据库快照
# 3. 开始导入数据库快照
# 4. SQL快照导入成功
# 5. 数据库已初始化，跳过迁移步骤
```

### 模式 B: 标准迁移模式（推荐生产环境）
```bash
# 配置: IMPORT_DB_SNAPSHOT=false 或未设置
# 特点: 执行完整迁移，创建干净数据库
# 适用: 生产环境、首次部署、数据迁移

# 启动命令
docker-compose up -d

# 预期日志
# 1. 等待数据库准备就绪
# 2. 检查是否需要导入数据库快照
# 3. IMPORT_DB_SNAPSHOT 不为 true，跳过数据库快照导入
# 4. 数据库未初始化，执行迁移步骤
# 5. 创建迁移文件...
# 6. 应用所有迁移...
```

### 🔍 如何选择部署模式？

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| **开发测试** | 快照导入模式 | 快速启动，包含测试数据 |
| **快速演示** | 快照导入模式 | 立即可用，无需等待 |
| **生产环境** | 标准迁移模式 | 数据安全，完整迁移 |
| **首次部署** | 标准迁移模式 | 建立干净的数据库结构 |
| **数据恢复** | 快照导入模式 | 快速恢复预设数据 |

## 验证部署

```bash
# 检查服务状态
docker-compose ps

# 访问应用
# 在浏览器中打开: http://localhost:8000/api/schema/swagger-ui/

# 检查数据库
docker-compose exec db mysql -u django -pdjango_password multi_tenant_db_dev -e "SHOW TABLES;"
```

### Windows 用户注意事项

在 Windows 中，某些命令可能需要调整：

```powershell
# 检查服务状态
docker-compose ps

# 使用浏览器访问应用
Start-Process "http://localhost:8000/api/schema/swagger-ui/"

# 检查数据库
docker-compose exec db mysql -u django -pdjango_password multi_tenant_db_dev -e "SHOW TABLES;"
```

## 常用命令

### 基础服务管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f web

# 重启服务
docker-compose restart

# 清理数据
docker-compose down -v

# 重新构建
docker-compose build --no-cache
```

### Windows PowerShell 兼容命令
```powershell
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志（实时跟踪）
docker-compose logs -f web

# 重启服务
docker-compose restart

# 清理数据
docker-compose down -v

# 重新构建
docker-compose build --no-cache
```

## 故障排除

### 快速诊断

#### Linux/macOS 用户
```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs web | grep -i error

# 检查数据库连接
docker-compose exec web python -c "
import pymysql
conn = pymysql.connect(host='db', user='django', password='django_password', db='multi_tenant_db_dev')
print('数据库连接成功')
conn.close()
"
```

#### Windows 用户
```powershell
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs web | Select-String -Pattern "error" -CaseSensitive:$false

# 检查数据库连接
docker-compose exec web python -c "
import pymysql
conn = pymysql.connect(host='db', user='django', password='django_password', db='multi_tenant_db_dev')
print('数据库连接成功')
conn.close()
"
```

### 常见问题

#### 通用问题
1. **数据库连接失败**
   ```bash
   docker-compose restart db
   ```

2. **迁移冲突**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

3. **权限问题**
   ```bash
   docker-compose exec web chmod -R 755 /app/media/
   ```

#### Windows 特定问题
1. **PowerShell 执行策略限制**
   ```powershell
   # 检查执行策略
   Get-ExecutionPolicy
   
   # 临时允许脚本执行
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **路径问题**
   ```powershell
   # 使用正斜杠或双反斜杠
   cd D:\GitHub\lipeaks_backend
   # 或者
   cd "D:\GitHub\lipeaks_backend"
   ```

3. **环境变量设置失败**
   ```powershell
   # 检查环境变量
   $env:IMPORT_DB_SNAPSHOT
   
   # 重新设置
   $env:IMPORT_DB_SNAPSHOT="true"
   ```

#### IMPORT_DB_SNAPSHOT 相关问题
1. **快照导入失败**
   ```bash
   # 检查 SQL 文件是否存在
   ls -la docs/init_sql/multi_tenant_db_dev.sql
   
   # 检查文件权限
   docker-compose exec web ls -la /app/docs/init_sql/
   
   # 查看详细错误日志
   docker-compose logs web | grep -i "快照\|SQL\|错误"
   ```

2. **环境变量未生效**
   ```bash
   # 检查容器内的环境变量
   docker-compose exec web env | grep IMPORT_DB_SNAPSHOT
   
   # 重新构建并启动
   docker-compose down
   docker-compose up -d --build
   ```

3. **数据库状态检测问题**
   ```bash
   # 手动检查数据库状态
   docker-compose exec web python -c "
   import pymysql
   conn = pymysql.connect(host='db', user='django', password='django_password', db='multi_tenant_db_dev')
   cursor = conn.cursor()
   cursor.execute('SHOW TABLES')
   tables = cursor.fetchall()
   print(f'数据库表数量: {len(tables)}')
   conn.close()
   "
   ```

## 访问地址

- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/schema/swagger-ui/
- **管理后台**: http://localhost:8000/admin/
- **默认超级用户**: admin / admin_main

## Windows 兼容性说明

### PowerShell 环境变量
在 Windows PowerShell 中，环境变量使用 `$env:` 前缀：
```powershell
# 设置环境变量
$env:IMPORT_DB_SNAPSHOT="true"

# 查看环境变量
$env:IMPORT_DB_SNAPSHOT

# 清除环境变量
Remove-Item Env:IMPORT_DB_SNAPSHOT
```

### 推荐使用 .env 文件
为了避免 PowerShell 环境变量设置的复杂性，推荐使用 `.env` 文件：
```bash
# 创建 .env 文件（跨平台兼容）
IMPORT_DB_SNAPSHOT=true
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=admin_main
```

### 命令兼容性
- `docker-compose` 命令在所有平台都相同
- 日志查看命令在所有平台都相同
- 环境变量设置方式因平台而异

## ✅ 快速配置检查清单

在启动服务前，请确认以下配置：

### 🔧 必需文件检查
- [ ] `docker-compose.yml` 文件存在
- [ ] `Dockerfile` 文件存在
- [ ] `docs/init_sql/multi_tenant_db_dev.sql` 文件存在（如果使用快照导入）

### ⚙️ 环境变量配置检查
- [ ] `IMPORT_DB_SNAPSHOT` 已正确设置
- [ ] 数据库连接参数已配置
- [ ] 超级用户参数已配置

### 🐳 Docker 环境检查
- [ ] Docker Desktop 已启动
- [ ] Docker Compose 可用
- [ ] 端口 8000 和 3306 未被占用

### 📋 启动命令
```bash
# 标准启动
docker-compose up -d

# 查看启动日志
docker-compose logs -f web

# 检查服务状态
docker-compose ps
```

---

**更多详细信息请参考**: [完整部署指南](./docker_deployment_guide.md)

## 📚 Docker 更新命令快速参考

### 🔄 常用更新命令

| 操作 | Linux/macOS | Windows PowerShell | 说明 |
|------|-------------|-------------------|------|
| **代码更新** | `docker-compose up -d --build web` | `docker-compose up -d --build web` | 重新构建并启动 web 服务 |
| **完整重建** | `docker-compose up -d --build` | `docker-compose up -d --build` | 重新构建所有服务 |
| **强制重建** | `docker-compose build --no-cache` | `docker-compose build --no-cache` | 不使用缓存重新构建 |
| **重启服务** | `docker-compose restart web` | `docker-compose restart web` | 重启指定服务 |
| **停止服务** | `docker-compose stop web` | `docker-compose stop web` | 停止指定服务 |
| **启动服务** | `docker-compose start web` | `docker-compose start web` | 启动指定服务 |
| **查看日志** | `docker-compose logs -f web` | `docker-compose logs -f web` | 实时查看服务日志 |
| **检查状态** | `docker-compose ps` | `docker-compose ps` | 查看所有服务状态 |

### 🗄️ 数据库操作命令

| 操作 | 命令 | 说明 |
|------|------|------|
| **应用迁移** | `docker-compose exec web python manage.py migrate` | 应用数据库迁移 |
| **检查迁移** | `docker-compose exec web python manage.py showmigrations` | 查看迁移状态 |
| **创建迁移** | `docker-compose exec web python manage.py makemigrations` | 创建新的迁移文件 |
| **备份数据库** | `docker-compose exec db mysqldump -u django -pdjango_password multi_tenant_db_dev > backup.sql` | 备份数据库 |
| **恢复数据库** | `docker-compose exec -T db mysql -u django -pdjango_password multi_tenant_db_dev < backup.sql` | 恢复数据库 |

### 🔧 环境变量和配置

| 操作 | 命令 | 说明 |
|------|------|------|
| **查看环境变量** | `docker-compose exec web env` | 查看容器内的环境变量 |
| **验证配置** | `docker-compose config` | 验证 docker-compose.yml 配置 |
| **拉取镜像** | `docker-compose pull` | 拉取最新的镜像 |
| **清理资源** | `docker-compose down --rmi all --volumes` | 清理所有镜像和卷 |

### 🚨 故障排除命令

| 问题 | 命令 | 说明 |
|------|------|------|
| **查看错误日志** | `docker-compose logs web --tail=100` | 查看最近的错误日志 |
| **进入容器** | `docker-compose exec web bash` | 进入 web 容器进行调试 |
| **检查应用状态** | `docker-compose exec web python manage.py check` | 检查 Django 应用状态 |
| **查看容器资源** | `docker stats` | 查看容器资源使用情况 |

### 📋 更新流程检查清单

#### 更新前准备
- [ ] 备份数据库
- [ ] 记录当前版本
- [ ] 确认更新内容
- [ ] 准备回滚方案

#### 更新执行
- [ ] 停止相关服务
- [ ] 备份重要数据
- [ ] 执行更新操作
- [ ] 启动服务
- [ ] 验证功能

#### 更新后验证
- [ ] 检查服务状态
- [ ] 验证核心功能
- [ ] 测试关键 API
- [ ] 检查日志
- [ ] 更新文档

---

**💡 提示**: 在生产环境中执行更新操作前，请务必进行充分的测试和备份！

## 🔧 租户中间件修改说明

### 🚨 问题描述

在原始版本中，访问 `http://localhost:8000/admin/cms/category/` 会出现以下错误：

```json
{
    "success": false,
    "code": 4001,
    "message": "未提供租户ID，无法访问CMS资源",
    "data": null
}
```

这是因为租户中间件错误地将Admin路径当作需要租户验证的API路径处理。

### ✅ 解决方案

已修改 `common/middleware/tenant_middleware.py`，实现了精确的路径判断逻辑：

#### 修改前（问题代码）
```python
# 从settings获取需要租户验证的路径关键字
tenant_required_paths = getattr(settings, 'TENANT_REQUIRED_PATHS', ['cms'])

# 检查当前路径是否需要租户验证
path_requires_tenant = False
for path_keyword in tenant_required_paths:
    if path_keyword in request.path:  # 过于宽泛的匹配
        path_requires_tenant = True
        break
```

#### 修改后（解决方案）
```python
def requires_tenant_verification(self, path):
    """判断路径是否需要租户验证"""
    # Admin路径不需要租户验证（由Django Admin自己处理）
    if path.startswith('/admin/'):
        return False
    
    # 静态资源不需要租户验证
    if path.startswith(('/static/', '/media/')):
        return False
    
    # API文档不需要租户验证
    if path.startswith(('/api/v1/schema/', '/api/v1/docs/', '/api/v1/redoc/')):
        return False
    
    # 只对真正的API路径进行租户验证
    api_prefixes = ['/api/', '/cms/', '/customers/', '/orders/']
    return any(path.startswith(prefix) for prefix in api_prefixes)
```

### 🎯 修改效果

#### ✅ 现在可以正常访问
- **Admin主页面**: `http://localhost:8000/admin/`
- **CMS管理**: `http://localhost:8000/admin/cms/category/`
- **菜单管理**: `http://localhost:8000/admin/menus/menu/`
- **客户管理**: `http://localhost:8000/admin/customers/customer/`

#### 🔒 仍然需要租户验证
- **CMS API**: `http://localhost:8000/api/v1/cms/categories/`
- **客户API**: `http://localhost:8000/api/v1/customers/customers/`
- **订单API**: `http://localhost:8000/api/v1/orders/orders/`

#### 🌐 不需要租户验证
- **API文档**: `http://localhost:8000/api/v1/docs/`
- **静态资源**: `/static/`, `/media/`
- **Admin界面**: 所有 `/admin/` 路径

### 🔍 技术原理

#### 路径分类处理
1. **Admin路径** (`/admin/*`): 由Django Admin自己处理认证和权限
2. **API路径** (`/api/*`, `/cms/*`, `/customers/*`, `/orders/*`): 需要租户验证
3. **静态资源** (`/static/*`, `/media/*`): 直接访问，无需验证
4. **文档路径** (`/api/v1/docs/*`): 公开访问，无需验证

#### 中间件执行顺序
```
请求 → 租户中间件 → 路径判断 → 跳过/验证 → Django Admin/API视图
```

### 🚀 使用建议

1. **Admin管理**: 直接通过浏览器访问 `/admin/` 路径
2. **API调用**: 需要提供 `X-Tenant-ID` 请求头
3. **超级管理员**: 可以通过 `X-Tenant-ID` 指定操作租户
4. **开发调试**: 使用 `/api/v1/docs/` 查看API文档

### 📝 注意事项

- 修改不影响现有的API租户验证逻辑
- 所有Admin功能现在都可以正常使用
- 菜单管理等公共功能不受租户限制
- 保持了系统的安全性和多租户隔离
