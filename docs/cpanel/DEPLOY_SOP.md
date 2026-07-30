# LiPeaks Backend 部署到 cPanel 完整 SOP（标准作业流程）

> **文档定位**：这是将 LiPeaks Backend 部署到 cPanel 共享/商业主机的**唯一权威主文档**，按阶段顺序、可逐步执行。
> 本 SOP 已对齐当前代码库实际状态（Django 6.0.6、`.env.prod`、`passenger_wsgi.py`、`scripts/deploy_cpanel.sh`），
> 并**更正**了仓库中旧文档（`docker_localhost/docs/deploy_to_cpanel.md`、`docs/cpanel/01~10`）里的若干错误。
> 当旧文档与本 SOP 冲突时，**以本 SOP 为准**。

---

## 0. 阅读前必读：3 个关键更正

旧文档里有 3 处会直接导致部署失败或行为异常的描述，请先记住：

| 项 | 旧文档（错误） | 实际情况（本 SOP） |
|---|---|---|
| **关闭调试模式** | 在 `.env` 写 `DEBUG=False` | **`DEBUG` 变量根本不被读取**。`core/settings.py` 从 **`INFO`** 环境变量读取（历史遗留）。生产环境必须写 `INFO=False`。 |
| **环境变量文件** | 使用 `.env` | 生产模板是 **`.env.prod`**（由 `.env.prod.example` 复制）。一键脚本 `deploy_cpanel.sh` 也读 `.env.prod`。 |
| **Django 版本** | 写“Django 5.2” | 实际是 **Django 6.0.6**，要求 Python 3.10+。cPanel 请选 Python **3.12**（或 3.13，若主机提供）。 |

另外一个本项目特有的坑（后文详述）：
- **Celery**：cPanel 共享主机一般跑不了 Redis + Worker，**必须** `CELERY_ENABLED=false`（任务改为同步执行）。

---

## 1. 部署架构总览

cPanel 通过 **Apache + Passenger（Phusion Passenger）** 运行 Python WSGI 应用：

```
浏览器 (HTTPS)
   │
   ▼
Apache (cPanel, 443/80)
   │  ~/public_html/.htaccess  →  强制 HTTPS、直出静态/媒体、其余转发 Passenger
   ▼
Passenger  ──加载──  ~/lipeaks_backend/passenger_wsgi.py
   │                     └─ 加载 core/wsgi.py（已内置 cPanel 编码修复 + PyMySQL + 线程限制）
   ▼
Django 6.0.6 (core.settings)
   ├── MySQL 8（cPanel 本地 /home/USERNAME 同机，PyMySQL 驱动）
   ├── WhiteNoise  →  服务 /static/（来自 staticfiles/）
   ├── /media/     →  Apache 直接服务（软链到 ~/lipeaks_backend/media）
   └── Celery：CELERY_ENABLED=false → 任务同步内联执行（无 Redis/Worker）
```

**关键文件速查**（均已存在于仓库，无需新建）：

| 文件 | 作用 |
|---|---|
| `passenger_wsgi.py`（根目录） | Passenger 入口，加载 `core/wsgi.py` |
| `core/wsgi.py` | WSGI 应用；内置 UTF-8 编码修复、`pymysql.install_as_MySQLdb()`、OpenBLAS 线程限制 |
| `core/settings.py` | 主配置；`pymysql.install_as_MySQLdb()` 已写在顶部 |
| `.env.prod.example` | 生产环境变量模板（复制为 `.env.prod`） |
| `scripts/deploy_cpanel.sh` | 一键部署/更新脚本 |
| `requirements.txt` | 依赖清单（含 PyMySQL、WhiteNoise、gunicorn、celery） |

---

## 2. 前置条件清单

部署前逐项确认（✅ 打勾再继续）：

- [ ] cPanel 账号已开通，且 **“Setup Python App”（Python 应用程序）** 功能可用
- [ ] cPanel 提供 **Python 3.12**（或 3.13）选项
- [ ] cPanel **MySQL 数据库向导** 可用（MySQL 8 或 MariaDB 10.x+）
- [ ] 有 **SSH 访问权限** 或 cPanel 内置 **Terminal（终端）**（强烈推荐，本文命令以 SSH 为准）
- [ ] 一个已解析到该主机的**域名或子域名**（例如 `api.yourdomain.com`）
- [ ] 本地已能 `git clone https://github.com/fx083/lipeaks_backend.git`（或用 cPanel Git 版本控制直接拉取）
- [ ] 已生成一个强随机 `SECRET_KEY`（见阶段 4 生成命令）

> **路径约定**：下文用 `USERNAME` 代表你的 cPanel 用户名，`api.yourdomain.com` 代表你的域名。请全程替换为真实值。家目录为 `/home/USERNAME`。

