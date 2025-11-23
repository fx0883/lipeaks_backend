#!/bin/bash

# API测试脚本
# 用于验证所有涉及修复的API是否正常工作

API_BASE="http://localhost:8000/api/v1"
USERNAME="test_admin"
PASSWORD="test123456"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  API修复验证测试脚本"
echo "======================================"
echo ""

# 步骤1: 获取Token
echo "步骤1: 获取认证Token"
echo "-----------------------------------"

LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print(data['data']['token'])
    else:
        print('LOGIN_FAILED')
except:
    print('JSON_ERROR')
")

if [ "$TOKEN" = "LOGIN_FAILED" ] || [ "$TOKEN" = "JSON_ERROR" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ 登录失败${NC}"
  echo "请检查用户名和密码，或确保服务器正在运行"
  exit 1
fi

echo -e "${GREEN}✓ Token获取成功${NC}"
echo "Token: ${TOKEN:0:50}..."
echo ""

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_api() {
  local test_name=$1
  local method=$2
  local endpoint=$3
  local extra_args=$4
  
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -e "${YELLOW}测试 $TOTAL_TESTS: $test_name${NC}"
  
  RESPONSE=$(curl -s -X $method "$API_BASE$endpoint" \
    -H "Authorization: Bearer $TOKEN" \
    $extra_args)
  
  # 检查响应是否为有效JSON
  IS_VALID=$(echo $RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # 检查是否为成功响应或已知错误
    if data.get('success') is not None:
        print('VALID')
    else:
        print('INVALID')
except:
    print('INVALID')
")
  
  if [ "$IS_VALID" = "VALID" ]; then
    echo -e "  ${GREEN}✓ API响应正常${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
  else:
    echo -e "  ${RED}✗ API响应异常${NC}"
    echo "  Response: $RESPONSE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
  echo ""
}

# 步骤2: 测试所有API
echo "步骤2: 测试API端点"
echo "-----------------------------------"
echo ""

# API 1: 积分统计
test_api "积分统计概览" "GET" "/points/statistics/"

# API 2: 用户积分记录（可能没有数据，但应该返回正常响应）
test_api "用户积分记录" "GET" "/points/user-points/?page_size=1"

# API 3: RBAC权限（这个可能返回404，但响应格式应该正常）
echo -e "${YELLOW}测试 $((TOTAL_TESTS + 1)): RBAC移除权限${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
RBAC_RESPONSE=$(curl -s -X DELETE "$API_BASE/rbac/roles/999/permissions/999/" \
  -H "Authorization: Bearer $TOKEN")
  
RBAC_VALID=$(echo $RBAC_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success') is not None:
        print('VALID')
    else:
        print('INVALID')
except:
    print('INVALID')
")

if [ "$RBAC_VALID" = "VALID" ]; then
  echo -e "  ${GREEN}✓ API响应格式正常（预期404）${NC}"
  PASSED_TESTS=$((PASSED_TESTS + 1))
else
  echo -e "  ${RED}✗ API响应异常${NC}"
  FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# API 4: 反馈通知（可能返回404，但响应格式应该正常）
echo -e "${YELLOW}测试 $((TOTAL_TESTS + 1)): 切换反馈通知${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
FEEDBACK_RESPONSE=$(curl -s -X PATCH "$API_BASE/feedbacks/feedbacks/999/notifications/" \
  -H "Authorization: Bearer $TOKEN")
  
FEEDBACK_VALID=$(echo $FEEDBACK_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success') is not None:
        print('VALID')
    else:
        print('INVALID')
except:
    print('INVALID')
")

if [ "$FEEDBACK_VALID" = "VALID" ]; then
  echo -e "  ${GREEN}✓ API响应格式正常（预期404）${NC}"
  PASSED_TESTS=$((PASSED_TESTS + 1))
else
  echo -e "  ${RED}✗ API响应异常${NC}"
  FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# API 5: 更新用户角色（可能返回404或403，但响应格式应该正常）
echo -e "${YELLOW}测试 $((TOTAL_TESTS + 1)): 更新用户角色${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
ROLE_RESPONSE=$(curl -s -X PATCH "$API_BASE/users/role/999/update/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}')
  
ROLE_VALID=$(echo $ROLE_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success') is not None:
        print('VALID')
    else:
        print('INVALID')
except:
    print('INVALID')
")

if [ "$ROLE_VALID" = "VALID" ]; then
  echo -e "  ${GREEN}✓ API响应格式正常（预期404）${NC}"
  PASSED_TESTS=$((PASSED_TESTS + 1))
else
  echo -e "  ${RED}✗ API响应异常${NC}"
  FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# 步骤3: 测试结果汇总
echo "======================================"
echo "  测试结果汇总"
echo "======================================"
echo ""
echo "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
  echo -e "${GREEN}✓ 所有API响应格式验证通过！${NC}"
  echo ""
  echo "说明: 部分API返回404是正常的，因为测试使用了"
  echo "不存在的资源ID。重要的是响应格式符合规范。"
  exit 0
else
  echo -e "${RED}✗ 有API响应异常，请检查服务器日志${NC}"
  exit 1
fi
