#!/bin/bash

ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "CMS API CRUD测试"
echo "=========================================="

# 测试Article CRUD
echo -e "\n=== Article CRUD测试 ==="

# GET单篇文章
echo -n "GET /api/v1/cms/articles/10265/: "
RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/articles/10265/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
echo "$RESULT"

# UPDATE文章
echo -n "PATCH /api/v1/cms/articles/10265/: "
RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/articles/10265/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"更新后的标题"}' | jq -r '.success')
echo "$RESULT"

# DELETE文章
echo -n "DELETE /api/v1/cms/articles/10265/: "
RESULT=$(curl -s -X DELETE "$BASE_URL/api/v1/cms/articles/10265/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
echo "$RESULT"

# 测试Member Article CRUD
echo -e "\n=== Member Article CRUD测试 ==="

# GET单篇
echo -n "GET /api/v1/cms/member/articles/10266/: "
RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/member/articles/10266/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" | jq -r '.success')
echo "$RESULT"

# UPDATE
echo -n "PATCH /api/v1/cms/member/articles/10266/: "
RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/member/articles/10266/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"title":"Member更新后的标题"}' | jq -r '.success')
echo "$RESULT"

# 测试Comment CRUD
echo -e "\n=== Comment CRUD测试 ==="

# 创建评论
echo -n "POST /api/v1/cms/comments/: "
COMMENT_ID=$(curl -s -X POST "$BASE_URL/api/v1/cms/comments/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article":1,"content":"测试评论","status":"approved"}' | jq -r '.data.id // "error"')
echo "$COMMENT_ID"

if [ "$COMMENT_ID" != "error" ] && [ ! -z "$COMMENT_ID" ]; then
    # GET评论
    echo -n "GET /api/v1/cms/comments/$COMMENT_ID/: "
    RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/comments/$COMMENT_ID/" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
    echo "$RESULT"
    
    # UPDATE评论
    echo -n "PATCH /api/v1/cms/comments/$COMMENT_ID/: "
    RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/comments/$COMMENT_ID/" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"content":"更新后的评论"}' | jq -r '.success')
    echo "$RESULT"
fi

# 测试Category和Tag CRUD
echo -e "\n=== Category & Tag CRUD测试 ==="

# 获取单个分类
echo -n "GET /api/v1/cms/categories/1/: "
RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/categories/1/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
echo "$RESULT"

# 更新分类
echo -n "PATCH /api/v1/cms/categories/50/: "
RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/categories/50/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"translations":{"zh-hans":{"name":"更新后的分类名"}}}' | jq -r '.success')
echo "$RESULT"

# 获取单个标签
echo -n "GET /api/v1/cms/tags/2/: "
RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success')
echo "$RESULT"

# 更新标签
echo -n "PATCH /api/v1/cms/tags/2/: "
RESULT=$(curl -s -X PATCH "$BASE_URL/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"更新后的标签"}' | jq -r '.success')
echo "$RESULT"

echo -e "\n=========================================="
echo "CRUD测试完成"
echo "=========================================="
