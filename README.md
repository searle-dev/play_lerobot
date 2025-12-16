# Play LeRobot - 机械臂玩法集合

这是一个用于探索和开发各种 LeRobot 机械臂玩法的项目集合。

## 📁 项目结构

```
play_lerobot/
├── robot_web_ui/           # Web 调试平台
│   ├── backend/           # FastAPI 后端
│   ├── frontend/          # React 前端
│   └── README.md          # 详细文档
│
└── [未来的其他项目]/
    ├── robot_voice_control/   # 语音控制 (示例)
    ├── robot_vision/          # 视觉识别 (示例)
    └── robot_teaching/        # 示教编程 (示例)
```

## 🎮 当前项目

### 1. Robot Web UI - Web 调试平台

功能完整的 Web 界面，用于管理和调试 LeRobot 机械臂。

**主要功能**：
- 📡 端口扫描和设备识别
- 🤖 多机械臂管理
- ⚙️ 交互式校准
- 🎮 实时控制
- 📹 动作录制和回放
- 💾 本地配置缓存

**快速启动**：
```bash
cd robot_web_ui
# 查看详细文档
cat README.md
```

**技术栈**：FastAPI + React + WebSocket + SQLite

---

## 🚀 开始使用

### 1. 选择一个项目

```bash
cd robot_web_ui   # 进入 Web 调试平台
```

### 2. 按照项目内的 README 启动

每个项目都有自己的 README 和启动指南。

---

## 💡 未来项目想法

以下是一些可能的扩展方向：

### 🎙️ 语音控制 (`robot_voice_control`)
- 使用语音指令控制机械臂
- 集成语音识别和自然语言处理
- 预设动作库

### 👁️ 视觉识别 (`robot_vision`)
- 目标检测和识别
- 视觉伺服控制
- 物体抓取定位

### 🎓 示教编程 (`robot_teaching`)
- 拖动示教
- 轨迹录制和优化
- 任务自动化

### 🎮 游戏控制 (`robot_game_control`)
- 使用游戏手柄控制
- VR/AR 集成
- 手势识别

### 🤖 AI 集成 (`robot_ai`)
- 强化学习训练
- 模仿学习
- 智能规划

### 📱 移动端控制 (`robot_mobile`)
- iOS/Android App
- 远程控制
- 实时视频流

---

## 📦 环境要求

### 基础环境
- Python 3.8+
- LeRobot 库（已安装在 `/Users/ai/Project/lerobot`）
- 机械臂硬件和驱动

### 项目特定依赖
每个项目有自己的依赖，详见各项目的 `requirements.txt` 或 `package.json`

---

## 🛠️ 创建新项目

### 1. 创建项目文件夹

```bash
mkdir my_new_robot_project
cd my_new_robot_project
```

### 2. 初始化项目结构

```bash
# Python 项目
python3 -m venv venv
source venv/bin/activate
touch requirements.txt
touch main.py
touch README.md

# 或者 Node.js 项目
npm init -y
touch index.js
touch README.md
```

### 3. 安装 LeRobot

```bash
pip install -e /Users/ai/Project/lerobot
```

### 4. 开始开发

参考 `robot_web_ui` 的实现，特别是如何：
- 连接机械臂
- 读取状态
- 发送控制指令
- 处理校准

---

## 📚 资源链接

- **LeRobot 官方文档**: https://github.com/huggingface/lerobot
- **SO101 机械臂文档**: `/Users/ai/Project/lerobot/docs/source/so101.mdx`
- **示例代码**: `/Users/ai/Project/lerobot/examples/`

---

## 🤝 贡献

欢迎添加新的玩法和项目！每个项目应该：
1. 有独立的文件夹
2. 包含详细的 README
3. 提供快速启动脚本
4. 记录依赖和环境要求

---

## 📝 项目规范

### 命名规范
- 使用小写字母和下划线
- 名称应该清晰描述项目功能
- 例如：`robot_voice_control`, `robot_vision`

### 文档规范
每个项目应包含：
- `README.md` - 项目说明和使用指南
- `requirements.txt` / `package.json` - 依赖列表
- `.gitignore` - 忽略文件配置

### 代码规范
- Python: 遵循 PEP 8
- TypeScript/JavaScript: 使用 ESLint
- 添加必要的注释和类型标注

---

## 📞 联系和支持

如有问题或想法，可以：
1. 查看各项目的 README
2. 参考 LeRobot 官方文档
3. 创建 Issue 讨论

---

**祝你玩得开心！** 🎉