---

## 3. 阶段 1：cPanel 环境准备

### 3.1 创建 MySQL 数据库与用户

1. 登录 cPanel → 找到 **“MySQL® 数据库向导”**（MySQL Database Wizard）。
2. **新建数据库**：命名为 `lipeaks_prod`（cPanel 会自动加用户名前缀，最终形如 `USERNAME_lipeaks_prod`）。**记下完整库名**。
3. **创建用户**：用户名如 `lipeaks_user`，生成强密码并**保存**（最终形如 `USERNAME_lipeaks_user`）。**记下完整用户名和密码**。
4. **授权**：将该用户加入数据库，**勾选 ALL PRIVILEGES（所有权限）**。
5. **字符集**：在 **phpMyAdmin** 中打开该库，执行（若向导未指定）：
   ```sql
   ALTER DATABASE `USERNAME_lipeaks_prod` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

> 记录卡（填好备用）：
> - DB_NAME = `USERNAME_lipeaks_prod`
> - DB_USER = `USERNAME_lipeaks_user`
> - DB_PASSWORD = `********`
> - DB_HOST = `localhost`
> - DB_PORT = `3306`

### 3.2 确认 Python 版本与终端

1. cPanel → **“Setup Python App”** → 顶部 “Python version” 下拉，确认存在 **3.12**（首选）或 3.13。
2. cPanel → **“Terminal”**（终端）或在 “SSH 访问” 中配置公钥后用 SSH 客户端登录。验证：
   ```bash
   whoami        # 应输出你的 USERNAME
   python3 --version
   ```

### 3.3 了解资源限制（共享主机）

cPanel 共享主机通常限制：进程数、内存（常 1~2GB）、无后台常驻进程。本项目已做适配：
- `core/wsgi.py` 已把 `OPENBLAS/OMP` 等线程数限制为 1，避免资源耗尽。
- 关闭 Celery 后无后台 Worker 进程。
- 如主机限制过严（如内存 <512MB），`pandas`/`numpy`/`lxml` 导入可能 OOM——见第 12 节排查。

---

## 4. 阶段 2：上传项目代码

**推荐**：在 cPanel 服务器上直接 `git clone`（最快、便于后续 `git pull` 更新）。

### 4.1 方式 A：SSH 内 Git 克隆（推荐）

```bash
cd ~
git clone https://github.com/fx0883/lipeaks_backend.git
cd lipeaks_backend
# 如需指定分支：
# git checkout main
```

### 4.2 方式 B：cPanel “Git™ 版本控制”

1. cPanel → **“Git™ 版本控制”** → **“创建”**。
2. 克隆 URL：`https://github.com/fx0883/lipeaks_backend.git`；存储库路径：`lipeaks_backend`。
3. 创建后，代码位于 `~/lipeaks_backend`。

### 4.3 方式 C：文件管理器上传 ZIP

本地打包（**务必排除 `media/`、`logs/`、`staticfiles/`、`.env`**，见 `.gitignore`）→ cPanel “文件管理器”上传到 `~/` → 解压为 `~/lipeaks_backend`。

### ✅ 验证

```bash
ls ~/lipeaks_backend/manage.py ~/lipeaks_backend/passenger_wsgi.py ~/lipeaks_backend/core/settings.py
# 三者都应存在，无报错
```

---

## 5. 阶段 3：创建 Python 应用程序

1. cPanel → **“Setup Python App”** → **“Create Application”（创建应用程序）**。
2. 填写：
   - **Python version**：`3.12`
   - **Application root（应用根目录）**：`lipeaks_backend`
   - **Application URL（应用 URL）**：你的域名/子域名，如 `api.yourdomain.com`
   - **Application startup file（启动文件）**：`passenger_wsgi.py`
   - **Application Entry point（入口点）**：`application`
3. **“Create”（创建）**。
4. 创建后，cPanel 会显示一段**激活虚拟环境的命令**，形如：
   ```bash
   source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate
   ```
   **记下这条路径**（下文称 `VENV_ACTIVATE`），后续所有命令都需先激活它。

> 说明：仓库根目录已自带 `passenger_wsgi.py`（加载 `core/wsgi.py`，含 cPanel 编码修复），**无需使用 cPanel 自动生成的那个**；cPanel 创建应用时会保留你仓库里的版本。若 cPanel 覆盖了它，用 `git checkout passenger_wsgi.py` 恢复。

---

## 6. 阶段 4：配置生产环境变量 `.env.prod`

### 6.1 复制模板

```bash
cd ~/lipeaks_backend
cp .env.prod.example .env.prod
```

### 6.2 生成强 SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
把输出填入 `.env.prod` 的 `SECRET_KEY=`。

