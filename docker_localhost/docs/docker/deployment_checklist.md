# Docker部署检查清单

使用以下检查清单确保Docker部署流程顺利完成。

## 环境准备检查

- [ ] 已安装Docker Desktop for Windows
- [ ] Docker服务正在运行
- [ ] 已登录Docker Hub账户
- [ ] 已克隆或更新项目代码

## 文件准备检查

- [ ] 项目根目录中存在`Dockerfile`
- [ ] 已创建`docker-entrypoint.sh`文件（从sample文件复制）
- [ ] 已设置`docker-entrypoint.sh`执行权限
- [ ] 已创建或更新`docker-compose.yml`文件
- [ ] 已从`.env.example`创建并配置`.env`文件
- [ ] 已确认MySQL初始化SQL文件路径正确

## 构建与测试检查

- [ ] 已成功构建Docker镜像：`docker build -t lipeaks_backend:latest .`
- [ ] 已验证镜像创建成功：`docker images`
- [ ] 已启动测试容器：`docker-compose up -d`
- [ ] 数据库容器运行状态正常：`docker-compose ps`
- [ ] Web应用容器运行状态正常：`docker-compose ps`
- [ ] 已验证应用访问：`http://localhost:8000`
- [ ] 已检查应用日志无错误：`docker-compose logs web`

## Docker Hub发布检查

- [ ] 已登录Docker Hub：`docker login`
- [ ] 已为镜像添加标签：`docker tag lipeaks_backend:latest your_username/lipeaks_backend:latest`
- [ ] 已成功推送镜像：`docker push your_username/lipeaks_backend:latest`
- [ ] 已在Docker Hub网站验证镜像存在

## 部署后检查

- [ ] 已关闭测试容器：`docker-compose down`
- [ ] 已使用Docker Hub镜像重新启动容器
- [ ] 已验证服务正常运行
- [ ] 已备份配置和数据库

## 安全检查

- [ ] 已修改默认数据库密码
- [ ] 已生成新的Django SECRET_KEY
- [ ] 已确保.env文件未被提交到代码仓库
- [ ] 已配置必要的防火墙规则

## 性能检查

- [ ] 容器资源使用情况正常：`docker stats`
- [ ] 应用响应时间正常
- [ ] 数据库连接数正常

## 备注

添加部署过程中的特殊情况或需要注意的事项：

```
# 部署中遇到的问题和解决方案记录在此
``` 