# LiPeaks Backend 部署到 cPanel 完整指南

> 日期：2026-07-11
> 适用版本：Django 6.0 + DRF + MySQL +（可选）Celery/Redis
> 目标环境：cPanel 共享主机 / 商业主机（支持 Python App + MySQL + SSH）

## 本文档目标

把 `lipeaks_backend` 项目部署到 cPanel 环境，使其可通过域名访问 API，并稳定运行多租户 CMS 服务。

## 部署前准备

### 1. cPanel 环境要求

| 组件 | 要求 | 说明 |
|------|------|------|
| Python | 3.11 / 3.12 / 3.13 | 项目使用 Python 3.13 开发，建议 3.12+ |
| Web 服务器 | Apache + Passenger | cPanel 默认使用 Phusion Passenger 运行 Python App |
| 数据库 | MySQL 8 | 与项目 `PyMySQL` 驱动兼容 |
| 缓存/队列 | 可选 | 共享主机通常**没有 Redis**，需关闭 Celery |
| SSH 访问 | 需要 | 用于执行 `pip`、`migrate`、`collectstatic` |
| 域名/子域名 | 需要 | 例如 `api.yourdomain.com` |

### 2. 本地准备

确保以下文件已正确配置并随代码一起上传：

- `passenger_wsgi.py`（已存在，用于 cPanel Passenger）
- `core/wsgi.py`（已包含 cPanel 编码修复）
- `requirements.txt`（已包含 `whitenoise`、`gunicorn`）
- `.env` 或 `.env.prod`（**部署前必须修改**，见下文）

---

## 部署流程概览

```
1. 创建 MySQL 数据库和用户
2. 上传代码到 cPanel
3. 创建 Python Application
4. 配置环境变量（.env）
5. 安装依赖
6. 运行数据库迁移
7. 收集静态文件
8. 创建超级管理员
9. 重启 Python App
10. 验证部署
```

### 快捷方式：一键部署脚本

项目已提供一键部署脚本 [`scripts/deploy_cpanel.sh`](../../scripts/deploy_cpanel.sh)，首次部署或后续更新均可使用：

```bash
# 首次部署（创建目录、执行完整初始化）
./scripts/deploy_cpanel.sh --setup

# 后续更新（拉取代码、安装依赖、迁移、重启）
./scripts/deploy_cpanel.sh --branch main

# 只执行迁移和重启，不拉代码
./scripts/deploy_cpanel.sh --skip-pull
```

详细用法：

```bash
./scripts/deploy_cpanel.sh --help
```

---

## 步骤 1：创建 MySQL 数据库和用户

1. 登录 cPanel，进入 **MySQL® 数据库向导** 或 **MySQL 数据库**。
2. 创建数据库：
   - 数据库名：`yourcpanel_lipeaks_db`
   - 记下完整名称（cPanel 会自动加前缀）
3. 创建数据库用户：
   - 用户名：`yourcpanel_lipeaks_user`
   - 密码：使用强密码（建议 16 位以上，包含大小写+数字+符号）
4. 将用户添加到数据库，勾选 **所有权限**。
5. 记录以下信息：
   - DB_NAME
   - DB_USER
   - DB_PASSWORD
   - DB_HOST（通常是 `localhost`）
   - DB_PORT（通常是 `3306`）

> 注意：cPanel 共享主机的 MySQL 主机名通常是 `localhost`，不是 IP 地址。

---

## 步骤 2：上传代码到 cPanel

### 方案 A：通过 Git 克隆（推荐）

1. 进入 cPanel → **Git™ 版本控制**。
2. 克隆仓库到目标目录，例如：
   ```
   /home/yourcpanel/lipeaks_backend
   ```
3. 确保当前分支为要部署的分支（如 `main` 或 `workbuddy0629`）。

### 方案 B：通过 FTP/SFTP 上传

1. 将本地项目打包为 `.zip`。
2. 通过 cPanel **文件管理器** 上传到 `/home/yourcpanel/` 并解压。
3. 确保文件权限正确：
   - 目录：`755`
   - 文件：`644`
   - `.env` 文件：`600`（仅所有者可读写）

### 目录结构示例

```
/home/yourcpanel/lipeaks_backend/
├── common/
├── core/
├── cms/
├── users/
├── manage.py
├── passenger_wsgi.py
├── requirements.txt
├── .env
├── staticfiles/          # 自动生成
├── media/                # 用户上传文件
└── logs/                 # 日志目录
```

