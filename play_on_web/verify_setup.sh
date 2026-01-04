#!/bin/bash

# 环境验证脚本 - 快速检查配置是否正确

echo "================================================"
echo "   XLerobot Web Teleop - 环境验证"
echo "================================================"
echo ""

# 检查 conda
echo "🔍 检查 Conda..."
if ! command -v conda &> /dev/null; then
    echo "⚠️  Conda 未安装（可选）"
    USE_CONDA=false
else
    echo "✅ Conda 已安装: $(conda --version)"
    USE_CONDA=true
    
    # 检查 lerobot 环境
    if conda env list | grep -q "^lerobot "; then
        echo "✅ lerobot conda 环境已创建"
        HAS_LEROBOT_ENV=true
    else
        echo "⚠️  lerobot conda 环境未创建"
        HAS_LEROBOT_ENV=false
    fi
fi
echo ""

# 检查 Python
echo "🔍 检查 Python..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python 未安装"
    exit 1
else
    PYTHON_CMD=$(command -v python3 || command -v python)
    echo "✅ Python 已安装: $($PYTHON_CMD --version)"
fi
echo ""

# 检查 Node.js
echo "🔍 检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
else
    echo "✅ Node.js 已安装: $(node --version)"
    echo "✅ npm 已安装: $(npm --version)"
fi
echo ""

# 如果有 conda 环境，激活并检查
if [ "$USE_CONDA" = true ] && [ "$HAS_LEROBOT_ENV" = true ]; then
    echo "🔍 检查 Python 包（conda 环境）..."
    CONDA_BASE=$(conda info --base)
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    conda activate lerobot
    
    cd backend
    python check_env.py
    CHECK_EXIT_CODE=$?
    cd ..
    
    if [ $CHECK_EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✅ 所有依赖检查通过！"
        echo ""
        echo "🚀 您可以使用以下命令启动服务:"
        echo "   ./start_conda.sh"
    else
        echo ""
        echo "❌ 依赖检查失败，请按照提示安装缺失的依赖"
        exit 1
    fi
else
    echo "⚠️  未使用 conda 环境"
    echo ""
    echo "建议使用 conda 环境以获得最佳体验："
    echo "  1. 安装 Anaconda/Miniconda"
    echo "  2. 创建 lerobot 环境"
    echo "  3. 运行 ./start_conda.sh"
    echo ""
    echo "或使用独立虚拟环境："
    echo "  ./start.sh"
fi
echo ""

echo "================================================"
echo "   验证完成"
echo "================================================"

