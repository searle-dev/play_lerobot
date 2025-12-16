# Robot Web UI - LeRobot 机械臂 Web 调试平台

一个功能完整的 Web 界面，用于管理和调试 LeRobot 机械臂。

> 📍 这是 `play_lerobot` 项目集合中的一个子项目

## 项目概述

提供现代化的 Web 界面，完全替代命令行操作，让机械臂的调试变得简单直观。

### 核心功能

- 📡 **端口扫描和识别** - 自动扫描串口并识别连接的电机
- 🤖 **多机械臂管理** - 支持同时管理多个机械臂（SO100, SO101, Koch, LeKiwi）
- ⚙️ **交互式校准** - 基于 WebSocket 的实时校准流程
- 🎮 **实时控制** - 20Hz 高频状态推送和动作控制
- 📹 **录制回放** - 50Hz 采样率的动作录制和精确回放
- 💾 **本地缓存** - SQLite 数据库存储配置和备注

## 技术栈

### 后端
- **框架**: FastAPI + WebSocket
- **数据模型**: Pydantic
- **数据库**: SQLite
- **集成**: LeRobot（同步 API 异步化封装）

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 库**: Ant Design 5
- **状态管理**: Zustand
- **HTTP 客户端**: Axios

## 快速开始

### 前置要求

- Python 3.8+
- Node.js 16+
- LeRobot 已安装（位于 `/Users/ai/Project/lerobot`）
- 机械臂硬件和串口驱动

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 启动服务器
python -m app.main
```

后端地址: **http://localhost:8000**
API 文档: **http://localhost:8000/docs**

### 2. 启动前端

打开新终端：

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端地址: **http://localhost:5173**

### 3. 开始使用

1. 在浏览器打开 http://localhost:5173
2. 点击"添加机械臂"
3. 填写机械臂信息（ID、类型、端口）
4. 点击"连接"开始使用

详细使用指南请查看 [QUICKSTART.md](./QUICKSTART.md)

## 项目结构

```
robot_web_ui/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── models/            # Pydantic 数据模型
│   │   ├── api/               # REST API 路由
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── robot_manager.py      # 机械臂管理器
│   │   │   ├── calibration_service.py # 校准服务
│   │   │   ├── recording_service.py   # 录制服务
│   │   │   └── port_scanner.py        # 端口扫描
│   │   ├── websocket/         # WebSocket 端点
│   │   ├── storage/           # SQLite 数据库
│   │   └── main.py            # 应用入口
│   └── requirements.txt
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── pages/             # 页面组件
│   │   ├── store/             # Zustand 状态管理
│   │   ├── services/          # API 服务层
│   │   ├── hooks/             # 自定义 Hooks
│   │   └── types/             # TypeScript 类型
│   └── package.json
│
├── data/                       # 数据存储
│   ├── robots.db              # SQLite 数据库
│   └── recordings/            # 录制文件
│
└── README.md                   # 本文件
```

## API 端点

### REST API

**端口扫描**
- `GET /api/ports` - 列出所有串口
- `POST /api/ports/scan` - 扫描指定端口

**机械臂管理**
- `GET /api/robots` - 列出所有机械臂
- `POST /api/robots` - 添加机械臂
- `POST /api/robots/{id}/connect` - 连接
- `POST /api/robots/{id}/disconnect` - 断开
- `PUT /api/robots/{id}` - 更新备注
- `DELETE /api/robots/{id}` - 删除

**录制回放**
- `POST /api/recording/{robot_id}/start` - 开始录制
- `POST /api/recording/{recording_id}/stop` - 停止录制
- `GET /api/recording/{robot_id}` - 列出录制
- `POST /api/recording/{recording_id}/playback` - 回放

### WebSocket

- `WS /ws/calibration/{robot_id}` - 校准流程（实时状态推送）
- `WS /ws/control/{robot_id}` - 实时控制（20Hz 状态推送）

## 架构设计

### 核心创新

1. **异步化改造** - 将 LeRobot 同步 API 封装为异步接口
2. **交互式校准** - WebSocket 实时推送替代命令行 input()
3. **并发安全** - 每个机械臂独立锁，支持多设备并发
4. **实时通信** - 20Hz 状态推送，50Hz 录制采样

详细架构说明请查看主文档。

## 配置

### 后端配置

编辑 `backend/app/config.py`:

```python
# CORS 配置
CORS_ORIGINS = ["http://localhost:5173"]

# WebSocket 配置
WS_STATE_UPDATE_FREQ = 20  # Hz

# 录制配置
RECORDING_SAMPLE_RATE = 50  # Hz
```

### 前端配置

编辑 `frontend/src/services/api.ts`:

```typescript
export const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});
```

## 开发状态

### ✅ 已完成

- 后端完整实现（所有 API 和服务）
- 前端基础框架和机械臂管理
- 数据库存储
- WebSocket 通信
- 完整文档

### ⏳ 待扩展

- 完整的校准 UI 界面
- 实时控制面板 UI
- 录制回放 UI 界面
- 端口扫描 UI
- 摄像头视频流

**当前可以**：
- 通过 Web 界面管理机械臂
- 通过 API 文档测试所有功能
- 使用 WebSocket 进行实时通信

## 故障排除

### 端口权限问题

Linux/macOS:
```bash
sudo usermod -a -G dialout $USER
# 重新登录
```

### LeRobot 导入错误

```bash
cd /Users/ai/Project/lerobot
pip install -e .
```

### CORS 错误

确保 `backend/app/config.py` 中的 `CORS_ORIGINS` 包含前端地址。

## 文档

- [快速启动指南](./QUICKSTART.md)
- [后端文档](./backend/README.md)
- [前端文档](./frontend/README.md)
- [API 文档](http://localhost:8000/docs)（需先启动后端）

## 许可证

MIT License

---

**返回上级项目**: [Play LeRobot](../README.md)
