@echo off
chcp 65001 >nul
echo ====================================
echo IReckon 3.0 Lite 启动脚本
echo ====================================
echo.

set VENV=D:\IReckon_venv
set PROJECT=%~dp0

if "%PROJECT:~-1%"=="\" set PROJECT=%PROJECT:~0,-1%

REM 检查虚拟环境是否存在
if not exist "%VENV%\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在: %VENV%
    echo 请先运行: python -m venv D:\IReckon_venv
    pause
    exit /b 1
)

REM 启动 API 服务 (Lite 模式仅启动 mock_llm)
echo [1/3] 正在启动 Mock LLM 服务...
start "IReckon Mock LLM" cmd /k "cd /d %PROJECT% && %VENV%\Scripts\activate.bat && python mock_llm.py"

REM 等待服务启动
echo [2/3] 等待服务启动...
timeout /t 3 /nobreak > nul

REM 启动 Streamlit UI (使用 run_streamlit.py 确保编码正确)
echo [3/3] 正在启动 Web 界面...
start "IReckon UI" cmd /k "cd /d %PROJECT% && %VENV%\Scripts\activate.bat && python run_streamlit.py"

REM 等待 UI 启动
timeout /t 3 /nobreak > nul

REM 打开浏览器
echo.
echo ====================================
echo 服务已启动！
echo ====================================
echo Mock LLM:  http://localhost:8001
echo Web 界面:  http://localhost:8501
echo ====================================
echo.
start http://localhost:8501

echo 按任意键停止所有服务...
pause > nul

REM 停止服务
echo 正在停止服务...
taskkill /FI "WINDOWTITLE eq IReckon Mock LLM*" /T /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq IReckon UI*" /T /F > nul 2>&1
echo 服务已停止。
pause
