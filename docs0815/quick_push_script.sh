#!/bin/bash
# 快速推送脚本 - 多租户后端系统 Docker 镜像
# 使用方法: ./quick_push_script.sh [用户名] [仓库名] [版本]

set -e

# 默认配置
DEFAULT_USERNAME="your-username"
DEFAULT_REPO="lipeaks-backend"
DEFAULT_VERSION="v1.0.0"

# 获取参数或使用默认值
USERNAME=${1:-$DEFAULT_USERNAME}
REPO=${2:-$DEFAULT_REPO}
VERSION=${3:-$DEFAULT_VERSION}
DATE=$(date +%Y%m%d)

echo "=== 多租户后端系统 Docker 镜像快速推送 ==="
echo "用户名: $USERNAME"
echo "仓库名: $REPO"
echo "版本: $VERSION"
echo "日期: $DATE"
echo ""

# 检查参数
if [ "$USERNAME" = "$DEFAULT_USERNAME" ]; then
    echo "使用方法: $0 [用户名] [仓库名] [版本]"
    echo "示例: $0 john lipeaks-backend v1.0.0"
    echo ""
    echo "或者编辑脚本修改默认值"
    exit 1
fi

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

# 检查当前目录
if [ ! -f "Dockerfile" ]; then
    echo "错误: 请在包含 Dockerfile 的项目根目录执行此脚本"
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
echo "=== 推送完成 ==="
echo "镜像地址: https://hub.docker.com/r/$USERNAME/$REPO"
echo "拉取命令: docker pull $USERNAME/$REPO:latest"
echo ""

# 显示镜像信息
echo "推送的镜像:"
docker images | grep $USERNAME/$REPO

echo ""
echo "是否清理本地镜像？(y/N): "
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "清理本地镜像..."
    docker rmi lipeaks-backend:latest 2>/dev/null || true
    docker rmi $USERNAME/$REPO:latest 2>/dev/null || true
    docker rmi $USERNAME/$REPO:$VERSION 2>/dev/null || true
    docker rmi $USERNAME/$REPO:$DATE 2>/dev/null || true
    echo "本地镜像清理完成"
fi

echo ""
echo "推送完成！可以更新 docker-compose.yml 使用远程镜像："
echo "image: $USERNAME/$REPO:latest"
