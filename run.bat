@echo off
chcp 65001 >nul
echo ====================================
echo IReckon 3.0 启动脚本
echo ====================================
echo.

set VENV=D:\IReckon_venv
set PROJECT=C:\Users\IReckon-0.1.0\IReckon-0.1.0

REM 检查虚拟环境是否存在
if not exist "%VENV%\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在: %VENV%
    echo 请先运行: python -m venv D:\IReckon_venv
    pause
    exit /b 1
)

REM 启动 API 服务
echo [1/3] 正在启动 API 服务...
start "IReckon API" cmd /k "cd /d %PROJECT% && %VENV%\Scripts\activate.bat && python main.py"

REM 等待 API 启动
echo [2/3] 等待 API 启动...
timeout /t 5 /nobreak > nul

REM 启动 Streamlit UI
echo [3/3] 正在启动 Web 界面...
start "IReckon UI" cmd /k "cd /d %PROJECT% && %VENV%\Scripts\activate.bat && streamlit run ui/app.py --server.port 8501 --server.headless true"

REM 等待 UI 启动
timeout /t 3 /nobreak > nul

REM 打开浏览器
echo.
echo ====================================
echo 服务已启动！
echo ====================================
echo API 文档: http://localhost:8000/docs
echo Web 界面: http://localhost:8501
echo ====================================
echo.
start http://localhost:8000/docs
start http://localhost:8501

echo 按任意键停止所有服务...
pause > nul

REM 停止服务
echo 正在停止服务...
taskkill /FI "WINDOWTITLE eq IReckon API*" /T /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq IReckon UI*" /T /F > nul 2>&1
echo 服务已停止。
pause
