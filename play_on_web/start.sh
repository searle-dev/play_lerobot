#!/bin/bash

# XLerobot Web Teleop 启动脚本

echo "================================================"
echo "   XLerobot Web Teleop 启动脚本"
echo "================================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo "请先安装 Node.js 16 或更高版本"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"
echo "✅ Node.js 版本: $(node --version)"
echo ""

# 安装后端依赖
echo "📦 安装后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
echo "✅ 后端依赖安装完成"
echo ""

# 安装前端依赖
echo "📦 安装前端依赖..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "✅ 前端依赖已安装"
fi
echo ""

# 启动服务
echo "🚀 启动服务..."
echo ""
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 在后台启动后端
cd ../backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 在前台启动前端
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# 捕获退出信号
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM

# 等待进程
wait