---

## 步骤 3：创建 Python Application

1. 进入 cPanel → **Setup Python App**（或 **Select Python Version**）。
2. 点击 **Create Application**：
   - **Python version**：选择 `3.12` 或 `3.13`
   - **Application root**：`lipeaks_backend`
   - **Application URL**：选择你的域名或子域名，例如 `api.yourdomain.com`
   - **Application startup file**：`passenger_wsgi.py`
   - **Application Entry point**：`application`
3. 点击 **Create**。

### 关于 Application URL 的选择

| 场景 | 推荐配置 |
|------|----------|
| 独立子域名 | `api.yourdomain.com`，根目录指向 `lipeaks_backend` |
| 子目录 | `yourdomain.com/api`，但会多一层路径前缀，需前端配合 |
| 主域名 | `yourdomain.com`，适合只部署后端 |

---

## 步骤 4：配置环境变量

项目通过 `python-dotenv` 读取 `.env` 文件。**必须**在部署前创建或修改 `.env`。

项目已提供干净的生产环境模板 [`.env.prod.example`](../../.env.prod.example)，可直接复制使用：

```bash
cd /home/yourcpanel/lipeaks_backend
cp .env.prod.example .env.prod
# 或命名为 .env（两者均可，优先级由 python-dotenv 决定）
cp .env.prod.example .env
```

### 4.1 创建生产环境 .env 文件

在项目根目录创建 `.env`：

```bash
cd /home/yourcpanel/lipeaks_backend
nano .env
```

填入以下内容（**根据你的实际环境修改**）：

```env
# 数据库配置
DB_NAME=yourcpanel_lipeaks_db
DB_USER=yourcpanel_lipeaks_user
DB_PASSWORD=your_strong_password_here
DB_HOST=localhost
DB_PORT=3306

# Django 密钥（必须修改，且保密）
SECRET_KEY=your-very-long-random-secret-key-at-least-50-chars

# 调试模式（生产环境必须关闭）
# 注意：项目从 INFO 环境变量读取 DEBUG，而不是 DEBUG 变量
INFO=False
LOG_TO_CONSOLE=False

# 允许的主机（生产环境必须限制）
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com,localhost,127.0.0.1

# Redis / Celery
# cPanel 共享主机通常没有 Redis，必须关闭 Celery，任务会同步执行
CELERY_ENABLED=false

# 邮件配置（可选，用于密码重置等功能）
EMAIL_USE_CONSOLE=false
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_app_password
DEFAULT_FROM_EMAIL=your_email@example.com

# 微信小程序配置（如需使用）
WECHAT_APPID=your_wechat_appid
WECHAT_SECRET=your_wechat_secret

# 站点 URL
SITE_URL=https://api.yourdomain.com
FRONTEND_URL=https://admin.yourdomain.com
```

### 4.2 设置 .env 文件权限

```bash
chmod 600 /home/yourcpanel/lipeaks_backend/.env
```

### 4.3 生成安全的 SECRET_KEY

在本地或服务器执行以下命令生成随机密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

将输出复制到 `.env` 的 `SECRET_KEY`。

---

## 步骤 5：安装 Python 依赖

1. 通过 SSH 登录 cPanel。
2. 激活 Python 虚拟环境（cPanel 创建 App 时会自动生成）：

```bash
cd /home/yourcpanel/lipeaks_backend
source /home/yourcpanel/virtualenv/lipeaks_backend/3.12/bin/activate
```

> 注意：虚拟环境路径可能因 cPanel 版本不同而变化。如果不确定，可在 cPanel 的 "Setup Python App" 页面查看。

3. 升级 pip 并安装依赖：

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 常见问题

#### 安装失败：缺少系统依赖

如果遇到 `mysql_config not found` 或编译错误，说明 cPanel 缺少 MySQL 开发库。由于 `requirements.txt` 使用 `PyMySQL`，通常不需要 `mysqlclient`，但如果某些依赖需要编译：

```bash
# 尝试单独安装可能出问题的包
pip install --only-binary :all: pymysql
pip install -r requirements.txt
```

如果仍然失败，联系主机商确认是否允许安装 C 扩展，或考虑使用 VPS。

---

