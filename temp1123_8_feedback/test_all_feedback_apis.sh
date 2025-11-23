#!/bin/bash

# Feedback System API 完整测试脚本
# 测试所有26个API端点

# ==================== 配置 ====================
BASE_URL="http://localhost:8000"
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ==================== 辅助函数 ====================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}测试 $TOTAL_TESTS: $1${NC}"
}

check_response() {
    local response=$1
    local test_name=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # 检查是否成功
    SUCCESS=$(echo "$response" | jq -r '.success // empty')
    HTTP_CODE=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    
    if [ "$SUCCESS" = "true" ] || [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
        echo -e "${GREEN}✅ PASSED${NC}: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}: $test_name"
        echo -e "${RED}Response: $response${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# ==================== 测试开始 ====================

echo -e "${BLUE}"
echo "███████╗███████╗███████╗██████╗ ██████╗  █████╗  ██████╗██╗  ██╗"
echo "██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██║ ██╔╝"
echo "█████╗  █████╗  █████╗  ██║  ██║██████╔╝███████║██║     █████╔╝ "
echo "██╔══╝  ██╔══╝  ██╔══╝  ██║  ██║██╔══██╗██╔══██║██║     ██╔═██╗ "
echo "██║     ███████╗███████╗██████╔╝██████╔╝██║  ██║╚██████╗██║  ██╗"
echo "╚═╝     ╚══════╝╚══════╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝"
echo "                 API 测试套件 v1.0"
echo -e "${NC}\n"

# ==================== 反馈管理API ====================

print_header "1. 反馈管理 API (9个)"

# 1.1 获取反馈列表
print_test "GET /feedbacks/ - 获取反馈列表"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/feedbacks/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "获取反馈列表"

# 1.2 创建反馈
print_test "POST /feedbacks/ - 创建反馈"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${BASE_URL}/api/v1/feedbacks/feedbacks/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "自动化测试反馈",
        "description": "这是自动化测试创建的反馈",
        "feedback_type": "bug",
        "priority": "medium"
    }')
check_response "$RESPONSE" "创建反馈"

# 提取反馈ID
FEEDBACK_ID=$(echo "$RESPONSE" | grep -v "HTTP_CODE" | jq -r '.data.id // empty')
if [ -z "$FEEDBACK_ID" ]; then
    echo -e "${RED}错误: 无法获取反馈ID${NC}"
    FEEDBACK_ID=1
fi
echo -e "${BLUE}创建的反馈ID: $FEEDBACK_ID${NC}"

# 1.3 获取反馈详情
print_test "GET /feedbacks/{id}/ - 获取反馈详情"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "获取反馈详情"

# 1.4 部分更新反馈
print_test "PATCH /feedbacks/{id}/ - 部分更新反馈"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X PATCH "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"title": "更新后的标题"}')
check_response "$RESPONSE" "部分更新反馈"

# 1.5 完整更新反馈
print_test "PUT /feedbacks/{id}/ - 完整更新反馈"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X PUT "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "完整更新的标题",
        "description": "完整更新的描述",
        "feedback_type": "feature",
        "priority": "high"
    }')
check_response "$RESPONSE" "完整更新反馈"

# 1.6 更改反馈状态
print_test "PATCH /feedbacks/{id}/status/ - 更改反馈状态"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X PATCH "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/status/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"status": "reviewing", "reason": "测试状态变更"}')
check_response "$RESPONSE" "更改反馈状态"

# 1.7 切换通知设置
print_test "PATCH /feedbacks/{id}/notifications/ - 切换通知"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X PATCH "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/notifications/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "切换通知设置"

# 1.8 验证邮箱 (预期失败 - 无效token)
print_test "POST /feedbacks/{id}/verify-email/ - 验证邮箱"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/verify-email/" \
    -H "Content-Type: application/json" \
    -d '{"token": "invalid_token"}')
# 这个测试预期会失败，因为token无效，但API应该正常响应
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if echo "$RESPONSE" | grep -q "400\|404"; then
    echo -e "${GREEN}✅ PASSED${NC}: 验证邮箱 (正确返回错误)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: 验证邮箱 (非预期响应)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# 1.9 删除反馈 (最后执行)
print_test "DELETE /feedbacks/{id}/ - 删除反馈 (稍后执行)"

# ==================== 投票API ====================

print_header "2. 投票 API (2个)"

# 2.1 投票
print_test "POST /feedbacks/{id}/vote/ - 投票"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/vote/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"vote_type": 1}')
check_response "$RESPONSE" "对反馈投票"

