# 项目状态

**最后更新**: 2026-01-02  
**状态**: ✅ 主要问题已修复

## 快速开始

### 启动系统

```bash
# 启动后端（终端 1）
cd /Users/ai/Project/play_lerobot/play_on_web
./start_conda.sh backend

# 启动前端（终端 2）
cd /Users/ai/Project/play_lerobot/play_on_web
./start_conda.sh frontend

# 访问 Web 界面
open http://localhost:3000
```

### 运行测试

```bash
# 测试设备扫描
cd /Users/ai/Project/play_lerobot/play_on_web
conda run -n lerobot python backend/test_device_scan.py

# 测试串口检测（交互式）
conda run -n lerobot python backend/test_port_detection.py
```

## 当前功能状态

### ✅ 已完成并测试

| 功能 | 状态 | 备注 |
|------|------|------|
| 串口扫描 | ✅ | 支持 macOS/Linux/Windows |
| 串口自动检测 | ✅ | 通过拔插 USB 自动识别 |
| macOS tty/cu 设备对处理 | ✅ | 智能识别配对设备 |
| OpenCV 相机扫描 | ✅ | 自动发现可用相机 |
| RealSense 相机扫描 | ✅ | 优雅处理未安装情况 |
| 相机配置可选 | ✅ | 可跳过相机配置 |
| 设备配置 Web UI | ✅ | 直观的配置界面 |
| 端口手动刷新 | ✅ | 支持手动重新扫描 |
| **安全复位位置** | ✅ | **自定义复位位置，防止断电掉落** |
| 前端 TypeScript 编译 | ✅ | 无编译错误 |
| 设备扫描自动化测试 | ✅ | 100% 通过 |

### 🔄 需要硬件测试

| 功能 | 状态 | 备注 |
|------|------|------|
| 机器人连接 | 🔄 | 已修复 EOF 错误，需硬件验证 |
| 校准恢复 | 🔄 | 自动从文件恢复，需硬件验证 |
| 键盘控制 | 🔄 | 代码已实现，需硬件测试 |
| Xbox 手柄控制 | 🔄 | 代码已实现，需硬件测试 |
| 相机实时视频流 | 🔄 | WebSocket 已实现，需测试 |
| 机械臂运动控制 | 🔄 | P 控制和 IK 已实现，需测试 |
| 底盘控制 | 🔄 | 代码已实现，需硬件测试 |

### 📋 待实现

| 功能 | 状态 | 优先级 |
|------|------|--------|
| Xbox 手柄 Web 支持 | 📋 | 中 |
| 录制和回放 | 📋 | 低 |
| 数据集导出 | 📋 | 低 |
| 高级校准 UI | 📋 | 低 |

## 最近新增功能和修复

### 1. 底盘控制松开停止 (2026-01-02) - ✨ 最新

**问题描述**: 底盘控制按键松开后不停止，需要按其他键才能停止。

**根本原因**: 底盘使用速度命令，一旦设置速度会持续运动，直到接收到速度为0的命令。前端 keyup 时没有发送停止命令。

**解决方案**:
- 后端添加 `stop_base()` 方法发送速度为 0 的命令
- 前端 keyup 时检测底盘按键并自动发送停止
- WebSocket 添加 `base_stop` 消息类型处理

**效果**: 
- 短按 → 动一次
- 长按 → 持续运动
- 松开 → 立即停止 ✅

**文件**: `backend/robot_controller.py`, `backend/main.py`, `frontend/src/components/KeyboardControl.tsx`, `BASE_CONTROL_FIX.md`

### 2. 平滑控制优化 (2026-01-02)

**问题描述**: 机械臂控制有抖动，不如参考代码平滑。

**根本原因**: xy_step 被错误地从 8.1mm 改为 5mm，导致移动不连贯。

**解决方案**:
- 恢复参考代码的配置值：xy_step = 0.0081 (8.1mm)
- degree_step 改为整数类型保持一致性
- 重新调整三档步长配置

**文件**: `backend/robot_controller.py`, `SMOOTH_CONTROL_FIX.md`

### 2. 安全复位位置功能 (2026-01-02)

**功能描述**: 允许用户自定义机械臂的复位位置，避免归零位置断电时前臂掉落。

**主要特性**:
- 记录当前位置作为复位位置
- 保存复位位置到配置文件
- 在校准页面设置复位位置
- 在控制页面快捷复位按钮
- 独立设置左臂/右臂复位位置

**文件**:
- 后端: `backend/robot_controller.py`, `backend/main.py`
- 前端: `frontend/src/components/DeviceSetup.tsx`, `frontend/src/components/TeleopControl.tsx`
- 文档: `SAFE_RESET_POSITION_GUIDE.md`

### 2. 相机配置按钮无法点击 (2026-01-02)

**问题**: 在相机配置步骤中，"继续"按钮被禁用，无法点击。

**原因**: 按钮要求必须至少选择一个相机才能继续。

**解决**: 
- 移除相机数量的禁用条件
- 允许跳过相机配置
- 按钮文本动态显示："跳过（不使用相机）" 或 "继续"

**文件**: `frontend/src/components/DeviceSetup.tsx:372-390`

### 2. 机器人连接 EOF 错误 (2026-01-02)

**问题**: 
```
robot_controller - ERROR - 连接机器人时出错: EOF when reading a line
```

