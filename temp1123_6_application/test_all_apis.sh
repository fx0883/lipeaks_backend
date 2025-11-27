#!/bin/bash

# Application APIs 完整测试脚本
# 租户管理员Token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
BASE_URL="http://localhost:8000/api/v1"

echo "============================================"
echo "Application APIs 测试"
echo "============================================"
echo ""

echo "1. GET /api/v1/applications/ - 获取应用列表"
echo "--------------------------------------------"
curl -X GET "${BASE_URL}/applications/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -s | jq .
echo ""
echo ""

echo "2. POST /api/v1/applications/ - 创建应用"
echo "--------------------------------------------"
CREATED_APP=$(curl -X POST "${BASE_URL}/applications/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试应用-'$(date +%s)'",
    "code": "test-app-'$(date +%s)'",
    "description": "自动化测试创建的应用",
    "current_version": "1.0.0",
    "status": "development",
    "logo": "https://example.com/logo.png",
    "website": "https://example.com",
    "contact_email": "test@example.com",
    "owner": "测试负责人",
    "team": "测试团队",
    "tags": ["测试", "自动化"],
    "is_active": true
  }' \
  -s | jq .)
echo "${CREATED_APP}"
APP_ID=$(echo "${CREATED_APP}" | jq -r '.data.id // empty')
echo ""
echo "创建的应用ID: ${APP_ID}"
echo ""

if [ -z "${APP_ID}" ]; then
  echo "创建失败，使用默认ID 1进行后续测试"
  APP_ID=1
fi
echo ""

echo "3. GET /api/v1/applications/{id}/ - 获取应用详情"
echo "--------------------------------------------"
curl -X GET "${BASE_URL}/applications/${APP_ID}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -s | jq .
echo ""
echo ""

echo "4. PUT /api/v1/applications/{id}/ - 完整更新应用"
echo "--------------------------------------------"
curl -X PUT "${BASE_URL}/applications/${APP_ID}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试应用-已更新",
    "code": "test-app-'$(date +%s)'",
    "description": "完整更新后的描述",
    "current_version": "2.0.0",
    "status": "active",
    "logo": "https://example.com/logo-new.png",
    "website": "https://newexample.com",
    "contact_email": "updated@example.com",
    "owner": "新负责人",
    "team": "新团队",
    "tags": ["更新", "测试"],
    "is_active": true
  }' \
  -s | jq .
echo ""
echo ""

echo "5. PATCH /api/v1/applications/{id}/ - 部分更新应用"
echo "--------------------------------------------"
curl -X PATCH "${BASE_URL}/applications/${APP_ID}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "current_version": "2.1.0",
    "description": "部分更新：只修改版本号和描述"
  }' \
  -s | jq .
echo ""
echo ""

echo "6. GET /api/v1/applications/{id}/statistics/ - 获取应用统计"
echo "--------------------------------------------"
curl -X GET "${BASE_URL}/applications/${APP_ID}/statistics/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -s | jq .
echo ""
echo ""

echo "7. GET /api/v1/applications/{id}/articles/ - 获取应用关联文章"
echo "--------------------------------------------"
curl -X GET "${BASE_URL}/applications/${APP_ID}/articles/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -s | jq .
echo ""
echo ""

echo "8. DELETE /api/v1/applications/{id}/ - 删除应用"
echo "--------------------------------------------"
if [ "${APP_ID}" != "1" ]; then
  curl -X DELETE "${BASE_URL}/applications/${APP_ID}/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -s | jq .
  echo ""
  echo "应用已删除"
else
  echo "跳过删除ID=1的应用（保留用于测试）"
fi
echo ""

echo "============================================"
echo "测试完成"
echo "============================================"