### 6.3 编辑 `.env.prod`（逐项填写）

```bash
nano .env.prod      # 或 vim
```

完整字段说明（**对照 `.env.prod.example`**）：

| 变量 | 必填 | 示例/说明 |
|---|---|---|
| `DB_NAME` | ✅ | `USERNAME_lipeaks_prod` |
| `DB_USER` | ✅ | `USERNAME_lipeaks_user` |
| `DB_PASSWORD` | ✅ | 你的数据库密码 |
| `DB_HOST` | ✅ | `localhost` |
| `DB_PORT` | ✅ | `3306` |
| `SECRET_KEY` | ✅ | 上一步生成的 50 字符随机串 |
| `INFO` | ✅ | **`False`**（关闭调试；⚠️ 不是 `DEBUG`） |
| `LOG_TO_CONSOLE` | ✅ | `False`（写 `logs/` 轮转文件，保留 15 天） |
| `ALLOWED_HOSTS` | ✅ | `api.yourdomain.com,yourdomain.com,localhost,127.0.0.1` |
| `CELERY_ENABLED` | ✅ | **`false`**（共享主机无 Redis/Worker） |
| `EMAIL_USE_CONSOLE` | 可选 | `false` |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `DEFAULT_FROM_EMAIL` | 可选 | QQ 邮箱地址 + **授权码**（非登录密码） |
| `WECHAT_APPID` / `WECHAT_SECRET` | 可选 | 不用微信可留空 |
| `SITE_URL` | 推荐 | `https://api.yourdomain.com` |
| `FRONTEND_URL` | 推荐 | `https://admin.yourdomain.com` |


### 6.4 设置权限（必须）

```bash
chmod 600 .env.prod
```

### ✅ 验证

```bash
# 确认关键变量已写入
grep -E '^(DB_NAME|DB_USER|SECRET_KEY|INFO|CELERY_ENABLED|ALLOWED_HOSTS)=' .env.prod
# 应能看到 6 行，且 INFO=False、CELERY_ENABLED=false
```

---

## 7. 阶段 5：安装 Python 依赖

### 7.1 激活虚拟环境

```bash
source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate
cd ~/lipeaks_backend
python --version        # 确认 3.12.x
```

### 7.2 安装依赖

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

> **国内主机加速**（可选）：`pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`

### 7.3 处理编译失败

cPanel 通常**没有** `gcc`/`mysqlclient` 开发头文件，以下是预期行为与对策：

- **`mysqlclient`**：本项目**不依赖**它（用 `PyMySQL`，已在 `requirements.txt` 与 `core/settings.py`、`core/wsgi.py` 中配置 `pymysql.install_as_MySQLdb()`）。若某包顺带要求 `mysqlclient` 失败，可忽略或 `pip install pymysql`。
- **`lxml` / `Pillow` / `cryptography`**：优先装预编译 wheel（`pip install wheel` 已装则自动用 wheel）。仍失败时：
  ```bash
  pip install --only-binary :all: lxml Pillow cryptography
  ```
- **`numpy` / `pandas`**：体积大、编译重。务必用 wheel：`pip install --only-binary :all: numpy pandas`。若主机内存过小导致安装/导入 OOM，见第 12 节。

### ✅ 验证

```bash
python -m django --version        # 6.0.6
python -c "import django, pymysql, dotenv, rest_framework, whitenoise, parler; print('核心模块导入成功')"
```

---

## 8. 阶段 6：数据库字符集修复

`core/settings.py` 的 `DATABASES.OPTIONS.init_command` 已设 `SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'`，但建库/建表时的默认 collation 可能仍是 `utf8mb4_0900_ai_ci` 或 latin1。迁移前先统一：

### 8.1 创建并运行修复脚本

```bash
cd ~/lipeaks_backend
cat > fix_charset.py << 'EOL'
#!/usr/bin/env python
import os, pymysql
from dotenv import load_dotenv
load_dotenv('.env.prod')
DB_HOST=os.getenv('DB_HOST','localhost'); DB_USER=os.getenv('DB_USER')
DB_PASSWORD=os.getenv('DB_PASSWORD'); DB_NAME=os.getenv('DB_NAME')
DB_PORT=int(os.getenv('DB_PORT','3306'))
try:
    c=pymysql.connect(host=DB_HOST,user=DB_USER,password=DB_PASSWORD,port=DB_PORT)
    with c.cursor() as cur:
        cur.execute(f"ALTER DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    c.close()
    c=pymysql.connect(host=DB_HOST,user=DB_USER,password=DB_PASSWORD,database=DB_NAME,port=DB_PORT,charset='utf8mb4')
    with c.cursor() as cur:
        cur.execute("SHOW TABLES"); tables=cur.fetchall()
        for (t,) in tables:
            print(f"  修复表 {t}")
            cur.execute(f"ALTER TABLE `{t}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    c.commit(); print("字符集修复完成")
