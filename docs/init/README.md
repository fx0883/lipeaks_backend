# 部署指南

本目录包含项目的部署文档和配置示例。

## 文档列表

- [本地部署指南](./local_deployment_guide.md) - 如何在本地环境部署项目
- [Docker部署指南](./docker_deployment_guide.md) - 如何使用Docker部署项目

## 配置文件示例

本目录还包含以下Docker部署所需的配置文件示例：

- [Dockerfile.sample](./Dockerfile.sample) - Docker容器配置示例
- [docker-compose.yml.sample](./docker-compose.yml.sample) - Docker Compose配置示例
- [docker-entrypoint.sh.sample](./docker-entrypoint.sh.sample) - Docker启动脚本示例

## 使用方法

1. 复制示例配置文件到项目根目录：
   ```bash
   cp docs/init/Dockerfile.sample ./Dockerfile
   cp docs/init/docker-compose.yml.sample ./docker-compose.yml
   cp docs/init/docker-entrypoint.sh.sample ./docker-entrypoint.sh
   chmod +x ./docker-entrypoint.sh
   ```

2. 根据需要修改配置文件中的参数

3. 按照相应的部署指南进行部署

## 注意事项

- 请确保在生产环境中更改默认密码
- 建议为生产环境配置HTTPS
- 定期备份数据库 