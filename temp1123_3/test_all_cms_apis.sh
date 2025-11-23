#!/bin/bash

# CMS API 完整测试脚本
# 测试所有CMS相关的API接口

BASE_URL="http://localhost:8000/api/v1/cms"
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
TENANT_ID="3"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试结果数组
declare -a FAILED_API_LIST

# 测试函数
test_api() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local token=$4
    local data=$5
    local expected_status=$6
    local use_tenant_header=$7
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    echo "Method: $method $endpoint"
    
    # 构建curl命令
    local curl_cmd="curl -s -w '\n%{http_code}' -X $method"
    curl_cmd="$curl_cmd '$BASE_URL$endpoint'"
    curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ "$use_tenant_header" = "true" ]; then
        curl_cmd="$curl_cmd -H 'X-Tenant-ID: $TENANT_ID'"
    fi
    
    if [ ! -z "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    # 执行curl命令
    local response=$(eval $curl_cmd)
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    # 检查响应状态码
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (Status: $http_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC} (Expected: $expected_status, Got: $http_code)"
        echo "Response: $body"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_API_LIST+=("$test_name - Expected: $expected_status, Got: $http_code")
    fi
}

echo "========================================="
echo "     CMS API Complete Test Suite"
echo "========================================="

# ============================================
# 文章管理 API 测试
# ============================================
echo -e "\n\n${YELLOW}===== 文章管理 API 测试 =====${NC}"

# 1. GET /api/v1/cms/articles/ - 获取文章列表
test_api \
    "cms_articles_list - Admin" \
    "GET" \
    "/articles/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "false"

# 2. GET /api/v1/cms/articles/ - Member获取文章列表（需要X-Tenant-ID）
test_api \
    "cms_articles_list - Member with Tenant-ID" \
    "GET" \
    "/articles/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 3. POST /api/v1/cms/articles/ - Admin创建文章
test_api \
    "cms_articles_create - Admin" \
    "POST" \
    "/articles/" \
    "$ADMIN_TOKEN" \
    '{"title":"Test Article Admin","content":"Content","content_type":"markdown","status":"draft"}' \
    "201" \
    "false"

# 4. POST /api/v1/cms/articles/ - Member创建文章
test_api \
    "cms_articles_create - Member" \
    "POST" \
    "/articles/" \
    "$MEMBER_TOKEN" \
    '{"title":"Test Article Member","content":"Content","content_type":"markdown","status":"draft"}' \
    "201" \
    "true"

# 5. GET /api/v1/cms/articles/{id}/ - 获取单篇文章（使用存在的文章ID）
test_api \
    "cms_articles_retrieve - Admin" \
    "GET" \
    "/articles/10298/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "false"

# 6. GET /api/v1/cms/articles/{id}/ - Member获取单篇文章
test_api \
    "cms_articles_retrieve - Member" \
    "GET" \
    "/articles/10298/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 7. PUT /api/v1/cms/articles/{id}/ - 更新文章
test_api \
    "cms_articles_update - Admin" \
    "PUT" \
    "/articles/10298/" \
    "$ADMIN_TOKEN" \
    '{"title":"Updated Title","content":"Updated Content","content_type":"markdown"}' \
    "200" \
    "false"

# 8. PATCH /api/v1/cms/articles/{id}/ - 部分更新文章
test_api \
    "cms_articles_partial_update - Admin" \
    "PATCH" \
    "/articles/10298/" \
    "$ADMIN_TOKEN" \
    '{"status":"published"}' \
    "200" \
    "false"

# 9. POST /api/v1/cms/articles/{id}/publish/ - 发布文章
test_api \
    "cms_articles_publish - Member" \
    "POST" \
    "/articles/10300/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 10. POST /api/v1/cms/articles/{id}/unpublish/ - 取消发布文章
test_api \
    "cms_articles_unpublish - Member" \
    "POST" \
    "/articles/10298/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 11. POST /api/v1/cms/articles/{id}/archive/ - 归档文章
