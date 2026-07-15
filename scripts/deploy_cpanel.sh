#!/usr/bin/env bash
# =============================================================================
# LiPeaks Backend cPanel 一键部署脚本
# =============================================================================
# 用法：
#   首次部署：./scripts/deploy_cpanel.sh --setup
#   更新部署：./scripts/deploy_cpanel.sh
#   指定分支更新：./scripts/deploy_cpanel.sh --branch main
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# 颜色输出
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# -----------------------------------------------------------------------------
# 默认配置（根据你的 cPanel 环境修改）
# -----------------------------------------------------------------------------
# cPanel 用户名
CPANEL_USER="${CPANEL_USER:-$(whoami)}"

# 项目路径
PROJECT_DIR="${PROJECT_DIR:-/home/${CPANEL_USER}/lipeaks_backend}"

# Python 虚拟环境路径（cPanel Setup Python App 自动生成）
# 示例：/home/username/virtualenv/lipeaks_backend/3.12/bin/activate
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
VENV_DIR="${VENV_DIR:-/home/${CPANEL_USER}/virtualenv/lipeaks_backend/${PYTHON_VERSION}}"
VENV_ACTIVATE="${VENV_DIR}/bin/activate"

# 域名（用于健康检查）
DOMAIN="${DOMAIN:-}"

# Git 分支
BRANCH="${BRANCH:-}"

# 是否首次设置
SETUP_MODE=false

# 是否跳过 git pull
SKIP_PULL=false

# -----------------------------------------------------------------------------
# 参数解析
# -----------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        --setup)
            SETUP_MODE=true
            shift
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --skip-pull)
            SKIP_PULL=true
            shift
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --python-version)
            PYTHON_VERSION="$2"
            VENV_DIR="/home/${CPANEL_USER}/virtualenv/lipeaks_backend/${PYTHON_VERSION}"
            VENV_ACTIVATE="${VENV_DIR}/bin/activate"
            shift 2
            ;;
        --help|-h)
            cat << EOF
LiPeaks Backend cPanel 部署脚本

用法：
  ./scripts/deploy_cpanel.sh [选项]

选项：
  --setup              首次设置模式（创建目录、执行完整初始化）
  --branch <branch>   更新时切换到指定 Git 分支
  --skip-pull          跳过 git pull
  --domain <domain>   设置域名，用于部署后健康检查
  --python-version <v> 指定 Python 版本（默认 3.12）
  --help, -h           显示本帮助

环境变量：
  CPANEL_USER          cPanel 用户名（默认当前用户）
  PROJECT_DIR          项目路径
  VENV_DIR             虚拟环境路径
  DOMAIN               域名

示例：
  # 首次部署
  ./scripts/deploy_cpanel.sh --setup

  # 更新代码并重新部署
  ./scripts/deploy_cpanel.sh --branch main

  # 只执行迁移和重启，不拉代码
  ./scripts/deploy_cpanel.sh --skip-pull
EOF
            exit 0
            ;;
        *)
            error "未知参数: $1"
            exit 1
            ;;
    esac
done

# -----------------------------------------------------------------------------
# 前置检查
# -----------------------------------------------------------------------------
info "开始部署 LiPeaks Backend 到 cPanel..."
info "cPanel 用户: ${CPANEL_USER}"
info "项目目录: ${PROJECT_DIR}"
info "虚拟环境: ${VENV_DIR}"

# 检查项目目录
if [[ ! -d "${PROJECT_DIR}" ]]; then
    if [[ "${SETUP_MODE}" == "true" ]]; then
        warn "项目目录不存在，创建中: ${PROJECT_DIR}"
        mkdir -p "${PROJECT_DIR}"
    else
        error "项目目录不存在: ${PROJECT_DIR}"
        error "如果是首次部署，请使用 --setup 参数"
        exit 1
    fi
fi

cd "${PROJECT_DIR}"

# 检查 .env 文件
if [[ ! -f ".env" && ! -f ".env.prod" ]]; then
    if [[ -f ".env.prod.example" ]]; then
        warn "未找到 .env 或 .env.prod，将从 .env.prod.example 创建 .env.prod"
        cp .env.prod.example .env.prod
        warn "请先编辑 .env.prod 填入实际值，然后重新运行脚本"
        error "部署已中止，请配置环境变量后再试"
        exit 1
    else
        error "未找到 .env、.env.prod 或 .env.prod.example"
        exit 1
    fi
fi

