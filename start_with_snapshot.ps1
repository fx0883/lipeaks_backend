# 多租户后端系统 - 数据库快照导入模式启动脚本
# 使用方法: .\start_with_snapshot.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "多租户后端系统 - 数据库快照导入模式" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 状态
Write-Host "检查 Docker 状态..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✓ Docker 运行正常" -ForegroundColor Green
} catch {
    Write-Host "✗ 错误: Docker 未运行，请启动 Docker Desktop" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""

# 显示当前配置
Write-Host "当前配置:" -ForegroundColor Yellow
Write-Host "- IMPORT_DB_SNAPSHOT=true" -ForegroundColor White
Write-Host "- CREATE_SUPERUSER=true" -ForegroundColor White
Write-Host "- 超级用户: admin / admin_main" -ForegroundColor White
Write-Host ""

# 启动服务
Write-Host "启动服务..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 错误: 服务启动失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "✓ 服务启动成功！" -ForegroundColor Green
Write-Host ""

# 显示服务状态
Write-Host "服务状态:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "查看启动日志..." -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止日志查看" -ForegroundColor Gray

# 查看日志
docker-compose logs -f web

Write-Host ""
Write-Host "脚本执行完成" -ForegroundColor Green