test_api \
    "cms_articles_archive - Member" \
    "POST" \
    "/articles/10299/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 12. GET /api/v1/cms/articles/{id}/statistics/ - 获取文章统计
test_api \
    "cms_articles_statistics - Admin" \
    "GET" \
    "/articles/10298/statistics/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "false"

# 13. POST /api/v1/cms/articles/{id}/view/ - 记录文章阅读
test_api \
    "cms_articles_view - No Auth" \
    "POST" \
    "/articles/10298/view/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 14. GET /api/v1/cms/articles/{id}/versions/ - 获取文章版本历史
test_api \
    "cms_articles_versions_list - Admin" \
    "GET" \
    "/articles/10298/versions/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "false"

# 15. POST /api/v1/cms/articles/batch-delete/ - 批量删除文章
test_api \
    "cms_articles_batch_delete - Admin" \
    "POST" \
    "/articles/batch-delete/" \
    "$ADMIN_TOKEN" \
    '{"article_ids":[10285],"force":false}' \
    "200" \
    "false"

# ============================================
# 分类管理 API 测试
# ============================================
echo -e "\n\n${YELLOW}===== 分类管理 API 测试 =====${NC}"

# 16. GET /api/v1/cms/categories/ - 获取分类列表
test_api \
    "cms_categories_list - Admin" \
    "GET" \
    "/categories/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 17. POST /api/v1/cms/categories/ - 创建分类
test_api \
    "cms_categories_create - Admin" \
    "POST" \
    "/categories/" \
    "$ADMIN_TOKEN" \
    '{"name":"Test Category","slug":"test-category","description":"Test"}' \
    "201" \
    "true"

# 18. GET /api/v1/cms/categories/{id}/ - 获取分类详情
test_api \
    "cms_categories_retrieve - Admin" \
    "GET" \
    "/categories/1/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 19. PUT /api/v1/cms/categories/{id}/ - 更新分类
test_api \
    "cms_categories_update - Admin" \
    "PUT" \
    "/categories/1/" \
    "$ADMIN_TOKEN" \
    '{"name":"Updated Category","slug":"updated-category"}' \
    "200" \
    "true"

# 20. PATCH /api/v1/cms/categories/{id}/ - 部分更新分类
test_api \
    "cms_categories_partial_update - Admin" \
    "PATCH" \
    "/categories/1/" \
    "$ADMIN_TOKEN" \
    '{"is_active":true}' \
    "200" \
    "true"

# 21. DELETE /api/v1/cms/categories/{id}/ - 删除分类
test_api \
    "cms_categories_destroy - Admin" \
    "DELETE" \
    "/categories/999/" \
    "$ADMIN_TOKEN" \
    "" \
    "404" \
    "true"

# 22. GET /api/v1/cms/categories/tree/ - 获取分类树
test_api \
    "get_category_tree - Admin" \
    "GET" \
    "/categories/tree/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# ============================================
# 标签管理 API 测试
# ============================================
echo -e "\n\n${YELLOW}===== 标签管理 API 测试 =====${NC}"

# 23. GET /api/v1/cms/tags/ - 获取标签列表
test_api \
    "cms_tags_list - Admin" \
    "GET" \
    "/tags/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 24. POST /api/v1/cms/tags/ - 创建标签
test_api \
    "cms_tags_create - Admin" \
    "POST" \
    "/tags/" \
    "$ADMIN_TOKEN" \
    '{"name":"Test Tag","slug":"test-tag"}' \
    "201" \
    "true"

# 25. GET /api/v1/cms/tags/{id}/ - 获取标签详情
test_api \
    "cms_tags_retrieve - Admin" \
    "GET" \
    "/tags/1/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 26. PUT /api/v1/cms/tags/{id}/ - 更新标签
test_api \
    "cms_tags_update - Admin" \
    "PUT" \
    "/tags/1/" \
    "$ADMIN_TOKEN" \
    '{"name":"Updated Tag","slug":"updated-tag"}' \
    "200" \
    "true"

