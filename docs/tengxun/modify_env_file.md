# 修改前端容器中的 .env 文件指南

本文档提供了如何进入前端容器内部并修改 .env 文件的详细步骤。

## 1. 进入前端容器

首先，登录到腾讯云服务器，然后执行以下命令进入前端容器：

```bash
# 登录到服务器
ssh root@your-server-ip

# 进入项目目录
cd ~/lipeaks_backend

# 获取前端容器ID
docker-compose -f docker-compose-ro.yml ps -q frontend

# 进入前端容器
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) /bin/sh
```

## 2. 查找 .env 文件

在容器内部，需要找到 .env 文件的位置。通常，前端应用的 .env 文件位于应用的根目录或 `/usr/share/nginx/html` 目录中：

```bash
# 进入 Nginx 的默认网站目录
cd /usr/share/nginx/html

# 查找 .env 文件
find . -name ".env*" -type f

# 如果没有找到，可以尝试搜索整个容器
find / -name ".env*" -type f 2>/dev/null
```

## 3. 检查现有环境配置

在修改 .env 文件之前，先检查是否存在其他环境配置文件：

```bash
# 查看目录内容
ls -la

# 查看可能存在的环境配置文件
cat .env
cat .env.production
cat env-config.js
cat config.js
```

## 4. 修改 .env 文件

找到 .env 文件后，可以使用 `vi` 或 `nano` 编辑器进行修改。如果容器中没有这些编辑器，可以使用 `cat` 和重定向来修改文件：

```bash
# 使用 vi 编辑器（如果容器中有）
vi .env

# 或者使用 nano 编辑器（如果容器中有）
nano .env

# 如果容器中没有编辑器，可以使用以下方法：
# 1. 查看当前内容
cat .env

# 2. 创建新的内容并覆盖原文件
cat > .env << EOF
VITE_API_BASE_URL=/api
VITE_API_VERSION=v1
# 添加其他需要的环境变量
EOF

# 3. 确认修改
cat .env
```

## 5. 如果 .env 文件不存在

如果找不到 .env 文件，可以创建一个新的环境配置文件：

```bash
# 创建 env-config.js 文件
cat > env-config.js << EOF
window.ENV = {
  API_URL: '/api',
  API_VERSION: 'v1'
};
EOF

# 确认文件内容
cat env-config.js
```

## 6. 修改 index.html

有时候，环境变量可能是在 index.html 文件中硬编码的。检查并修改 index.html：

```bash
# 查找 index.html
find . -name "index.html" -type f

# 查看 index.html 内容
cat index.html

# 备份原始文件
cp index.html index.html.bak

# 修改 index.html 中的 API URL
# 例如，将 http://localhost:8000 替换为空字符串
sed -i 's|http://localhost:8000||g' index.html

# 确认修改
grep -n "localhost:8000" index.html
```

## 7. 修改 JavaScript 文件

如果 API URL 是在编译后的 JavaScript 文件中硬编码的，可能需要找到并修改这些文件：

```bash
# 查找可能包含 localhost:8000 的 JS 文件
grep -r "localhost:8000" . --include="*.js"

# 对于找到的每个文件，可以进行替换
# 例如，如果在 assets/index-abc123.js 中找到了硬编码的 URL
cp assets/index-abc123.js assets/index-abc123.js.bak
sed -i 's|http://localhost:8000||g' assets/index-abc123.js
```

## 8. 退出容器并重启

修改完成后，退出容器并重启前端服务：

```bash
# 退出容器
exit

# 重启前端容器
docker-compose -f docker-compose-ro.yml restart frontend
```

## 9. 验证修改

重启后，验证修改是否生效：

```bash
# 查看前端容器日志
docker-compose -f docker-compose-ro.yml logs frontend

# 使用 curl 测试前端页面
curl -s http://localhost | grep -i "api"
```

## 10. 持久化修改

如果修改成功，可能希望将这些更改持久化，以便在容器重新创建时自动应用：

```bash
# 创建自定义 Dockerfile
cat > Dockerfile.frontend << EOF
FROM fx0883/lipeaks_admin:latest
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
RUN echo 'window.ENV = { API_URL: "/api", API_VERSION: "v1" };' > /usr/share/nginx/html/env-config.js
EOF

# 构建新镜像
docker build -t fx0883/lipeaks_admin:custom -f Dockerfile.frontend .

# 修改 docker-compose-ro.yml 使用新镜像
sed -i 's|fx0883/lipeaks_admin:latest|fx0883/lipeaks_admin:custom|g' docker-compose-ro.yml

# 重启服务
docker-compose -f docker-compose-ro.yml up -d
```

---

**注意**：修改容器内的文件是临时的，如果容器被删除或重新创建，这些修改将会丢失。为了永久保存修改，建议使用上述第 10 步中的方法创建自定义镜像。 