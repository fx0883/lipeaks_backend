# 租户管理模块开发指南

## 简介

租户管理模块是一个多租户SaaS应用的核心组件，用于管理系统中的租户及其资源配额。该模块提供了完整的租户生命周期管理，包括创建、查询、更新、删除租户，以及管理租户的配额和状态。

本文档旨在指导开发人员如何与租户管理API进行交互，实现租户管理功能。

## 文档结构

- [租户管理概述](./README.md)：本文档，提供模块概述和文档导航
- [租户基础操作](./01-tenant-basic-operations.md)：租户的创建、查询、更新和删除
- [租户配额管理](./02-tenant-quota-management.md)：租户配额的查询和更新
- [租户状态管理](./03-tenant-status-management.md)：租户的激活和暂停
- [租户用户管理](./04-tenant-user-management.md)：租户下用户的管理
- [租户API完整参考](./05-tenant-api-reference.md)：所有API端点的详细参考
- [前端开发计划](./06-frontend-development-plan.md)：租户管理模块的前端开发计划

## 认证与授权

租户管理API需要JWT认证。在调用API之前，需要先获取访问令牌，并在请求头中包含：

```
Authorization: Bearer {access_token}
```

大多数租户管理API仅允许超级管理员访问，部分API（如查询配额使用情况）允许租户管理员访问。

## 下一步

请从[租户基础操作](./01-tenant-basic-operations.md)开始，了解如何实现租户的基本管理功能。 