## 步骤 6：运行数据库迁移

```bash
cd /home/yourcpanel/lipeaks_backend
source /home/yourcpanel/virtualenv/lipeaks_backend/3.12/bin/activate
python manage.py migrate
```

### 如果需要导入初始数据

```bash
python manage.py loaddata docs/init_sql/initial_data.json
```

> 仅当存在初始数据文件时执行。

---

## 步骤 7：收集静态文件

项目使用 WhiteNoise 提供静态文件。执行：

```bash
cd /home/yourcpanel/lipeaks_backend
source /home/yourcpanel/virtualenv/lipeaks_backend/3.12/bin/activate
python manage.py collectstatic --noinput
```

执行后会在 `staticfiles/` 目录生成收集的静态文件。

---

## 步骤 8：创建超级管理员

```bash
cd /home/yourcpanel/lipeaks_backend
source /home/yourcpanel/virtualenv/lipeaks_backend/3.12/bin/activate
python manage.py createsuperuser
```

按提示输入用户名、邮箱、密码。

---

## 步骤 9：配置 Passenger WSGI

项目已包含 `passenger_wsgi.py` 和修复过的 `core/wsgi.py`，通常无需修改。

确认 `passenger_wsgi.py` 内容如下：

```python
import importlib.machinery
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

wsgi = load_source('wsgi', 'core/wsgi.py')
application = wsgi.application
```

---

## 步骤 10：重启 Python App

1. 进入 cPanel → **Setup Python App**。
2. 找到你的应用，点击 **Restart**。

或者通过 SSH：

```bash
touch /home/yourcpanel/lipeaks_backend/tmp/restart.txt
```

> 某些 cPanel 版本支持通过 `touch restart.txt` 重启 Passenger。

---

## 步骤 11：验证部署

### 11.1 检查应用是否运行

在浏览器访问：

```
https://api.yourdomain.com/api/v1/docs/
```

应能看到 Swagger UI API 文档页面。

### 11.2 检查健康接口

```bash
curl https://api.yourdomain.com/api/v1/feedbacks/health/
```

### 11.3 测试登录

```bash
curl -X POST 'https://api.yourdomain.com/api/v1/auth/login/' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your_superuser",
    "password": "your_password"
  }'
```

---

## cPanel 共享主机特殊说明

### Redis / Celery

cPanel 共享主机通常**不提供 Redis**。项目已支持通过环境变量关闭 Celery：

```env
CELERY_ENABLED=false
```

关闭后：
- 所有 Celery 任务会**同步执行**。
- 不需要运行 `celery worker` 和 `celery beat`。
- 缺点是耗时任务会阻塞请求，适合轻量使用场景。

如果需要异步任务，可考虑：
- 升级到 VPS / 云服务器。
- 使用外部 Redis 服务（如 Upstash、Redis Cloud）。
- 使用 cPanel Cron Jobs 模拟定时任务。

### 定时任务替代方案（Cron Jobs）

在 cPanel → **Cron Jobs** 中添加：

```bash
cd /home/yourcpanel/lipeaks_backend && source /home/yourcpanel/virtualenv/lipeaks_backend/3.12/bin/activate && python manage.py cleanup_old_email_logs
```

### 媒体文件 / 用户上传

cPanel 环境下，Django 默认将上传文件保存到 `media/` 目录。确保：

```bash
mkdir -p /home/yourcpanel/lipeaks_backend/media
chmod 755 /home/yourcpanel/lipeaks_backend/media
```

### 日志文件

项目日志默认写入 `logs/` 目录。确保目录可写：

```bash
mkdir -p /home/yourcpanel/lipeaks_backend/logs
chmod 755 /home/yourcpanel/lipeaks_backend/logs
```

---

## 生产环境安全检查清单

部署完成后，请务必确认以下事项：

| 检查项 | 要求 | 状态 |
|--------|------|------|
| `INFO=False` | 关闭 DEBUG 模式 | ☐ |
| `SECRET_KEY` | 已修改为新随机值，且不泄露 | ☐ |
| `ALLOWED_HOSTS` | 限制为实际域名，不是 `['*']` | ☐ |
| `CORS_ALLOW_ALL_ORIGINS` | 生产环境应设为 `False` | ☐ |
| `CSRF_TRUSTED_ORIGINS` | 包含 HTTPS 域名 | ☐ |
| `.env` 文件权限 | `chmod 600` | ☐ |
| 数据库密码 | 强密码，不重复使用 | ☐ |
| 管理员密码 | 强密码 | ☐ |
| SSL/HTTPS | 通过 cPanel 申请并启用 SSL | ☐ |
| Celery | 无 Redis 时 `CELERY_ENABLED=false` | ☐ |

