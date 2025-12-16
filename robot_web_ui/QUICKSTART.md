# 快速启动指南

## 一键启动

### 1. 后端

```bash
cd backend

# 首次运行：创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动服务器
./run.sh
# 或者
python -m app.main
```

后端将运行在: **http://localhost:8000**

API 文档: **http://localhost:8000/docs**

### 2. 前端

打开新终端：

```bash
cd frontend

# 首次运行：安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在: **http://localhost:5173**

## 验证安装

### 测试后端

```bash
curl http://localhost:8000/health
```

应该返回：
```json
{
  "status": "healthy",
  "robots_count": 0
}
```

### 测试前端

在浏览器中打开 http://localhost:5173，应该看到"LeRobot 机械臂调试平台"页面。

## 首次使用

### 1. 查看可用串口

使用 API 文档测试：http://localhost:8000/docs

找到 `GET /api/ports`，点击 "Try it out" → "Execute"

### 2. 添加机械臂

在 Web 界面中：
1. 点击"添加机械臂"
2. 填写信息：
   - ID: `robot1`
   - 类型: 选择你的机械臂类型（如 `so101_follower`）
   - 串口: 从第一步获取的端口（如 `/dev/tty.usbmodem123`）
   - 昵称: `我的SO101机械臂`
3. 点击"添加"

### 3. 连接机械臂

在机械臂列表中点击"连接"按钮。

**注意**: 首次连接会提示校准，暂时点击"取消"，校准功能的完整 UI 正在开发中。

## 使用 API 直接测试

### 连接机械臂

```bash
curl -X POST "http://localhost:8000/api/robots/robot1/connect?calibrate=false"
```

### 获取机械臂状态

```bash
curl http://localhost:8000/api/robots/robot1
```

### 获取观测（关节位置）

```bash
curl http://localhost:8000/api/robots/robot1/observation
```

## 下一步

- 查看完整文档: `README.md`
- 后端文档: `backend/README.md`
- 前端文档: `frontend/README.md`
- API 文档: http://localhost:8000/docs

## 常见问题

### Q: 端口被占用

**A**: 修改端口
- 后端: 编辑 `backend/app/main.py`，修改 `uvicorn.run(port=8000)` 中的端口
- 前端: 编辑 `frontend/vite.config.ts`，修改 `server.port`

### Q: 找不到 LeRobot

**A**: 确保 LeRobot 已安装

```bash
cd /Users/ai/Project/lerobot
pip install -e .
```

### Q: 串口权限问题

**A**: 添加用户到 dialout 组（Linux/macOS）

```bash
sudo usermod -a -G dialout $USER
# 重新登录
```

### Q: 前端无法连接后端

**A**: 检查 CORS 配置

编辑 `backend/app/config.py`，确保 `CORS_ORIGINS` 包含前端地址：

```python
CORS_ORIGINS = [
    "http://localhost:5173",
]
```

## 停止服务

- 后端: 在终端中按 `Ctrl+C`
- 前端: 在终端中按 `Ctrl+C`

## 重新启动

```bash
# 后端
cd backend && ./run.sh

# 前端
cd frontend && npm run dev
```

祝使用愉快！ 🤖