except Exception as e:
    print(f"错误: {e}")
finally:
    if 'c' in locals(): c.close()
EOL
source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate
python fix_charset.py
```

> 迁移**之前**运行此脚本（此时表还很少）；迁移后如出现 `Incorrect string value` 报错，再运行一次即可。

### ✅ 验证

```bash
python manage.py shell -c "from django.db import connection; cur=connection.cursor(); cur.execute('SELECT @@character_set_database, @@collation_database'); print(cur.fetchone())"
# 应输出 ('utf8mb4', 'utf8mb4_unicode_ci')
```

---

## 9. 阶段 7：执行数据库迁移

```bash
cd ~/lipeaks_backend
source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate

python manage.py showmigrations      # 查看待应用迁移
python manage.py migrate --noinput   # 应用迁移
```

### 常见迁移错误处理

- **“表已存在”**（从快照导过数据）：`python manage.py migrate <app> --fake` 标记为已应用；**慎用** `--fake`（全局），仅在确知表结构已与代码一致时。
- **外键约束冲突**：
  ```bash
  python manage.py shell -c "from django.db import connection; connection.cursor().execute('SET FOREIGN_KEY_CHECKS=0')"
  python manage.py migrate
  python manage.py shell -c "from django.db import connection; connection.cursor().execute('SET FOREIGN_KEY_CHECKS=1')"
  ```
- **字段类型不兼容**：用 phpMyAdmin 或 `mysql` 客户端手动 `ALTER TABLE` 后重试。

### ✅ 验证

```bash
python manage.py showmigrations | grep -v '\[X\]' | grep '\[ \]'
# 无输出 = 全部迁移已应用
```

---

## 10. 阶段 8：初始化数据与超级管理员

按顺序执行（已按项目实际管理命令整理）：

```bash
cd ~/lipeaks_backend
source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate

# 1) 创建超级管理员（带参数，非交互；会自动设置 is_super_admin/is_admin/is_staff）
python manage.py create_super_admin \
    --username admin --password '你的强密码' --email admin@yourdomain.com --nick_name '超管'

# 2) 初始化超级管理员菜单配置（写入 common.Config）
python manage.py init_super_admin_menu

# 3) 初始化 RBAC 权限数据
python manage.py init_rbac_data

# 4) 加载初始菜单
python manage.py load_initial_menus
```

> **可选命令**（按需）：
> - `python manage.py init_rbac` —— RBAC 初始化（若 `init_rbac_data` 已覆盖则可跳过）
> - `python manage.py load_cms_menus` —— CMS 菜单
> - `python manage.py init_feedback_templates` —— 反馈模板
> - `python manage.py sync_license_configs` —— 许可证配置同步
>
> **关于 `run_config_sql`**：该命令读取 `docs/init_sql/common_config.sql`，但**当前仓库此文件缺失**（仅有 `docs/init_sql/multi_tenant_db_dev.sql` 开发快照）。因此**不要**运行 `run_config_sql`，否则只会打印“SQL文件不存在”。如需该配置，请新增该 SQL 文件后再运行。
>
> **关于开发快照 `multi_tenant_db_dev.sql`**：这是含开发测试数据的整库快照，**生产环境禁止导入**（会覆盖并带入测试数据）。仅本地/Docker 初始化用。

### ✅ 验证

```bash
# 系统检查（关键！能捕获导入/配置错误）
python manage.py check

# 登录验证超管
python manage.py shell -c "from users.models import User; u=User.objects.filter(username='admin').first(); print('超管存在:', bool(u), '| is_super_admin:', u.is_super_admin if u else None)"
```


---

## 11. 阶段 9：收集静态文件

```bash
cd ~/lipeaks_backend
source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate
python manage.py collectstatic --noinput --clear
```

说明：
- `STATIC_ROOT = BASE_DIR/staticfiles`，即 `~/lipeaks_backend/staticfiles`。
- `STORAGES.staticfiles` 用 `whitenoise.storage.CompressedManifestStaticFilesStorage`，WhiteNoise 中间件已注册，**`/static/` 由应用自身服务**，无需 Apache 额外配置。
- `STATICFILES_DIRS` 含 `~/lipeaks_backend/static`（仓库已提交 admin、drf-spectacular 等静态资源），会被一并收集。

### ✅ 验证

```bash
ls ~/lipeaks_backend/staticfiles | head
# 应看到 admin/、rest_framework/、drf_spectacular/ 等
```

---

## 12. 阶段 10：配置 Apache（.htaccess）与媒体文件

`/static/` 已由 WhiteNoise 处理；**`/media/` 在 DEBUG=False 下 Django 不服务**，需让 Apache 直接服务。

### 12.1 创建媒体目录软链

cPanel 域名文档根通常是 `~/public_html`。把媒体目录软链进去，让 Apache 直出：

```bash
mkdir -p ~/lipeaks_backend/media
chmod -R 755 ~/lipeaks_backend/media
ln -sfn ~/lipeaks_backend/media ~/public_html/media
```

### 12.2 配置 `.htaccess`

编辑域名文档根下的 `.htaccess`（通常 `~/public_html/.htaccess`）：

```bash
nano ~/public_html/.htaccess
```

内容（强制 HTTPS + 直出已存在文件 + 其余转发 Passenger + 保护敏感文件）：

```apache
# === 强制 HTTPS ===
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# === 已存在的文件/目录（含 /media/ 软链）由 Apache 直接服务 ===
RewriteCond %{REQUEST_FILENAME} -f [OR]
RewriteCond %{REQUEST_FILENAME} -d
RewriteRule ^ - [L]

