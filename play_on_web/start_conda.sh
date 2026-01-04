#!/bin/bash

# XLerobot Web Teleop 启动脚本 (Conda 版本)
# 使用已有的 lerobot conda 环境

echo "================================================"
echo "   XLerobot Web Teleop 启动脚本 (Conda)"
echo "================================================"
echo ""

# 检查 conda 是否可用
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到 conda"
    echo "请先安装 Anaconda 或 Miniconda"
    echo "或使用 ./start.sh 使用 venv 方式启动"
    exit 1
fi

# 检查 lerobot 环境是否存在
if ! conda env list | grep -q "^lerobot "; then
    echo "❌ 错误: 未找到 lerobot conda 环境"
    echo ""
    echo "请先创建并配置 lerobot 环境："
    echo "  conda create -n lerobot python=3.10"
    echo "  conda activate lerobot"
    echo "  cd /Users/ai/Project/lerobot"
    echo "  pip install -e .[all]"
    echo ""
    exit 1
fi

echo "✅ 找到 lerobot conda 环境"
echo ""

# 获取 conda 路径
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 激活 lerobot 环境
conda activate lerobot

# 检查 Python 版本
echo "✅ Python 版本: $(python --version)"
echo ""

# 检查 lerobot 是否已安装
if ! python -c "import lerobot" 2>/dev/null; then
    echo "⚠️  警告: lerobot 未安装或未正确安装"
    echo ""
    echo "正在安装 lerobot..."
    cd /Users/ai/Project/lerobot
    pip install -e .[all]
    cd /Users/ai/Project/play_lerobot/play_on_web
    echo ""
fi

# 安装后端依赖
echo "📦 检查后端依赖..."
cd backend

# 检查关键依赖
NEED_INSTALL=false
if ! python -c "import fastapi" 2>/dev/null; then
    NEED_INSTALL=true
fi

if [ "$NEED_INSTALL" = true ]; then
    echo "安装 Web 服务依赖..."
    pip install -r requirements.txt -q
    echo "✅ 后端依赖安装完成"
else
    echo "✅ 后端依赖已安装"
fi
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo "请先安装 Node.js 16 或更高版本"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo ""

# 安装前端依赖
echo "📦 检查前端依赖..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
    echo "✅ 前端依赖安装完成"
else
    echo "✅ 前端依赖已安装"
fi
echo ""

# 显示环境信息
echo "🔍 环境信息:"
echo "  Conda 环境: lerobot"
echo "  Python: $(which python)"
echo "  Node: $(which node)"
echo ""

# 启动服务
echo "🚀 启动服务..."
echo ""
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "使用 conda 环境: lerobot"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 在后台启动后端
cd ../backend
python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 在前台启动前端
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# 捕获退出信号
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID; conda deactivate; exit" INT TERM

# 等待进程
wait

