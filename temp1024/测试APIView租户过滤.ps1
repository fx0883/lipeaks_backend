# API 测试脚本 - 验证 APIView 租户过滤功能
# PowerShell 版本

# 配置
$API_BASE = "http://localhost:8000/api/v1/feedbacks"
$TENANT_ID = "1"
$JWT_TOKEN = "YOUR_JWT_TOKEN_HERE"  # 替换为实际的JWT Token

Write-Host "=========================================" -ForegroundColor Green
Write-Host "反馈系统 APIView 租户过滤测试" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# 设置headers
$headers = @{
    "X-Tenant-ID" = $TENANT_ID
    "Authorization" = "Bearer $JWT_TOKEN"
    "Content-Type" = "application/json"
}

# 测试1：软件分类列表 (带租户ID)
Write-Host "✅ 测试1：软件分类列表 (带租户ID)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/software-categories/" -Method Get -Headers $headers
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试2：反馈列表 (带租户ID)
Write-Host "✅ 测试2：反馈列表 (带租户ID)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/feedbacks/" -Method Get -Headers $headers
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试3：创建反馈 (租户ID自动设置)
Write-Host "✅ 测试3：创建反馈 (租户ID自动设置)" -ForegroundColor Yellow
$feedbackData = @{
    title = "API测试反馈"
    description = "测试APIView租户过滤"
    feedback_type = "bug"
    priority = "medium"
    software = 1
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/feedbacks/" -Method Post -Headers $headers -Body $feedbackData
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试4：邮件模板列表 (带租户ID)
Write-Host "✅ 测试4：邮件模板列表 (带租户ID)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/email-templates/" -Method Get -Headers $headers
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试5：软件版本列表 (带租户ID)
Write-Host "✅ 测试5：软件版本列表 (带租户ID)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/software-versions/" -Method Get -Headers $headers
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试6：反馈回复列表 (嵌套路由)
Write-Host "✅ 测试6：反馈回复列表 (嵌套路由)" -ForegroundColor Yellow
$FEEDBACK_ID = 1  # 替换为实际的反馈ID
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/feedbacks/$FEEDBACK_ID/replies/" -Method Get -Headers $headers
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "=========================================" -ForegroundColor Green
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 检查要点：" -ForegroundColor Cyan
Write-Host "1. 所有响应都应该只包含当前租户的数据" -ForegroundColor White
Write-Host "2. 创建操作返回的对象应该包含正确的 tenant 信息" -ForegroundColor White
Write-Host "3. 不应该看到其他租户的数据" -ForegroundColor White
Write-Host "4. 嵌套路由应该正常工作" -ForegroundColor White
Write-Host ""

# 测试跨租户访问（应该被拒绝）
Write-Host "🔒 测试跨租户访问保护..." -ForegroundColor Magenta
$OTHER_TENANT_ID = "999"  # 不存在的租户ID
$headers["X-Tenant-ID"] = $OTHER_TENANT_ID
Write-Host "尝试访问其他租户数据 (Tenant-ID: $OTHER_TENANT_ID)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/feedbacks/1/" -Method Get -Headers $headers
    Write-Host "警告：跨租户访问未被阻止！" -ForegroundColor Red
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✅ 正确：跨租户访问被拒绝 - $_" -ForegroundColor Green
}
Write-Host ""

