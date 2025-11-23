#!/bin/bash

# CMS API 修复后的完整测试脚本
# 正确使用租户ID传递方式：
# - Admin用户使用查询参数 ?tenant_id=3
# - Member用户使用HTTP Header X-Tenant-ID: 3

BASE_URL="http://localhost:8000/api/v1/cms"
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
TENANT_ID="3"
TIMESTAMP=$(date +%s)

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
declare -a FAILED_API_LIST

test_api() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local token=$4
    local data=$5
    local expected_status=$6
    local use_tenant_mode=$7  # "header" or "param"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "\n${YELLOW}[$TOTAL_TESTS] Testing: $test_name${NC}"
    
    local curl_cmd="curl -s -w '\n%{http_code}' -X $method"
    
    # 根据租户模式构建endpoint
    if [ "$use_tenant_mode" = "param" ]; then
        # Admin用户：使用查询参数
        if [[ "$endpoint" == *"?"* ]]; then
            curl_cmd="$curl_cmd '$BASE_URL$endpoint&tenant_id=$TENANT_ID'"
        else
            curl_cmd="$curl_cmd '$BASE_URL$endpoint?tenant_id=$TENANT_ID'"
        fi
        echo "  URL: $endpoint (with ?tenant_id=$TENANT_ID)"
    else
        # Member用户：使用header
        curl_cmd="$curl_cmd '$BASE_URL$endpoint'"
        echo "  URL: $endpoint"
    fi
    
    curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ "$use_tenant_mode" = "header" ]; then
        curl_cmd="$curl_cmd -H 'X-Tenant-ID: $TENANT_ID'"
    fi
    
    if [ ! -z "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    local response=$(eval $curl_cmd 2>&1)
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC} (Status: $http_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC} (Expected: $expected_status, Got: $http_code)"
        echo "  Response: ${body:0:200}..."
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_API_LIST+=("$test_name - Expected: $expected_status, Got: $http_code")
    fi
}

echo "========================================="
echo "  CMS API Complete Test Suite (Fixed)"
echo "========================================="
echo ""
echo "租户ID传递规则:"
echo "- Admin用户: 使用查询参数 ?tenant_id=$TENANT_ID"
echo "- Member用户: 使用HTTP Header X-Tenant-ID: $TENANT_ID"
echo "========================================="

# ============================================
# 文章管理 API 测试
# ============================================
echo -e "\n\n${BLUE}===== 文章管理 API 测试 =====${NC}"

test_api "cms_articles_list - Admin" "GET" "/articles/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_articles_list - Member" "GET" "/articles/" "$MEMBER_TOKEN" "" "200" "header"
test_api "cms_articles_create - Admin" "POST" "/articles/" "$ADMIN_TOKEN" '{"title":"Test Article Admin","content":"Content","content_type":"markdown","status":"draft"}' "201" "param"
test_api "cms_articles_create - Member" "POST" "/articles/" "$MEMBER_TOKEN" '{"title":"Test Article Member","content":"Content","content_type":"markdown","status":"draft"}' "201" "header"
test_api "cms_articles_retrieve - Admin" "GET" "/articles/10298/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_articles_retrieve - Member" "GET" "/articles/10298/" "$MEMBER_TOKEN" "" "200" "header"
test_api "cms_articles_update - Admin" "PUT" "/articles/10292/" "$ADMIN_TOKEN" '{"title":"Updated Title Admin","content":"Updated Content","content_type":"markdown"}' "200" "param"
test_api "cms_articles_partial_update - Admin" "PATCH" "/articles/10292/" "$ADMIN_TOKEN" '{"status":"published"}' "200" "param"
test_api "cms_articles_delete - Admin" "DELETE" "/articles/10285/" "$ADMIN_TOKEN" "" "204" "param"
test_api "cms_articles_statistics - Admin" "GET" "/articles/10298/statistics/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_articles_view - No Auth" "POST" "/articles/10298/view/" "$MEMBER_TOKEN" "" "200" "header"
test_api "cms_articles_versions - Admin" "GET" "/articles/10298/versions/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_articles_batch_delete - Admin" "POST" "/articles/batch-delete/" "$ADMIN_TOKEN" '{"article_ids":[10290],"force":false}' "200" "param"

