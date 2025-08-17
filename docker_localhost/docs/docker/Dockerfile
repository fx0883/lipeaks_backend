FROM python:3.13-slim-bullseye

WORKDIR /app

# 更改apt源为中国镜像源并安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org/debian-security|mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    default-libmysqlclient-dev \
    build-essential \
    python3-dev \
    gcc \
    netcat-openbsd \
    pkg-config \
    libxml2-dev \
    libxslt1-dev \
    libssl-dev \
    libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .

# 分步安装 Python 依赖 - 先安装基础工具
RUN pip install --upgrade pip
RUN pip install --no-cache-dir setuptools wheel

# 尝试使用国内镜像源安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ || \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建必要的目录
RUN mkdir -p logs
RUN mkdir -p staticfiles
RUN mkdir -p media

# 使容器可执行
RUN chmod +x /app/docker-entrypoint.sh

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"] 