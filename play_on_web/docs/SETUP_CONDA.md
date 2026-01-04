# 🐍 使用 Conda 环境配置指南

本指南说明如何使用已有的 `lerobot` conda 环境运行 XLerobot Web Teleop。

## 🎯 推荐方式：复用 lerobot 环境

如果您已经配置了 `lerobot` conda 环境，这是最推荐的方式！

### 前置条件

确认您已经安装了 lerobot 环境：

```bash
# 检查 conda 环境
conda env list

# 应该能看到 lerobot 环境
```

### 步骤 1: 激活 lerobot 环境

```bash
conda activate lerobot
```

### 步骤 2: 确认 lerobot 已安装

```bash
cd /Users/ai/Project/lerobot
pip install -e .[all]
```

如果已经安装过，会提示已满足要求。

### 步骤 3: 安装 Web 服务额外依赖

```bash
cd /Users/ai/Project/play_lerobot/play_on_web/backend
pip install -r requirements.txt
```

`requirements.txt` 已经优化，只包含 Web 服务特有的依赖：
- FastAPI 和 Uvicorn（Web 框架）
- WebSocket 支持
- 配置管理工具
- 异步文件操作

### 步骤 4: 安装前端依赖

```bash
cd ../frontend
npm install
```

### 步骤 5: 启动服务

#### 使用更新后的启动脚本

```bash
cd /Users/ai/Project/play_lerobot/play_on_web
./start_conda.sh
```

#### 或手动启动

**终端 1 - 后端:**
```bash
conda activate lerobot
cd /Users/ai/Project/play_lerobot/play_on_web/backend
python main.py
```

**终端 2 - 前端:**
```bash
cd /Users/ai/Project/play_lerobot/play_on_web/frontend
npm run dev
```

## 📦 依赖说明

### lerobot 环境已提供

lerobot 安装时已包含这些依赖（不需要重复安装）：

- ✅ **opencv-python** - 图像处理
- ✅ **numpy** - 数值计算
- ✅ **pyserial** - 串口通信
- ✅ **torch** - 深度学习框架
- ✅ **gymnasium** - 强化学习环境
- ✅ 以及其他机器人控制相关依赖

### play_on_web 额外需要

只需要安装这些 Web 服务相关的依赖：

- 🌐 **FastAPI** - 现代 Web 框架
- 🚀 **Uvicorn** - ASGI 服务器
- 🔌 **WebSocket** - 实时通信
- ⚙️ **Pydantic Settings** - 配置管理
- 📁 **aiofiles** - 异步文件操作

## 🔍 验证安装

### 检查 Python 包

```bash
conda activate lerobot

# 检查 lerobot 相关
python -c "import lerobot; print('lerobot OK')"
python -c "import cv2; print('OpenCV OK')"
python -c "import numpy; print('NumPy OK')"

# 检查 Web 服务相关
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"
python -c "import websockets; print('WebSocket OK')"
```

全部输出 OK 表示安装成功！

### 检查 Node 包

```bash
cd frontend
npm list react
npm list vite
```

## 🎨 环境管理最佳实践

### 1. 保持环境纯净

```bash
# 只在 lerobot 环境中安装必要的包
conda activate lerobot
pip list  # 查看已安装的包
```

### 2. 更新依赖

```bash
# 更新 lerobot
cd /Users/ai/Project/lerobot
git pull
pip install -e .[all] --upgrade

# 更新 play_on_web 依赖
cd /Users/ai/Project/play_lerobot/play_on_web/backend
pip install -r requirements.txt --upgrade
```

### 3. 冻结依赖（可选）

如果要精确控制版本：

```bash
conda activate lerobot
pip freeze > requirements-frozen.txt
```

## 🆚 对比：Conda vs Venv

### 使用 Conda 环境（推荐）

**优点：**
- ✅ 复用 lerobot 的所有依赖
- ✅ 避免重复安装（节省空间和时间）
- ✅ 版本一致性好
- ✅ 管理更简单

**缺点：**
- ❌ 需要先安装 conda
- ❌ 环境较大

### 使用独立 Venv

