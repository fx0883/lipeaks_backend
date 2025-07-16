# Docker部署指南

本文档描述了如何使用Docker部署本项目。

## 前提条件

- Docker 20.10+
- Docker Compose 2.0+

## 部署步骤

### 1. 创建Docker配置文件

#### 创建Dockerfile

在项目根目录创建`Dockerfile`文件：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建日志目录
RUN mkdir -p logs

# 使容器可执行
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

#### 创建docker-compose.yml

在项目根目录创建`docker-compose.yml`文件：

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: multi_tenant_db
      MYSQL_USER: django
      MYSQL_PASSWORD: django_password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./docs/init_sql/common_config.sql:/docker-entrypoint-initdb.d/common_config.sql
    ports:
      - "3306:3306"
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 5s
      retries: 10

  web:
    build: .
    restart: always
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your_production_secret_key
      - DB_NAME=multi_tenant_db
      - DB_USER=django
      - DB_PASSWORD=django_password
      - DB_HOST=db
      - DB_PORT=3306
    depends_on:
      db:
        condition: service_healthy

volumes:
  mysql_data:
  static_volume:
  media_volume:
```

#### 创建docker-entrypoint.sh

在项目根目录创建`docker-entrypoint.sh`文件：

```bash
#!/bin/bash

# 等待数据库准备就绪
echo "等待数据库..."
while ! nc -z db 3306; do
  sleep 1
done
echo "数据库已准备就绪!"

# 创建迁移文件
python manage.py makemigrations common tenants users rbac menus cms check_system charts customers orders

# 应用迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 启动Gunicorn服务器
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

确保给脚本添加执行权限：

```bash
chmod +x docker-entrypoint.sh
```

### 2. 构建和启动容器

```bash
docker-compose up -d
```

### 3. 创建超级用户

```bash
docker-compose exec web python manage.py createsuperuser
```

## 访问应用

应用将在 http://localhost:8000 上运行。

## 常见问题

### 数据库初始化失败

如果数据库初始化失败，可能原因有：

- 检查`common_config.sql`文件是否可访问
- MySQL容器可能未正确挂载卷
- 尝试手动导入SQL文件：
  ```bash
  docker-compose exec db mysql -uroot -ppassword multi_tenant_db < docs/init_sql/common_config.sql
  ```

### 容器启动问题

如果容器无法正常启动：

- 查看容器日志：`docker-compose logs web`
- 确认所有环境变量已正确设置
- 检查网络连接是否正常

## 生产环境部署

对于生产环境，建议：

1. 更改所有默认密码
2. 配置HTTPS
3. 使用非root用户运行容器
4. 启用数据库备份
5. 设置监控和日志收集

```bash
# 示例：使用Docker Swarm部署
docker stack deploy -c docker-compose.production.yml app
``` 