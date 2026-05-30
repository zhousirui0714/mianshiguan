@echo off
chcp 65001 >nul
cd /d "%~dp0"

:restart
echo [启动] 正在启动面试成长伴侣...
echo [启动] 时间：%date% %time%
python app.py
echo [启动] 服务已停止，5秒后自动重启...
timeout /t 5 /nobreak >nul
goto restart