**优点：**
- ✅ 环境隔离
- ✅ 不需要 conda

**缺点：**
- ❌ 需要重复安装所有依赖
- ❌ 可能出现版本冲突
- ❌ 占用更多空间

## 🐛 常见问题

### Q1: 找不到 lerobot 模块？

**A:** 确认已安装 lerobot：

```bash
conda activate lerobot
cd /Users/ai/Project/lerobot
pip install -e .[all]
```

### Q2: 导入错误？

**A:** 检查 Python 路径：

```bash
python -c "import sys; print('\n'.join(sys.path))"
```

应该能看到 lerobot 的路径。

### Q3: 版本冲突？

**A:** 如果出现版本冲突，可以指定兼容版本：

```bash
# 例如，如果 pydantic 冲突
pip install pydantic>=2.0.0
```

### Q4: FastAPI 启动报错？

**A:** 确认所有依赖都已安装：

```bash
pip install -r requirements.txt
```

### Q5: 想创建独立环境？

**A:** 如果不想使用 lerobot 环境，可以创建新的：

```bash
# 创建新环境
conda create -n xlerobot_web python=3.10

# 激活新环境
conda activate xlerobot_web

# 安装所有依赖
cd /Users/ai/Project/lerobot
pip install -e .[all]

cd /Users/ai/Project/play_lerobot/play_on_web/backend
pip install -r requirements.txt
```

## 📝 配置文件说明

### backend/.env（可选）

创建环境变量文件：

```bash
cp backend/.env.example backend/.env
```

默认配置已经很好，通常不需要修改。

### 验证配置

```bash
conda activate lerobot
cd backend
python -c "from config import settings; print(settings.backend_port)"
```

应该输出 `8000`。

## 🚀 快速启动命令

### 一键启动（使用 conda）

```bash
# 从项目根目录
cd /Users/ai/Project/play_lerobot/play_on_web
./start_conda.sh
```

### 分步启动

```bash
# 终端 1
conda activate lerobot
cd /Users/ai/Project/play_lerobot/play_on_web/backend
python main.py

# 终端 2
cd /Users/ai/Project/play_lerobot/play_on_web/frontend
npm run dev
```

## 📊 依赖树

```
lerobot (conda env)
├── lerobot 库 (pip install -e .[all])
│   ├── opencv-python
│   ├── numpy
│   ├── pyserial
│   ├── torch
│   └── ... (其他依赖)
│
└── play_on_web 额外依赖 (pip install -r requirements.txt)
    ├── fastapi
    ├── uvicorn
    ├── websockets
    ├── pydantic-settings
    └── aiofiles
```

## 💡 开发建议

1. **始终在 conda 环境中工作**
   ```bash
   conda activate lerobot
   ```

2. **使用相对路径导入 lerobot**
   ```python
   from lerobot.robots.xlerobot import XLerobot
   ```

3. **定期更新依赖**
   ```bash
   git pull  # 更新代码
   pip install -e .[all] --upgrade  # 更新 lerobot
   pip install -r requirements.txt --upgrade  # 更新 Web 依赖
   ```

4. **保持环境干净**
   ```bash
   # 只安装必要的包
   # 避免全局安装（不使用 pip install --user）
   ```

## ✅ 验证清单

完成配置后，检查这些项目：

- [ ] conda 环境 `lerobot` 已创建
- [ ] lerobot 库已安装 (`pip install -e .[all]`)
- [ ] play_on_web 依赖已安装 (`pip install -r requirements.txt`)
- [ ] 前端依赖已安装 (`npm install`)
- [ ] 可以导入 lerobot (`python -c "import lerobot"`)
- [ ] 可以导入 fastapi (`python -c "import fastapi"`)
- [ ] 后端可以启动 (`python main.py`)
- [ ] 前端可以启动 (`npm run dev`)
- [ ] 可以访问 `http://localhost:3000`
- [ ] 可以访问 `http://localhost:8000/docs`

全部打勾？**恭喜！您已经成功配置了 conda 环境！** 🎉

---

**享受使用 conda 环境的便利！** 🐍✨