**原因**: XLerobot.connect() 包含交互式 input() 提示

**解决**: 使用 monkey patch 自动选择恢复校准

**文件**: `backend/robot_controller.py:117-130`

### 2. RealSense 相机扫描错误 (2026-01-02)

**问题**:
```
device_scanner - ERROR - 扫描 RealSense 相机时出错: name 'rs' is not defined
```

**原因**: pyrealsense2 未安装

**解决**: 添加依赖检查，优雅降级

**文件**: `backend/device_scanner.py:210-220`

### 3. 端口检测后不显示 (2026-01-02)

**问题**: 自动检测成功但下拉框中看不到端口

**原因**: 状态更新逻辑问题

**解决**: 手动添加到 availablePorts + 刷新按钮

**文件**: `frontend/src/components/DeviceSetup.tsx:88-92`

### 4. 相机配置可选性 (2026-01-02)

**问题**: 必须选择相机才能继续，限制了灵活性

**原因**: 业务逻辑设计不够灵活

**解决**: 允许跳过相机配置，相机变为可选

**文件**: `frontend/src/components/DeviceSetup.tsx:372-390`

### 5. macOS 重复端口检测 (2026-01-02)

**问题**: 检测到多个端口变化（tty + cu）

**原因**: macOS 为每个 USB 创建两个设备文件

**解决**: 智能识别 tty/cu 配对，返回 tty 版本

**文件**: `backend/device_scanner.py:125-145`

## 文档

### 用户文档
- `README.md` - 项目概述
- `QUICKSTART.md` - 快速开始指南
- `PORT_DETECTION_GUIDE.md` - 端口检测使用指南
- `ROBOT_CONNECTION_TEST.md` - 机器人连接测试

### 开发文档
- `SETUP_CONDA.md` - Conda 环境设置
- `CHANGES.md` - 详细变更记录
- `MACOS_PORTS.md` - macOS 串口行为说明
- `FIX_SUMMARY_20260102.md` - 最新修复摘要

### 技术文档
- `backend/test_device_scan.py` - 自动化测试脚本
- `backend/test_port_detection.py` - 交互式端口检测测试

## 系统架构

```
play_on_web/
├── backend/               # FastAPI 后端
│   ├── main.py           # API 入口
│   ├── device_scanner.py # 设备扫描 ✅
│   ├── robot_controller.py # 机器人控制 ✅
│   └── requirements.txt  # Python 依赖
│
├── frontend/             # React 前端
│   ├── src/
│   │   ├── components/   # React 组件
│   │   │   ├── DeviceSetup.tsx ✅
│   │   │   ├── RobotControl.tsx ✅
│   │   │   └── CameraView.tsx ✅
│   │   ├── store/        # Zustand 状态管理 ✅
│   │   └── api/          # API 客户端 ✅
│   └── package.json
│
├── start_conda.sh        # 启动脚本 ✅
└── verify_setup.sh       # 环境验证脚本 ✅
```

## 环境要求

### Python (通过 lerobot conda 环境)
- Python 3.10+
- FastAPI 0.109.0
- uvicorn 0.27.0
- pyserial
- opencv-python
- numpy
- lerobot (通过 `pip install -e .[all]`)

### Node.js (前端)
- Node.js 18+
- React 18
- TypeScript 5
- Vite 5

### 硬件（可选）
- XLerobot 机器人
- USB 串口设备（2 个）
- OpenCV 相机（可选）
- RealSense 相机（可选）

## 已知限制

1. **Monkey Patch**
   - 只在机器人连接期间生效
   - 如果需要手动校准，需要修改代码

2. **RealSense 支持**
   - pyrealsense2 是可选依赖
   - 如果未安装，RealSense 相机扫描会被跳过

3. **macOS 串口**
   - 每个 USB 创建 tty/cu 两个设备
   - 系统默认使用 tty 设备
   - cu 设备在下拉框中被隐藏

4. **Xbox 手柄**
   - Web Gamepad API 支持有限
   - 某些浏览器可能需要 HTTPS

## 故障排查

### 后端无法启动

```bash
# 检查 conda 环境
conda env list
conda activate lerobot

# 验证依赖
python backend/check_env.py

# 查看详细错误
cd backend && python main.py
```

### 前端无法启动

```bash
# 检查 Node.js 版本
node --version  # 应该 >= 18

# 重新安装依赖
cd frontend && npm install

# 查看详细错误
npm run dev
```

### 无法扫描设备

```bash
# 测试设备扫描
conda run -n lerobot python backend/test_device_scan.py

# 检查 USB 连接
ls -la /dev/tty.usb*      # macOS
ls -la /dev/ttyUSB*       # Linux
```

### 机器人连接失败

1. 检查串口配置是否正确
2. 确保机器人已上电
3. 验证校准文件存在: `~/.cache/huggingface/lerobot/calibration/robots/xlerobot/`
4. 查看后端日志中的详细错误

## 贡献者

- AI Assistant - 初始开发和问题修复
- 用户反馈 - 问题发现和测试

## 许可

遵循 lerobot 项目的 Apache 2.0 许可证

---

**需要帮助？**
- 查看 `ROBOT_CONNECTION_TEST.md` 进行详细测试
- 查看 `FIX_SUMMARY_20260102.md` 了解最新修复
- 运行 `backend/test_device_scan.py` 进行自动化测试