# 27. PATCH /api/v1/cms/tags/{id}/ - 部分更新标签
test_api \
    "cms_tags_partial_update - Admin" \
    "PATCH" \
    "/tags/1/" \
    "$ADMIN_TOKEN" \
    '{"is_active":true}' \
    "200" \
    "true"

# 28. DELETE /api/v1/cms/tags/{id}/ - 删除标签
test_api \
    "cms_tags_destroy - Admin" \
    "DELETE" \
    "/tags/999/" \
    "$ADMIN_TOKEN" \
    "" \
    "404" \
    "true"

# 29. GET /api/v1/cms/tags/usage-stats/ - 获取标签使用统计
test_api \
    "cms_tags_usage_stats - Admin" \
    "GET" \
    "/tags/usage-stats/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# ============================================
# 标签组管理 API 测试
# ============================================
echo -e "\n\n${YELLOW}===== 标签组管理 API 测试 =====${NC}"

# 30. GET /api/v1/cms/tag-groups/ - 获取标签组列表
test_api \
    "cms_tag_groups_list - Admin" \
    "GET" \
    "/tag-groups/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 31. POST /api/v1/cms/tag-groups/ - 创建标签组
test_api \
    "cms_tag_groups_create - Admin" \
    "POST" \
    "/tag-groups/" \
    "$ADMIN_TOKEN" \
    '{"name":"Test Group","slug":"test-group"}' \
    "201" \
    "true"

# 32. GET /api/v1/cms/tag-groups/{id}/ - 获取标签组详情
test_api \
    "cms_tag_groups_retrieve - Admin" \
    "GET" \
    "/tag-groups/1/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 33. PUT /api/v1/cms/tag-groups/{id}/ - 更新标签组
test_api \
    "cms_tag_groups_update - Admin" \
    "PUT" \
    "/tag-groups/1/" \
    "$ADMIN_TOKEN" \
    '{"name":"Updated Group","slug":"updated-group"}' \
    "200" \
    "true"

# 34. PATCH /api/v1/cms/tag-groups/{id}/ - 部分更新标签组
test_api \
    "cms_tag_groups_partial_update - Admin" \
    "PATCH" \
    "/tag-groups/1/" \
    "$ADMIN_TOKEN" \
    '{"is_active":true}' \
    "200" \
    "true"

# 35. DELETE /api/v1/cms/tag-groups/{id}/ - 删除标签组
test_api \
    "cms_tag_groups_destroy - Admin" \
    "DELETE" \
    "/tag-groups/999/" \
    "$ADMIN_TOKEN" \
    "" \
    "404" \
    "true"

# ============================================
# 评论管理 API 测试
# ============================================
echo -e "\n\n${YELLOW}===== 评论管理 API 测试 =====${NC}"

# 36. GET /api/v1/cms/comments/ - 获取评论列表
test_api \
    "cms_comments_list - Admin" \
    "GET" \
    "/comments/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 37. POST /api/v1/cms/comments/ - 创建评论
test_api \
    "cms_comments_create - Member" \
    "POST" \
    "/comments/" \
    "$MEMBER_TOKEN" \
    '{"article":10298,"content":"Test Comment"}' \
    "201" \
    "true"

# 38. GET /api/v1/cms/comments/{id}/ - 获取评论详情
test_api \
    "cms_comments_retrieve - Admin" \
    "GET" \
    "/comments/1/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 39. PUT /api/v1/cms/comments/{id}/ - 更新评论
test_api \
    "cms_comments_update - Admin" \
    "PUT" \
    "/comments/1/" \
    "$ADMIN_TOKEN" \
    '{"content":"Updated Comment","article":10298}' \
    "200" \
    "true"

# 40. PATCH /api/v1/cms/comments/{id}/ - 部分更新评论
test_api \
    "cms_comments_partial_update - Admin" \
    "PATCH" \
    "/comments/1/" \
    "$ADMIN_TOKEN" \
    '{"status":"approved"}' \
    "200" \
    "true"

