#!/bin/bash
# 启动后端服务器

echo "=== LeRobot 调试服务器 ==="
echo ""

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "✗ 虚拟环境不存在，请先运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 启动服务器
echo "✓ 启动服务器..."
echo ""
python -m app.main
