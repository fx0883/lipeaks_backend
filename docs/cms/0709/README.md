# 0709 API 文档

> 创建日期：2026-07-09
> 模块：CMS

## 文档列表

| # | API | 文件 |
|---|-----|------|
| 1 | 获取管理员专属分类（is_admin_only=true） | [01_list_admin_only_categories.md](01_list_admin_only_categories.md) |
| 2 | 获取分类下所有文章 | [02_list_articles_by_category.md](02_list_articles_by_category.md) |

## 共同说明

两个接口均为 **GET** 请求、**无需登录 token**，但由于系统是多租户架构，必须带 `X-Tenant-ID` 请求头指定租户。

### 标准响应包裹

成功：

```json
{ "success": true, "code": 2000, "message": "操作成功", "data": ... }
```

缺少 `X-Tenant-ID` 时（HTTP 400）：

```json
{ "success": false, "code": 4001, "message": "未提供租户ID，无法访问CMS资源", "data": null }
```

### 请求头约定

| 名称 | 必填 | 说明 |
|------|------|------|
| X-Tenant-ID | 是 | 租户 ID（数字） |
| Authorization | 否 | 登录 token；不传即游客身份 |
| Accept-Language | 否 | 语言，默认 `zh-hans` |
