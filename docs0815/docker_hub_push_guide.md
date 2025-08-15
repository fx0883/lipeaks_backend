# Docker Hub 推送指南

## 概述

本指南详细说明如何将多租户后端系统的 web 容器构建并推送到 Docker Hub，包括镜像构建、标记、推送、版本管理和最佳实践。

## 前置要求

### 必需工具
- Docker 20.10+
- Docker Hub 账户
- 命令行终端

### 账户准备
1. **注册 Docker Hub 账户**
   - 访问 [hub.docker.com](https://hub.docker.com)
   - 完成注册和邮箱验证

2. **创建仓库**
   - 登录 Docker Hub
   - 点击 "Create Repository"
   - 选择仓库类型（Public 或 Private）
   - 输入仓库名称（如：`your-username/lipeaks-backend`）

## 镜像构建与推送流程

### 步骤 1: 登录 Docker Hub

```bash
# 登录 Docker Hub
docker login

# 输入用户名和密码
Username: your-username
Password: your-password

# 验证登录状态
docker info | grep Username
```

### 步骤 2: 构建镜像

#### 基础构建命令

```bash
# 在项目根目录执行
cd lipeaks_backend

# 构建镜像（使用当前目录的 Dockerfile）
docker build -t lipeaks-backend:latest .

# 查看构建的镜像
docker images | grep lipeaks-backend
```

#### 指定标签构建

```bash
# 构建带版本号的镜像
docker build -t lipeaks-backend:v1.0.0 .

# 构建带日期的镜像
docker build -t lipeaks-backend:$(date +%Y%m%d) .

# 构建多个标签
docker build -t lipeaks-backend:latest -t lipeaks-backend:v1.0.0 .
```

### 步骤 3: 标记镜像

#### 标记为 Docker Hub 仓库

```bash
# 标记镜像（替换为你的 Docker Hub 用户名和仓库名）
docker tag lipeaks-backend:latest your-username/lipeaks-backend:latest
docker tag lipeaks-backend:v1.0.0 your-username/lipeaks-backend:v1.0.0

# 查看所有标记的镜像
docker images | grep lipeaks-backend
```

#### 批量标记示例

```bash
# 创建标记脚本
cat > tag_images.sh << 'EOF'
#!/bin/bash
USERNAME="your-username"
REPO="lipeaks-backend"
VERSION="v1.0.0"
DATE=$(date +%Y%m%d)

echo "标记镜像..."
docker tag lipeaks-backend:latest $USERNAME/$REPO:latest
docker tag lipeaks-backend:latest $USERNAME/$REPO:$VERSION
docker tag lipeaks-backend:latest $USERNAME/$REPO:$DATE

echo "标记完成，查看镜像列表："
docker images | grep $USERNAME/$REPO
EOF

# 执行标记脚本
chmod +x tag_images.sh
./tag_images.sh
```

### 步骤 4: 推送镜像

#### 推送单个镜像

```bash
# 推送最新版本
docker push your-username/lipeaks-backend:latest

# 推送特定版本
docker push your-username/lipeaks-backend:v1.0.0
```

#### 批量推送

```bash
# 推送所有标记的镜像
docker push your-username/lipeaks-backend:latest
docker push your-username/lipeaks-backend:v1.0.0
docker push your-username/lipeaks-backend:20250815
```

#### 推送脚本示例

```bash
# 创建推送脚本
cat > push_images.sh << 'EOF'
#!/bin/bash
USERNAME="your-username"
REPO="lipeaks-backend"
VERSION="v1.0.0"
DATE=$(date +%Y%m%d)

echo "开始推送镜像到 Docker Hub..."

echo "推送 latest 标签..."
docker push $USERNAME/$REPO:latest

echo "推送版本标签 $VERSION..."
docker push $USERNAME/$REPO:$VERSION

echo "推送日期标签 $DATE..."
docker push $USERNAME/$REPO:$DATE

echo "所有镜像推送完成！"
echo "访问: https://hub.docker.com/r/$USERNAME/$REPO"
EOF

# 执行推送脚本
chmod +x push_images.sh
./push_images.sh
```

## 版本管理策略

### 标签命名规范

| 标签类型 | 格式 | 示例 | 说明 |
|----------|------|------|------|
| 最新版本 | `latest` | `latest` | 始终指向最新稳定版本 |
| 语义版本 | `vX.Y.Z` | `v1.0.0` | 遵循语义化版本控制 |
| 日期版本 | `YYYYMMDD` | `20250815` | 按日期标记的版本 |
| 分支版本 | `branch-name` | `develop` | 开发分支版本 |
| 提交版本 | `commit-hash` | `a1b2c3d` | Git 提交哈希 |

### 推荐标签策略

```bash
# 构建并标记多个版本
docker build -t lipeaks-backend:latest .
docker build -t lipeaks-backend:v1.0.0 .
docker build -t lipeaks-backend:$(date +%Y%m%d) .

# 标记为 Docker Hub 仓库
docker tag lipeaks-backend:latest your-username/lipeaks-backend:latest
docker tag lipeaks-backend:v1.0.0 your-username/lipeaks-backend:v1.0.0
docker tag lipeaks-backend:$(date +%Y%m%d) your-username/lipeaks-backend:$(date +%Y%m%d)

# 推送所有版本
docker push your-username/lipeaks-backend:latest
docker push your-username/lipeaks-backend:v1.0.0
docker push your-username/lipeaks-backend:$(date +%Y%m%d)
```

## 自动化脚本

### 完整构建推送脚本

```bash
#!/bin/bash
# 文件名: build_and_push.sh

set -e  # 遇到错误立即退出

# 配置变量
USERNAME="your-username"
REPO="lipeaks-backend"
VERSION="v1.0.0"
DATE=$(date +%Y%m%d)

echo "=== 多租户后端系统 Docker 镜像构建与推送 ==="
echo "用户名: $USERNAME"
echo "仓库名: $REPO"
echo "版本: $VERSION"
echo "日期: $DATE"
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行，请启动 Docker 服务"
    exit 1
fi

# 检查登录状态
if ! docker info | grep -q "Username"; then
    echo "请先登录 Docker Hub:"
    echo "docker login"
    exit 1
fi

echo "1. 构建 Docker 镜像..."
docker build -t lipeaks-backend:latest .

echo "2. 标记镜像..."
docker tag lipeaks-backend:latest $USERNAME/$REPO:latest
docker tag lipeaks-backend:latest $USERNAME/$REPO:$VERSION
docker tag lipeaks-backend:latest $USERNAME/$REPO:$DATE

echo "3. 推送镜像到 Docker Hub..."
echo "推送 latest 标签..."
docker push $USERNAME/$REPO:latest

echo "推送版本标签 $VERSION..."
docker push $USERNAME/$REPO:$VERSION

echo "推送日期标签 $DATE..."
docker push $USERNAME/$REPO:$DATE

echo ""
echo "=== 构建与推送完成 ==="
echo "镜像地址: https://hub.docker.com/r/$USERNAME/$REPO"
echo "拉取命令: docker pull $USERNAME/$REPO:latest"
echo ""

# 清理本地镜像（可选）
read -p "是否清理本地镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理本地镜像..."
    docker rmi lipeaks-backend:latest
    docker rmi $USERNAME/$REPO:latest
    docker rmi $USERNAME/$REPO:$VERSION
    docker rmi $USERNAME/$REPO:$DATE
    echo "本地镜像清理完成"
fi
```

### 使用自动化脚本

```bash
# 创建脚本文件
cat > build_and_push.sh << 'EOF'
# 将上面的脚本内容粘贴到这里
EOF

# 设置执行权限
chmod +x build_and_push.sh

# 执行脚本
./build_and_push.sh
```

## 验证推送结果

### 检查推送状态

```bash
# 查看本地镜像
docker images | grep your-username/lipeaks-backend

# 查看远程仓库信息
docker search your-username/lipeaks-backend

# 测试拉取镜像
docker pull your-username/lipeaks-backend:latest
```

### 访问 Docker Hub 仓库

1. 登录 [hub.docker.com](https://hub.docker.com)
2. 进入你的个人资料页面
3. 点击仓库名称
4. 查看推送的镜像和标签

## 更新 docker-compose.yml

### 使用 Docker Hub 镜像

推送完成后，可以更新 `docker-compose.yml` 文件使用远程镜像：

```yaml
version: '3.8'
services:
  web:
    # 使用本地构建的镜像
    # image: lipeaks_backend:latest
    
    # 使用 Docker Hub 镜像
    image: your-username/lipeaks-backend:latest
    
    # 或者使用特定版本
    # image: your-username/lipeaks-backend:v1.0.0
    
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    # ... 其他配置
```

### 生产环境配置

```yaml
version: '3.8'
services:
  web:
    # 生产环境使用固定版本标签
    image: your-username/lipeaks-backend:v1.0.0
    
    # 移除 build 配置，直接使用远程镜像
    restart: always
    environment:
      - DEBUG=False
      - IMPORT_DB_SNAPSHOT=false
    # ... 其他配置
```

## 最佳实践

### 构建优化

1. **使用 .dockerignore 文件**
   ```bash
   # 创建 .dockerignore 文件
   cat > .dockerignore << EOF
   .git
   .gitignore
   README.md
   docs/
   .env
   *.log
   __pycache__/
   .pytest_cache/
   .coverage
   EOF
   ```

2. **多阶段构建**
   ```dockerfile
   # 在 Dockerfile 中使用多阶段构建
   FROM python:3.13-slim-bullseye as builder
   # ... 构建阶段
   
   FROM python:3.13-slim-bullseye
   # ... 运行阶段
   ```

### 标签管理

1. **保持 latest 标签最新**
2. **使用语义化版本号**
3. **定期清理过期标签**
4. **为重要版本保留标签**

### 安全考虑

1. **不要在镜像中包含敏感信息**
2. **定期更新基础镜像**
3. **扫描镜像漏洞**
4. **使用私有仓库存储敏感镜像**

## 故障排除

### 常见问题

#### 1. 推送失败 - 认证错误

```bash
# 重新登录
docker logout
docker login

# 检查登录状态
docker info | grep Username
```

#### 2. 推送失败 - 网络问题

```bash
# 检查网络连接
ping hub.docker.com

# 使用代理（如果在中国大陆）
export DOCKER_PROXY="http://your-proxy:port"
```

#### 3. 镜像过大

```bash
# 查看镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 优化 Dockerfile
# - 使用 .dockerignore
# - 合并 RUN 命令
# - 清理缓存文件
```

#### 4. 标签冲突

```bash
# 删除冲突的标签
docker rmi your-username/lipeaks-backend:latest

# 重新标记
docker tag lipeaks-backend:latest your-username/lipeaks-backend:latest
```

### 调试命令

```bash
# 查看构建历史
docker history your-username/lipeaks-backend:latest

# 检查镜像内容
docker run --rm -it your-username/lipeaks-backend:latest ls -la /app

# 查看镜像详细信息
docker inspect your-username/lipeaks-backend:latest
```

## 维护操作

### 定期清理

```bash
# 清理未使用的镜像
docker image prune -f

# 清理所有未使用的资源
docker system prune -f

# 清理特定镜像
docker rmi $(docker images -q your-username/lipeaks-backend)
```

### 更新策略

```bash
# 拉取最新镜像
docker pull your-username/lipeaks-backend:latest

# 更新本地标签
docker tag your-username/lipeaks-backend:latest lipeaks-backend:latest

# 重启服务
docker-compose restart web
```

## 监控和统计

### 查看仓库统计

1. 登录 Docker Hub
2. 进入仓库页面
3. 查看下载统计
4. 监控仓库活动

### 设置通知

1. 在仓库设置中启用通知
2. 配置邮件或 Slack 通知
3. 监控推送和拉取活动

---

**相关文档：**
- [快速开始指南](./quick_start_guide.md)
- [完整部署指南](./docker_deployment_guide.md)
- [环境变量参考](./environment_variables_reference.md)

**文档版本：** 1.0  
**最后更新：** 2025-08-15  
**适用版本：** Docker 20.10+
