#!/bin/bash

# CMS API完整测试脚本
# 测试租户管理员和Member用户的所有API端点

ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "CMS API 完整测试"
echo "=========================================="
echo ""

# 测试分类管理
echo "=== 测试分类管理 ==="
echo -n "GET /api/v1/cms/categories/: "
curl -s -X GET "$BASE_URL/api/v1/cms/categories/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success' 

echo -n "GET /api/v1/cms/categories/tree/: "
curl -s -X GET "$BASE_URL/api/v1/cms/categories/tree/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success'

echo -n "POST /api/v1/cms/categories/: "
curl -s -X POST "$BASE_URL/api/v1/cms/categories/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug":"test-'$(date +%s)'","translations":{"zh-hans":{"name":"测试分类"}}}' | jq -r '.success'

echo ""

# 测试标签管理
echo "=== 测试标签管理 ==="
echo -n "GET /api/v1/cms/tags/: "
curl -s -X GET "$BASE_URL/api/v1/cms/tags/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success'

echo -n "GET /api/v1/cms/tag-groups/: "
curl -s -X GET "$BASE_URL/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success'

echo ""

# 测试文章列表
echo "=== 测试文章管理 (Admin) ==="
echo -n "GET /api/v1/cms/articles/: "
curl -s -X GET "$BASE_URL/api/v1/cms/articles/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success'

echo ""

# 测试评论管理
echo "=== 测试评论管理 (Admin) ==="
echo -n "GET /api/v1/cms/comments/: "
curl -s -X GET "$BASE_URL/api/v1/cms/comments/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success'

echo ""

# 测试Member文章
echo "=== 测试Member文章管理 ==="
echo -n "GET /api/v1/cms/member/articles/: "
curl -s -X GET "$BASE_URL/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" | jq -r '.success'

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
