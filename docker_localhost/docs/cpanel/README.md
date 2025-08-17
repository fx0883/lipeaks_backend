# Django项目部署到cPanel指南

这个目录包含了将Django项目部署到cPanel托管环境的详细指南。

## 快速入门

请从[索引文档](index.md)开始阅读，该文档提供了所有指南的概述和链接。

## 文档结构

文档按照部署流程的顺序组织，从环境准备到维护和更新：

1. [部署概述](01_deployment_guide.md)
2. [准备cPanel环境](02_cpanel_preparation.md)
3. [上传和配置项目代码](03_code_upload.md)
4. [配置Python环境](04_python_setup.md)
5. [数据库配置与迁移](05_database_setup.md)
6. [静态文件与媒体文件配置](06_static_media_files.md)
7. [域名配置与应用启动](07_domain_launch.md)
8. [性能优化与安全配置](08_optimization_security.md)
9. [常见问题排查](09_troubleshooting.md)
10. [维护与更新指南](10_maintenance.md)

## 使用建议

- 按照顺序阅读文档
- 根据您的具体环境调整命令和配置
- 在执行任何命令前，确保已经备份重要数据

## 注意事项

这些文档基于Django 5.2和Python 3.12版本编写，适用于支持Python应用程序的cPanel主机。 