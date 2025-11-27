#!/bin/bash

# 完整的CMS API测试脚本

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
BASE_URL="http://localhost:8000"

TOTAL=0
PASSED=0
FAILED=0
FAILED_LIST=()

# 用于存储创建的资源ID
ADMIN_ARTICLE_ID=""
MEMBER_ARTICLE_ID=""
CATEGORY_ID=""
TAG_ID=""
TAG_GROUP_ID=""
COMMENT_ID=""

test_api() {
    local name=$1
    local method=$2
    local url=$3
    local token=$4
    local data=$5
    local use_tenant=$6
    
    TOTAL=$((TOTAL + 1))
    echo -e "\n${BLUE}[测试 $TOTAL]${NC} $name"
    
    local cmd="curl -s -w '\nSTATUS:%{http_code}' -X $method"
    cmd="$cmd -H 'Authorization: Bearer $token'"
    cmd="$cmd -H 'Content-Type: application/json'"
    
    if [ "$use_tenant" = "true" ]; then
        cmd="$cmd -H 'X-Tenant-ID: 3'"
    fi
    
    if [ -n "$data" ]; then
        cmd="$cmd -d '$data'"
    fi
    
    cmd="$cmd '$url'"
    
    response=$(eval $cmd)
    status=$(echo "$response" | grep "STATUS:" | cut -d: -f2)
    body=$(echo "$response" | sed '/STATUS:/d')
    
    if [[ $status =~ ^(200|201|204)$ ]]; then
        echo -e "${GREEN}✓ 通过${NC} (HTTP $status)"
        PASSED=$((PASSED + 1))
        echo "$body"
    else
        echo -e "${RED}✗ 失败${NC} (HTTP $status)"
        echo "$body"
        FAILED=$((FAILED + 1))
        FAILED_LIST+=("$name (HTTP $status)")
    fi
}

echo "========================================="
echo "  完整的CMS API测试"
echo "========================================="

# ============ 文章管理API ============
echo -e "\n${YELLOW}========== 文章管理API (管理员) ==========${NC}"

test_api "1. 获取文章列表" \
    "GET" "${BASE_URL}/api/v1/cms/articles/" "$ADMIN_TOKEN" "" "false"

test_api "2. 获取文章列表(带状态过滤)" \
    "GET" "${BASE_URL}/api/v1/cms/articles/?status=published" "$ADMIN_TOKEN" "" "false"

test_api "3. 获取文章列表(带搜索)" \
    "GET" "${BASE_URL}/api/v1/cms/articles/?search=test" "$ADMIN_TOKEN" "" "false"

# 获取第一篇文章的ID用于后续测试
ARTICLE_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "${BASE_URL}/api/v1/cms/articles/" | \
    grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

if [ -n "$ARTICLE_ID" ]; then
    echo -e "${GREEN}获取到文章ID: $ARTICLE_ID${NC}"
    
    test_api "4. 获取单篇文章" \
        "GET" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/" "$ADMIN_TOKEN" "" "false"
    
    test_api "5. 部分更新文章" \
        "PATCH" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/" "$ADMIN_TOKEN" \
        '{"excerpt":"更新的摘要"}' "false"
    
    test_api "6. 发布文章" \
        "POST" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/publish/" "$ADMIN_TOKEN" \
        '{}' "false"
    
    test_api "7. 取消发布文章" \
        "POST" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/unpublish/" "$ADMIN_TOKEN" \
        '{}' "false"
    
    test_api "8. 归档文章" \
        "POST" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/archive/" "$ADMIN_TOKEN" \
        '{}' "false"
    
    test_api "9. 获取文章统计" \
        "GET" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/statistics/" "$ADMIN_TOKEN" "" "false"
    
    test_api "10. 记录文章阅读" \
        "POST" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/view/" "$ADMIN_TOKEN" \
        '{}' "false"
    
    test_api "11. 获取文章版本历史" \
        "GET" "${BASE_URL}/api/v1/cms/articles/${ARTICLE_ID}/versions/" "$ADMIN_TOKEN" "" "false"
fi

test_api "12. 批量删除文章" \
    "POST" "${BASE_URL}/api/v1/cms/articles/batch-delete/" "$ADMIN_TOKEN" \
    '{"article_ids":[99999],"force":false}' "false"

# ============ 分类管理API ============
echo -e "\n${YELLOW}========== 分类管理API (管理员) ==========${NC}"

test_api "13. 获取分类列表" \
    "GET" "${BASE_URL}/api/v1/cms/categories/" "$ADMIN_TOKEN" "" "false"

test_api "14. 获取分类树" \
    "GET" "${BASE_URL}/api/v1/cms/categories/tree/" "$ADMIN_TOKEN" "" "false"

