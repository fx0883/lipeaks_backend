#!/bin/bash

# CMS API测试脚本
# 租户管理员Token
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDU4NDI2MCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.uXCp3J6_qNm9LMclT--47PzZLZDwnlbZOpQNqsQft94"

# Member用户Token
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NTkwMzUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.1Cu5_gyY5n_rV9MTNf6wNQaov7BBUZQJizE4J0OmpNw"

BASE_URL="http://localhost:8000/api/v1/cms"

echo "=========================================="
echo "开始测试 CMS API"
echo "=========================================="

# 1. 测试文章管理API（租户管理员）
echo -e "\n[1] 测试获取文章列表（租户管理员）"
curl -s -X GET "$BASE_URL/articles/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .message'

echo -e "\n[2] 测试创建文章（租户管理员）"
ARTICLE_ID=$(curl -s -X POST "$BASE_URL/articles/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章-自动化测试",
    "content": "这是自动化测试创建的文章内容",
    "content_type": "markdown",
    "excerpt": "测试摘要",
    "status": "draft"
  }' | jq -r '.data.id')
echo "创建的文章ID: $ARTICLE_ID"

echo -e "\n[3] 测试获取单篇文章（租户管理员）"
curl -s -X GET "$BASE_URL/articles/$ARTICLE_ID/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.title'

echo -e "\n[4] 测试更新文章（租户管理员）"
curl -s -X PATCH "$BASE_URL/articles/$ARTICLE_ID/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "excerpt": "更新后的摘要"
  }' | jq '.success, .data.title'

echo -e "\n[5] 测试发布文章（租户管理员）"
curl -s -X POST "$BASE_URL/articles/$ARTICLE_ID/publish/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.status'

echo -e "\n[6] 测试取消发布文章（租户管理员）"
curl -s -X POST "$BASE_URL/articles/$ARTICLE_ID/unpublish/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.status'

echo -e "\n[7] 测试归档文章（租户管理员）"
curl -s -X POST "$BASE_URL/articles/$ARTICLE_ID/archive/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.status'

echo -e "\n[8] 测试记录文章阅读（无需认证）"
curl -s -X POST "$BASE_URL/articles/$ARTICLE_ID/view/" | jq '.success, .message'

echo -e "\n[9] 测试获取文章统计（租户管理员）"
curl -s -X GET "$BASE_URL/articles/$ARTICLE_ID/statistics/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.basic_stats.views_count'

echo -e "\n[10] 测试获取文章版本历史（租户管理员）"
curl -s -X GET "$BASE_URL/articles/$ARTICLE_ID/versions/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, (.data | length)'

# 2. 测试分类管理API
echo -e "\n[11] 测试获取分类列表（租户管理员）"
curl -s -X GET "$BASE_URL/categories/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, (.data.results | length)'

echo -e "\n[12] 测试创建分类（租户管理员）"
CATEGORY_ID=$(curl -s -X POST "$BASE_URL/categories/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "自动化测试分类",
        "description": "测试描述"
      }
    },
    "is_active": true
  }' | jq -r '.data.id')
echo "创建的分类ID: $CATEGORY_ID"

echo -e "\n[13] 测试获取分类详情（租户管理员）"
curl -s -X GET "$BASE_URL/categories/$CATEGORY_ID/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.name'

echo -e "\n[14] 测试更新分类（租户管理员）"
curl -s -X PATCH "$BASE_URL/categories/$CATEGORY_ID/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "更新后的分类名"
      }
    }
  }' | jq '.success, .data.name'

echo -e "\n[15] 测试获取分类树（租户管理员）"
curl -s -X GET "$BASE_URL/categories/tree/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success'

# 3. 测试标签管理API
echo -e "\n[16] 测试获取标签列表（租户管理员）"
curl -s -X GET "$BASE_URL/tags/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, (.data.results | length)'

echo -e "\n[17] 测试创建标签（租户管理员）"
TAG_ID=$(curl -s -X POST "$BASE_URL/tags/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "自动化测试标签",
    "description": "测试描述",
    "color": "#FF5733"
  }' | jq -r '.data.id')
echo "创建的标签ID: $TAG_ID"

echo -e "\n[18] 测试获取标签详情（租户管理员）"
curl -s -X GET "$BASE_URL/tags/$TAG_ID/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.name'

echo -e "\n[19] 测试更新标签（租户管理员）"
curl -s -X PATCH "$BASE_URL/tags/$TAG_ID/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的标签"
  }' | jq '.success, .data.name'

# 4. 测试标签组API
echo -e "\n[20] 测试获取标签组列表（租户管理员）"
curl -s -X GET "$BASE_URL/tag-groups/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success'

echo -e "\n[21] 测试创建标签组（租户管理员）"
TAG_GROUP_ID=$(curl -s -X POST "$BASE_URL/tag-groups/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "自动化测试标签组",
    "description": "测试描述"
  }' | jq -r '.data.id')
echo "创建的标签组ID: $TAG_GROUP_ID"

# 5. 测试评论管理API
echo -e "\n[22] 测试获取评论列表（租户管理员）"
curl -s -X GET "$BASE_URL/comments/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success'

echo -e "\n[23] 测试创建评论（Member）"
COMMENT_ID=$(curl -s -X POST "$BASE_URL/comments/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d "{
    \"article\": $ARTICLE_ID,
    \"content\": \"这是测试评论\"
  }" | jq -r '.data.id')
echo "创建的评论ID: $COMMENT_ID"

echo -e "\n[24] 测试批准评论（租户管理员）"
curl -s -X POST "$BASE_URL/comments/$COMMENT_ID/approve/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.success, .data.status'

# 6. 测试Member文章管理API
echo -e "\n[25] 测试Member获取文章列表"
curl -s -X GET "$BASE_URL/member/articles/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" | jq '.success, (.data.results | length)'

echo -e "\n[26] 测试Member创建文章"
MEMBER_ARTICLE_ID=$(curl -s -X POST "$BASE_URL/member/articles/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Member自动化测试文章",
    "content": "这是Member创建的文章",
    "content_type": "markdown",
    "excerpt": "测试摘要",
    "status": "draft"
  }' | jq -r '.data.id')
echo "Member创建的文章ID: $MEMBER_ARTICLE_ID"

echo -e "\n[27] 测试Member发布文章"
curl -s -X POST "$BASE_URL/member/articles/$MEMBER_ARTICLE_ID/publish/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" | jq '.success, .data.status'

echo -e "\n[28] 测试Member获取文章统计"
curl -s -X GET "$BASE_URL/member/articles/$MEMBER_ARTICLE_ID/statistics/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" | jq '.success'

echo -e "\n=========================================="
echo "CMS API 测试完成"
echo "=========================================="