# === 其余请求转发给 Passenger ===
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [QSA,L]

# === 静态资源缓存 ===
<FilesMatch "\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$">
    Header set Cache-Control "max-age=2592000, public"
</FilesMatch>

# === 文本压缩 ===
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/javascript application/json
</IfModule>

# === 禁止访问敏感文件 ===
<FilesMatch "^(\.env|\.env\.prod|manage\.py|settings\.py|\.gitignore)$">
    Require all denied
</FilesMatch>
```

> 说明：若你的 cPanel 把应用根直接设为域名文档根（即 `passenger_wsgi.py` 就在 `~/public_html`），则无需软链 `media`，但务必保留“禁止访问敏感文件”规则，避免 `.env.prod` 泄露。

### ✅ 验证

```bash
# 放一个测试文件
echo "media-ok" > ~/lipeaks_backend/media/_probe.txt
# 浏览器访问 https://api.yourdomain.com/media/_probe.txt 应看到 media-ok
# 完成后删除：rm ~/lipeaks_backend/media/_probe.txt
```

---

## 13. 阶段 11：域名与 SSL

### 13.1 域名/子域名指向

- **子域名（推荐）**：cPanel → **“子域名”** → 创建 `api`，文档根设为 `public_html`（配合上面的 `.htaccess` 软链方案）。
- **附加域**：cPanel → **“附加域”** → 域名 `api.yourdomain.com`，文档根 `public_html`。

### 13.2 DNS

确保 `api.yourdomain.com` 的 A 记录指向该 cPanel 服务器 IP（在 cPanel “区域编辑器”或域名注册商处配置）。

### 13.3 SSL 证书

1. cPanel → **“SSL/TLS Status”** → 找到该域名 → **“Run AutoSSL”**（Let's Encrypt 自动签发）。
2. `.htaccess` 已强制 HTTPS（见 12.2）。
3. （可选，更稳妥）在 `.env.prod` 确认 `SITE_URL=https://api.yourdomain.com`。

> Django 侧 HTTPS 安全头（`SECURE_SSL_REDIRECT` 等）当前 `settings.py` 未默认开启，避免与 cPanel 已有的 Apache 强制跳转重复 301。如需在 Django 层也加固，见第 15 节。

---

## 14. 阶段 12：重启应用与上线验证

### 14.1 重启 Passenger

任选其一：

- **方式 A（推荐，命令行）**：在项目根创建/更新重启标记文件，Passenger 检测到后自动重启：
  ```bash
  mkdir -p ~/lipeaks_backend/tmp
  touch ~/lipeaks_backend/tmp/restart.txt
  ```
  > 之后再重启只需重复 `touch tmp/restart.txt`。
- **方式 B（cPanel UI）**：cPanel → “Setup Python App” → 找到应用 → 点 **“Restart”（重启）**。

### 14.2 上线验证清单

逐项 curl 或浏览器访问（替换域名）：

```bash
# 1) 公开健康检查端点（无需鉴权，见 settings.TENANT_PUBLIC_API_PATHS）
curl -i https://api.yourdomain.com/api/v1/feedbacks/health/
# 期望 HTTP 200

# 2) OpenAPI Schema
curl -s https://api.yourdomain.com/api/v1/schema/ -o /dev/null -w "%{http_code}\n"
# 期望 200

# 3) Swagger UI（浏览器）
# https://api.yourdomain.com/api/v1/docs/

# 4) Django Admin（浏览器，用阶段 8 创建的 admin 账号登录）
# https://api.yourdomain.com/admin/
```

### 14.3 查看日志（排错必看）