test_api "15. 创建分类" \
    "POST" "${BASE_URL}/api/v1/cms/categories/" "$ADMIN_TOKEN" \
    '{"translations":{"zh-hans":{"name":"测试分类","description":"测试描述"}},"slug":"test-cat-'$(date +%s)'","is_active":true}' "false"

# 获取第一个分类ID
CATEGORY_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "${BASE_URL}/api/v1/cms/categories/" | \
    grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

if [ -n "$CATEGORY_ID" ]; then
    echo -e "${GREEN}获取到分类ID: $CATEGORY_ID${NC}"
    
    test_api "16. 获取分类详情" \
        "GET" "${BASE_URL}/api/v1/cms/categories/${CATEGORY_ID}/" "$ADMIN_TOKEN" "" "false"
    
    test_api "17. 更新分类" \
        "PUT" "${BASE_URL}/api/v1/cms/categories/${CATEGORY_ID}/" "$ADMIN_TOKEN" \
        '{"translations":{"zh-hans":{"name":"更新的分类","description":"更新的描述"}},"is_active":true}' "false"
    
    test_api "18. 部分更新分类" \
        "PATCH" "${BASE_URL}/api/v1/cms/categories/${CATEGORY_ID}/" "$ADMIN_TOKEN" \
        '{"is_active":true}' "false"
fi

# ============ 标签组管理API ============
echo -e "\n${YELLOW}========== 标签组管理API (管理员) ==========${NC}"

test_api "19. 获取标签组列表" \
    "GET" "${BASE_URL}/api/v1/cms/tag-groups/" "$ADMIN_TOKEN" "" "false"

test_api "20. 创建标签组" \
    "POST" "${BASE_URL}/api/v1/cms/tag-groups/" "$ADMIN_TOKEN" \
    '{"name":"测试标签组-'$(date +%s)'","slug":"test-group-'$(date +%s)'","description":"测试描述","is_active":true}' "false"

# 获取第一个标签组ID
TAG_GROUP_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "${BASE_URL}/api/v1/cms/tag-groups/" | \
    grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

if [ -n "$TAG_GROUP_ID" ]; then
    echo -e "${GREEN}获取到标签组ID: $TAG_GROUP_ID${NC}"
    
    test_api "21. 获取标签组详情" \
        "GET" "${BASE_URL}/api/v1/cms/tag-groups/${TAG_GROUP_ID}/" "$ADMIN_TOKEN" "" "false"
    
    test_api "22. 更新标签组" \
        "PUT" "${BASE_URL}/api/v1/cms/tag-groups/${TAG_GROUP_ID}/" "$ADMIN_TOKEN" \
        '{"name":"更新的标签组","slug":"updated-group","description":"更新的描述","is_active":true}' "false"
    
    test_api "23. 部分更新标签组" \
        "PATCH" "${BASE_URL}/api/v1/cms/tag-groups/${TAG_GROUP_ID}/" "$ADMIN_TOKEN" \
        '{"is_active":true}' "false"
fi

# ============ 标签管理API ============
echo -e "\n${YELLOW}========== 标签管理API (管理员) ==========${NC}"

test_api "24. 获取标签列表" \
    "GET" "${BASE_URL}/api/v1/cms/tags/" "$ADMIN_TOKEN" "" "false"

test_api "25. 获取标签使用统计" \
    "GET" "${BASE_URL}/api/v1/cms/tags/usage-stats/" "$ADMIN_TOKEN" "" "false"

test_api "26. 创建标签" \
    "POST" "${BASE_URL}/api/v1/cms/tags/" "$ADMIN_TOKEN" \
    '{"name":"测试标签-'$(date +%s)'","slug":"test-tag-'$(date +%s)'","description":"测试描述","is_active":true}' "false"

# 获取第一个标签ID
TAG_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "${BASE_URL}/api/v1/cms/tags/" | \
    grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

if [ -n "$TAG_ID" ]; then
    echo -e "${GREEN}获取到标签ID: $TAG_ID${NC}"
    
    test_api "27. 获取标签详情" \
        "GET" "${BASE_URL}/api/v1/cms/tags/${TAG_ID}/" "$ADMIN_TOKEN" "" "false"
    
    test_api "28. 更新标签" \
        "PUT" "${BASE_URL}/api/v1/cms/tags/${TAG_ID}/" "$ADMIN_TOKEN" \
        '{"name":"更新的标签","slug":"updated-tag","description":"更新的描述","is_active":true}' "false"
    
    test_api "29. 部分更新标签" \
        "PATCH" "${BASE_URL}/api/v1/cms/tags/${TAG_ID}/" "$ADMIN_TOKEN" \
        '{"color":"#FF0000"}' "false"
fi

# ============ 评论管理API ============
echo -e "\n${YELLOW}========== 评论管理API (管理员) ==========${NC}"

