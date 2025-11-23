#!/bin/bash
# 租户隔离功能性能压力测试脚本
# 使用 Apache Bench (ab) 进行基础性能测试

echo "======================================================================"
echo "租户隔离功能性能压力测试"
echo "======================================================================"

# 配置
BASE_URL="http://localhost:8000"
TENANT_ID="3"
TOKEN="YOUR_TOKEN_HERE"  # 需要替换为实际的Token

# 检查ab工具是否安装
if ! command -v ab &> /dev/null; then
    echo "❌ Apache Bench (ab) 未安装"
    echo "安装方法:"
    echo "  macOS: brew install httpd"
    echo "  Ubuntu: sudo apt-get install apache2-utils"
    exit 1
fi

echo ""
echo "测试配置:"
echo "  - Base URL: $BASE_URL"
echo "  - Tenant ID: $TENANT_ID"
echo "  - 工具: Apache Bench"
echo ""

# 测试1: Applications API 性能
echo "======================================================================"
echo "测试1: Applications API 查询性能"
echo "======================================================================"
echo ""
echo "测试参数:"
echo "  - 总请求数: 100"
echo "  - 并发数: 10"
echo "  - 端点: /api/v1/applications/"
echo ""

ab -n 100 -c 10 \
   -H "X-Tenant-ID: $TENANT_ID" \
   -H "Authorization: Bearer $TOKEN" \
   "${BASE_URL}/api/v1/applications/"

echo ""
echo "======================================================================"
echo "测试2: Orders API 查询性能"
echo "======================================================================"
echo ""

ab -n 100 -c 10 \
   -H "X-Tenant-ID: $TENANT_ID" \
   -H "Authorization: Bearer $TOKEN" \
   "${BASE_URL}/api/v1/orders/"

echo ""
echo "======================================================================"
echo "测试3: Customers API 查询性能"
echo "======================================================================"
echo ""

ab -n 100 -c 10 \
   -H "X-Tenant-ID: $TENANT_ID" \
   -H "Authorization: Bearer $TOKEN" \
   "${BASE_URL}/api/v1/customers/"

echo ""
echo "======================================================================"
echo "测试4: 高并发测试 (Applications)"
echo "======================================================================"
echo ""
echo "测试参数:"
echo "  - 总请求数: 1000"
echo "  - 并发数: 50"
echo ""

ab -n 1000 -c 50 \
   -H "X-Tenant-ID: $TENANT_ID" \
   -H "Authorization: Bearer $TOKEN" \
   "${BASE_URL}/api/v1/applications/"

echo ""
echo "======================================================================"
echo "测试完成"
echo "======================================================================"
echo ""
echo "性能指标说明:"
echo "  - Time per request: 平均响应时间 (越低越好)"
echo "  - Requests per second: 每秒请求数 (越高越好)"
echo "  - Transfer rate: 传输速率"
echo ""
echo "建议标准:"
echo "  - 平均响应时间: < 100ms (优秀)"
echo "  - 平均响应时间: 100-500ms (良好)"
echo "  - 平均响应时间: > 500ms (需要优化)"
echo ""
