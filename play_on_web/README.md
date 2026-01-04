# XLerobot Web Teleop 🤖

基于 Web 的 XLerobot 机械臂小车遥操作系统。支持设备扫描、多机位视频流、键盘和 Xbox 手柄控制。

> 💡 **推荐**: 使用已有的 `lerobot` conda 环境，避免重复安装依赖！查看 [SETUP_CONDA.md](SETUP_CONDA.md)

## ✨ 功能特性

### 🔍 设备管理
- **串口扫描**: 自动扫描和识别可用串口
- **相机检测**: 支持 OpenCV 和 RealSense 相机
- **智能识别**: 通过拔插 USB 自动识别设备端口

### 🎮 多种控制方式
- **键盘控制**: 完整的键盘映射，支持双臂独立控制
- **Xbox 手柄**: 摇杆控制机械臂，D-Pad 控制底盘
- **实时反馈**: WebSocket 低延迟双向通信

### 📹 多机位视频
- **多路同显**: 支持同时显示多个相机画面
- **网格/单屏**: 灵活切换显示模式
- **实时流传输**: 基于 WebSocket 的视频流

### 🤖 机器人控制
- **双臂控制**: 独立控制左右机械臂
- **运动学求解**: 支持 XY 平面逆运动学控制
- **底盘移动**: 前后左右旋转全方位控制
- **一键归零**: 快速回到安全初始位置

## 🏗️ 架构设计

```
play_on_web/
├── backend/                # Python 后端
│   ├── main.py            # FastAPI 主应用
│   ├── config.py          # 配置管理
│   ├── device_scanner.py  # 设备扫描
│   ├── robot_controller.py # 机器人控制
│   ├── camera_manager.py  # 相机管理
│   └── requirements.txt   # Python 依赖
│
└── frontend/              # React 前端
    ├── src/
    │   ├── components/    # React 组件
    │   │   ├── DeviceSetup.tsx      # 设备配置
    │   │   ├── TeleopControl.tsx    # 遥操作主界面
    │   │   ├── KeyboardControl.tsx  # 键盘控制
    │   │   ├── XboxControl.tsx      # Xbox 控制
    │   │   ├── CameraView.tsx       # 相机视图
    │   │   └── RobotStatus.tsx      # 状态显示
    │   ├── stores/        # 状态管理
    │   ├── api/          # API 客户端
    │   └── App.tsx       # 主应用
    └── package.json      # Node 依赖
```

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Node.js 16+
- XLerobot 机械臂小车硬件
- （可选）Xbox 手柄
- **推荐**: 已配置的 `lerobot` conda 环境

### 方式 1: 使用 Conda 环境（推荐）⭐

如果您已经配置了 `lerobot` conda 环境，这是最推荐的方式！

#### 一键启动
```bash
cd play_on_web
./start_conda.sh
```

#### 手动启动
```bash
# 1. 激活 conda 环境
conda activate lerobot

# 2. 确保 lerobot 已安装
cd /Users/ai/Project/lerobot
pip install -e .[all]

# 3. 安装 Web 服务依赖
cd /Users/ai/Project/play_lerobot/play_on_web/backend
pip install -r requirements.txt

# 4. 安装前端依赖
cd ../frontend
npm install

# 5. 启动后端（新终端）
conda activate lerobot
cd backend
python main.py

# 6. 启动前端（新终端）
cd frontend
npm run dev
```

**优点**:
- ✅ 复用 lerobot 的所有依赖（opencv、numpy 等）
- ✅ 避免重复安装，节省空间和时间
- ✅ 版本一致性好，减少冲突

详细说明请查看 [SETUP_CONDA.md](SETUP_CONDA.md)

### 方式 2: 使用独立虚拟环境

#### 一键启动
```bash
cd play_on_web
./start.sh
```

#### 手动启动
```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 前端
cd frontend
npm install
npm run dev
```

### 访问服务

- **前端**: `http://localhost:3000`
- **后端**: `http://localhost:8000`
- **API 文档**: `http://localhost:8000/docs`

### 使用步骤

1. **打开浏览器**: 访问 `http://localhost:3000`

2. **配置串口**:
   - 选择两个串口分别连接 SO101 和头部相机
   - 可以手动选择或使用自动检测功能
   - 点击"连接机器人"

3. **配置相机**:
   - 为左手腕、右手腕、头部选择相机
   - 系统会自动检测可用的相机设备
   - 点击"继续"

4. **校准**:
   - 将机器人移动到安全的初始零位
   - 点击"开始遥操作"

5. **遥操作**:
   - 选择控制模式（键盘/Xbox）
   - 使用对应的控制方式操作机器人
   - 实时查看多机位视频和状态反馈

## ⌨️ 键盘控制映射

### 左臂控制
| 按键 | 功能 |
|------|------|
| Q/E | 肩部旋转 +/- |
| R/F | 腕部旋转 +/- |
| T/G | 夹爪开合 +/- |
| W/S | X 轴 +/- |
| A/D | Y 轴 +/- |
| Z/X | 俯仰 +/- |
| C | 归零 |