```bash
# 应用日志（settings.LOGGING 写入 ~/lipeaks_backend/logs/，轮转保留 15 天）
ls ~/lipeaks_backend/logs/
tail -n 100 ~/lipeaks_backend/logs/error.*.log

# cPanel Apache/Passenger 错误日志
tail -n 100 ~/logs/api.yourdomain.com/error_log 2>/dev/null \
  || tail -n 100 ~/public_html/error_log 2>/dev/null \
  || ls ~/logs/
```

> 若 500 且日志无内容，可临时把 `.env.prod` 的 `LOG_TO_CONSOLE=True` 让日志进 Passenger stderr（即 cPanel 错误日志），排错完再改回 `False`。

---

## 15. 一键部署脚本（推荐日常使用）

仓库自带 `scripts/deploy_cpanel.sh`，封装了“激活 venv → git pull → 装依赖 → migrate → collectstatic → 重启 → 健康检查”。

### 15.1 前提

- `.env.prod` 已存在并填好（脚本检测 `.env`/`.env.prod`，缺失会中止并提示）。
- 虚拟环境路径与脚本默认一致：`/home/USERNAME/virtualenv/lipeaks_backend/3.12`。

### 15.2 首次部署（已手动完成前述阶段后，可跳过；用于全新机器）

```bash
cd ~/lipeaks_backend
./scripts/deploy_cpanel.sh --setup --domain api.yourdomain.com
```

### 15.3 日常更新（最常用）

```bash
cd ~/lipeaks_backend
./scripts/deploy_cpanel.sh --domain api.yourdomain.com
# 指定分支：./scripts/deploy_cpanel.sh --branch main --domain api.yourdomain.com
# 仅迁移+重启不拉代码：./scripts/deploy_cpanel.sh --skip-pull
```

脚本参数：`--setup`、`--branch <分支>`、`--skip-pull`、`--domain <域名>`、`--python-version 3.12`、`--help`。

---

## 16. 上线后安全加固清单

生产环境务必收紧（当前 `settings.py` 默认偏宽松，见 `CLAUDE.md`/`WORKBUDDY.md` 注意事项）：

- [ ] `ALLOWED_HOSTS`：已通过 `.env.prod` 限定为具体域名（**不要**保留 `*`）。
- [ ] `INFO=False`（即 DEBUG 关闭）已确认。
- [ ] **CORS**：当前 `CORS_ALLOW_ALL_ORIGINS=True`。生产建议改白名单——在 `.env.prod` 无法直接改此布尔（它是硬编码），可在 `settings.py` 末尾追加覆盖，或后续改造为环境变量。临时方案：编辑 `core/settings.py`：
  ```python
  CORS_ALLOW_ALL_ORIGINS = False
  CORS_ALLOWED_ORIGINS = ["https://admin.yourdomain.com", "https://yourdomain.com"]
  ```
- [ ] **CSRF_TRUSTED_ORIGINS**：同步加入你的真实域名（`https://api.yourdomain.com` 及前端域名）。
- [ ] `.env.prod` 权限 `600`：`chmod 600 ~/lipeaks_backend/.env.prod`。
- [ ] **HTTPS 安全头**（可选，若 Apache 已强制跳转则不必在 Django 重复）：
  ```python
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True   # settings 中已随 DEBUG 切换，确认 INFO=False 即为 True
  ```
- [ ] **数据库定时备份**（cPanel “Cron Jobs” 每日 02:00）：
  ```bash
  0 2 * * * mysqldump -u USERNAME_lipeaks_user -p'密码' USERNAME_lipeaks_prod | gzip > ~/backups/db_$(date +\%Y\%m\%d).sql.gz && find ~/backups -name 'db_*.sql.gz' -mtime +30 -delete
  ```
- [ ] **健康检查 cron**（每 10 分钟，失败自动 `touch tmp/restart.txt` 重启）：
  ```bash
  */10 * * * * code=$(curl -s -o /dev/null -w "%{http_code}" https://api.yourdomain.com/api/v1/feedbacks/health/); [ "$code" = "200" ] || touch ~/lipeaks_backend/tmp/restart.txt
  ```

---

## 17. 维护与更新流程

### 17.1 日常发布新代码

```bash
cd ~/lipeaks_backend
git pull origin main
./scripts/deploy_cpanel.sh --skip-pull --domain api.yourdomain.com
# 或完整：./scripts/deploy_cpanel.sh --domain api.yourdomain.com
```

脚本会自动：装依赖 → `migrate` → `collectstatic` → `touch tmp/restart.txt` → 健康检查。

### 17.2 仅改了静态/配置无需拉代码

```bash
cd ~/lipeaks_backend
source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate
python manage.py collectstatic --noinput
touch tmp/restart.txt
```

### 17.3 回滚

```bash
cd ~/lipeaks_backend
git log --oneline -10          # 找到上一个稳定 commit
git checkout <stable-commit>
./scripts/deploy_cpanel.sh --skip-pull --domain api.yourdomain.com
```

