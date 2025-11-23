#!/bin/bash

# CMS API 测试脚本
# 服务器地址
BASE_URL="http://0.0.0.0:8000/api/v1/cms"

# Token配置
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
TENANT_ID="3"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL=0
PASSED=0
FAILED=0

# 测试结果记录
RESULTS_FILE="temp1123_2/test_results.md"
echo "# CMS API 测试结果" > $RESULTS_FILE
echo "" >> $RESULTS_FILE
echo "测试时间: $(date)" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

# 测试函数
test_api() {
    local name=$1
    local method=$2
    local endpoint=$3
    local token=$4
    local data=$5
    local expect_success=$6
    local use_tenant_header=$7  # 新增参数：是否使用X-Tenant-ID头
    
    TOTAL=$((TOTAL + 1))
    
    echo -e "\n${YELLOW}[测试 $TOTAL] $name${NC}"
    echo "方法: $method"
    echo "端点: $endpoint"
    
    # 确定是否需要租户头
    # Admin用户不应该带X-Tenant-ID头
    # Member用户必须带X-Tenant-ID头
    # 匿名用户可以带X-Tenant-ID头
    local tenant_header=""
    if [ "$use_tenant_header" == "true" ] || [ -z "$token" ]; then
        tenant_header="-H X-Tenant-ID: $TENANT_ID"
    fi
    
    # 构建curl命令
    if [ "$method" == "GET" ]; then
        if [ -z "$token" ]; then
            response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" $tenant_header)
        else
            response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" -H "Authorization: Bearer $token" $tenant_header)
        fi
    elif [ "$method" == "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            $tenant_header \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" == "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            $tenant_header \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" == "PATCH" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            $tenant_header \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" == "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            $tenant_header)
    fi
    
    # 提取HTTP状态码和响应体
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    # 判断测试结果
    if [ "$expect_success" == "true" ]; then
        if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
            echo -e "${GREEN}✓ 通过${NC} (HTTP $http_code)"
            PASSED=$((PASSED + 1))
            echo "## ✓ $name" >> $RESULTS_FILE
            echo "- **方法**: $method" >> $RESULTS_FILE
            echo "- **端点**: $endpoint" >> $RESULTS_FILE
            echo "- **状态码**: $http_code" >> $RESULTS_FILE
            echo "" >> $RESULTS_FILE
        else
            echo -e "${RED}✗ 失败${NC} (HTTP $http_code)"
            echo "响应: $body" | head -c 500
            FAILED=$((FAILED + 1))
            echo "## ✗ $name" >> $RESULTS_FILE
            echo "- **方法**: $method" >> $RESULTS_FILE
            echo "- **端点**: $endpoint" >> $RESULTS_FILE
            echo "- **状态码**: $http_code" >> $RESULTS_FILE
            echo "- **错误**: \`\`\`$(echo $body | head -c 300)\`\`\`" >> $RESULTS_FILE
            echo "" >> $RESULTS_FILE
        fi
    else
        if [ "$http_code" -ge 400 ]; then
            echo -e "${GREEN}✓ 通过${NC} (HTTP $http_code - 预期失败)"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ 失败${NC} (HTTP $http_code - 应该失败但成功了)"
            FAILED=$((FAILED + 1))
        fi
    fi
}

echo "========================================"
echo "  CMS API 完整测试"
echo "========================================"

# ============ 文章管理 API ============
echo -e "\n${YELLOW}=== 文章管理 API ===${NC}"

# GET /api/v1/cms/articles/ - 获取文章列表
test_api "获取文章列表(匿名)" "GET" "/articles/" "" "" "true" "true"
test_api "获取文章列表(Admin)" "GET" "/articles/" "$ADMIN_TOKEN" "" "true" "false"
test_api "获取文章列表(Member)" "GET" "/articles/" "$MEMBER_TOKEN" "" "true" "true"

# POST /api/v1/cms/articles/ - 创建文章 (Admin)
test_api "创建文章(Admin)" "POST" "/articles/" "$ADMIN_TOKEN" \
    '{"title":"测试文章-Admin","content":"测试内容","excerpt":"摘要","status":"draft"}' "true" "false"

