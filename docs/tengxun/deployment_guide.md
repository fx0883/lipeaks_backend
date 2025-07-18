# 腾讯云服务器部署指南

本文档将指导您如何使用 docker-compose-ro.yml 将应用部署到腾讯云服务器上。

## 目录

1. [前提条件](#前提条件)
2. [准备工作](#准备工作)
3. [部署步骤](#部署步骤)
4. [验证部署](#验证部署)
5. [常见问题及解决方案](#常见问题及解决方案)
6. [Docker 镜像拉取超时问题](#Docker-镜像拉取超时问题)
7. [API 请求连接问题](#API-请求连接问题)
8. [维护与更新](#维护与更新)

## 前提条件

- 已购买并初始化腾讯云服务器（CVM）
- 服务器操作系统：CentOS 7+ 或 Ubuntu 18.04+
- 已开放以下端口：
  - 80（HTTP）
  - 8000（后端API，可选）
  - 3306（MySQL，仅内部访问）

## 准备工作

### 1. 安装 Docker 和 Docker Compose

**CentOS 7:**

```bash
# 安装必要的依赖
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加Docker仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动Docker并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Ubuntu:**

```bash
# 更新包索引
sudo apt-get update

# 安装必要的依赖
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 创建项目目录

```bash
# 创建项目目录
mkdir -p ~/lipeaks_backend
cd ~/lipeaks_backend

# 创建必要的子目录
mkdir -p nginx logs media staticfiles docs/init_sql
```

## 部署步骤

### 1. 上传必要文件到服务器

将以下文件上传到服务器的项目目录：

- `docker-compose-ro.yml`
- `nginx/default.conf`
- `docs/init_sql/common_config.sql`

您可以使用 SCP、SFTP 或其他文件传输工具：

```bash
# 示例：使用SCP从本地上传文件
scp docker-compose-ro.yml user@your-server-ip:~/lipeaks_backend/
scp nginx/default.conf user@your-server-ip:~/lipeaks_backend/nginx/
scp docs/init_sql/common_config.sql user@your-server-ip:~/lipeaks_backend/docs/init_sql/
```

### 2. 登录 Docker Hub（可选）

如果您的 Docker Hub 镜像是私有的，需要先登录：

```bash
docker login
# 输入您的Docker Hub用户名和密码
```

### 3. 启动应用

```bash
cd ~/lipeaks_backend

# 使用docker-compose-ro.yml启动应用
docker-compose -f docker-compose-ro.yml up -d
```

首次启动时，Docker 会自动从 Docker Hub 拉取所需的镜像，这可能需要一些时间，具体取决于您的网络速度。

### 4. 检查容器状态

```bash
docker-compose -f docker-compose-ro.yml ps
```

确保所有容器都处于 "Up" 状态。

## 验证部署

### 1. 访问前端应用

在浏览器中访问：`http://your-server-ip`

### 2. 检查后端API

```bash
curl http://your-server-ip/api/
```

### 3. 查看容器日志

如果遇到问题，可以查看容器日志：

```bash
# 查看web容器日志
docker-compose -f docker-compose-ro.yml logs web

# 查看frontend容器日志
docker-compose -f docker-compose-ro.yml logs frontend

# 查看db容器日志
docker-compose -f docker-compose-ro.yml logs db
```

## 常见问题及解决方案

### 1. 数据库连接问题

如果遇到数据库连接问题，请检查：

```bash
# 检查数据库容器是否正常运行
docker-compose -f docker-compose-ro.yml ps db

# 查看数据库日志
docker-compose -f docker-compose-ro.yml logs db
```

### 2. 前端无法访问

如果前端无法访问，请检查：

```bash
# 检查nginx配置
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) nginx -t

# 重启前端容器
docker-compose -f docker-compose-ro.yml restart frontend
```

### 3. 后端API无法访问

如果后端API无法访问，请检查：

```bash
# 查看后端日志
docker-compose -f docker-compose-ro.yml logs web

# 重启后端容器
docker-compose -f docker-compose-ro.yml restart web
```

## Docker 镜像拉取超时问题

在中国大陆地区，从 Docker Hub 拉取镜像时经常会遇到网络超时问题，例如：

```
ERROR: Get "https://registry-1.docker.io/v2/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)
```

### 解决方案

#### 1. 配置国内 Docker 镜像加速器

腾讯云提供了 Docker 镜像加速服务，可以大幅提高镜像下载速度。

**对于 Ubuntu/Debian 系统：**

```bash
# 创建或修改 daemon.json 文件
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ]
}
EOF

# 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker
```

**对于 CentOS 系统：**

```bash
# 创建或修改 daemon.json 文件
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ]
}
EOF

# 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### 2. 增加 Docker 拉取超时时间

如果配置镜像加速器后仍然遇到超时问题，可以尝试增加 Docker 拉取超时时间：

```bash
# 创建或修改 /etc/systemd/system/docker.service.d/timeout.conf 文件
sudo mkdir -p /etc/systemd/system/docker.service.d/
sudo tee /etc/systemd/system/docker.service.d/timeout.conf <<-'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --containerd=/run/containerd/containerd.sock --default-ulimit nofile=65536:65536 --max-concurrent-downloads=10 --max-download-attempts=5 --mtu=1400
EOF

# 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### 3. 手动下载并导入镜像

如果以上方法都不奏效，可以考虑在其他网络环境下载镜像，然后手动导入到服务器：

```bash
# 在网络良好的环境中，下载镜像并保存为文件
docker pull mysql:8.0
docker pull fx0883/lipeaks_backend:latest
docker pull fx0883/lipeaks_admin:latest

docker save -o mysql.tar mysql:8.0
docker save -o lipeaks_backend.tar fx0883/lipeaks_backend:latest
docker save -o lipeaks_admin.tar fx0883/lipeaks_admin:latest

# 将这些文件传输到腾讯云服务器
scp mysql.tar lipeaks_backend.tar lipeaks_admin.tar user@your-server-ip:~/lipeaks_backend/

# 在腾讯云服务器上加载这些镜像
docker load -i ~/lipeaks_backend/mysql.tar
docker load -i ~/lipeaks_backend/lipeaks_backend.tar
docker load -i ~/lipeaks_backend/lipeaks_admin.tar
```

加载完镜像后，再次尝试启动应用：

```bash
docker-compose -f docker-compose-ro.yml up -d
```

#### 4. 使用腾讯云容器镜像服务

如果您经常需要在腾讯云上部署 Docker 应用，可以考虑使用腾讯云容器镜像服务（TCR）：

1. 在腾讯云控制台创建个人版或企业版镜像仓库
2. 将您的镜像推送到腾讯云 TCR
3. 修改 docker-compose-ro.yml 文件，将镜像地址指向腾讯云 TCR

```yaml
services:
  web:
    image: ccr.ccs.tencentyun.com/your-namespace/lipeaks_backend:latest
    # ...其他配置...

  frontend:
    image: ccr.ccs.tencentyun.com/your-namespace/lipeaks_admin:latest
    # ...其他配置...
```

## API 请求连接问题

部署到腾讯云服务器后，前端应用可能会出现 API 请求错误：

```
POST http://localhost:8000/api/v1/auth/login/ net::ERR_CONNECTION_REFUSED
```

这是因为前端代码中的 API 请求地址被硬编码为 `localhost:8000`，而不是使用服务器的实际 IP 地址或域名。

### 解决方案

#### 1. 修改 Nginx 配置

Nginx 配置文件需要正确代理 API 请求，确保前端请求被正确转发到后端服务。

1. 检查并修改 `nginx/default.conf` 文件：

```bash
# 查看当前配置
cat ~/lipeaks_backend/nginx/default.conf
```

2. 确保配置文件包含以下代理设置：

```nginx
server {
    listen 80;
    server_name localhost;
    
    # 前端静态资源路径
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API 请求代理 - 确保包含 v1 路径
    location /api/ {
        proxy_pass http://web:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 特别处理 /api/v1 路径
    location /api/v1/ {
        proxy_pass http://web:8000/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 后端静态资源
    location /backend-static/ {
        proxy_pass http://web:8000/static/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /media/ {
        proxy_pass http://web:8000/media/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

3. 保存修改后的配置文件，并重新启动 frontend 容器：

```bash
docker-compose -f docker-compose-ro.yml restart frontend
```

#### 2. 修改前端环境变量配置

如果前端应用使用环境变量来配置 API 基础 URL，可以通过以下方式修改：

1. 创建或修改前端环境变量文件：

```bash
# 进入前端容器
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) /bin/sh

# 在容器内创建或修改环境变量文件
cd /usr/share/nginx/html
cat > env-config.js << EOF
window.ENV = {
  API_URL: '/api',
  API_VERSION: 'v1'
};
EOF

# 退出容器
exit
```

2. 确保前端代码使用这些环境变量，而不是硬编码的 URL。

#### 3. 使用 Nginx 重写规则

如果前端代码无法修改，可以使用 Nginx 的 URL 重写功能：

```nginx
server {
    listen 80;
    server_name localhost;
    
    # 其他配置...
    
    # 重写 localhost:8000 的请求
    location ~ ^/localhost:8000/(.*)$ {
        rewrite ^/localhost:8000/(.*)$ /$1 break;
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # 捕获所有对 localhost:8000 的请求
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 使用 sub_filter 替换 HTML 和 JS 中的 localhost:8000
        sub_filter 'http://localhost:8000' '';
        sub_filter_once off;
        sub_filter_types application/javascript text/javascript;
    }
    
    # 其他配置...
}
```

这种配置需要确保 Nginx 编译时包含了 `http_sub_module` 模块。

#### 4. 调试步骤

如果以上配置后仍然遇到问题，可以按照以下步骤进行调试：

1. 检查 Nginx 配置是否正确：

```bash
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) nginx -t
```

2. 查看 Nginx 访问日志和错误日志：

```bash
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) tail -f /var/log/nginx/access.log
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) tail -f /var/log/nginx/error.log
```

3. 使用 curl 测试 API 连接：

```bash
# 在服务器上测试
curl -v http://localhost/api/v1/auth/login/
```

4. 检查浏览器开发者工具中的网络请求，确认请求的实际 URL 和响应状态。

## 维护与更新

### 1. 更新镜像

当有新版本的镜像发布时，可以按以下步骤更新：

```bash
# 拉取最新镜像
docker-compose -f docker-compose-ro.yml pull

# 重新启动服务
docker-compose -f docker-compose-ro.yml up -d
```

### 2. 备份数据

定期备份数据库数据：

```bash
# 创建备份目录
mkdir -p ~/backups

# 备份数据库
docker exec $(docker-compose -f docker-compose-ro.yml ps -q db) mysqldump -u root -ppassword multi_tenant_db_dev > ~/backups/db_backup_$(date +%Y%m%d).sql
```

### 3. 监控服务状态

```bash
# 查看所有容器状态
docker-compose -f docker-compose-ro.yml ps

# 查看容器资源使用情况
docker stats
```

---

如有任何问题，请联系技术支持团队。 