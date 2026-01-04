# XLerobot Web Teleop - 后端

基于 FastAPI 的 XLerobot 机械臂小车网页遥操作系统后端。

## 功能特性

- 🔍 **设备扫描**: 自动扫描串口和相机设备
- 🤖 **机器人控制**: 实时控制双臂机械臂和底盘
- 📹 **多机位视频**: 支持多路相机同时流式传输
- ⚡ **实时通信**: WebSocket 低延迟双向通信
- 🎮 **多种控制方式**: 支持键盘和 Xbox 手柄

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

## 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

## API 文档

启动后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 主要端点

### 设备扫描
- `GET /api/devices/ports` - 获取所有串口
- `GET /api/devices/cameras` - 获取所有相机
- `GET /api/devices/ports/detect/start` - 开始端口检测
- `POST /api/devices/ports/detect/complete` - 完成端口检测

### 机器人控制
- `POST /api/robot/connect` - 连接机器人
- `POST /api/robot/disconnect` - 断开机器人
- `POST /api/robot/zero` - 移动到零位
- `GET /api/robot/observation` - 获取观测值

### 相机管理
- `POST /api/cameras/add` - 添加相机
- `DELETE /api/cameras/{name}` - 移除相机
- `GET /api/cameras/{name}/frame` - 获取单帧

### WebSocket
- `WS /ws/teleop` - 遥操作 WebSocket
- `WS /ws/camera` - 相机流 WebSocket

## 项目结构

```
backend/
├── main.py              # FastAPI 主应用
├── config.py            # 配置管理
├── device_scanner.py    # 设备扫描
├── robot_controller.py  # 机器人控制
├── camera_manager.py    # 相机管理
├── requirements.txt     # 依赖列表
└── README.md           # 文档
```