# 保存文章ID用于后续测试
ADMIN_ARTICLE_ID=$(curl -s -X POST "$BASE_URL/articles/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"用于测试的文章","content":"测试内容","excerpt":"摘要","status":"draft"}' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

if [ ! -z "$ADMIN_ARTICLE_ID" ]; then
    echo "创建的测试文章ID: $ADMIN_ARTICLE_ID"
    
    # GET /api/v1/cms/articles/{id}/ - 获取单篇文章
    test_api "获取单篇文章" "GET" "/articles/$ADMIN_ARTICLE_ID/" "" "" "true" "true"
    
    # PUT /api/v1/cms/articles/{id}/ - 更新文章
    test_api "更新文章(PUT)" "PUT" "/articles/$ADMIN_ARTICLE_ID/" "$ADMIN_TOKEN" \
        '{"title":"更新后的文章","content":"更新的内容","excerpt":"更新摘要","status":"draft"}' "true" "false"
    
    # PATCH /api/v1/cms/articles/{id}/ - 部分更新文章
    test_api "部分更新文章(PATCH)" "PATCH" "/articles/$ADMIN_ARTICLE_ID/" "$ADMIN_TOKEN" \
        '{"title":"PATCH更新标题"}' "true" "false"
    
    # POST /api/v1/cms/articles/{id}/publish/ - 发布文章
    test_api "发布文章" "POST" "/articles/$ADMIN_ARTICLE_ID/publish/" "$ADMIN_TOKEN" "" "true" "false"
    
    # POST /api/v1/cms/articles/{id}/unpublish/ - 取消发布
    test_api "取消发布文章" "POST" "/articles/$ADMIN_ARTICLE_ID/unpublish/" "$ADMIN_TOKEN" "" "true" "false"
    
    # GET /api/v1/cms/articles/{id}/statistics/ - 获取文章统计
    test_api "获取文章统计" "GET" "/articles/$ADMIN_ARTICLE_ID/statistics/" "$ADMIN_TOKEN" "" "true" "false"
    
    # POST /api/v1/cms/articles/{id}/view/ - 记录阅读
    test_api "记录文章阅读" "POST" "/articles/$ADMIN_ARTICLE_ID/view/" "" "" "true" "true"
    
    # GET /api/v1/cms/articles/{id}/versions/ - 获取版本历史
    test_api "获取版本历史" "GET" "/articles/$ADMIN_ARTICLE_ID/versions/" "$ADMIN_TOKEN" "" "true" "false"
    
    # POST /api/v1/cms/articles/{id}/archive/ - 归档文章
    test_api "归档文章" "POST" "/articles/$ADMIN_ARTICLE_ID/archive/" "$ADMIN_TOKEN" "" "true" "false"
fi

# POST /api/v1/cms/articles/batch-delete/ - 批量删除
if [ ! -z "$ADMIN_ARTICLE_ID" ]; then
    test_api "批量删除文章" "POST" "/articles/batch-delete/" "$ADMIN_TOKEN" \
        "{\"article_ids\":[$ADMIN_ARTICLE_ID],\"force\":false}" "true" "false"
fi

# ============ 分类管理 API ============
echo -e "\n${YELLOW}=== 分类管理 API ===${NC}"

# GET /api/v1/cms/categories/ - 获取分类列表
test_api "获取分类列表" "GET" "/categories/" "" "" "true"

# POST /api/v1/cms/categories/ - 创建分类
CAT_RESPONSE=$(curl -s -X POST "$BASE_URL/categories/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{"name":"测试分类","slug":"test-cat","description":"测试描述"}')

CATEGORY_ID=$(echo "$CAT_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

test_api "创建分类" "POST" "/categories/" "$ADMIN_TOKEN" \
    '{"name":"测试分类2","slug":"test-cat-2","description":"测试描述"}' "true"

if [ ! -z "$CATEGORY_ID" ]; then
    echo "创建的测试分类ID: $CATEGORY_ID"
    
    # GET /api/v1/cms/categories/{id}/ - 获取分类详情
    test_api "获取分类详情" "GET" "/categories/$CATEGORY_ID/" "" "" "true"
    
    # PUT /api/v1/cms/categories/{id}/ - 更新分类
    test_api "更新分类(PUT)" "PUT" "/categories/$CATEGORY_ID/" "$ADMIN_TOKEN" \
        '{"name":"更新后的分类","slug":"test-cat","description":"更新描述"}' "true"
    
    # PATCH /api/v1/cms/categories/{id}/ - 部分更新分类
    test_api "部分更新分类(PATCH)" "PATCH" "/categories/$CATEGORY_ID/" "$ADMIN_TOKEN" \
        '{"name":"PATCH更新分类"}' "true"
    
    # DELETE /api/v1/cms/categories/{id}/ - 删除分类
    test_api "删除分类" "DELETE" "/categories/$CATEGORY_ID/" "$ADMIN_TOKEN" "" "true"
fi

# GET /api/v1/cms/categories/tree/ - 获取分类树
test_api "获取分类树" "GET" "/categories/tree/" "" "" "true"

# ============ 标签管理 API ============
echo -e "\n${YELLOW}=== 标签管理 API ===${NC}"

# GET /api/v1/cms/tags/ - 获取标签列表
test_api "获取标签列表" "GET" "/tags/" "" "" "true"

# POST /api/v1/cms/tags/ - 创建标签
TAG_RESPONSE=$(curl -s -X POST "$BASE_URL/tags/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{"name":"测试标签","slug":"test-tag","description":"测试标签"}')

TAG_ID=$(echo "$TAG_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

test_api "创建标签" "POST" "/tags/" "$ADMIN_TOKEN" \
    '{"name":"测试标签2","slug":"test-tag-2"}' "true"

if [ ! -z "$TAG_ID" ]; then
    echo "创建的测试标签ID: $TAG_ID"
    
    # GET /api/v1/cms/tags/{id}/ - 获取标签详情
    test_api "获取标签详情" "GET" "/tags/$TAG_ID/" "" "" "true"
    
    # PUT /api/v1/cms/tags/{id}/ - 更新标签
    test_api "更新标签(PUT)" "PUT" "/tags/$TAG_ID/" "$ADMIN_TOKEN" \
        '{"name":"更新后的标签","slug":"test-tag"}' "true"
    
    # PATCH /api/v1/cms/tags/{id}/ - 部分更新标签
    test_api "部分更新标签(PATCH)" "PATCH" "/tags/$TAG_ID/" "$ADMIN_TOKEN" \
        '{"name":"PATCH更新标签"}' "true"
    
    # DELETE /api/v1/cms/tags/{id}/ - 删除标签
    test_api "删除标签" "DELETE" "/tags/$TAG_ID/" "$ADMIN_TOKEN" "" "true"
fi

# GET /api/v1/cms/tags/usage-stats/ - 获取标签使用统计
test_api "获取标签使用统计" "GET" "/tags/usage-stats/" "" "" "true"

# ============ 标签组管理 API ============
echo -e "\n${YELLOW}=== 标签组管理 API ===${NC}"

# GET /api/v1/cms/tag-groups/ - 获取标签组列表
test_api "获取标签组列表" "GET" "/tag-groups/" "" "" "true"

# POST /api/v1/cms/tag-groups/ - 创建标签组
TAG_GROUP_RESPONSE=$(curl -s -X POST "$BASE_URL/tag-groups/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{"name":"测试标签组","slug":"test-tag-group"}')

TAG_GROUP_ID=$(echo "$TAG_GROUP_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

test_api "创建标签组" "POST" "/tag-groups/" "$ADMIN_TOKEN" \
    '{"name":"测试标签组2","slug":"test-tag-group-2"}' "true"

if [ ! -z "$TAG_GROUP_ID" ]; then
    echo "创建的测试标签组ID: $TAG_GROUP_ID"
    
    # GET /api/v1/cms/tag-groups/{id}/ - 获取标签组详情
    test_api "获取标签组详情" "GET" "/tag-groups/$TAG_GROUP_ID/" "" "" "true"
    
    # PUT /api/v1/cms/tag-groups/{id}/ - 更新标签组
    test_api "更新标签组(PUT)" "PUT" "/tag-groups/$TAG_GROUP_ID/" "$ADMIN_TOKEN" \
        '{"name":"更新后的标签组","slug":"test-tag-group"}' "true"
    
    # PATCH /api/v1/cms/tag-groups/{id}/ - 部分更新标签组
    test_api "部分更新标签组(PATCH)" "PATCH" "/tag-groups/$TAG_GROUP_ID/" "$ADMIN_TOKEN" \
        '{"name":"PATCH更新标签组"}' "true"
    
    # DELETE /api/v1/cms/tag-groups/{id}/ - 删除标签组
    test_api "删除标签组" "DELETE" "/tag-groups/$TAG_GROUP_ID/" "$ADMIN_TOKEN" "" "true"
fi

# ============ 评论管理 API ============
echo -e "\n${YELLOW}=== 评论管理 API ===${NC}"

# GET /api/v1/cms/comments/ - 获取评论列表
test_api "获取评论列表" "GET" "/comments/" "" "" "true"

# 需要先有文章才能创建评论
COMMENT_ARTICLE_ID=$(curl -s -X POST "$BASE_URL/articles/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{"title":"用于评论测试的文章","content":"内容","excerpt":"摘要","status":"published"}' | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

if [ ! -z "$COMMENT_ARTICLE_ID" ]; then
    # POST /api/v1/cms/comments/ - 创建评论
    COMMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/comments/" \
        -H "Authorization: Bearer $MEMBER_TOKEN" \
        -H "X-Tenant-ID: $TENANT_ID" \
        -H "Content-Type: application/json" \
        -d "{\"article\":$COMMENT_ARTICLE_ID,\"content\":\"测试评论内容\"}")
    
    COMMENT_ID=$(echo "$COMMENT_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
    
    test_api "创建评论(Member)" "POST" "/comments/" "$MEMBER_TOKEN" \
        "{\"article\":$COMMENT_ARTICLE_ID,\"content\":\"测试评论2\"}" "true"
    
    if [ ! -z "$COMMENT_ID" ]; then
        echo "创建的测试评论ID: $COMMENT_ID"
        
        # GET /api/v1/cms/comments/{id}/ - 获取评论详情
        test_api "获取评论详情" "GET" "/comments/$COMMENT_ID/" "" "" "true"
        
        # PUT /api/v1/cms/comments/{id}/ - 更新评论
        test_api "更新评论(PUT)" "PUT" "/comments/$COMMENT_ID/" "$MEMBER_TOKEN" \
            "{\"article\":$COMMENT_ARTICLE_ID,\"content\":\"更新后的评论\"}" "true"
        
        # PATCH /api/v1/cms/comments/{id}/ - 部分更新评论
        test_api "部分更新评论(PATCH)" "PATCH" "/comments/$COMMENT_ID/" "$MEMBER_TOKEN" \
            '{"content":"PATCH更新评论"}' "true"
        
        # GET /api/v1/cms/comments/{id}/replies/ - 获取评论回复
        test_api "获取评论回复" "GET" "/comments/$COMMENT_ID/replies/" "" "" "true"
        
        # POST /api/v1/cms/comments/{id}/approve/ - 批准评论 (Admin)
        test_api "批准评论(Admin)" "POST" "/comments/$COMMENT_ID/approve/" "$ADMIN_TOKEN" "" "true"
        
        # POST /api/v1/cms/comments/{id}/reject/ - 拒绝评论 (Admin)
        test_api "拒绝评论(Admin)" "POST" "/comments/$COMMENT_ID/reject/" "$ADMIN_TOKEN" "" "true"
        
        # POST /api/v1/cms/comments/{id}/mark-spam/ - 标记垃圾评论 (Admin)
        test_api "标记垃圾评论(Admin)" "POST" "/comments/$COMMENT_ID/mark-spam/" "$ADMIN_TOKEN" "" "true"
        
        # DELETE /api/v1/cms/comments/{id}/ - 删除评论
        test_api "删除评论(Admin)" "DELETE" "/comments/$COMMENT_ID/" "$ADMIN_TOKEN" "" "true"
    fi
fi

# POST /api/v1/cms/comments/batch/ - 批量处理评论
test_api "批量处理评论" "POST" "/comments/batch/" "$ADMIN_TOKEN" \
    '{"comment_ids":[],"action":"approve"}' "true" "false"

# ============ Member文章管理 API ============
echo -e "\n${YELLOW}=== Member文章管理 API ===${NC}"

# GET /api/v1/cms/member/articles/ - Member获取文章列表
test_api "Member获取文章列表" "GET" "/member/articles/" "$MEMBER_TOKEN" "" "true" "true"

# POST /api/v1/cms/member/articles/ - Member创建文章
MEMBER_ARTICLE_RESPONSE=$(curl -s -X POST "$BASE_URL/member/articles/" \
    -H "Authorization: Bearer $MEMBER_TOKEN" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{"title":"Member测试文章","content":"Member内容","excerpt":"Member摘要","status":"draft"}')

MEMBER_ARTICLE_ID=$(echo "$MEMBER_ARTICLE_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

test_api "Member创建文章" "POST" "/member/articles/" "$MEMBER_TOKEN" \
    '{"title":"Member测试文章2","content":"Member内容2","excerpt":"Member摘要2","status":"draft"}' "true" "true"

if [ ! -z "$MEMBER_ARTICLE_ID" ]; then
    echo "Member创建的测试文章ID: $MEMBER_ARTICLE_ID"
    
    # GET /api/v1/cms/member/articles/{id}/ - Member获取单篇文章
    test_api "Member获取单篇文章" "GET" "/member/articles/$MEMBER_ARTICLE_ID/" "$MEMBER_TOKEN" "" "true" "true"
    
    # PUT /api/v1/cms/member/articles/{id}/ - Member更新文章
    test_api "Member更新文章(PUT)" "PUT" "/member/articles/$MEMBER_ARTICLE_ID/" "$MEMBER_TOKEN" \
        '{"title":"Member更新文章","content":"Member更新内容","excerpt":"Member更新摘要","status":"draft"}' "true" "true"
    
    # PATCH /api/v1/cms/member/articles/{id}/ - Member部分更新文章
    test_api "Member部分更新文章(PATCH)" "PATCH" "/member/articles/$MEMBER_ARTICLE_ID/" "$MEMBER_TOKEN" \
        '{"title":"Member PATCH更新"}' "true" "true"
    
    # POST /api/v1/cms/member/articles/{id}/publish/ - Member发布文章
    test_api "Member发布文章" "POST" "/member/articles/$MEMBER_ARTICLE_ID/publish/" "$MEMBER_TOKEN" "" "true" "true"
    
    # GET /api/v1/cms/member/articles/{id}/statistics/ - Member获取文章统计
    test_api "Member获取文章统计" "GET" "/member/articles/$MEMBER_ARTICLE_ID/statistics/" "$MEMBER_TOKEN" "" "true" "true"
    
    # DELETE /api/v1/cms/member/articles/{id}/ - Member删除文章
    test_api "Member删除文章" "DELETE" "/member/articles/$MEMBER_ARTICLE_ID/" "$MEMBER_TOKEN" "" "true" "true"
fi

# ============ 测试总结 ============
echo ""
echo "========================================"
echo "  测试总结"
echo "========================================"
echo "总计: $TOTAL"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo ""
echo "详细结果已保存到: $RESULTS_FILE"

# 添加总结到结果文件
echo "" >> $RESULTS_FILE
echo "---" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE
echo "## 测试总结" >> $RESULTS_FILE
echo "- **总计**: $TOTAL" >> $RESULTS_FILE
echo "- **通过**: $PASSED" >> $RESULTS_FILE
echo "- **失败**: $FAILED" >> $RESULTS_FILE
echo "- **成功率**: $(awk "BEGIN {printf \"%.2f\", ($PASSED/$TOTAL)*100}")%" >> $RESULTS_FILE