### 17.4 数据库备份恢复

```bash
gunzip < ~/backups/db_YYYYMMDD.sql.gz | mysql -u USERNAME_lipeaks_user -p USERNAME_lipeaks_prod
touch ~/lipeaks_backend/tmp/restart.txt
```

---

## 18. 常见问题排查

### 18.1 500 Internal Server Error

1. 看日志：`tail -n 100 ~/lipeaks_backend/logs/error.*.log` 与 `~/logs/api.yourdomain.com/error_log`。
2. 临时开启控制台日志：`.env.prod` 设 `LOG_TO_CONSOLE=True` → `touch tmp/restart.txt` → 看 cPanel 错误日志。
3. 验证 WSGI 能否独立加载：
   ```bash
   source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate
   cd ~/lipeaks_backend
   python -c "import core.wsgi; print('WSGI 加载成功')"
   ```
   报错会直接打印 traceback。

### 18.2 `Incorrect string value: '\xE6\x97...'`（中文写入失败）

数据库/表字符集不对。重跑阶段 6 的 `fix_charset.py`，确认库为 `utf8mb4_unicode_ci`。

### 18.3 `mysqlclient` 安装失败

本项目不依赖 `mysqlclient`，用 `PyMySQL` 即可（已配置）。忽略该错误。

### 18.4 静态文件 404（`/static/` 加载不出）

- 确认 `collectstatic` 已执行且 `~/lipeaks_backend/staticfiles` 非空。
- 确认 `whitenoise.middleware.WhiteNoiseMiddleware` 在 `MIDDLEWARE` 顶部（已默认）。
- 确认 `INFO=False` 时 WhiteNoise 仍服务静态（WhiteNoise 与 DEBUG 无关，正常工作）。

### 18.5 媒体文件 404（`/media/`）

- 确认软链 `~/public_html/media -> ~/lipeaks_backend/media` 存在：`ls -l ~/public_html/media`。
- 确认 `.htaccess` 有 `RewriteCond %{REQUEST_FILENAME} -f` 直出规则。
- 确认 `~/public_html` 为域名文档根。

### 18.6 `ModuleNotFoundError`（启动/检查期）

- 重新 `pip install -r requirements.txt`（确认在已激活的 venv 内）。
- 确认 `passenger_wsgi.py` 用的 venv 与你装包的 venv 一致（路径见阶段 3）。

### 18.7 应用跑一会儿就停（内存/进程超限）

- 共享主机限制。`core/wsgi.py` 已限线程数。
- 若 `pandas`/`numpy` 导致内存高，评估是否真需要；可尝试 `pip install --only-binary :all: numpy pandas` 用更省内存的 wheel。
- 用第 16 节的健康检查 cron 自动重启。

### 18.8 CORS / CSRF 跨域失败

- `CORS_ALLOW_ALL_ORIGINS=True` 时不应有 CORS 错误；若改了白名单，确保前端域名在 `CORS_ALLOWED_ORIGINS` 与 `CSRF_TRUSTED_ORIGINS` 中。
- 带 cookie 的请求需 `CORS_ALLOW_CREDENTIALS=True`（已默认）且前端域名必须在白名单。

### 18.9 Celery 相关（任务不执行 / 报 Redis 连接）

- cPanel 上 `CELERY_ENABLED=false`，任务同步执行，**不应**有 Redis 连接报错。
- 若仍报 Redis 连接失败，说明 `CELERY_ENABLED` 未生效：检查 `.env.prod` 是否真的写了 `CELERY_ENABLED=false` 且无拼写错误；`touch tmp/restart.txt` 重启。
- 定时任务（如 `cleanup_old_email_logs`）在 Celery 关闭后不会自动跑；如需要，用 cPanel Cron 调用 `python manage.py clean_old_logs`。

### 18.10 时区显示不对

`TIME_ZONE='UTC'`、`USE_TZ=True`。时间在库中以 UTC 存储，前端按需转换。若需改成本地时区展示，在业务层格式化，不建议改全局 `TIME_ZONE`（会影响多租户数据一致性）。

---

## 附录 A：命令速查表

```bash
# === 一次性环境变量（每次新 SSH 会话先执行）===
source /home/USERNAME/virtualenv/lipeaks_backend/3.12/bin/activate
cd ~/lipeaks_backend

# === 部署/更新 ===
./scripts/deploy_cpanel.sh --domain api.yourdomain.com             # 日常更新
./scripts/deploy_cpanel.sh --setup --domain api.yourdomain.com     # 首次
./scripts/deploy_cpanel.sh --skip-pull --domain api.yourdomain.com # 仅迁移+重启

# === 日常单步 ===
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear
python manage.py create_super_admin --username admin --password 'PWD' --email a@b.c
python manage.py check
touch tmp/restart.txt                                  # 重启 Passenger

# === 排错 ===
python -c "import core.wsgi"                           # 验证 WSGI
python manage.py shell -c "from django.db import connection; connection.cursor().execute('SELECT 1'); print('DB OK')"
tail -n 100 logs/error.*.log
curl -i https://api.yourdomain.com/api/v1/feedbacks/health/
```

