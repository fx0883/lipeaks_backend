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
