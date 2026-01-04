# 🐍 Conda 环境配置总结

## 为什么使用 Conda 环境？

您已经配置了 `lerobot` conda 环境，其中包含：
- ✅ lerobot 核心库（通过 `pip install -e .[all]` 安装）
- ✅ opencv-python（图像处理）
- ✅ numpy（数值计算）
- ✅ pyserial（串口通信）
- ✅ torch 等深度学习依赖
- ✅ 所有机器人控制相关依赖

**复用这个环境的好处：**
1. 🎯 **避免重复安装** - 节省磁盘空间和时间
2. 🔒 **版本一致性** - 确保 lerobot 和 Web 服务使用相同的依赖版本
3. 🛠️ **简化管理** - 只需维护一个环境
4. ⚡ **启动更快** - 不需要创建新的虚拟环境

## 修改内容

### 1. 简化后端依赖 (`backend/requirements.txt`)

**修改前**（独立环境）:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0
opencv-python==4.9.0.80      # lerobot 已提供
numpy==1.26.3                # lerobot 已提供
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
```

**修改后**（复用 lerobot 环境）:
```txt
# lerobot 已提供: opencv-python, numpy, pyserial 等
# 只安装 Web 服务额外需要的依赖

fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
```

### 2. 新增 Conda 启动脚本 (`start_conda.sh`)

自动检测和使用 `lerobot` conda 环境：
```bash
./start_conda.sh
```

功能：
- ✅ 检查 conda 是否安装
- ✅ 检查 lerobot 环境是否存在
- ✅ 激活 lerobot 环境
- ✅ 安装 Web 服务依赖
- ✅ 启动后端和前端

### 3. 新增环境检查脚本 (`backend/check_env.py`)

验证所有依赖是否正确安装：
```bash
conda activate lerobot
cd backend
python check_env.py
```

检查内容：
- ✅ lerobot 核心依赖
- ✅ Web 服务依赖
- ✅ 图像处理依赖
- ✅ 通信依赖

### 4. 新增详细配置文档 (`SETUP_CONDA.md`)

包含：
- 📖 为什么使用 conda 环境
- 🚀 如何配置和使用
- 🔍 依赖树和版本说明
- 🐛 常见问题解答
- ✅ 验证清单

### 5. 更新主文档

所有文档都已更新，推荐使用 conda 环境：
- `README.md` - 添加 conda 使用说明
- `QUICKSTART.md` - 优先推荐 conda 方式
- `.env.example` - 移除不需要的 LEROBOT_ROOT 配置

## 快速开始

### 方案 A: 全自动（推荐）

```bash
# 1. 进入项目目录
cd /Users/ai/Project/play_lerobot/play_on_web

# 2. 验证环境（可选）
./verify_setup.sh

# 3. 一键启动
./start_conda.sh
```

### 方案 B: 手动启动

```bash
# 1. 激活 conda 环境
conda activate lerobot

# 2. 确保 lerobot 已安装
cd /Users/ai/Project/lerobot
pip install -e .[all]

# 3. 安装 Web 依赖
cd /Users/ai/Project/play_lerobot/play_on_web/backend
pip install -r requirements.txt

# 4. 启动后端（新终端）
conda activate lerobot
cd /Users/ai/Project/play_lerobot/play_on_web/backend
python main.py

# 5. 启动前端（新终端）
cd /Users/ai/Project/play_lerobot/play_on_web/frontend
npm install
npm run dev
```

## 依赖对比

### lerobot 环境提供（不需要重复安装）

```
✅ opencv-python  - 图像处理
✅ numpy          - 数值计算
✅ pyserial       - 串口通信
✅ torch          - 深度学习
✅ gymnasium      - 强化学习
✅ 以及所有 lerobot 依赖
```

### play_on_web 额外需要（需要安装）

```
🌐 fastapi        - Web 框架
🚀 uvicorn        - ASGI 服务器
🔌 websockets     - 实时通信
⚙️ pydantic       - 配置管理
📁 aiofiles       - 异步文件操作
```

## 验证安装

```bash
conda activate lerobot
cd backend
python check_env.py
```

如果全部通过，您会看到：
```
✅ 环境检查通过！所有依赖已正确安装。
```

## 文件结构

```
play_on_web/
├── start_conda.sh           # Conda 环境启动脚本 ⭐ 新增
├── start.sh                 # 独立环境启动脚本
├── verify_setup.sh          # 环境验证脚本 ⭐ 新增
├── SETUP_CONDA.md          # Conda 配置详细文档 ⭐ 新增
├── CONDA_SETUP_SUMMARY.md  # 本文件 ⭐ 新增
├── backend/
│   ├── requirements.txt    # 简化后的依赖列表 ⭐ 更新
│   ├── config.py          # 移除 lerobot_root 配置 ⭐ 更新
│   └── check_env.py       # 环境检查脚本 ⭐ 新增
└── ... (其他文件)
```

## 常见问题

### Q: 我还能用原来的 venv 方式吗？

**A:** 可以！`start.sh` 仍然保留，使用独立的虚拟环境。但推荐使用 conda 方式。

### Q: 如果 lerobot 更新了怎么办？

**A:** 在 lerobot 目录执行：
```bash
conda activate lerobot
cd /Users/ai/Project/lerobot
git pull
pip install -e .[all] --upgrade
```

### Q: 会有版本冲突吗？

**A:** 很少。我们选择的依赖版本都与 lerobot 兼容。如有冲突，可以调整 requirements.txt 中的版本号。

### Q: 如何卸载？

**A:** 如果不想用了：
```bash
# 只删除 Web 依赖
pip uninstall fastapi uvicorn websockets pydantic-settings aiofiles

# 或删除整个环境
conda env remove -n lerobot
```

## 优势总结

| 特性 | Conda 环境 | 独立 Venv |
|-----|-----------|-----------|
| 安装速度 | ⚡⚡⚡ 快 | ⚡⚡ 中等 |
| 磁盘占用 | 💾 小（共享） | 💾💾 大（重复） |
| 版本一致性 | ✅ 好 | ⚠️ 可能冲突 |
| 维护成本 | 🛠️ 低 | 🛠️🛠️ 高 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 下一步

1. ✅ **验证环境**: `./verify_setup.sh`
2. ✅ **启动服务**: `./start_conda.sh`
3. ✅ **打开浏览器**: `http://localhost:3000`
4. ✅ **开始遥操作**: 配置设备并控制机器人！

## 需要帮助？

- 📖 详细文档: `SETUP_CONDA.md`
- 🚀 快速上手: `QUICKSTART.md`
- 📁 项目结构: `STRUCTURE.md`
- ✅ 功能检查: `CHECKLIST.md`

---

**现在您可以享受使用 conda 环境的便利了！** 🐍✨

复用环境，事半功倍！