## 附录 B：环境变量完整表（`.env.prod`）

| 变量 | 必填 | 生产推荐值 |
|---|---|---|
| `DB_NAME` | ✅ | `USERNAME_lipeaks_prod` |
| `DB_USER` | ✅ | `USERNAME_lipeaks_user` |
| `DB_PASSWORD` | ✅ | 强密码 |
| `DB_HOST` | ✅ | `localhost` |
| `DB_PORT` | ✅ | `3306` |
| `SECRET_KEY` | ✅ | `secrets.token_urlsafe(50)` |
| `INFO` | ✅ | `False`（⚠️ 非 `DEBUG`） |
| `LOG_TO_CONSOLE` | ✅ | `False` |
| `ALLOWED_HOSTS` | ✅ | 具体域名列表 |
| `CELERY_ENABLED` | ✅ | `false` |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` / `REDIS_URL` | ❌ | 仅当用外部 Redis（如 Upstash）时配置；否则保持关闭 |
| `EMAIL_USE_CONSOLE` | 可选 | `false` |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `DEFAULT_FROM_EMAIL` | 可选 | QQ 邮箱 + 授权码 |
| `WECHAT_APPID` / `WECHAT_SECRET` | 可选 | 微信小程序 |
| `SITE_URL` | 推荐 | `https://api.yourdomain.com` |
| `FRONTEND_URL` | 推荐 | `https://admin.yourdomain.com` |
| `FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER` | 可选 | 默认 `True`，灰度时可 `False` |
| `TENANT_MIDDLEWARE_DEBUG` | 可选 | 生产 `False` |

## 附录 C：关键目录与文件清单

| 路径 | 说明 |
|---|---|
| `~/lipeaks_backend/` | 项目根（= Python 应用根） |
| `~/lipeaks_backend/passenger_wsgi.py` | Passenger 入口 |
| `~/lipeaks_backend/core/settings.py` | 主配置 |
| `~/lipeaks_backend/.env.prod` | 生产环境变量（权限 600，不入 Git） |
| `~/lipeaks_backend/staticfiles/` | collectstatic 产物（WhiteNoise 服务） |
| `~/lipeaks_backend/media/` | 用户上传（Apache 经软链服务） |
| `~/lipeaks_backend/logs/` | 应用轮转日志（保留 15 天） |
| `~/lipeaks_backend/tmp/restart.txt` | Passenger 重启标记 |
| `~/lipeaks_backend/scripts/deploy_cpanel.sh` | 一键部署脚本 |
| `/home/USERNAME/virtualenv/lipeaks_backend/3.12/` | Python 虚拟环境 |
| `~/public_html/.htaccess` | Apache 路由/安全规则 |
| `~/public_html/media` | 软链 → `~/lipeaks_backend/media` |
| `~/backups/` | 数据库备份（cron 生成） |

---

## 部署完成自检总表

| # | 检查项 | 命令/方式 | 期望 |
|---|---|---|---|
| 1 | 依赖安装 | `python -m django --version` | `6.0.6` |
| 2 | 环境变量 | `grep INFO= .env.prod` | `INFO=False` |
| 3 | Celery 关闭 | `grep CELERY_ENABLED= .env.prod` | `false` |
| 4 | 字符集 | shell 查询 `@@collation_database` | `utf8mb4_unicode_ci` |
| 5 | 迁移完成 | `showmigrations \| grep '[ ]'` | 无输出 |
| 6 | 系统检查 | `python manage.py check` | 无问题 |
| 7 | 超管存在 | shell 查询 `User(username='admin')` | True |
| 8 | 静态收集 | `ls staticfiles/admin` | 存在 |
| 9 | 健康检查 | `curl /api/v1/feedbacks/health/` | 200 |
| 10 | Swagger | 浏览器 `/api/v1/docs/` | 页面正常 |
| 11 | Admin | 浏览器 `/admin/` | 可登录 |
| 12 | 媒体可访问 | `/media/_probe.txt` | 200 |
| 13 | HTTPS | `curl -I http://...` | 301 到 https |
| 14 | 备份 cron | cPanel Cron Jobs | 已设置 |
| 15 | 健康检查 cron | cPanel Cron Jobs | 已设置 |

全部 ✅ 即部署成功。
