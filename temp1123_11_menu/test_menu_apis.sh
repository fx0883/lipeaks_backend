#!/bin/bash

# 菜单API测试脚本
# 服务器地址
BASE_URL="http://localhost:8000/api/v1/menus"

# 租户管理员Token
TENANT_ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"

# 超级管理员Token
SUPER_ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzY0NTEwNzExLCJtb2RlbF90eXBlIjoidXNlciIsImlzX2FkbWluIjp0cnVlLCJpc19zdXBlcl9hZG1pbiI6dHJ1ZSwiaXNfc3RhZmYiOnRydWV9.fr23WBsROaD207MCYN-cLzVpR3gqA7EPiFoivmmfNeQ"

echo "=========================================="
echo "菜单API测试 - 租户管理员"
echo "=========================================="

echo ""
echo "1. 测试: GET /api/v1/menus/ - 获取菜单列表"
curl -X GET "${BASE_URL}/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "2. 测试: GET /api/v1/menus/{id}/ - 获取单个菜单"
curl -X GET "${BASE_URL}/23/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "3. 测试: POST /api/v1/menus/ - 创建菜单"
curl -X POST "${BASE_URL}/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_menu_tenant",
    "code": "test_menu_tenant",
    "path": "/test_tenant",
    "title": "租户测试菜单",
    "rank": 100,
    "is_active": true
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "4. 测试: GET /api/v1/menus/tree/ - 获取菜单树形结构"
curl -X GET "${BASE_URL}/tree/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" | head -c 500

echo ""
echo ""
echo "----------------------------------------"
echo ""
echo "5. 测试: GET /api/v1/menus/admin/routes/ - 获取管理员菜单路由"
curl -X GET "${BASE_URL}/admin/routes/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" | head -c 500

echo ""
echo ""
echo "----------------------------------------"
echo ""
echo "6. 测试: GET /api/v1/menus/user/ - 获取current用户的菜单"
curl -X GET "${BASE_URL}/user/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" | head -c 500

echo ""
echo ""
echo "----------------------------------------"
echo ""
echo "7. 测试: GET /api/v1/menus/admins/{user_id}/menus/ - 获取用户的菜单列表"
curl -X GET "${BASE_URL}/admins/3/menus/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "8. 测试: POST /api/v1/menus/admins/{user_id}/menus/ - 分配菜单给用户 (需要超级管理员)"
curl -X POST "${BASE_URL}/admins/3/menus/" \
  -H "Authorization: Bearer ${TENANT_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"menu_ids": [23, 28]}' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "=========================================="
echo "需要超级管理员权限的API测试"
echo "=========================================="

echo ""
echo "9. 测试: POST /api/v1/menus/admins/{user_id}/menus/ - 分配菜单给用户 (使用超级管理员)"
curl -X POST "${BASE_URL}/admins/3/menus/" \
  -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"menu_ids": [23, 28, 29]}' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "10. 测试: DELETE /api/v1/menus/admins/{user_id}/menus/{id}/ - 移除用户的菜单"
curl -X DELETE "${BASE_URL}/admins/3/menus/23/" \
  -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "11. 测试: DELETE /api/v1/menus/admins/{user_id}/menus/batch/ - 批量移除用户菜单"
curl -X DELETE "${BASE_URL}/admins/3/menus/batch/" \
  -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"menu_ids": [28, 29]}' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "12. 测试: PUT /api/v1/menus/{id}/ - 更新菜单 (需要超级管理员)"
curl -X PUT "${BASE_URL}/23/" \
  -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ArticleManagement",
    "code": "articleManagement",
    "path": "/cms/article",
    "title": "cms.menu.articleManagement",
    "icon": "ri:file-list-line",
    "rank": 0,
    "parent_id": 22,
    "is_active": true
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "13. 测试: PATCH /api/v1/menus/{id}/ - 部分更新菜单 (需要超级管理员)"
curl -X PATCH "${BASE_URL}/23/" \
  -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "cms.menu.articleManagement"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "----------------------------------------"
echo ""
echo "测试完成!"
