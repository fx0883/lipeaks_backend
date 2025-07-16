# Windows 下部署到 Docker Hub 指南

本文档提供了在 Windows 操作系统下将 Lipeaks Backend 项目部署到 Docker Hub 的详细步骤。

## 前提条件

1. Windows 10/11 操作系统
2. 已安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
3. 已创建 [Docker Hub](https://hub.docker.com/) 账户
4. Git 客户端 (可选，用于克隆代码仓库)

## 1. 安装 Docker Desktop for Windows

1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 安装过程中，选择使用 WSL 2 后端（推荐，性能更好）
3. 安装完成后启动 Docker Desktop
4. 验证安装：打开 PowerShell 或命令提示符，运行以下命令：

```powershell
docker --version
docker-compose --version
```

## 2. 准备项目文件

1. 确保项目中已包含以下文件：
   - `Dockerfile`（项目根目录）
   - `docker-compose.yml`（项目根目录）
   - `docker-entrypoint.sh`（项目根目录）
   - `.env`文件（根据`.env.example`创建）

2. 创建或更新 `docker-entrypoint.sh` 文件并设置执行权限：

```powershell
# 在PowerShell中创建文件
Copy-Item -Path "docs\init\docker-entrypoint.sh.sample" -Destination "docker-entrypoint.sh"
```

3. 创建 `.env` 文件：

```powershell
# 在PowerShell中创建文件
Copy-Item -Path ".env.example" -Destination ".env"
# 使用记事本或其他编辑器打开并填写配置
notepad .env
```

## 3. 构建 Docker 镜像

1. 打开 PowerShell，进入项目根目录：

```powershell
cd D:\GitHub\lipeaks_backend  # 替换为您的实际项目路径
```

2. 构建 Docker 镜像：

```powershell
docker build -t lipeaks_backend:latest .
```

3. 检查构建的镜像：

```powershell
docker images
```

## 4. 本地测试 Docker 镜像

1. 启动容器：

```powershell
docker-compose up -d
```

2. 查看容器状态：

```powershell
docker-compose ps
```

3. 查看容器日志：

```powershell
docker-compose logs -f web
```

4. 访问应用：在浏览器中访问 `http://localhost:8000`

## 5. 发布到 Docker Hub

1. 登录到 Docker Hub：

```powershell
docker login
# 输入您的 Docker Hub 用户名和密码
```

2. 为镜像添加标签（替换 `your_username` 为您的 Docker Hub 用户名）：

```powershell
docker tag lipeaks_backend:latest your_username/lipeaks_backend:latest
```

3. 推送镜像到 Docker Hub：

```powershell
docker push your_username/lipeaks_backend:latest
```

4. 验证推送结果：访问 `https://hub.docker.com/r/your_username/lipeaks_backend`

## 6. 使用 Docker Hub 镜像部署

1. 在任何安装了 Docker 的环境中，创建 `.env` 文件和 `docker-compose.yml` 文件。

2. 修改 `docker-compose.yml` 文件中的镜像名称：

```yaml
services:
  web:
    image: your_username/lipeaks_backend:latest
    # 其他配置...
```

3. 启动服务：

```bash
docker-compose up -d
```

## 常见问题和故障排除

### 构建过程中出现网络错误

如果在构建过程中遇到网络问题，尝试设置 Docker 镜像加速：

1. 打开 Docker Desktop
2. 进入 Settings > Docker Engine
3. 添加或修改 registry-mirrors 配置：

```json
{
  "registry-mirrors": [
    "https://registry.docker-cn.com",
    "https://mirror.baidubce.com"
  ]
}
```

### 数据库连接问题

如果应用无法连接到数据库：

1. 检查 `.env` 文件中的数据库配置
2. 确认 MySQL 容器是否正常运行：`docker-compose ps`
3. 查看 MySQL 容器日志：`docker-compose logs db`

### 文件权限问题

如果出现文件权限错误：

1. 检查 `docker-entrypoint.sh` 是否具有执行权限
2. 在 Windows 环境中可能需要编辑 `Dockerfile` 并确保包含：

```dockerfile
RUN chmod +x /app/docker-entrypoint.sh
```

### 端口冲突

如果端口已被占用：

1. 修改 `docker-compose.yml` 中的端口映射
2. 例如，将 `8000:8000` 改为 `8001:8000`

## 其他资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Docker Hub 文档](https://docs.docker.com/docker-hub/) 