# ============================================
# 分类管理 API 测试
# ============================================
echo -e "\n\n${BLUE}===== 分类管理 API 测试 =====${NC}"

test_api "cms_categories_list - Admin" "GET" "/categories/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_categories_create - Admin" "POST" "/categories/" "$ADMIN_TOKEN" "{\"slug\":\"test-cat-$TIMESTAMP\",\"translations\":{\"zh-hans\":{\"name\":\"测试分类\",\"description\":\"测试描述\"}}}" "201" "param"
test_api "cms_categories_tree - Admin" "GET" "/categories/tree/" "$ADMIN_TOKEN" "" "200" "param"

# ============================================
# 标签管理 API 测试
# ============================================
echo -e "\n\n${BLUE}===== 标签管理 API 测试 =====${NC}"

test_api "cms_tags_list - Admin" "GET" "/tags/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_tags_create - Admin" "POST" "/tags/" "$ADMIN_TOKEN" "{\"name\":\"Test Tag\",\"slug\":\"test-tag-$TIMESTAMP\"}" "201" "param"
test_api "cms_tags_usage_stats - Admin" "GET" "/tags/usage-stats/" "$ADMIN_TOKEN" "" "200" "param"

# ============================================
# 标签组管理 API 测试
# ============================================
echo -e "\n\n${BLUE}===== 标签组管理 API 测试 =====${NC}"

test_api "cms_tag_groups_list - Admin" "GET" "/tag-groups/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_tag_groups_create - Admin" "POST" "/tag-groups/" "$ADMIN_TOKEN" "{\"name\":\"Test Group\",\"slug\":\"test-group-$TIMESTAMP\"}" "201" "param"

# ============================================
# 评论管理 API 测试
# ============================================
echo -e "\n\n${BLUE}===== 评论管理 API 测试 =====${NC}"

test_api "cms_comments_list - Admin" "GET" "/comments/" "$ADMIN_TOKEN" "" "200" "param"
test_api "cms_comments_create - Member" "POST" "/comments/" "$MEMBER_TOKEN" '{"article":10298,"content":"Test Comment"}' "201" "header"

# ============================================
# Member文章管理 API 测试
# ============================================
echo -e "\n\n${BLUE}===== Member文章管理 API 测试 =====${NC}"

test_api "cms_member_articles_list" "GET" "/member/articles/" "$MEMBER_TOKEN" "" "200" "header"
test_api "cms_member_articles_create" "POST" "/member/articles/" "$MEMBER_TOKEN" '{"title":"Member Article","content":"Content","content_type":"markdown","status":"draft"}' "201" "header"
test_api "cms_member_articles_retrieve" "GET" "/member/articles/10295/" "$MEMBER_TOKEN" "" "200" "header"
test_api "cms_member_articles_update" "PUT" "/member/articles/10295/" "$MEMBER_TOKEN" '{"title":"Updated Member Article","content":"Updated","content_type":"markdown"}' "200" "header"
test_api "cms_member_articles_partial_update" "PATCH" "/member/articles/10295/" "$MEMBER_TOKEN" '{"status":"draft"}' "200" "header"
test_api "cms_member_articles_publish" "POST" "/member/articles/10295/publish/" "$MEMBER_TOKEN" "" "200" "header"
test_api "cms_member_articles_statistics" "GET" "/member/articles/10295/statistics/" "$MEMBER_TOKEN" "" "200" "header"

# ============================================
# 测试总结
# ============================================
echo -e "\n\n========================================="
echo "          Test Summary"
echo "========================================="
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo -e "Pass Rate: $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%"

if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "\n${RED}Failed API List:${NC}"
    for failed_api in "${FAILED_API_LIST[@]}"; do
        echo -e "  ${RED}✗${NC} $failed_api"
    done
    exit 1
else
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
fi

echo "========================================="
