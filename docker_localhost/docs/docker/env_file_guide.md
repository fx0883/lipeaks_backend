# Docker环境变量配置指南

本文档提供了如何在Windows环境下为Docker部署创建和配置`.env`文件的指南。

## 环境变量文件的作用

`.env`文件用于存储Docker容器运行时需要的配置参数，包括数据库连接信息、Django设置、邮箱配置等。这样可以避免在代码中硬编码敏感信息，提高安全性和可维护性。

## 创建.env文件

在Windows环境下，可以使用以下方法创建`.env`文件：

### 方法一：使用记事本创建

1. 在项目根目录右键 -> 新建 -> 文本文档
2. 将文件命名为`.env`（注意包含前面的点）
3. 如果Windows隐藏了文件扩展名，可能需要先修改文件命名为`.env.`，Windows会自动去掉最后一个点

### 方法二：使用PowerShell创建

```powershell
# 在PowerShell中创建空的.env文件
New-Item -Path ".env" -ItemType "file" -Force
```

## 配置.env文件内容

将以下内容复制到您的`.env`文件中，并根据实际情况修改各项参数值：

```
# Django设置
DEBUG=False
SECRET_KEY=your_production_secret_key_here

# 数据库设置
DB_NAME=multi_tenant_db
DB_USER=django
DB_PASSWORD=django_password
DB_HOST=db
DB_PORT=3306
MYSQL_ROOT_PASSWORD=secure_root_password

# 端口映射设置
DB_PORT_EXTERNAL=3306
WEB_PORT=8000

# Docker镜像设置
DOCKER_IMAGE=yourname/lipeaks_backend:latest

# 邮箱设置(QQ邮箱)
EMAIL_HOST_USER=your_email@qq.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@qq.com

# 前端URL
FRONTEND_URL=http://localhost:3000

# 日志设置
LOG_TO_CONSOLE=False
```

## 重要参数说明

### Django设置

- `DEBUG`: 生产环境应设为`False`
- `SECRET_KEY`: Django密钥，生产环境必须更改，可使用以下命令生成：

```powershell
# 在PowerShell中使用Python生成随机密钥
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 数据库设置

- `DB_NAME`: 数据库名称
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `MYSQL_ROOT_PASSWORD`: MySQL root用户密码

### Docker镜像设置

- `DOCKER_IMAGE`: Docker Hub上的镜像名称，格式为`用户名/镜像名:标签`

## 安全注意事项

1. **绝不要**将包含敏感信息的`.env`文件提交到Git仓库
2. 确保将`.env`添加到`.gitignore`文件中
3. 在生产环境中使用强密码
4. 定期更换密码和密钥

## 验证.env文件是否生效

启动Docker容器后，可以通过以下命令检查环境变量是否正确加载：

```powershell
# 检查web容器的环境变量
docker-compose exec web env

# 检查数据库容器的环境变量
docker-compose exec db env
``` 