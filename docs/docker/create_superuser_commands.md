# Docker 环境中创建超级用户

## 自动创建方式

在 `docker-compose.yml` 中已经配置了自动创建超级用户的环境变量：

```yaml
environment:
  # 超级管理员设置
  - CREATE_SUPERUSER=true
  - SUPERUSER_USERNAME=admin
  - SUPERUSER_EMAIL=admin@example.com
  - SUPERUSER_PASSWORD=admin123456
```

当 `CREATE_SUPERUSER=true` 时，容器启动过程中会自动创建超级用户。

您可以修改这些环境变量来设置自己的超级用户名和密码。

## 手动创建方式

如果您需要在容器已经运行后手动创建超级用户，可以使用以下命令：

```powershell
# 进入运行中的容器
docker-compose exec web python manage.py createsuperuser
```

这将启动交互式命令行，提示您输入用户名、电子邮件和密码。

## 非交互式方式创建

如果您需要以非交互式方式创建超级用户（例如在脚本中），可以使用以下命令：

```powershell
# 一行命令创建超级用户
docker-compose exec -T web python -c "import django; django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123456') if not User.objects.filter(username='admin').exists() else print('用户已存在')"
```

## 修改超级用户密码

如果您需要修改现有超级用户的密码，可以使用以下命令：

```powershell
# 修改超级用户密码
docker-compose exec web python manage.py changepassword admin
```

## 验证超级用户

创建超级用户后，您可以访问 Django 管理站点来验证账户：

```
http://localhost:8000/admin/
```

使用创建的用户名和密码登录。 