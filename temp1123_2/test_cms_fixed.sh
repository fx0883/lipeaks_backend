#!/bin/bash

# CMS API 测试脚本 (修复版)
BASE_URL="http://0.0.0.0:8000/api/v1/cms"

# Token配置
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
TENANT_ID="3"

echo "=========================================="
echo "  CMS API 测试开始"
echo "=========================================="

# 测试计数
TOTAL=0
PASSED=0
FAILED=0

# 1. 获取文章列表 - 匿名用户 (需要X-Tenant-ID)
echo -e "\n[测试 $((++TOTAL))] 获取文章列表 - 匿名"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/articles/" -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 2. 获取文章列表 - Admin (不应该带X-Tenant-ID)
echo -e "\n[测试 $((++TOTAL))] 获取文章列表 - Admin"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/articles/" -H "Authorization: Bearer $ADMIN_TOKEN")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 3. 获取文章列表 - Member (需要X-Tenant-ID)
echo -e "\n[测试 $((++TOTAL))] 获取文章列表 - Member"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/articles/" -H "Authorization: Bearer $MEMBER_TOKEN" -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 4. Admin创建文章 (不需要X-Tenant-ID)
echo -e "\n[测试 $((++TOTAL))] Admin创建文章"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/articles/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"测试文章","content":"测试内容","excerpt":"摘要","status":"draft"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" == "201" ]; then 
    echo "✓ 通过"; 
    ((PASSED++)); 
    ARTICLE_ID=$(echo "$BODY" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
    echo "创建的文章ID: $ARTICLE_ID"
else 
    echo "✗ 失败 ($HTTP_CODE)"; 
    ((FAILED++)); 
fi

# 5-8. 如果创建成功，测试其他文章API
if [ ! -z "$ARTICLE_ID" ]; then
    # 5. 获取单篇文章 - 匿名
    echo -e "\n[测试 $((++TOTAL))] 获取单篇文章 - 匿名"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/articles/$ARTICLE_ID/" -H "X-Tenant-ID: $TENANT_ID")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
    
    # 6. Admin更新文章
    echo -e "\n[测试 $((++TOTAL))] Admin更新文章 (PATCH)"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/articles/$ARTICLE_ID/" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"更新后的标题"}')
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
    
    # 7. Admin发布文章
    echo -e "\n[测试 $((++TOTAL))] Admin发布文章"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/articles/$ARTICLE_ID/publish/" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
    
    # 8. 获取文章统计
    echo -e "\n[测试 $((++TOTAL))] 获取文章统计"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/articles/$ARTICLE_ID/statistics/" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
fi

# 9. 获取分类列表 - 匿名
echo -e "\n[测试 $((++TOTAL))] 获取分类列表 - 匿名"
RESPONSE=$(curl -s -w "\n%{http_CODE}" -X GET "$BASE_URL/categories/" -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 10. Admin创建分类 (需要translations字段)
echo -e "\n[测试 $((++TOTAL))] Admin创建分类"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/categories/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"测试分类","slug":"test-cat-final","description":"测试","translations":{"zh-hans":{"name":"测试分类","description":"测试"}}}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" == "201" ]; then 
    echo "✓ 通过"; 
    ((PASSED++)); 
    CATEGORY_ID=$(echo "$BODY" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
else 
    echo "✗ 失败 ($HTTP_CODE)"; 
    ((FAILED++)); 
fi

# 11. 获取分类树
echo -e "\n[测试 $((++TOTAL))] 获取分类树"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/categories/tree/" -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 12. 获取标签列表
echo -e "\n[测试 $((++TOTAL))] 获取标签列表 - 匿名"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/tags/" -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 13. Admin创建标签
echo -e "\n[测试 $((++TOTAL))] Admin创建标签"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/tags/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"测试标签","slug":"test-tag-final"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "201" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 14. 获取标签组列表
echo -e "\n[测试 $((++TOTAL))] 获取标签组列表 - 匿名"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/tag-groups/" -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 15. Admin创建标签组
echo -e "\n[测试 $((++TOTAL))] Admin创建标签组"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/tag-groups/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"测试标签组","slug":"test-group-final"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" == "201" ]; then 
    echo "✓ 通过"; 
    ((PASSED++));
    TAG_GROUP_ID=$(echo "$BODY" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
else 
    echo "✗ 失败 ($HTTP_CODE)"; 
    ((FAILED++)); 
fi

# 16-17. 如果标签组创建成功，测试更新和删除
if [ ! -z "$TAG_GROUP_ID" ]; then
    # 16. Admin更新标签组
    echo -e "\n[测试 $((++TOTAL))] Admin更新标签组 (PATCH)"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/tag-groups/$TAG_GROUP_ID/" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name":"更新后的标签组"}')
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
    
    # 17. Admin删除标签组
    echo -e "\n[测试 $((++TOTAL))] Admin删除标签组"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/tag-groups/$TAG_GROUP_ID/" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "204" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
fi

# 18. 获取评论列表
echo -e "\n[测试 $((++TOTAL))] 获取评论列表 - 匿名"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/comments/" -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 19. Member获取文章列表
echo -e "\n[测试 $((++TOTAL))] Member获取文章列表"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/member/articles/" \
    -H "Authorization: Bearer $MEMBER_TOKEN" \
    -H "X-Tenant-ID: $TENANT_ID")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi

# 20. Member创建文章
echo -e "\n[测试 $((++TOTAL))] Member创建文章"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/member/articles/" \
    -H "Authorization: Bearer $MEMBER_TOKEN" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{"title":"Member文章","content":"Member内容","excerpt":"摘要","status":"draft"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" == "201" ]; then 
    echo "✓ 通过"; 
    ((PASSED++)); 
    MEMBER_ARTICLE_ID=$(echo "$BODY" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
else 
    echo "✗ 失败 ($HTTP_CODE)"; 
    ((FAILED++)); 
fi

# 21-23. Member文章操作
if [ ! -z "$MEMBER_ARTICLE_ID" ]; then
    # 21. Member更新文章
    echo -e "\n[测试 $((++TOTAL))] Member更新文章 (PATCH)"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/member/articles/$MEMBER_ARTICLE_ID/" \
        -H "Authorization: Bearer $MEMBER_TOKEN" \
        -H "X-Tenant-ID: $TENANT_ID" \
        -H "Content-Type: application/json" \
        -d '{"title":"Member更新"}')
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
    
    # 22. Member发布文章
    echo -e "\n[测试 $((++TOTAL))] Member发布文章"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/member/articles/$MEMBER_ARTICLE_ID/publish/" \
        -H "Authorization: Bearer $MEMBER_TOKEN" \
        -H "X-Tenant-ID: $TENANT_ID")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
    
    # 23. Member获取文章统计
    echo -e "\n[测试 $((++TOTAL))] Member获取文章统计"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/member/articles/$MEMBER_ARTICLE_ID/statistics/" \
        -H "Authorization: Bearer $MEMBER_TOKEN" \
        -H "X-Tenant-ID: $TENANT_ID")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "200" ]; then echo "✓ 通过"; ((PASSED++)); else echo "✗ 失败 ($HTTP_CODE)"; ((FAILED++)); fi
fi

echo ""
echo "=========================================="
echo "  测试总结"
echo "=========================================="
echo "总计: $TOTAL"
echo "通过: $PASSED"
echo "失败: $FAILED"
SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")
echo "成功率: ${SUCCESS_RATE}%"
