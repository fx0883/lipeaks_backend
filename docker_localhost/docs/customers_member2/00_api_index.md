# 成员(Member)管理 API 文档索引

## 简介

成员(Member)管理API提供了对系统中普通成员用户的创建、查询、更新和删除等功能。这些API专门设计用于操作`Member`模型的实例，区别于管理员用户API。

## Base URL

```
/api/v1/members/
```

## 认证方式

所有 API 请求需要在 HTTP 头部包含有效的 JWT 令牌：

```
Authorization: Bearer <token>
```

## 权限控制

- **超级管理员**：可以访问所有成员 API
- **租户管理员**：可以管理自己租户内的成员
- **普通成员**：只能访问和修改自己的信息和子账号

## API 文档目录

1. [成员基本操作 API](./01_member_basic_api.md)
   - 获取成员列表
   - 创建成员
   - 获取成员详情
   - 更新成员信息
   - 删除成员
   - 获取当前登录成员信息

2. [成员头像上传 API](./02_member_avatar_api.md)
   - 上传当前成员头像
   - 为特定成员上传头像

3. [子账号管理 API](./03_member_subaccount_api.md)
   - 获取子账号列表
   - 创建子账号
   - 获取子账号详情
   - 更新子账号
   - 删除子账号

4. [密码管理 API](./04_member_password_api.md)
   - 修改当前成员密码

5. [客户-联系人关系 API](./05_customer_member_relation_api.md)
   - 获取客户下的所有联系人列表
   - 获取联系人所属的所有客户列表

## 数据模型

### Member 模型

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| id | BigAutoField | 主键 | PK |
| username | CharField | 用户名 | unique |
| password | CharField | 密码 | - |
| email | EmailField | 邮箱 | - |
| phone | CharField | 手机号 | null=True |
| nick_name | CharField | 昵称 | null=True |
| avatar | CharField | 头像 | blank=True |
| first_name | CharField | 名 | blank=True |
| last_name | CharField | 姓 | blank=True |
| is_active | BooleanField | 是否激活 | default=True |
| status | CharField | 状态 | default='active' |
| tenant_id | ForeignKey | 关联租户ID | null=True |
| parent | ForeignKey | 父账号ID | null=True |
| is_deleted | BooleanField | 是否删除 | default=False |
| last_login | DateTimeField | 最后登录时间 | null=True |
| last_login_ip | CharField | 最后登录IP | null=True |
| date_joined | DateTimeField | 注册时间 | auto_now_add=True |

## 响应格式

所有 API 响应均使用统一的 JSON 格式：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    // 响应数据
  }
}
```

错误响应格式：

```json
{
  "success": false,
  "code": 4000,
  "message": "操作失败",
  "data": {
    "detail": "错误详情"
  }
}
```

## 状态码说明

| 状态码 | 说明 |
|-------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 | 