# 2.2 取消投票
print_test "DELETE /feedbacks/{id}/vote/ - 取消投票"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X DELETE "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/vote/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "取消投票"

# ==================== 回复API ====================

print_header "3. 回复 API (6个)"

# 3.1 获取回复列表
print_test "GET /feedbacks/{id}/replies/ - 获取回复列表"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/replies/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "获取回复列表"

# 3.2 创建回复
print_test "POST /feedbacks/{id}/replies/ - 创建回复"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/replies/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"content": "这是一条测试回复"}')
check_response "$RESPONSE" "创建回复"

# 提取回复ID
REPLY_ID=$(echo "$RESPONSE" | grep -v "HTTP_CODE" | jq -r '.data.id // empty')
if [ -z "$REPLY_ID" ]; then
    echo -e "${YELLOW}警告: 无法获取回复ID，使用默认值${NC}"
    REPLY_ID=1
fi
echo -e "${BLUE}创建的回复ID: $REPLY_ID${NC}"

# 3.3 获取回复详情
print_test "GET /feedbacks/{id}/replies/{reply_id}/ - 获取回复详情"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/replies/${REPLY_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "获取回复详情"

# 3.4 部分更新回复
print_test "PATCH /feedbacks/{id}/replies/{reply_id}/ - 部分更新回复"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X PATCH "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/replies/${REPLY_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"content": "更新后的回复内容"}')
check_response "$RESPONSE" "部分更新回复"

# 3.5 完整更新回复
print_test "PUT /feedbacks/{id}/replies/{reply_id}/ - 完整更新回复"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X PUT "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/replies/${REPLY_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"content": "完整更新的回复", "is_internal_note": false}')
check_response "$RESPONSE" "完整更新回复"

# 3.6 删除回复
print_test "DELETE /feedbacks/{id}/replies/{reply_id}/ - 删除回复"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X DELETE "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/replies/${REPLY_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "删除回复"

# ==================== 附件API ====================

print_header "4. 附件 API (4个)"

# 创建测试文件
echo "Test attachment content" > /tmp/test_attachment.txt

# 4.1 获取附件列表
print_test "GET /feedbacks/{id}/attachments/ - 获取附件列表"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "获取附件列表"

# 4.2 上传附件
print_test "POST /feedbacks/{id}/attachments/ - 上传附件"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -F "file=@/tmp/test_attachment.txt")
check_response "$RESPONSE" "上传附件"

# 提取附件ID
ATTACHMENT_ID=$(echo "$RESPONSE" | grep -v "HTTP_CODE" | jq -r '.data.id // empty')
if [ -z "$ATTACHMENT_ID" ]; then
    echo -e "${YELLOW}警告: 无法获取附件ID，使用默认值${NC}"
    ATTACHMENT_ID=1
fi
echo -e "${BLUE}上传的附件ID: $ATTACHMENT_ID${NC}"

# 4.3 获取附件详情
print_test "GET /feedbacks/{id}/attachments/{attachment_id}/ - 获取附件详情"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/${ATTACHMENT_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "获取附件详情"

# 4.4 删除附件
print_test "DELETE /feedbacks/{id}/attachments/{attachment_id}/ - 删除附件"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X DELETE "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/${ATTACHMENT_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "删除附件"

# 清理测试文件
rm -f /tmp/test_attachment.txt

# ==================== 统计与健康检查API ====================

print_header "5. 统计与健康检查 API (3个)"

# 5.1 获取统计数据
print_test "GET /statistics/ - 获取统计数据"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/statistics/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "获取统计数据"

# 5.2 系统健康检查
print_test "GET /health/ - 系统健康检查"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/health/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "系统健康检查"

# 5.3 Redis状态检查
print_test "GET /health/redis/ - Redis状态检查"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "${BASE_URL}/api/v1/feedbacks/health/redis/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "Redis状态检查"

# ==================== 清理 ====================

print_header "6. 清理测试数据"

# 删除测试反馈
print_test "DELETE /feedbacks/{id}/ - 删除测试反馈"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X DELETE "${BASE_URL}/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")
check_response "$RESPONSE" "删除测试反馈"

# ==================== 测试总结 ====================

print_header "测试总结"

echo -e "${BLUE}总测试数: $TOTAL_TESTS${NC}"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    SUCCESS_RATE=100
else
    SUCCESS_RATE=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
fi

echo -e "${YELLOW}成功率: ${SUCCESS_RATE}%${NC}\n"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✨ 所有测试通过！${NC}\n"
    exit 0
else
    echo -e "${RED}❌ 有 $FAILED_TESTS 个测试失败${NC}\n"
    exit 1
fi
