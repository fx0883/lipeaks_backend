# 测试反馈系统匿名访问功能
# PowerShell 脚本

$API_BASE = "http://localhost:8000/api/v1/feedbacks"
$TENANT_ID = "1"

Write-Host "=========================================" -ForegroundColor Green
Write-Host "测试反馈系统匿名访问功能" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# 不需要 JWT Token 的headers
$headers = @{
    "X-Tenant-ID" = $TENANT_ID
    "Content-Type" = "application/json"
}

# 测试1：匿名访问软件列表（原问题）
Write-Host "✅ 测试1：匿名访问软件列表（原问题）" -ForegroundColor Yellow
Write-Host "URL: $API_BASE/software/?is_active=true&status=released&ordering=name" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/software/?is_active=true&status=released&ordering=name" -Method Get -Headers $headers
    Write-Host "[成功] 状态码: 200" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
    Write-Host "状态码: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}
Write-Host ""

# 测试2：匿名访问软件分类列表
Write-Host "✅ 测试2：匿名访问软件分类列表" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/software-categories/" -Method Get -Headers $headers
    Write-Host "[成功] 返回 $($response.data.Count) 个分类" -ForegroundColor Green
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试3：匿名访问软件版本列表
Write-Host "✅ 测试3：匿名访问软件版本列表" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/software-versions/" -Method Get -Headers $headers
    Write-Host "[成功] 返回 $($response.data.Count) 个版本" -ForegroundColor Green
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试4：匿名访问反馈列表
Write-Host "✅ 测试4：匿名访问反馈列表" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/feedbacks/" -Method Get -Headers $headers
    Write-Host "[成功] 返回数据" -ForegroundColor Green
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试5：匿名提交反馈（最重要）
Write-Host "✅ 测试5：匿名提交反馈（最重要）" -ForegroundColor Yellow
$feedbackData = @{
    title = "匿名反馈测试"
    description = "测试匿名用户提交反馈功能"
    feedback_type = "bug"
    priority = "medium"
    software = 1
    contact_email = "anonymous@example.com"
    contact_name = "匿名测试用户"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/feedbacks/" -Method Post -Headers $headers -Body $feedbackData
    Write-Host "[成功] 反馈ID: $($response.data.id)" -ForegroundColor Green
    Write-Host "标题: $($response.data.title)" -ForegroundColor Cyan
    Write-Host "联系邮箱: $($response.data.contact_email)" -ForegroundColor Cyan
    $feedbackId = $response.data.id
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
    $feedbackId = 1  # 使用默认ID继续测试
}
Write-Host ""

# 测试6：匿名访问反馈详情
Write-Host "✅ 测试6：匿名访问反馈详情" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/feedbacks/$feedbackId/" -Method Get -Headers $headers
    Write-Host "[成功] 反馈标题: $($response.data.title)" -ForegroundColor Green
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试7：匿名访问邮件模板列表
Write-Host "✅ 测试7：匿名访问邮件模板列表" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/email-templates/" -Method Get -Headers $headers
    Write-Host "[成功] 返回数据" -ForegroundColor Green
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
}
Write-Host ""

# 测试8：匿名访问邮件日志列表
Write-Host "✅ 测试8：匿名访问邮件日志列表" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/email-logs/" -Method Get -Headers $headers
    Write-Host "[成功] 返回数据" -ForegroundColor Green
} catch {
    Write-Host "[失败] 错误: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "=========================================" -ForegroundColor Green
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 测试总结：" -ForegroundColor Cyan
Write-Host "1. ✅ 所有 GET API 应该返回 200 状态码" -ForegroundColor White
Write-Host "2. ✅ POST /feedbacks/ 应该允许匿名提交" -ForegroundColor White
Write-Host "3. ✅ 不需要 Authorization header" -ForegroundColor White
Write-Host "4. ✅ 只需要 X-Tenant-ID header" -ForegroundColor White
Write-Host ""

# 测试负面案例：匿名用户尝试修改（应该被拒绝）
Write-Host "🔒 测试负面案例：匿名用户尝试修改软件（应该被拒绝）" -ForegroundColor Magenta
$softwareData = @{
    name = "测试软件修改"
    code = "test_modify"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/software/" -Method Post -Headers $headers -Body $softwareData
    Write-Host "⚠️ 警告：匿名用户可以创建软件！这可能不正确。" -ForegroundColor Red
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401 -or $statusCode -eq 403) {
        Write-Host "✅ 正确：匿名用户无法创建软件 (状态码: $statusCode)" -ForegroundColor Green
    } else {
        Write-Host "❓ 未知错误: $statusCode" -ForegroundColor Yellow
    }
}
Write-Host ""

