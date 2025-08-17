# 环境变量配置指南

本项目使用环境变量来配置各种设置。您可以在项目根目录创建一个 `.env` 文件来设置这些变量。

## 核心环境变量

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| SECRET_KEY | Django 密钥 | django-insecure-w7&3bzjc1s*bty@)%c3w&#fro!wu5@(9jxac46lqm^klo9^1df | 任意长字符串 |
| DEBUG | 调试模式 | True | True 或 False |
| ALLOWED_HOSTS | 允许的主机名 | localhost,127.0.0.1 | 逗号分隔的主机名列表 |

## 数据库配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| DB_NAME | 数据库名称 | multi_tenant_db | your_db_name |
| DB_USER | 数据库用户名 | root | your_db_user |
| DB_PASSWORD | 数据库密码 | password | your_db_password |
| DB_HOST | 数据库主机 | localhost | localhost 或 IP 地址 |
| DB_PORT | 数据库端口 | 3306 | 3306 |

## 日志配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| LOG_TO_CONSOLE | 控制日志输出位置 | 与 DEBUG 相同 | True 或 False |

- 当 `LOG_TO_CONSOLE=True` 时，日志将输出到控制台（适合开发环境）
- 当 `LOG_TO_CONSOLE=False` 时，日志将输出到文件（适合生产环境）
- 如果未设置，默认会跟随 `DEBUG` 的值

### 日志文件管理

系统配置了按日期命名日志文件：

- 日志文件名格式为 `base_name.YYYY-MM-DD.log`
- 例如：`debug.2023-05-01.log`、`error.2023-05-01.log`
- 系统默认保留最近 15 天的日志文件
- 超过 15 天的旧日志文件会被自动删除

您可以通过以下命令手动清理旧日志：

```bash
python manage.py clean_old_logs
```

或指定保留天数：

```bash
python manage.py clean_old_logs --days=30
```

## 邮件配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| EMAIL_HOST_USER | 邮箱地址 | 空 | your_email@qq.com |
| EMAIL_HOST_PASSWORD | 邮箱授权码 | 空 | your_auth_code |
| DEFAULT_FROM_EMAIL | 发件人邮箱 | 空 | your_email@qq.com |

## 前端配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| FRONTEND_URL | 前端 URL | http://localhost:3000 | https://your-domain.com |

## 示例 .env 文件

```
# Django项目环境变量配置
SECRET_KEY=django-insecure-w7&3bzjc1s*bty@)%c3w&#fro!wu5@(9jxac46lqm^klo9^1df
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DB_NAME=multi_tenant_db
DB_USER=root
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306

# 日志配置
LOG_TO_CONSOLE=True  # 设为True时输出到控制台，False时输出到文件

# 邮件配置
EMAIL_HOST_USER=your_email@qq.com
EMAIL_HOST_PASSWORD=your_auth_code
DEFAULT_FROM_EMAIL=your_email@qq.com

# 前端URL
FRONTEND_URL=http://localhost:3000 