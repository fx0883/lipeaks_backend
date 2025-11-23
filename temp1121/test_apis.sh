#!/bin/bash

# API测试脚本
# 使用方法: bash temp1121/test_apis.sh

BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/api/v1"

echo "================================"
echo "  LiPeaks Backend API 测试"
echo "================================"
echo ""

# 1. 测试服务器状态
echo "1. 测试服务器状态..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/")
if [ "$response" == "401" ] || [ "$response" == "403" ]; then
    echo "   ✅ 服务器运行正常 (返回 $response)"
else
    echo "   ❌ 服务器异常 (返回 $response)"
    exit 1
fi
echo ""

# 2. 创建测试用户并获取Token
echo "2. 获取认证Token..."
echo "   请手动执行以下命令创建测试用户并获取token:"
echo "   python3 manage.py createsuperuser --username testadmin --email test@example.com"
echo ""
echo "   然后使用curl获取token:"
echo '   TOKEN=$(curl -s -X POST "$API_URL/auth/login/" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d'"'"'{"username": "testadmin", "password": "your_password"}'"'"' \'
echo '     | jq -r ".data.access")'
echo ""
echo "   提示: 将获取的token设置为环境变量:"
echo '   export TOKEN="your_token_here"'
echo ""

# 检查是否已设置TOKEN
if [ -z "$TOKEN" ]; then
    echo "   ⚠️  TOKEN未设置，跳过需要认证的测试"
    echo "   请设置环境变量: export TOKEN=your_token"
    echo ""
    echo "================================"
    echo "  部分测试完成"
    echo "================================"
    exit 0
fi

echo "   ✅ Token已设置"
echo ""

# 3. 测试Applications API
echo "3. 测试Applications API..."
echo ""

# 3.1 获取应用列表
echo "   3.1 GET /applications/ - 获取应用列表"
response=$(curl -s -X GET "$API_URL/applications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1")
echo "   响应: $(echo $response | jq -r '.success // "ERROR"')"
if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
    echo "   ✅ 成功"
    count=$(echo "$response" | jq -r '.data.count // 0')
    echo "   应用数量: $count"
else
    echo "   ❌ 失败"
    echo "   错误: $(echo $response | jq -r '.message // .detail // .')"
fi
echo ""

# 3.2 创建应用
echo "   3.2 POST /applications/ - 创建应用"
timestamp=$(date +%s)
response=$(curl -s -X POST "$API_URL/applications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"测试应用_$timestamp\",
    \"code\": \"test-app-$timestamp\",
    \"description\": \"API测试创建的应用\",
    \"owner\": \"测试团队\",
    \"team\": \"开发部\"
  }")
if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
    echo "   ✅ 创建成功"
    app_id=$(echo "$response" | jq -r '.data.id')
    echo "   应用ID: $app_id"
    
    # 3.3 获取应用详情
    echo ""
    echo "   3.3 GET /applications/$app_id/ - 获取应用详情"
    detail_response=$(curl -s -X GET "$API_URL/applications/$app_id/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Tenant-ID: 1")
    if echo "$detail_response" | jq -e '.success' > /dev/null 2>&1; then
        echo "   ✅ 获取成功"
        echo "   应用名称: $(echo $detail_response | jq -r '.data.name')"
        echo "   当前版本: $(echo $detail_response | jq -r '.data.current_version')"
    else
        echo "   ❌ 获取失败"
    fi
    
    # 3.4 更新应用
    echo ""
    echo "   3.4 PATCH /applications/$app_id/ - 更新应用"
    update_response=$(curl -s -X PATCH "$API_URL/applications/$app_id/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Tenant-ID: 1" \
      -H "Content-Type: application/json" \
      -d '{"current_version": "2.0.0"}')
    if echo "$update_response" | jq -e '.success' > /dev/null 2>&1; then
        echo "   ✅ 更新成功"
        echo "   新版本: $(echo $update_response | jq -r '.data.current_version')"
    else
        echo "   ❌ 更新失败"
    fi
    
    # 3.5 获取统计信息
    echo ""
    echo "   3.5 GET /applications/$app_id/statistics/ - 获取统计"
    stats_response=$(curl -s -X GET "$API_URL/applications/$app_id/statistics/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Tenant-ID: 1")
    if echo "$stats_response" | jq -e '.success' > /dev/null 2>&1; then
        echo "   ✅ 获取成功"
        echo "   许可证: $(echo $stats_response | jq -r '.data.licenses.total // 0')"
        echo "   反馈: $(echo $stats_response | jq -r '.data.feedbacks.total // 0')"
    else
        echo "   ❌ 获取失败"
    fi
else
    echo "   ❌ 创建失败"
    echo "   错误: $(echo $response | jq -r '.message // .detail // .')"
fi
echo ""

# 4. 测试Feedbacks API
echo "4. 测试Feedbacks API..."
echo ""

# 4.1 创建反馈（匿名）
echo "   4.1 POST /feedbacks/feedbacks/ - 创建反馈（匿名）"
if [ ! -z "$app_id" ]; then
    feedback_response=$(curl -s -X POST "$API_URL/feedbacks/feedbacks/" \
      -H "Content-Type: application/json" \
      -H "Tenant-ID: 1" \
      -d "{
        \"title\": \"测试反馈_$timestamp\",
        \"description\": \"这是一个测试反馈\",
        \"feedback_type\": \"bug\",
        \"priority\": \"medium\",
        \"application\": $app_id,
        \"contact_email\": \"test@example.com\"
      }")
    if echo "$feedback_response" | jq -e '.success' > /dev/null 2>&1; then
        echo "   ✅ 创建成功"
        feedback_id=$(echo "$feedback_response" | jq -r '.data.id')
        echo "   反馈ID: $feedback_id"
    else
        echo "   ❌ 创建失败"
        echo "   错误: $(echo $feedback_response | jq -r '.message // .detail // .')"
    fi
else
    echo "   ⚠️  跳过（无可用应用ID）"
fi
echo ""

# 5. 测试CMS API
echo "5. 测试CMS API..."
echo ""

# 5.1 获取分类列表
echo "   5.1 GET /cms/categories/ - 获取分类列表"
categories_response=$(curl -s -X GET "$API_URL/cms/categories/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1")
if echo "$categories_response" | jq -e '.success' > /dev/null 2>&1; then
    echo "   ✅ 成功"
    count=$(echo "$categories_response" | jq -r '.data.count // 0')
    echo "   分类数量: $count"
else
    echo "   ❌ 失败"
fi
echo ""

echo "================================"
echo "  测试完成"
echo "================================"
echo ""
echo "📝 注意事项:"
echo "1. 部分测试需要有效的JWT Token"
echo "2. 请检查Tenant-ID是否正确"
echo "3. 确保数据库中有相应的租户数据"
echo ""
