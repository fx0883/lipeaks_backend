#!/bin/bash

# CMS API 完整验证脚本
# 验证所有20+个API端点是否正常工作

ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
BASE_URL="http://localhost:8000"

PASSED=0
FAILED=0

# 测试函数
test_api() {
    local name="$1"
    local result="$2"
    
    if [ "$result" = "true" ]; then
        echo "✅ $name"
        ((PASSED++))
    else
        echo "❌ $name"
        ((FAILED++))
    fi
}

echo "=========================================="
echo "CMS API 完整验证"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# ============================================
# GET 列表查询 (7个)
# ============================================
echo "=== GET 列表查询 (7个) ==="

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/articles/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/articles/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/categories/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/categories/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/categories/tree/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/categories/tree/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/tags/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/tags/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/tag-groups/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/comments/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/comments/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" | jq -r '.success')
test_api "GET /api/v1/cms/member/articles/" "$RESULT"

echo ""

# ============================================
# POST 创建操作 (5个)
# ============================================
echo "=== POST 创建操作 (5个) ==="

RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/articles/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"验证测试文章","content":"测试内容","status":"draft"}' | jq -r '.success')
test_api "POST /api/v1/cms/articles/" "$RESULT"

RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/categories/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"slug\":\"verify-$(date +%s)\",\"translations\":{\"zh-hans\":{\"name\":\"验证分类\"}}}" | jq -r '.success')
test_api "POST /api/v1/cms/categories/" "$RESULT"

RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/tags/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"验证标签$(date +%s)\",\"slug\":\"verify-tag-$(date +%s)\"}" | jq -r '.success')
test_api "POST /api/v1/cms/tags/" "$RESULT"

RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"title":"Member验证文章","content":"Member内容","status":"draft"}' | jq -r '.success')
test_api "POST /api/v1/cms/member/articles/" "$RESULT"

RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/comments/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article":10266,"content":"验证评论","status":"approved"}' | jq -r '.success')
test_api "POST /api/v1/cms/comments/" "$RESULT"

echo ""

# ============================================
# GET 单项查询 (4个)
# ============================================
echo "=== GET 单项查询 (4个) ==="

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/articles/10274/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/articles/10274/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/categories/41/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/categories/41/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
test_api "GET /api/v1/cms/tags/2/" "$RESULT"

RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/member/articles/10266/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" | jq -r '.success')
test_api "GET /api/v1/cms/member/articles/10266/" "$RESULT"

echo ""

# ============================================
# PATCH 更新操作 (4个)
# ============================================
echo "=== PATCH 更新操作 (4个) ==="

RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/articles/10274/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"验证更新"}' | jq -r '.success')
test_api "PATCH /api/v1/cms/articles/10274/" "$RESULT"

RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/categories/41/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"translations":{"zh-hans":{"name":"验证更新分类"}}}' | jq -r '.success')
test_api "PATCH /api/v1/cms/categories/41/" "$RESULT"

RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"验证更新标签"}' | jq -r '.success')
test_api "PATCH /api/v1/cms/tags/2/" "$RESULT"

RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/member/articles/10266/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"title":"Member验证更新"}' | jq -r '.success')
test_api "PATCH /api/v1/cms/member/articles/10266/" "$RESULT"

echo ""

# ============================================
# 总结
# ============================================
TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

echo "=========================================="
echo "验证完成"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""
echo "测试总数: $TOTAL"
echo "通过: $PASSED"
echo "失败: $FAILED"
echo "通过率: $PERCENTAGE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 所有API验证通过！"
    exit 0
else
    echo "⚠️  存在 $FAILED 个失败的测试"
    exit 1
fi