test_api "30. 获取评论列表" \
    "GET" "${BASE_URL}/api/v1/cms/comments/" "$ADMIN_TOKEN" "" "false"

# 获取第一个评论ID
COMMENT_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "${BASE_URL}/api/v1/cms/comments/" | \
    grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

if [ -n "$COMMENT_ID" ]; then
    echo -e "${GREEN}获取到评论ID: $COMMENT_ID${NC}"
    
    test_api "31. 获取评论详情" \
        "GET" "${BASE_URL}/api/v1/cms/comments/${COMMENT_ID}/" "$ADMIN_TOKEN" "" "false"
    
    test_api "32. 批准评论" \
        "POST" "${BASE_URL}/api/v1/cms/comments/${COMMENT_ID}/approve/" "$ADMIN_TOKEN" \
        '{}' "false"
    
    test_api "33. 拒绝评论" \
        "POST" "${BASE_URL}/api/v1/cms/comments/${COMMENT_ID}/reject/" "$ADMIN_TOKEN" \
        '{}' "false"
    
    test_api "34. 标记为垃圾评论" \
        "POST" "${BASE_URL}/api/v1/cms/comments/${COMMENT_ID}/mark-spam/" "$ADMIN_TOKEN" \
        '{}' "false"
    
    test_api "35. 获取评论回复" \
        "GET" "${BASE_URL}/api/v1/cms/comments/${COMMENT_ID}/replies/" "$ADMIN_TOKEN" "" "false"
fi

test_api "36. 批量处理评论" \
    "POST" "${BASE_URL}/api/v1/cms/comments/batch/" "$ADMIN_TOKEN" \
    '{"comment_ids":['$COMMENT_ID'],"action":"approve"}' "false"

# ============ Member文章管理API ============
echo -e "\n${YELLOW}========== Member文章管理API ==========${NC}"

test_api "37. 获取我的文章列表" \
    "GET" "${BASE_URL}/api/v1/cms/member/articles/" "$MEMBER_TOKEN" "" "true"

test_api "38. 创建文章(Member)" \
    "POST" "${BASE_URL}/api/v1/cms/member/articles/" "$MEMBER_TOKEN" \
    '{"title":"Member测试文章-'$(date +%s)'","content":"这是测试内容","content_type":"markdown","excerpt":"测试摘要","status":"draft"}' "true"

# 获取Member的第一篇文章ID
MEMBER_ARTICLE_ID=$(curl -s -H "Authorization: Bearer $MEMBER_TOKEN" \
    -H "X-Tenant-ID: 3" \
    "${BASE_URL}/api/v1/cms/member/articles/" | \
    grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

if [ -n "$MEMBER_ARTICLE_ID" ]; then
    echo -e "${GREEN}获取到Member文章ID: $MEMBER_ARTICLE_ID${NC}"
    
    test_api "39. 获取我的单篇文章" \
        "GET" "${BASE_URL}/api/v1/cms/member/articles/${MEMBER_ARTICLE_ID}/" "$MEMBER_TOKEN" "" "true"
    
    test_api "40. 更新文章(Member)" \
        "PUT" "${BASE_URL}/api/v1/cms/member/articles/${MEMBER_ARTICLE_ID}/" "$MEMBER_TOKEN" \
        '{"title":"更新的标题","content":"更新的内容","content_type":"markdown","status":"draft"}' "true"
    
    test_api "41. 部分更新文章(Member)" \
        "PATCH" "${BASE_URL}/api/v1/cms/member/articles/${MEMBER_ARTICLE_ID}/" "$MEMBER_TOKEN" \
        '{"excerpt":"更新的摘要"}' "true"
    
    test_api "42. 发布文章(Member)" \
        "POST" "${BASE_URL}/api/v1/cms/member/articles/${MEMBER_ARTICLE_ID}/publish/" "$MEMBER_TOKEN" \
        '{}' "true"
    
    test_api "43. 获取文章统计(Member)" \
        "GET" "${BASE_URL}/api/v1/cms/member/articles/${MEMBER_ARTICLE_ID}/statistics/" "$MEMBER_TOKEN" "" "true"
    
    test_api "44. 删除文章(Member)" \
        "DELETE" "${BASE_URL}/api/v1/cms/member/articles/${MEMBER_ARTICLE_ID}/" "$MEMBER_TOKEN" "" "true"
fi

# ============ 测试总结 ============
echo -e "\n========================================="
echo -e "   测试总结"
echo -e "========================================="
echo -e "总测试数: $TOTAL"
echo -e "${GREEN}成功: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo -e "成功率: $(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")%"

if [ $FAILED -gt 0 ]; then
    echo -e "\n${RED}失败的API:${NC}"
    for api in "${FAILED_LIST[@]}"; do
        echo -e "  ${RED}✗${NC} $api"
    done
fi

echo -e "\n========================================="
