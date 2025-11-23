#!/bin/bash

ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "CMS API 特殊端点测试"
echo "=========================================="

# 测试文章特殊操作
echo -e "\n=== Article特殊端点 ==="

# 创建一篇新文章用于测试
ARTICLE_ID=$(curl -s -X POST "$BASE_URL/api/v1/cms/articles/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"特殊操作测试","content":"测试内容","status":"draft"}' | jq -r '.data.id')

if [ ! -z "$ARTICLE_ID" ] && [ "$ARTICLE_ID" != "null" ]; then
    echo "测试文章ID: $ARTICLE_ID"
    
    # 发布文章
    echo -n "POST /api/v1/cms/articles/$ARTICLE_ID/publish/: "
    RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/articles/$ARTICLE_ID/publish/" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success // "error"')
    echo "$RESULT"
    
    # 归档文章
    echo -n "POST /api/v1/cms/articles/$ARTICLE_ID/archive/: "
    RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/articles/$ARTICLE_ID/archive/" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success // "error"')
    echo "$RESULT"
    
    # 获取文章统计
    echo -n "GET /api/v1/cms/articles/$ARTICLE_ID/statistics/: "
    RESULT=$(curl -s -X GET "$BASE_URL/api/v1/cms/articles/$ARTICLE_ID/statistics/" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.success // "error"')
    echo "$RESULT"
fi

# 测试评论特殊操作
echo -e "\n=== Comment特殊端点 ==="

# 审核评论
echo -n "POST /api/v1/cms/comments/{id}/approve/: "
echo "需要有效评论ID"

# 标记垃圾评论
echo -n "POST /api/v1/cms/comments/{id}/mark_spam/: "
echo "需要有效评论ID"

# 批量操作
echo -n "POST /api/v1/cms/comments/batch_action/: "
RESULT=$(curl -s -X POST "$BASE_URL/api/v1/cms/comments/batch_action/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"approve","ids":[]}' | jq -r '.success // "error"')
echo "$RESULT"

echo -e "\n=========================================="
echo "特殊端点测试完成"
echo "=========================================="
