@echo off
chcp 65001 >nul
echo ==========================================
echo       政企标书助手 - 一键启动脚本
echo ==========================================

echo [1/2] 正在启动 Python FastAPI 后端服务 (端口 8000)...
cd backend
start cmd /k ".\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] 正在启动 Next.js 前端交互界面 (端口 3000)...
cd ../frontend
start cmd /k "npm run dev"

echo.
echo 系统服务启动指令已发送！
echo 正在打开浏览器...
timeout /t 3
start http://localhost:3000
echo ==========================================
