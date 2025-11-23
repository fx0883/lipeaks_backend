#!/bin/bash

# 许可证API完整测试脚本
# 测试所有许可证相关的API端点

BASE_URL="http://localhost:8000/api/v1/licenses"
ADMIN_TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"
MEMBER_TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
PASSED=0
FAILED=0
TOTAL=0

# 测试函数
test_api() {
    local name=$1
    local method=$2
    local endpoint=$3
    local token=$4
    local data=$5
    
    TOTAL=$((TOTAL + 1))
    echo -e "\n${YELLOW}[TEST $TOTAL] $name${NC}"
    echo "Method: $method"
    echo "Endpoint: $endpoint"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Authorization: $token" \
            -H "Content-Type: application/json")
    else
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Authorization: $token" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d':' -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')
    
    echo "HTTP Code: $http_code"
    echo "Response: $body" | python3 -m json.tool 2>/dev/null || echo "$body"
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 400 ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo "=========================================="
echo "许可证API测试开始"
echo "=========================================="

# ==================== 1. 产品管理 ====================
echo -e "\n${YELLOW}========== 1. 产品管理 ==========${NC}"

test_api "获取产品列表" "GET" "/admin/products/" "$ADMIN_TOKEN"
test_api "获取产品详情" "GET" "/admin/products/1/" "$ADMIN_TOKEN"

# ==================== 2. 方案管理 ====================
echo -e "\n${YELLOW}========== 2. 方案管理 ==========${NC}"

test_api "获取方案列表" "GET" "/admin/plans/" "$ADMIN_TOKEN"
test_api "获取方案详情" "GET" "/admin/plans/15/" "$ADMIN_TOKEN"

# ==================== 3. 许可证管理 ====================
echo -e "\n${YELLOW}========== 3. 许可证管理 ==========${NC}"

test_api "获取许可证列表" "GET" "/admin/licenses/" "$ADMIN_TOKEN"
test_api "获取许可证详情" "GET" "/admin/licenses/34/" "$ADMIN_TOKEN"

# ==================== 4. 分配管理 ====================
echo -e "\n${YELLOW}========== 4. 分配管理 ==========${NC}"

test_api "获取分配列表" "GET" "/admin/assignments/" "$ADMIN_TOKEN"
test_api "获取分配统计" "GET" "/admin/assignments/statistics/" "$ADMIN_TOKEN"
test_api "获取即将过期的分配" "GET" "/admin/assignments/expiring_soon/?days=30" "$ADMIN_TOKEN"

# ==================== 5. 激活记录 ====================
echo -e "\n${YELLOW}========== 5. 激活记录 ==========${NC}"

test_api "获取激活记录列表" "GET" "/admin/activations/" "$ADMIN_TOKEN"

# ==================== 6. 机器绑定 ====================
echo -e "\n${YELLOW}========== 6. 机器绑定 ==========${NC}"

test_api "获取机器绑定列表" "GET" "/admin/machine-bindings/" "$ADMIN_TOKEN"

# ==================== 7. 安全审计日志 ====================
echo -e "\n${YELLOW}========== 7. 安全审计日志 ==========${NC}"

test_api "获取审计日志列表" "GET" "/admin/audit-logs/" "$ADMIN_TOKEN"

# ==================== 8. 租户配额 ====================
echo -e "\n${YELLOW}========== 8. 租户配额 ==========${NC}"

test_api "获取配额列表" "GET" "/admin/quotas/" "$ADMIN_TOKEN"

# ==================== 9. 报告和统计 ====================
echo -e "\n${YELLOW}========== 9. 报告和统计 ==========${NC}"

test_api "获取统计数据" "GET" "/statistics/" "$ADMIN_TOKEN"
test_api "获取仪表板数据" "GET" "/reports/dashboard/" "$ADMIN_TOKEN"

# ==================== 10. 服务状态 ====================
echo -e "\n${YELLOW}========== 10. 服务状态 ==========${NC}"

test_api "获取服务状态" "GET" "/status/" ""

# ==================== 11. Member API ====================
echo -e "\n${YELLOW}========== 11. Member API ==========${NC}"

test_api "获取可申请产品" "GET" "/member/available-products/" "$MEMBER_TOKEN"
test_api "获取我的许可证" "GET" "/member/my-licenses/" "$MEMBER_TOKEN"

# ==================== 测试结果汇总 ====================
echo -e "\n=========================================="
echo "测试结果汇总"
echo "=========================================="
echo -e "总计: $TOTAL"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo -e "通过率: $((PASSED * 100 / TOTAL))%"
echo "=========================================="
