# 📁 项目结构

完整的 XLerobot Web Teleop 项目文件结构。

## 整体结构

```
play_on_web/
├── backend/                    # Python 后端服务
│   ├── main.py                # FastAPI 主应用
│   ├── config.py              # 配置管理
│   ├── device_scanner.py      # 设备扫描模块
│   ├── robot_controller.py    # 机器人控制模块
│   ├── camera_manager.py      # 相机管理模块
│   ├── requirements.txt       # Python 依赖
│   ├── .env.example          # 环境变量示例
│   └── README.md             # 后端文档
│
├── frontend/                  # React 前端应用
│   ├── public/               # 静态资源
│   ├── src/                  # 源代码
│   │   ├── components/       # React 组件
│   │   │   ├── DeviceSetup.tsx      # 设备配置向导
│   │   │   ├── DeviceSetup.css      # 设备配置样式
│   │   │   ├── TeleopControl.tsx    # 遥操作主界面
│   │   │   ├── TeleopControl.css    # 遥操作样式
│   │   │   ├── KeyboardControl.tsx  # 键盘控制面板
│   │   │   ├── KeyboardControl.css  # 键盘控制样式
│   │   │   ├── XboxControl.tsx      # Xbox 手柄控制
│   │   │   ├── XboxControl.css      # Xbox 控制样式
│   │   │   ├── CameraView.tsx       # 相机视图组件
│   │   │   ├── CameraView.css       # 相机视图样式
│   │   │   ├── RobotStatus.tsx      # 机器人状态显示
│   │   │   └── RobotStatus.css      # 状态显示样式
│   │   ├── stores/           # Zustand 状态管理
│   │   │   └── robotStore.ts        # 机器人状态 store
│   │   ├── api/             # API 客户端
│   │   │   └── client.ts            # HTTP 和 WebSocket 客户端
│   │   ├── App.tsx          # 主应用组件
│   │   ├── App.css          # 主应用样式
│   │   ├── main.tsx         # 应用入口
│   │   └── index.css        # 全局样式
│   ├── index.html           # HTML 模板
│   ├── package.json         # Node.js 依赖
│   ├── tsconfig.json        # TypeScript 配置
│   ├── tsconfig.node.json   # Node TypeScript 配置
│   ├── vite.config.ts       # Vite 配置
│   └── README.md           # 前端文档
│
├── README.md               # 项目主文档
├── QUICKSTART.md          # 快速开始指南
├── CHECKLIST.md           # 功能检查清单
├── STRUCTURE.md           # 项目结构说明（本文件）
├── .gitignore            # Git 忽略文件
└── start.sh              # 一键启动脚本
```

## 文件说明

### 后端文件

#### `main.py`
FastAPI 主应用，包含：
- HTTP 端点定义
- WebSocket 端点
- CORS 配置
- 全局状态管理
- 启动/关闭事件处理

**关键端点**:
- `/api/devices/*` - 设备扫描
- `/api/robot/*` - 机器人控制
- `/api/cameras/*` - 相机管理
- `/ws/teleop` - 遥操作 WebSocket
- `/ws/camera` - 相机流 WebSocket

#### `config.py`
配置管理模块，使用 Pydantic Settings：
- 服务器配置（主机、端口）
- CORS 配置
- 机器人配置
- 路径配置

#### `device_scanner.py`
设备扫描模块，功能：
- 扫描可用串口
- 通过拔插识别端口
- 扫描 OpenCV 相机
- 扫描 RealSense 相机

#### `robot_controller.py`
机器人控制核心模块，包含：
- `ArmState` - 机械臂状态数据类
- `HeadState` - 头部状态数据类
- `RobotController` - 机器人控制器类
- 连接/断开机器人
- 处理键盘/手柄动作
- 运动学计算
- P 控制器

#### `camera_manager.py`
相机管理模块，功能：
- 添加/移除相机
- 获取单帧图像
- WebSocket 流式传输
- 支持多路同时流传输

### 前端文件

#### 组件层次结构

```
App
├── DeviceSetup (设备配置向导)
│   ├── 步骤 1: 串口配置
│   ├── 步骤 2: 相机配置
│   └── 步骤 3: 校准
│
└── TeleopControl (遥操作主界面)
    ├── 控制头部
    │   ├── 模式切换
    │   ├── 归零按钮
    │   └── 返回按钮
    ├── 相机视图
    │   └── CameraView
    │       ├── 相机标签
    │       └── 视频画面
    ├── 控制面板
    │   ├── KeyboardControl (键盘模式)
    │   │   ├── 左臂键位
    │   │   ├── 右臂键位
    │   │   └── 底盘键位
    │   └── XboxControl (手柄模式)
    │       ├── 连接状态
    │       ├── 摇杆可视化
    │       └── 控制映射
    └── 状态侧边栏
        └── RobotStatus
            ├── 左臂状态
            ├── 右臂状态
            └── 头部状态
```

