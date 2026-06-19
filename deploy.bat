@echo off
echo ========================================
echo  海岛养殖网箱病害巡检平台 - 一键部署脚本
echo ========================================
echo.

echo [1/5] 检查 Docker 和 Docker Compose...
docker --version
docker compose version
if %errorlevel% neq 0 (
    echo 错误: 请先安装 Docker 和 Docker Compose
    pause
    exit /b 1
)
echo ✓ Docker 环境检查通过
echo.

echo [2/5] 停止并清理旧容器...
docker compose down
echo ✓ 旧容器已清理
echo.

echo [3/5] 创建必要的目录...
if not exist "media" mkdir media
if not exist "media/uploads" mkdir media\uploads
if not exist "media/disease" mkdir media\disease
if not exist "media/mortality" mkdir media\mortality
echo ✓ 目录创建完成
echo.

echo [4/5] 构建并启动所有服务...
docker compose build
docker compose up -d
echo ✓ 服务启动完成
echo.

echo [5/5] 等待服务就绪...
timeout /t 30 /nobreak >nul
echo.

echo ========================================
echo  部署完成！
echo ========================================
echo.
echo 服务访问地址:
echo   - 前端: http://localhost:5173
echo   - 后端 API: http://localhost:8000/api
echo   - API 文档: http://localhost:8000/swagger/
echo   - Django Admin: http://localhost:8000/admin/
echo   - RabbitMQ 管理: http://localhost:15672 (admin/admin123)
echo.
echo 常用命令:
echo   查看日志: docker compose logs -f
echo   重启服务: docker compose restart
echo   停止服务: docker compose down
echo.
echo 初始管理员账号: admin / admin123456
echo.
pause