# 检查虚拟环境
if [[ ! -f "${VENV_ACTIVATE}" ]]; then
    error "找不到虚拟环境激活脚本: ${VENV_ACTIVATE}"
    error "请确认:"
    error "1. 已在 cPanel 中创建 Python Application"
    error "2. PYTHON_VERSION 设置正确（默认 3.12）"
    error "3. 项目路径与 cPanel 中配置的 Application root 一致"
    exit 1
fi

# 检查是否在 Git 仓库中（用于拉取代码）
if [[ "${SKIP_PULL}" == "false" ]]; then
    if [[ ! -d ".git" ]]; then
        warn "当前目录不是 Git 仓库，跳过 git pull"
        SKIP_PULL=true
    fi
fi

# -----------------------------------------------------------------------------
# 激活虚拟环境
# -----------------------------------------------------------------------------
info "激活虚拟环境..."
source "${VENV_ACTIVATE}"
python --version

# -----------------------------------------------------------------------------
# 更新代码（可选）
# -----------------------------------------------------------------------------
if [[ "${SKIP_PULL}" == "false" ]]; then
    info "拉取最新代码..."
    if [[ -n "${BRANCH}" ]]; then
        git fetch origin
        git checkout "${BRANCH}"
        git pull origin "${BRANCH}"
    else
        git pull
    fi
    success "代码更新完成"
fi

# -----------------------------------------------------------------------------
# 首次设置：创建必要目录
# -----------------------------------------------------------------------------
if [[ "${SETUP_MODE}" == "true" ]]; then
    info "首次设置：创建必要目录..."
    mkdir -p logs
    mkdir -p media
    mkdir -p staticfiles
    mkdir -p tmp
    success "目录创建完成"
fi

# -----------------------------------------------------------------------------
# 安装依赖
# -----------------------------------------------------------------------------
info "安装/更新 Python 依赖..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
success "依赖安装完成"

# -----------------------------------------------------------------------------
# 数据库迁移
# -----------------------------------------------------------------------------
info "执行数据库迁移..."
python manage.py migrate --noinput
success "数据库迁移完成"

# -----------------------------------------------------------------------------
# 收集静态文件
# -----------------------------------------------------------------------------
info "收集静态文件..."
python manage.py collectstatic --noinput --clear
success "静态文件收集完成"

# -----------------------------------------------------------------------------
# 首次设置：创建超级管理员（可选）
# -----------------------------------------------------------------------------
if [[ "${SETUP_MODE}" == "true" ]]; then
    warn "是否创建超级管理员？(y/n)"
    read -r create_superuser
    if [[ "${create_superuser}" == "y" || "${create_superuser}" == "Y" ]]; then
        python manage.py createsuperuser
    fi
fi

# -----------------------------------------------------------------------------
# 设置文件权限
# -----------------------------------------------------------------------------
info "设置文件权限..."
chmod 600 .env 2>/dev/null || true
chmod 600 .env.prod 2>/dev/null || true
chmod -R 755 logs media staticfiles tmp 2>/dev/null || true
success "文件权限设置完成"

# -----------------------------------------------------------------------------
# 重启应用
# -----------------------------------------------------------------------------
info "重启 Python Application..."
if [[ -f "tmp/restart.txt" ]]; then
    touch tmp/restart.txt
    success "已触发 Passenger 重启"
elif command -v Passenger > /dev/null 2>&1; then
    passenger-config restart-app "${PROJECT_DIR}" 2>/dev/null || true
    success "已使用 passenger-config 重启"
else
    warn "未找到 tmp/restart.txt 或 passenger-config"
    warn "请在 cPanel → Setup Python App 中手动点击 Restart"
fi

# -----------------------------------------------------------------------------
# 健康检查
# -----------------------------------------------------------------------------
if [[ -n "${DOMAIN}" ]]; then
    info "等待应用启动..."
    sleep 3

    info "执行健康检查: https://${DOMAIN}/api/v1/feedbacks/health/"
    if command -v curl > /dev/null 2>&1; then
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/api/v1/feedbacks/health/" || echo "000")
        if [[ "${http_code}" == "200" ]]; then
            success "健康检查通过 (HTTP ${http_code})"
        else
            warn "健康检查返回 HTTP ${http_code}"
            warn "请检查日志: ${PROJECT_DIR}/logs/"
            warn "或 cPanel 错误日志: /home/${CPANEL_USER}/logs/${DOMAIN}/error_log"
        fi
    else
        warn "未安装 curl，跳过健康检查"
    fi
else
    warn "未设置 DOMAIN，跳过健康检查"
    info "可手动访问: https://your-domain.com/api/v1/feedbacks/health/"
fi

success "部署完成！"
