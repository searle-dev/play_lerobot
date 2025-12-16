# LeRobot 机械臂调试服务器 - 后端

基于 FastAPI 的机械臂管理和控制服务器。

## 功能特性

- 📡 端口扫描和电机识别
- 🤖 多机械臂管理（SO100, SO101, Koch, LeKiwi）
- ⚙️ 交互式校准（WebSocket）
- 🎮 实时控制（20Hz状态推送）
- 📹 动作录制和回放
- 💾 SQLite 本地存储

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
# 开发模式（自动重载）
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

## API 端点

### REST API

**端口扫描**
- `GET /api/ports` - 列出所有串口
- `POST /api/ports/scan` - 扫描指定端口

**机械臂管理**
- `GET /api/robots` - 列出所有机械臂
- `POST /api/robots` - 添加机械臂
- `GET /api/robots/{id}` - 获取机械臂状态
- `PUT /api/robots/{id}` - 更新备注
- `POST /api/robots/{id}/connect` - 连接
- `POST /api/robots/{id}/disconnect` - 断开
- `DELETE /api/robots/{id}` - 删除

**录制回放**
- `POST /api/recording/{robot_id}/start` - 开始录制
- `POST /api/recording/{recording_id}/stop` - 停止录制
- `GET /api/recording/{robot_id}` - 列出录制
- `POST /api/recording/{recording_id}/playback` - 回放

### WebSocket

- `WS /ws/calibration/{robot_id}` - 校准流程
- `WS /ws/control/{robot_id}` - 实时控制

## 项目结构

```
backend/
├── app/
│   ├── models/          # Pydantic 数据模型
│   ├── api/             # REST API 路由
│   ├── services/        # 业务逻辑
│   │   ├── robot_manager.py      # 机械臂管理器（核心）
│   │   ├── calibration_service.py # 校准服务
│   │   ├── recording_service.py   # 录制服务
│   │   └── port_scanner.py        # 端口扫描
│   ├── websocket/       # WebSocket 端点
│   ├── storage/         # 数据存储
│   ├── config.py        # 配置
│   └── main.py          # 应用入口
├── requirements.txt
└── README.md
```

## 配置

编辑 `app/config.py` 修改配置：

```python
# 数据目录
DATA_DIR = BASE_DIR / "data"

# CORS 配置
CORS_ORIGINS = ["http://localhost:5173"]

# WebSocket 配置
WS_STATE_UPDATE_FREQ = 20  # 状态更新频率（Hz）

# 录制配置
RECORDING_SAMPLE_RATE = 50  # 录制采样率（Hz）
```

## 开发说明

### 核心设计

1. **RobotManager**（单例模式）
   - 管理所有机械臂实例
   - 封装 LeRobot 同步 API 为异步接口
   - 每个机械臂独立锁，确保并发安全

2. **异步化改造**
   - 使用 `asyncio.run_in_executor` 将 LeRobot 同步操作转为异步
   - 避免阻塞事件循环

3. **校准流程**
   - 拆分为多个步骤
   - WebSocket 实时推送状态
   - 前端按钮替代命令行 `input()`

### 添加新机械臂类型

编辑 `app/services/robot_manager.py` 的 `_create_robot` 方法：

```python
elif self.config.robot_type == "new_robot":
    from lerobot.robots.new_robot import NewRobotConfig
    lerobot_config = NewRobotConfig(
        id=self.config.id,
        port=self.config.port
    )
```

## 故障排除

### 端口权限问题

```bash
# Linux/macOS: 添加用户到 dialout 组
sudo usermod -a -G dialout $USER
```

### LeRobot 导入错误

确保 LeRobot 已正确安装：

```bash
cd /Users/ai/Project/lerobot
pip install -e .
```

## 许可证

MIT
