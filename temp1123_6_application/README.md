# Application APIs 测试与文档

## 概述

本目录包含Application应用管理模块的所有API测试结果和文档。

## 目录结构

```
temp1123_6_application/
├── README.md                          # 本文件
├── 00_测试报告.md                     # 完整测试报告
├── 01_应用管理API文档.md              # 详细API文档
├── test_all_apis.sh                   # 自动化测试脚本
├── add_fields.py                      # 数据库修复脚本
├── fix_application_fields.sql         # SQL修复语句
├── check_db.py                        # 数据库检查脚本
├── test_articles.py                   # 文章关联测试
├── test_articles_full.py              # 文章完整测试
└── debug_shell.py                     # 调试脚本
```

## 快速开始

### 1. 运行完整测试

```bash
# 添加执行权限
chmod +x test_all_apis.sh

# 运行测试
./test_all_apis.sh
```

### 2. 查看API文档

详细的API使用说明请查看：
- [01_应用管理API文档.md](./01_应用管理API文档.md)

### 3. 查看测试报告

完整的测试结果和问题修复记录请查看：
- [00_测试报告.md](./00_测试报告.md)

## API列表

| 序号 | 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|------|
| 1 | GET | `/api/v1/applications/` | 获取应用列表 | ✅ |
| 2 | POST | `/api/v1/applications/` | 创建应用 | ✅ |
| 3 | GET | `/api/v1/applications/{id}/` | 获取应用详情 | ✅ |
| 4 | PUT | `/api/v1/applications/{id}/` | 完整更新应用 | ✅ |
| 5 | PATCH | `/api/v1/applications/{id}/` | 部分更新应用 | ✅ |
| 6 | DELETE | `/api/v1/applications/{id}/` | 删除应用 | ✅ |
| 7 | GET | `/api/v1/applications/{id}/statistics/` | 获取应用统计 | ✅ |
| 8 | GET | `/api/v1/applications/{id}/articles/` | 获取应用关联文章 | ✅ |

**测试结果**: 8/8 通过 ✅

## 已修复的问题

### 1. 数据库字段缺失

**问题**: `licenses_license`表缺少`application_id`字段

**修复**: 执行`add_fields.py`脚本添加字段

### 2. ViewSet方法错误

**问题**: `get_tenant_id()`方法不存在

**修复**: 修改为直接使用`application.tenant_id`

详细修复记录见[00_测试报告.md](./00_测试报告.md)

## 认证信息

测试使用的租户管理员Token（示例）:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM
```

**注意**: 
- 此Token仅用于开发测试
- 生产环境请使用自己的有效Token
- Token会过期，需要重新获取

## 使用curl测试单个API

```bash
# 设置Token
TOKEN="YOUR_TOKEN_HERE"

# 获取应用列表
curl -X GET "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq .

# 创建应用
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的应用",
    "code": "my-app",
    "description": "测试应用",
    "current_version": "1.0.0",
    "status": "development"
  }' | jq .

# 获取应用详情
curl -X GET "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq .

# 获取应用统计
curl -X GET "http://localhost:8000/api/v1/applications/1/statistics/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq .
```

## 相关文档

- Django REST Framework: https://www.django-rest-framework.org/
- Swagger API文档: http://localhost:8000/api/schema/swagger-ui/
- ReDoc API文档: http://localhost:8000/api/schema/redoc/

## 联系方式

如有问题，请参考：
- [00_测试报告.md](./00_测试报告.md) - 完整测试报告
- [01_应用管理API文档.md](./01_应用管理API文档.md) - API详细文档
