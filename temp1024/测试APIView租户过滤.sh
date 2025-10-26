#!/bin/bash
# API 测试脚本 - 验证 APIView 租户过滤功能

# 配置
API_BASE="http://localhost:8000/api/v1/feedbacks"
TENANT_ID="1"
JWT_TOKEN="YOUR_JWT_TOKEN_HERE"

echo "========================================="
echo "反馈系统 APIView 租户过滤测试"
echo "========================================="
echo ""

# 测试1：软件分类列表 (带租户ID)
echo "✅ 测试1：软件分类列表 (带租户ID)"
curl -s "${API_BASE}/software-categories/" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" | jq .
echo ""

# 测试2：反馈列表 (带租户ID)
echo "✅ 测试2：反馈列表 (带租户ID)"
curl -s "${API_BASE}/feedbacks/" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" | jq .
echo ""

# 测试3：创建反馈 (租户ID自动设置)
echo "✅ 测试3：创建反馈 (租户ID自动设置)"
curl -s "${API_BASE}/feedbacks/" \
  -X POST \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API测试反馈",
    "description": "测试APIView租户过滤",
    "feedback_type": "bug",
    "priority": "medium",
    "software": 1
  }' | jq .
echo ""

# 测试4：邮件模板列表 (带租户ID)
echo "✅ 测试4：邮件模板列表 (带租户ID)"
curl -s "${API_BASE}/email-templates/" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" | jq .
echo ""

# 测试5：软件版本列表 (带租户ID)
echo "✅ 测试5：软件版本列表 (带租户ID)"
curl -s "${API_BASE}/software-versions/" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" | jq .
echo ""

echo "========================================="
echo "测试完成！"
echo "========================================="
echo ""
echo "🔍 检查要点："
echo "1. 所有响应都应该只包含当前租户的数据"
echo "2. 创建操作返回的对象应该包含正确的 tenant_id"
echo "3. 不应该看到其他租户的数据"
echo ""