# 41. DELETE /api/v1/cms/comments/{id}/ - 删除评论
test_api \
    "cms_comments_destroy - Admin" \
    "DELETE" \
    "/comments/999/" \
    "$ADMIN_TOKEN" \
    "" \
    "404" \
    "true"

# 42. POST /api/v1/cms/comments/{id}/approve/ - 批准评论
test_api \
    "cms_comments_approve - Admin" \
    "POST" \
    "/comments/1/approve/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 43. POST /api/v1/cms/comments/{id}/reject/ - 拒绝评论
test_api \
    "cms_comments_reject - Admin" \
    "POST" \
    "/comments/1/reject/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 44. POST /api/v1/cms/comments/{id}/mark-spam/ - 标记为垃圾评论
test_api \
    "cms_comments_mark_spam - Admin" \
    "POST" \
    "/comments/1/mark-spam/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 45. GET /api/v1/cms/comments/{id}/replies/ - 获取评论回复
test_api \
    "cms_comments_replies - Admin" \
    "GET" \
    "/comments/1/replies/" \
    "$ADMIN_TOKEN" \
    "" \
    "200" \
    "true"

# 46. POST /api/v1/cms/comments/batch/ - 批量处理评论
test_api \
    "cms_comments_batch - Admin" \
    "POST" \
    "/comments/batch/" \
    "$ADMIN_TOKEN" \
    '{"comment_ids":[1],"action":"approve"}' \
    "200" \
    "true"

# ============================================
# Member文章管理 API 测试
# ============================================
echo -e "\n\n${YELLOW}===== Member文章管理 API 测试 =====${NC}"

# 47. GET /api/v1/cms/member/articles/ - Member获取我的文章列表
test_api \
    "cms_member_articles_list" \
    "GET" \
    "/member/articles/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 48. POST /api/v1/cms/member/articles/ - Member创建文章
test_api \
    "cms_member_articles_create" \
    "POST" \
    "/member/articles/" \
    "$MEMBER_TOKEN" \
    '{"title":"Member Article","content":"Content","content_type":"markdown","status":"draft"}' \
    "201" \
    "true"

# 49. GET /api/v1/cms/member/articles/{id}/ - Member获取我的单篇文章
test_api \
    "cms_member_articles_retrieve" \
    "GET" \
    "/member/articles/10295/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 50. PUT /api/v1/cms/member/articles/{id}/ - Member更新文章
test_api \
    "cms_member_articles_update" \
    "PUT" \
    "/member/articles/10295/" \
    "$MEMBER_TOKEN" \
    '{"title":"Updated Member Article","content":"Updated","content_type":"markdown"}' \
    "200" \
    "true"

# 51. PATCH /api/v1/cms/member/articles/{id}/ - Member部分更新文章
test_api \
    "cms_member_articles_partial_update" \
    "PATCH" \
    "/member/articles/10295/" \
    "$MEMBER_TOKEN" \
    '{"status":"draft"}' \
    "200" \
    "true"

# 52. DELETE /api/v1/cms/member/articles/{id}/ - Member删除文章
test_api \
    "cms_member_articles_destroy" \
    "DELETE" \
    "/member/articles/999/" \
    "$MEMBER_TOKEN" \
    "" \
    "404" \
    "true"

# 53. POST /api/v1/cms/member/articles/{id}/publish/ - Member发布文章
test_api \
    "cms_member_articles_publish" \
    "POST" \
    "/member/articles/10295/publish/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# 54. GET /api/v1/cms/member/articles/{id}/statistics/ - Member获取文章统计
test_api \
    "cms_member_articles_statistics" \
    "GET" \
    "/member/articles/10295/statistics/" \
    "$MEMBER_TOKEN" \
    "" \
    "200" \
    "true"

# ============================================
# 测试总结
# ============================================
echo -e "\n\n========================================="
echo "          Test Summary"
echo "========================================="
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "\n${RED}Failed API List:${NC}"
    for failed_api in "${FAILED_API_LIST[@]}"; do
        echo -e "  - $failed_api"
    done
fi

echo "========================================="