### 修改 ALLOWED_HOSTS 和 CORS

当前 `core/settings.py` 中：

```python
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True
```

生产环境建议改为从环境变量读取，或手动修改 `core/settings.py`：

```python
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'
```

> 注意：修改 `core/settings.py` 需要重新上传/提交代码。

---

## 故障排除

### 问题 1：访问域名显示 500 Internal Server Error

**排查步骤：**

1. 查看 Passenger 日志：
   ```bash
   tail -f /home/yourcpanel/logs/api.yourdomain.com/error_log
   ```
2. 查看应用日志：
   ```bash
   tail -f /home/yourcpanel/lipeaks_backend/logs/INFO.$(date +%Y-%m-%d).log
   ```
3. 确认虚拟环境已激活且依赖安装成功。
4. 确认 `.env` 文件存在且权限正确。

### 问题 2：静态文件 404

1. 确认已执行 `collectstatic`。
2. 确认 `staticfiles/` 目录存在。
3. 在 cPanel → **Setup Python App** 中重启应用。

### 问题 3：数据库连接失败

1. 确认 MySQL 用户名、密码、数据库名正确。
2. 确认数据库用户已添加到数据库并授予所有权限。
3. 确认 `DB_HOST=localhost`。
4. 测试连接：
   ```bash
   mysql -u yourcpanel_lipeaks_user -p -h localhost yourcpanel_lipeaks_db
   ```

### 问题 4：Unicode 编码错误

项目 `core/wsgi.py` 已包含 cPanel 编码修复。如果仍出现编码问题：

1. 确认 `.env` 文件为 UTF-8 编码。
2. 在 `passenger_wsgi.py` 开头添加：
   ```python
   import os
   os.environ['LANG'] = 'en_US.UTF-8'
   os.environ['LC_ALL'] = 'en_US.UTF-8'
   os.environ['PYTHONUTF8'] = '1'
   ```

### 问题 5：内存不足或进程被 kill

cPanel 共享主机通常限制内存。如果出现 OOM：

1. 在 `.env` 中关闭 Celery：`CELERY_ENABLED=false`
2. 减少并发 worker 数量（cPanel 已默认单进程）。
3. 考虑升级到更高配置的主机或 VPS。

### 问题 6：依赖安装失败（权限或编译错误）

1. 确认使用虚拟环境，而不是系统 Python。
2. 尝试使用预编译 wheel：
   ```bash
   pip install --only-binary :all: -r requirements.txt
   ```
3. 联系主机商确认是否支持编译 Python 扩展。

---

## 部署后推荐操作

1. **配置自动备份**：使用 cPanel 备份功能定期备份数据库和 `media/` 目录。
2. **启用 SSL**：cPanel → **SSL/TLS** → 申请 Let's Encrypt 免费证书。
3. **设置监控**：配置 UptimeRobot 等工具监控 `https://api.yourdomain.com/api/v1/feedbacks/health/`。
4. **定期清理日志**：`logs/` 目录会按日期生成，建议设置 Cron 定期清理旧日志。
5. **更新代码后操作**：
   ```bash
   cd /home/yourcpanel/lipeaks_backend
   git pull origin main
   source /home/yourcpanel/virtualenv/lipeaks_backend/3.12/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   # 重启应用
   touch tmp/restart.txt
   ```

---

## 参考文件

| 文件 | 说明 |
|------|------|
| `passenger_wsgi.py` | cPanel Passenger WSGI 入口 |
| `core/wsgi.py` | Django WSGI 配置，含 cPanel 编码修复 |
| `core/settings.py` | Django 主配置 |
| `requirements.txt` | Python 依赖 |
| `.env.example` | 环境变量模板 |
| `Dockerfile` | Docker 部署参考 |
| `docker-compose.yml` | 本地/服务器 Docker 部署参考 |
| `.env.prod.example` | 生产环境变量模板 |
| `scripts/deploy_cpanel.sh` | cPanel 一键部署脚本 |