#### 状态管理（Zustand）

```typescript
robotStore
├── isConnected: boolean              // 连接状态
├── availablePorts: string[]          // 可用串口列表
├── availableCameras: Camera[]        // 可用相机列表
├── robotConfig: RobotConfig          // 机器人配置
├── observation: RobotObservation     // 实时观测值
├── teleopWs: WebSocket               // 遥操作 WebSocket
├── cameraWs: WebSocket               // 相机 WebSocket
└── controlMode: 'keyboard' | 'xbox'  // 控制模式
```

#### API 客户端结构

```typescript
client.ts
├── apiClient (Axios 实例)
│   ├── deviceApi                    // 设备扫描 API
│   ├── robotApi                     // 机器人控制 API
│   └── cameraApi                    // 相机管理 API
├── createTeleopWebSocket()          // 创建遥操作 WebSocket
└── createCameraWebSocket()          // 创建相机流 WebSocket
```

## 数据流

### HTTP 请求流
```
Frontend Component
    ↓ (调用 API)
API Client (Axios)
    ↓ (HTTP Request)
FastAPI Backend
    ↓ (调用模块)
Device Scanner / Robot Controller / Camera Manager
    ↓ (访问硬件)
Lerobot Library → Hardware
```

### WebSocket 数据流

#### 遥操作控制流
```
用户输入 (键盘/手柄)
    ↓
KeyboardControl / XboxControl
    ↓ (WebSocket 发送)
Backend WebSocket Handler
    ↓
Robot Controller
    ↓
Lerobot → Robot Hardware
    ↓ (获取观测值)
Backend WebSocket Handler
    ↓ (WebSocket 接收)
RobotStatus / App State
```

#### 相机流传输流
```
Camera Hardware
    ↓
Camera Manager
    ↓ (读取帧)
JPEG 编码
    ↓
Base64 编码
    ↓ (WebSocket 发送)
Backend WebSocket Handler
    ↓ (WebSocket 接收)
CameraView
    ↓
显示图像
```

## 技术栈依赖

### 后端依赖
```
fastapi - Web 框架
uvicorn - ASGI 服务器
websockets - WebSocket 支持
opencv-python - 图像处理
numpy - 数值计算
pydantic - 数据验证
```

### 前端依赖
```
react - UI 框架
typescript - 类型安全
vite - 构建工具
zustand - 状态管理
axios - HTTP 客户端
```

## 配置文件

### 后端配置 (`.env`)
```env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000
ROBOT_ID=my_xlerobot
ROBOT_FPS=30
LEROBOT_ROOT=../../lerobot
```

### 前端配置 (`vite.config.ts`)
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': 'ws://localhost:8000',
  }
}
```

## 开发工作流

### 添加新功能

1. **后端新端点**:
   - 在 `main.py` 添加路由
   - 在相应模块添加实现
   - 更新 API 文档

2. **前端新组件**:
   - 在 `components/` 创建组件
   - 创建对应的 CSS 文件
   - 在父组件中引入

3. **新的状态**:
   - 在 `robotStore.ts` 添加状态
   - 添加相应的 setter 方法
   - 在组件中使用

### 调试技巧

- **后端**: 查看终端日志
- **前端**: 浏览器开发者工具
- **WebSocket**: Network 标签 → WS
- **API 测试**: `http://localhost:8000/docs`

## 部署结构

### 开发环境
```
开发机器
├── 后端: localhost:8000
├── 前端: localhost:3000
└── 机器人: USB 连接
```

### 生产环境（可选）
```
服务器
├── 后端: 0.0.0.0:8000
├── 前端: 静态文件服务
└── 反向代理 (Nginx)
    ├── / → 前端
    ├── /api → 后端
    └── /ws → 后端 WebSocket
```

## 代码规范

### Python (后端)
- PEP 8 代码风格
- Type hints
- Docstrings
- 异常处理
- 日志记录

### TypeScript (前端)
- ESLint 规则
- 函数式组件
- Hooks 优先
- Props 类型定义
- CSS Modules

## 维护清单

- [ ] 定期更新依赖
- [ ] 检查安全漏洞
- [ ] 优化性能
- [ ] 更新文档
- [ ] 备份配置
- [ ] 测试新功能
- [ ] 代码审查

---

通过这个结构文档，您应该能够：
- ✅ 理解项目整体架构
- ✅ 快速定位文件位置
- ✅ 了解数据流向
- ✅ 掌握开发工作流
- ✅ 进行有效的维护和扩展

