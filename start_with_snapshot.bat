@echo off
echo ========================================
echo 多租户后端系统 - 数据库快照导入模式
echo ========================================
echo.

echo 检查 Docker 状态...
docker info >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未运行，请启动 Docker Desktop
    pause
    exit /b 1
)

echo Docker 运行正常
echo.

echo 当前配置:
echo - IMPORT_DB_SNAPSHOT=true
echo - CREATE_SUPERUSER=true
echo - 超级用户: admin / admin_main
echo.

echo 启动服务...
docker-compose up -d

if errorlevel 1 (
    echo 错误: 服务启动失败
    pause
    exit /b 1
)

echo.
echo 服务启动成功！
echo.

echo 查看启动日志...
docker-compose logs -f web

echo.
echo 按任意键退出...
pause >nul
