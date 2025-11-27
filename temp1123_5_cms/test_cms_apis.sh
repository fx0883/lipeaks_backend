#!/bin/bash

# CMS API 测试脚本
# 服务器: localhost:8000

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Token配置
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
TENANT_ID="3"

BASE_URL="http://localhost:8000"

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试结果记录
FAILED_APIS=()

# 测试函数
test_api() {
    local test_name=$1
    local method=$2
    local url=$3
    local token=$4
    local data=$5
    local use_tenant_header=$6
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "\n${YELLOW}[测试 $TOTAL_TESTS] $test_name${NC}"
    echo "URL: $method $url"
    
    # 构建curl命令
    local curl_cmd="curl -s -w '\nHTTP_STATUS:%{http_code}' -X $method"
    curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ "$use_tenant_header" = "true" ]; then
        curl_cmd="$curl_cmd -H 'X-Tenant-ID: $TENANT_ID'"
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$url'"
    
    # 执行请求
    response=$(eval $curl_cmd)
    
    # 提取HTTP状态码
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    response_body=$(echo "$response" | sed '/HTTP_STATUS:/d')
    
    # 判断测试结果
    if [[ $http_status =~ ^(200|201|204)$ ]]; then
        echo -e "${GREEN}✓ 成功 (HTTP $http_status)${NC}"
        echo "响应: $response_body" | head -c 200
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ 失败 (HTTP $http_status)${NC}"
        echo "响应: $response_body"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_APIS+=("$test_name (HTTP $http_status)")
    fi
}

echo "========================================="
echo "   CMS API 测试"
echo "========================================="

# 1. 文章管理API测试
echo -e "\n${YELLOW}========== 1. 文章管理API ==========${NC}"

# 1.1 获取文章列表 - 管理员
test_api "获取文章列表 (管理员)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/articles/" \
    "$ADMIN_TOKEN" \
    "" \
    "false"

# 1.2 获取文章列表 - Member
test_api "获取文章列表 (Member)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/articles/" \
    "$MEMBER_TOKEN" \
    "" \
    "true"

# 1.3 创建文章 - 管理员
test_api "创建文章 (管理员)" \
    "POST" \
    "${BASE_URL}/api/v1/cms/articles/" \
    "$ADMIN_TOKEN" \
    '{"title":"测试文章-管理员","content":"这是测试内容","content_type":"markdown","excerpt":"测试摘要","status":"draft"}' \
    "false"

# 1.4 创建文章 - Member
test_api "创建文章 (Member)" \
    "POST" \
    "${BASE_URL}/api/v1/cms/articles/" \
    "$MEMBER_TOKEN" \
    '{"title":"测试文章-Member","content":"这是测试内容","content_type":"markdown","excerpt":"测试摘要","status":"draft"}' \
    "true"

# 2. 分类管理API测试
echo -e "\n${YELLOW}========== 2. 分类管理API ==========${NC}"

# 2.1 获取分类列表 - 管理员
test_api "获取分类列表 (管理员)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/categories/" \
    "$ADMIN_TOKEN" \
    "" \
    "false"

# 2.2 获取分类列表 - Member
test_api "获取分类列表 (Member)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/categories/" \
    "$MEMBER_TOKEN" \
    "" \
    "true"

# 2.3 获取分类树 - 管理员
test_api "获取分类树 (管理员)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/categories/tree/" \
    "$ADMIN_TOKEN" \
    "" \
    "false"

# 3. 标签管理API测试
echo -e "\n${YELLOW}========== 3. 标签管理API ==========${NC}"

# 3.1 获取标签列表 - 管理员
test_api "获取标签列表 (管理员)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/tags/" \
    "$ADMIN_TOKEN" \
    "" \
    "false"

# 3.2 获取标签列表 - Member
test_api "获取标签列表 (Member)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/tags/" \
    "$MEMBER_TOKEN" \
    "" \
    "true"

# 3.3 获取标签使用统计 - 管理员
test_api "获取标签使用统计 (管理员)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/tags/usage-stats/" \
    "$ADMIN_TOKEN" \
    "" \
    "false"

# 4. 标签组管理API测试
echo -e "\n${YELLOW}========== 4. 标签组管理API ==========${NC}"

# 4.1 获取标签组列表 - 管理员
test_api "获取标签组列表 (管理员)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/tag-groups/" \
    "$ADMIN_TOKEN" \
    "" \
    "false"

# 5. 评论管理API测试
echo -e "\n${YELLOW}========== 5. 评论管理API ==========${NC}"

# 5.1 获取评论列表 - 管理员
test_api "获取评论列表 (管理员)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/comments/" \
    "$ADMIN_TOKEN" \
    "" \
    "false"

# 5.2 获取评论列表 - Member
test_api "获取评论列表 (Member)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/comments/" \
    "$MEMBER_TOKEN" \
    "" \
    "true"

# 6. Member文章管理API测试
echo -e "\n${YELLOW}========== 6. Member文章管理API ==========${NC}"

# 6.1 获取我的文章列表
test_api "获取我的文章列表 (Member)" \
    "GET" \
    "${BASE_URL}/api/v1/cms/member/articles/" \
    "$MEMBER_TOKEN" \
    "" \
    "true"

# 输出测试总结
echo -e "\n========================================="
echo -e "   测试总结"
echo -e "========================================="
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}成功: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "\n${RED}失败的API:${NC}"
    for api in "${FAILED_APIS[@]}"; do
        echo -e "  - $api"
    done
fi

echo -e "\n========================================="
