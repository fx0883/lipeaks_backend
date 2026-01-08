# 通知系统API测试脚本
# 用于测试并收集真实的API响应数据

$ErrorActionPreference = "Continue"

# 登录获取token
Write-Host "=== 1. 租户管理员登录 ===" -ForegroundColor Green
$loginBody = @{username='admin_cms'; password='admin_main'} | ConvertTo-Json -Compress
$loginResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/auth/login/' -Method Post -Body $loginBody -ContentType 'application/json; charset=utf-8'
$adminToken = $loginResponse.data.token
$tenantId = $loginResponse.data.user.tenant_id
Write-Host "Token: $adminToken"
Write-Host "Tenant ID: $tenantId`n"

# 创建通知
Write-Host "=== 2. 创建通知（草稿） ===" -ForegroundColor Green
$createBody = @{
    title='System Maintenance Notice'
    content='We will perform system maintenance tonight from 22:00-23:00.'
    scope='tenant'
    notification_type='info'
    priority='normal'
    send_email=$false
} | ConvertTo-Json -Compress
$headers = @{'Authorization'="Bearer $adminToken"; 'Content-Type'='application/json; charset=utf-8'}
$createResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/notifications/' -Method Post -Headers $headers -Body $createBody
Write-Host ($createResponse | ConvertTo-Json -Depth 10)
$notificationId = $createResponse.data.id
Write-Host "`nCreated Notification ID: $notificationId`n"

# 获取通知列表
Write-Host "=== 3. 获取通知列表 ===" -ForegroundColor Green
$listResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/notifications/' -Headers $headers
Write-Host ($listResponse | ConvertTo-Json -Depth 10)
Write-Host ""

# 获取通知详情
Write-Host "=== 4. 获取通知详情 ===" -ForegroundColor Green
$detailResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/notifications/$notificationId/" -Headers $headers
Write-Host ($detailResponse | ConvertTo-Json -Depth 10)
Write-Host ""

# 发布通知
Write-Host "=== 5. 发布通知 ===" -ForegroundColor Green
$publishResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/notifications/$notificationId/publish/" -Method Post -Headers $headers
Write-Host ($publishResponse | ConvertTo-Json -Depth 10)
Write-Host ""

# 获取接收者列表
Write-Host "=== 6. 获取接收者列表 ===" -ForegroundColor Green
$recipientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/notifications/$notificationId/recipients/" -Headers $headers
Write-Host ($recipientsResponse | ConvertTo-Json -Depth 10)
Write-Host ""

# 获取统计信息
Write-Host "=== 7. 获取统计信息 ===" -ForegroundColor Green
$statsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/notifications/$notificationId/statistics/" -Headers $headers
Write-Host ($statsResponse | ConvertTo-Json -Depth 10)
Write-Host ""

# 创建应用通知
Write-Host "=== 8. 创建应用通知 ===" -ForegroundColor Green
$appNotifBody = @{
    title='New Feature Release'
    content='Blog system now supports Markdown editor and code highlighting!'
    scope='application'
    application=6
    notification_type='update'
    priority='high'
    send_email=$false
} | ConvertTo-Json -Compress
try {
    $appNotifResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/notifications/' -Method Post -Headers $headers -Body $appNotifBody
    Write-Host ($appNotifResponse | ConvertTo-Json -Depth 10)
    $appNotifId = $appNotifResponse.data.id
    Write-Host "`nPublishing application notification..."
    $appPublishResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/notifications/$appNotifId/publish/" -Method Post -Headers $headers
    Write-Host ($appPublishResponse | ConvertTo-Json -Depth 10)
} catch {
    Write-Host "Application notification creation failed (application might not exist)" -ForegroundColor Yellow
}
Write-Host ""

# 归档通知
Write-Host "=== 9. 归档通知 ===" -ForegroundColor Green
$archiveResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/notifications/$notificationId/archive/" -Method Post -Headers $headers
Write-Host ($archiveResponse | ConvertTo-Json -Depth 10)
Write-Host ""

Write-Host "=== API测试完成 ===" -ForegroundColor Green
Write-Host "主要通知ID: $notificationId"