### 右臂控制
| 按键 | 功能 |
|------|------|
| 7/9 | 肩部旋转 +/- |
| / / * | 腕部旋转 +/- |
| +/- | 夹爪开合 +/- |
| 8/2 | X 轴 +/- |
| 4/6 | Y 轴 +/- |
| 1/3 | 俯仰 +/- |
| 0 | 归零 |

### 底盘控制
| 按键 | 功能 |
|------|------|
| I/K | 前进/后退 |
| J/L | 左移/右移 |
| U/O | 左转/右转 |

## 🎮 Xbox 手柄映射

- **左摇杆**: 左臂 XY 控制
- **右摇杆**: 右臂 XY 控制
- **左扳机**: 左夹爪
- **右扳机**: 右夹爪
- **LB + 摇杆**: 左臂俯仰/旋转
- **RB + 摇杆**: 右臂俯仰/旋转
- **D-Pad**: 底盘移动
- **Back 键**: 全部归零

## 🛠️ 技术栈

### 后端
- **FastAPI**: 现代高性能 Web 框架
- **WebSocket**: 实时双向通信
- **OpenCV**: 图像处理
- **Lerobot**: 机器人控制库

### 前端
- **React 18**: UI 框架
- **TypeScript**: 类型安全
- **Vite**: 快速构建工具
- **Zustand**: 轻量级状态管理

## 📚 文档导航

### 快速链接
- **[快速开始](QUICKSTART.md)** - 5分钟快速上手指南
- **[项目状态](STATUS.md)** - 当前功能和最新进度
- **[CURSOR 指南](CURSOR.md)** - AI 助手和开发者技术要点

### 详细文档
- **[📖 文档索引](docs/README.md)** - 完整文档目录和导航
  - [🎮 用户指南](docs/guides/) - 操作指南和最佳实践
  - [🔧 技术修复](docs/fixes/) - 问题解决方案和技术细节
  - [🛠️ 开发文档](docs/) - 环境配置、项目结构、检查清单

## 📡 API 文档

启动后端后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 主要端点

#### 设备扫描
- `GET /api/devices/ports` - 获取所有串口
- `GET /api/devices/cameras` - 获取所有相机

#### 机器人控制
- `POST /api/robot/connect` - 连接机器人
- `POST /api/robot/zero` - 移动到零位
- `GET /api/robot/observation` - 获取状态

#### WebSocket
- `WS /ws/teleop` - 遥操作 WebSocket
- `WS /ws/camera` - 相机流 WebSocket

## 🎨 界面预览

### 设备配置界面
- 三步引导式配置流程
- 串口自动检测
- 相机位置分配
- 初始化校准

### 遥操作界面
- 顶部控制栏：模式切换、归零按钮
- 左侧：多机位视频网格
- 中间：键盘/手柄控制面板
- 右侧：实时状态监控

## 🔧 配置

### 后端配置 (backend/.env)
```env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000
ROBOT_ID=my_xlerobot
ROBOT_FPS=30
```

### 前端配置 (frontend/vite.config.ts)
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': 'ws://localhost:8000',
  },
}
```

## 🐛 故障排除

### 机器人无法连接
1. 检查串口是否正确
2. 确认机器人已通电
3. 检查 USB 连接
4. 查看后端日志

### 相机无法显示
1. 确认相机已连接
2. 检查相机权限
3. 查看浏览器控制台
4. 重启相机服务

### 键盘控制无响应
1. 确认焦点在浏览器窗口
2. 检查 WebSocket 连接
3. 查看网络标签
4. 刷新页面重试

### Xbox 手柄未识别
1. 确认手柄已连接
2. 按任意键激活手柄
3. 检查浏览器兼容性
4. 使用 Chrome/Edge 浏览器

## 🤝 参考项目

本项目基于 [lerobot](https://github.com/huggingface/lerobot) 开发，特别参考了以下示例：
- `examples/xlerobot/4_xlerobot_teleop_keyboard.py`
- `examples/xlerobot/5_xlerobot_teleop_xbox.py`
- `src/lerobot/scripts/lerobot_find_port.py`
- `src/lerobot/scripts/lerobot_find_cameras.py`

## 📄 许可证

本项目遵循 lerobot 的 Apache 2.0 许可证。

## 👨‍💻 开发者

开发过程中遵循了以下设计原则：
- ✅ **模块化设计**: 清晰的前后端分离
- ✅ **类型安全**: TypeScript 全面覆盖
- ✅ **实时通信**: WebSocket 低延迟
- ✅ **用户体验**: 精美的 UI 和流畅的交互
- ✅ **代码质量**: 注释完整，易于维护

## 🎯 未来计划

- [ ] 添加数据集录制功能
- [ ] 支持多个机器人同时控制
- [ ] 添加轨迹回放功能
- [ ] 支持移动端触控操作
- [ ] 添加语音控制
- [ ] 集成 AI 辅助控制

---

**享受您的 XLerobot Web 遥操作体验！** 🚀🤖

