# 腾讯云服务器更新操作指南

本文档提供在腾讯云服务器上应用新的 Nginx 配置并重启服务的详细步骤。

## 1. 上传修改后的 Nginx 配置文件

首先，将修改后的 `default.conf` 文件上传到腾讯云服务器：

```bash
# 使用 SCP 上传文件（在本地执行）
scp nginx/default.conf root@your-server-ip:~/lipeaks_backend/nginx/
```

## 2. 应用新的 Nginx 配置

登录到腾讯云服务器，然后执行以下命令：

```bash
# 登录到服务器
ssh root@your-server-ip

# 进入项目目录
cd ~/lipeaks_backend

# 检查配置文件是否已上传
cat nginx/default.conf

# 将配置文件复制到 frontend 容器中
docker cp nginx/default.conf $(docker-compose -f docker-compose-ro.yml ps -q frontend):/etc/nginx/conf.d/default.conf

# 检查 Nginx 配置语法是否正确
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) nginx -t
```

## 3. 重启 frontend 容器

如果 Nginx 配置语法检查通过，重启 frontend 容器以应用新配置：

```bash
# 重启 frontend 容器
docker-compose -f docker-compose-ro.yml restart frontend

# 检查容器状态
docker-compose -f docker-compose-ro.yml ps
```

## 4. 验证配置是否生效

执行以下命令检查 Nginx 是否正确处理请求：

```bash
# 查看 Nginx 访问日志
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) tail -f /var/log/nginx/access.log

# 在另一个终端窗口，尝试访问 API
curl -v http://localhost/api/v1/auth/login/
```

## 5. 检查前端应用

在浏览器中访问您的应用（使用服务器 IP 地址或域名），并使用浏览器开发者工具检查网络请求：

1. 打开浏览器开发者工具（F12 或右键 -> 检查）
2. 切换到"网络"或"Network"选项卡
3. 尝试登录或执行其他 API 操作
4. 检查请求是否成功，特别关注 `/api/v1/auth/login/` 请求

## 6. 故障排除

如果仍然遇到问题，请尝试以下步骤：

### 6.1 检查 Nginx 错误日志

```bash
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) tail -f /var/log/nginx/error.log
```

### 6.2 检查后端服务是否正常运行

```bash
# 检查 web 容器状态
docker-compose -f docker-compose-ro.yml ps web

# 查看 web 容器日志
docker-compose -f docker-compose-ro.yml logs web
```

### 6.3 尝试重启所有服务

如果单独重启 frontend 容器不解决问题，可以尝试重启所有服务：

```bash
docker-compose -f docker-compose-ro.yml down
docker-compose -f docker-compose-ro.yml up -d
```

### 6.4 检查容器网络

```bash
# 检查容器网络
docker network ls
docker network inspect lipeaks_backend_default
```

## 7. 持久化配置

如果一切正常，您可能希望将修改后的配置文件永久保存，以便在容器重新创建时自动使用：

```bash
# 备份原始配置文件
cp nginx/default.conf nginx/default.conf.bak

# 从容器中导出当前正在使用的配置（以防有任何运行时更改）
docker exec -it $(docker-compose -f docker-compose-ro.yml ps -q frontend) cat /etc/nginx/conf.d/default.conf > nginx/default.conf
```

## 8. 安全注意事项

确保您的服务器已配置适当的防火墙规则，只允许必要的端口（如 80、443）对外开放：

```bash
# 检查防火墙状态
ufw status

# 如果需要，允许 HTTP 和 HTTPS 流量
ufw allow 80/tcp
ufw allow 443/tcp
```

---

如果您在执行上述步骤时遇到任何问题，请参考完整的[腾讯云部署指南](deployment_guide.md)或联系技术支持团队。 