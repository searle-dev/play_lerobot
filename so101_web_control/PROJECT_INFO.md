# SO101 机械臂网页控制项目

## 📁 项目结构

```
so101_web_control/
├── app.py                 # Flask 服务器主程序
├── requirements.txt       # Python 依赖
├── start.sh              # 启动脚本
├── README.md             # 详细文档
├── QUICK_START.md        # 快速开始指南
├── PROJECT_INFO.md       # 项目说明（本文件）
├── templates/
│   └── index.html        # 网页主界面
└── static/
    ├── css/
    │   └── style.css     # 样式表
    └── js/
        └── app.js        # 前端控制逻辑
```

## 🎯 功能概览

### 核心功能
1. ✅ **实时控制**：基于 WebSocket 的实时双向通信
2. ✅ **双重输入**：键盘快捷键 + 虚拟按键
3. ✅ **状态监控**：实时显示所有关节的当前和目标位置
4. ✅ **参数调节**：可调节步进大小、比例增益等参数
5. ✅ **操作日志**：记录所有操作和状态变化

### 技术特性
- **后端**：Flask + Socket.IO + LeRobot
- **前端**：原生 HTML/CSS/JavaScript
- **控制算法**：P 控制（50Hz）
- **通信协议**：WebSocket (Socket.IO)
- **响应式设计**：支持手机/平板访问

## 🚀 快速开始

### 1. 安装依赖
```bash
cd /Users/ai/Project/play_lerobot/so101_web_control
pip install -r requirements.txt
```

### 2. 启动服务
```bash
bash start.sh
# 或
python app.py
```

### 3. 打开浏览器
访问：http://localhost:5000

## 📊 系统架构

```
┌─────────────┐         WebSocket        ┌─────────────┐
│   浏览器     │◄─────────────────────────►│ Flask Server│
│  (前端UI)   │                           │  (app.py)   │
└─────────────┘                           └──────┬──────┘
                                                 │
                                                 │ LeRobot API
                                                 ▼
                                          ┌─────────────┐
                                          │   SO101     │
                                          │  机械臂     │
                                          └─────────────┘
```

### 数据流
1. **用户输入** → 键盘/按键事件
2. **前端** → Socket.IO 发送命令
3. **后端** → P 控制循环处理
4. **LeRobot** → 控制机械臂
5. **反馈** → 实时状态更新回前端

## 🎮 控制说明

### 关节映射
| 按键 | 关节 | 功能 |
|------|------|------|
| Q/A | 关节1 | 底座左转/右转 |
| W/S | 关节2 | 大臂下降/上升 |
| E/D | 关节3 | 小臂弯曲/伸直 |
| R/F | 关节4 | 腕部下/上 |
| T/G | 关节5 | 腕部逆时针/顺时针 |
| Y/H | 夹爪 | 打开/关闭 |

### 控制参数
- **步进大小**：每次按键移动的角度（1-20°）
- **夹爪步进**：夹爪移动幅度（5-30）
- **比例增益 Kp**：P 控制增益（0.1-1.0）

## 🔧 配置说明

### 默认配置
```python
# 默认端口
current_port = "/dev/tty.usbmodem5A7C1163141"

# 控制参数
control_params = {
    'step_size': 5.0,      # 步进大小
    'gripper_step': 10.0,  # 夹爪步进
    'control_freq': 50,    # 控制频率 Hz
    'kp': 0.5              # 比例增益
}
```

### 修改端口
在 `app.py` 第 23 行修改默认端口，或在网页界面中输入新端口。

### 调整控制频率
在 `app.py` 第 31 行修改 `control_freq`。

## 📱 移动端支持

完全支持手机和平板访问：
1. 确保设备在同一局域网
2. 使用 Mac 的 IP 地址访问
3. 触摸操作虚拟按键

## 🛠️ 开发指南

### 添加新功能
1. **后端 API**：在 `app.py` 中添加 Socket.IO 事件处理
2. **前端界面**：修改 `templates/index.html`
3. **样式调整**：修改 `static/css/style.css`
4. **逻辑处理**：修改 `static/js/app.js`

### 调试
```bash
# 启用调试模式（app.py 最后一行）
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### 查看日志
- 后端日志：终端输出
- 前端日志：浏览器开发者工具 Console

## ⚠️ 注意事项

1. **安全第一**：
   - 确保手臂周围有足够空间
   - 首次使用建议小步进测试
   - 紧急情况按 Ctrl+C 停止服务

2. **网络安全**：
   - 仅在可信网络中使用
   - 不要暴露到公网
   - 考虑添加身份认证

3. **性能优化**：
   - 默认 50Hz 控制频率已足够
   - 如果延迟大，降低频率
   - 调整 Kp 值优化响应

## 🐛 常见问题

### 1. 连接失败
```bash
# 检查端口
ls /dev/tty.usb*

# 检查权限
ls -l /dev/tty.usb*

# 测试 LeRobot
python -c "from lerobot.robots.so100_follower import SO100Follower; print('✓ LeRobot 已安装')"
```

### 2. 网页无法访问
- 检查防火墙设置
- 尝试 `http://127.0.0.1:5000`
- 确认服务器正常运行

### 3. 控制延迟
- 降低控制频率
- 检查网络连接
- 调整 Kp 值

### 4. 夹爪不响应
- 确认已正确校准
- 检查夹爪步进参数
- 查看操作日志

## 📚 相关文档

- [README.md](README.md) - 完整文档
- [QUICK_START.md](QUICK_START.md) - 快速开始
- [XLeRobot 文档](https://xlerobot.readthedocs.io/)
- [LeRobot 文档](https://huggingface.co/docs/lerobot)

## 🔄 版本历史

- **v1.0** (2024-12-16)
  - 初始版本
  - 基础控制功能
  - 实时状态显示
  - 参数调节
  - 操作日志

## 📝 TODO

- [ ] 添加用户认证
- [ ] 支持多机械臂同时控制
- [ ] 录制和回放功能
- [ ] 3D 可视化
- [ ] 手机 App

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

Apache 2.0 License

---

**Happy Coding!** 🚀
