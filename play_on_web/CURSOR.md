# XLerobot Web Teleop - AI 助手指南

> 📌 本文档为 AI 编程助手（如 Cursor）提供项目概览和技术要点

## 📋 项目概览

**项目名称**: XLerobot Web Teleop  
**技术栈**: FastAPI (Python) + React (TypeScript) + WebSocket  
**目标**: 为 XLerobot 机械臂小车提供 Web 遥操作界面  
**状态**: ✅ 核心功能已完成，持续优化中

## 🏗️ 项目结构

```
play_on_web/
├── backend/              # FastAPI 后端
│   ├── main.py          # 主应用 + WebSocket
│   ├── robot_controller.py  # 机器人控制核心
│   ├── device_scanner.py    # 设备扫描
│   ├── camera_manager.py    # 相机管理
│   └── requirements.txt     # Python 依赖
│
├── frontend/            # React 前端
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── stores/      # Zustand 状态管理
│   │   ├── api/         # API 客户端
│   │   └── utils/       # 工具函数
│   └── package.json
│
└── docs/                # 文档目录
    ├── guides/          # 用户指南
    ├── fixes/           # 技术修复说明
    └── archives/        # 历史文档
```

## 🎯 核心功能

### 1. 设备配置
- ✅ 串口自动扫描（macOS tty/cu 设备处理）
- ✅ 相机检测（OpenCV + RealSense）
- ✅ 智能端口识别（通过拔插识别）
- ✅ 校准和初始化

### 2. 机器人控制
- ✅ 双臂独立控制（左臂/右臂）
- ✅ 逆运动学控制（XY 平面 + pitch）
- ✅ P 控制实现（kp=0.81）
- ✅ 底盘全向移动（前后左右旋转）
- ✅ 自定义安全复位位置
- ✅ 三档步长控制（slow/normal/fast）

### 3. 交互方式
- ✅ 键盘控制（完整键位映射）
- ✅ Xbox 手柄（开发中）
- ✅ 多机位视频流（WebSocket）
- ✅ 实时状态反馈

## 🔧 技术要点

### 1. 环境配置
**重要**: 项目复用 `lerobot` conda 环境，避免重复安装
```bash
conda activate lerobot
cd play_on_web/backend
pip install -r requirements.txt  # 只安装 Web 相关依赖
```

### 2. 参考代码
**必须参考**: `lerobot/examples/xlerobot/4_xlerobot_teleop_keyboard.py`
- 机械臂控制参数（degree_step=3, xy_step=0.0081）
- 逆运动学实现
- P 控制逻辑
- 键位映射

### 3. 关键配置参数

#### 机械臂控制（`robot_controller.py`）
```python
@dataclass
class ArmState:
    degree_step: int = 3       # 关节空间步长（度）⚠️ 必须是整数
    xy_step: float = 0.0081    # 笛卡尔空间步长（米）⚠️ 不要修改！
    kp: float = 0.81           # P 控制增益
    
    # 初始位置（参考点）
    current_x: float = 0.1629
    current_y: float = 0.1131
    pitch: float = 0.0
```

**警告**:
- `xy_step = 0.0081` 是经过验证的最佳值，不要随意修改
- 修改为更小的值（如 0.005）会导致运动抖动、不流畅
- 详见: `docs/fixes/SMOOTH_CONTROL_FIX.md`

#### 底盘控制
```python
# 底盘使用速度命令（不是位置命令）
stop_action = {
    "x.vel": 0.0,      # 必须显式发送停止命令
    "y.vel": 0.0,
    "theta.vel": 0.0
}
```

**关键**: 松开按键必须发送停止命令，否则机器人会持续运动  
详见: `docs/fixes/BASE_CONTROL_FIX.md`

### 4. macOS 串口处理
macOS 为每个 USB 串口创建两个设备文件：
- `/dev/tty.usbmodem*` - TTY 设备（推荐使用）
- `/dev/cu.usbmodem*` - Callout 设备

拔出 USB 时两个设备都会消失，需要智能判断为同一物理设备。  
详见: `backend/MACOS_PORTS.md`

### 5. 逆运动学耦合
```python
# wrist_flex 与其他关节耦合
wrist_flex = -shoulder_lift - elbow_flex + pitch
```

**注意**: y 方向移动会同时影响 shoulder_lift、elbow_flex、wrist_flex  
这是**正常行为**，由 IK 和耦合关系决定  
详见: `docs/fixes/IK_CONTROL_EXPLANATION.md`

## 🐛 常见问题和解决方案

### 问题 1: 机械臂移动抖动
**原因**: xy_step 值太小（如 0.005）  
**解决**: 使用参考值 0.0081  
**文档**: `docs/fixes/SMOOTH_CONTROL_FIX.md`

### 问题 2: 底盘按键松开不停止
**原因**: 速度命令需要显式发送停止（vel=0）  
**解决**: keyup 时发送 stop_base 命令  
**文档**: `docs/fixes/BASE_CONTROL_FIX.md`

### 问题 3: 端口检测显示多个设备
**原因**: macOS 的 tty/cu 设备对  
**解决**: 只返回 tty 设备，智能过滤 cu 设备  
**文档**: `backend/MACOS_PORTS.md`

### 问题 4: RealSense 相机扫描报错
**原因**: pyrealsense2 未安装  
**解决**: 检查导入，优雅降级（跳过 RealSense）  
**文档**: `docs/fixes/FIX_SUMMARY_20260102.md`

### 问题 5: 机器人连接报 EOF 错误
**原因**: 交互式校准提示在非交互环境失败  
**解决**: Monkey patch `input()` 自动选择恢复校准  
**文档**: `docs/fixes/ROBOT_CONNECTION_TEST.md`

### 问题 6: 前臂断电掉落
**原因**: 零位不是安全位置  
**解决**: 实现自定义安全复位位置功能  
**文档**: `docs/guides/SAFE_RESET_POSITION_GUIDE.md`

## 📝 最近的重要修复

### 2026-01-02 修复记录

#### 1. 平滑控制优化 ⭐⭐⭐⭐⭐
- **问题**: 机械臂移动抖动，不如参考代码平滑
- **原因**: xy_step 被错误修改为 0.005（应为 0.0081）
- **修复**: 恢复参考代码配置值
- **影响**: 核心控制体验

#### 2. 底盘控制修复 ⭐⭐⭐⭐⭐
- **问题**: 按键松开后底盘不停止
- **原因**: 速度命令需要显式停止，但 keyup 未发送
- **修复**: 添加 stop_base() 和 keyup 停止逻辑
- **影响**: 安全性和用户体验

#### 3. 安全复位位置 ⭐⭐⭐⭐
- **问题**: 零位断电时前臂掉落
- **解决**: 允许用户自定义安全复位位置
- **文件**: reset_positions.json

#### 4. 步长等级控制 ⭐⭐⭐
- **功能**: slow/normal/fast 三档步长
- **默认**: normal (参考代码值)
- **用途**: 适应不同精度需求

#### 5. 相机可选配置 ⭐⭐⭐
- **修复**: 允许跳过相机配置
- **原因**: 不是所有场景都需要相机

## 🎨 代码风格和约定

### Python (Backend)
```python
# 使用类型注解
def handle_action(self, action: dict[str, Any]) -> dict[str, Any]:
    """
    处理动作
    
    Args:
        action: 动作字典
        
    Returns:
        结果字典，包含 status 和其他信息
    """
    try:
        # ... 实现
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"处理动作失败: {e}")
        return {"status": "error", "message": str(e)}
```

### TypeScript (Frontend)
```typescript
// 使用 TypeScript 严格模式
interface RobotState {
  isConnected: boolean
  port1: string
  port2: string
  observation: Record<string, number>
}

// Zustand 状态管理
const useRobotStore = create<RobotState>((set) => ({
  // ...
}))
```

### WebSocket 消息格式
```typescript
// 客户端 → 服务器
{
  type: 'keyboard_action' | 'base_action' | 'base_stop' | 'get_observation',
  data?: { arm: string, action: string }
}

// 服务器 → 客户端
{
  type: 'action_result' | 'observation' | 'error',
  data: { status: string, ... }
}
```

## 🔍 调试技巧

### 1. 后端日志
```python
# 在 robot_controller.py 中启用调试日志
logger.debug(f"IK 更新: x={x:.4f}, y={y:.4f} -> joints={joint2:.2f}, {joint3:.2f}")
```

### 2. 前端 WebSocket 调试
```typescript
// 在浏览器控制台
console.log('WebSocket state:', ws.readyState)
// 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
```

### 3. 测试脚本
```bash
# 测试串口检测
python backend/test_port_detection.py

# 测试设备扫描
python backend/test_device_scan.py
```

## 📚 重要文档索引

### 用户指南
- `README.md` - 项目主文档
- `QUICKSTART.md` - 快速开始
- `docs/guides/SAFE_RESET_POSITION_GUIDE.md` - 安全复位指南
- `docs/guides/BASE_CONTROL_USAGE.md` - 底盘控制使用

### 技术文档
- `STATUS.md` - 项目当前状态
- `docs/fixes/SMOOTH_CONTROL_FIX.md` - 平滑控制优化
- `docs/fixes/BASE_CONTROL_FIX.md` - 底盘控制修复
- `docs/fixes/IK_CONTROL_EXPLANATION.md` - IK 控制原理
- `docs/fixes/SAFE_RESET_FEATURE_SUMMARY.md` - 复位功能实现

### 开发文档
- `SETUP_CONDA.md` - Conda 环境配置
- `CHECKLIST.md` - 功能检查清单
- `STRUCTURE.md` - 项目结构说明

### 平台特定
- `backend/MACOS_PORTS.md` - macOS 串口处理
- `frontend/PORT_DETECTION_GUIDE.md` - 端口检测指南

## ⚠️ 开发注意事项

### 1. 不要随意修改这些值
```python
xy_step = 0.0081      # ⚠️ 已验证的最佳值
degree_step = 3       # ⚠️ 必须是整数
kp = 0.81            # ⚠️ P 控制增益
current_x = 0.1629   # ⚠️ 初始参考点
current_y = 0.1131   # ⚠️ 初始参考点
```

### 2. 底盘控制必须处理停止
任何底盘运动相关的修改，务必确保：
- keydown → 发送速度命令
- keyup → 发送停止命令（vel=0）

### 3. macOS 串口处理
- 始终过滤只返回 `tty.*` 设备
- 检测断开时处理 tty/cu 设备对

### 4. 错误处理
所有 API 和 WebSocket 处理都应返回统一格式：
```python
{"status": "success" | "error", "message": str, ...}
```

### 5. 参考代码优先
遇到控制逻辑问题，优先参考：
- `lerobot/examples/xlerobot/4_xlerobot_teleop_keyboard.py`
- `lerobot/examples/xlerobot/5_xlerobot_teleop_xbox.py`

## 🚀 快速启动命令

```bash
# 使用 conda 环境启动（推荐）
cd /Users/ai/Project/play_lerobot/play_on_web
./start_conda.sh

# 或分别启动
conda activate lerobot

# 后端
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm run dev
```

## 📞 故障排查流程

1. **检查环境**: `conda list | grep lerobot`
2. **检查服务**: 
   - 后端: `curl http://localhost:8000/api/health`
   - 前端: 访问 `http://localhost:3000`
3. **检查日志**: 
   - 后端: 终端输出
   - 前端: 浏览器控制台 (F12)
4. **检查连接**:
   - 串口: `ls /dev/tty.usb*`
   - WebSocket: 浏览器 Network 标签
5. **参考文档**: 查看 `STATUS.md` 和 `docs/fixes/`

## 🎓 学习路径

### 新手
1. 阅读 `README.md` 了解项目
2. 运行 `QUICKSTART.md` 快速开始
3. 查看 `STATUS.md` 了解当前功能
4. 尝试操作，参考 `docs/guides/`

### 开发者
1. 阅读 `STRUCTURE.md` 了解架构
2. 查看 `SETUP_CONDA.md` 配置环境
3. 研究参考代码 `4_xlerobot_teleop_keyboard.py`
4. 阅读 `docs/fixes/` 了解技术细节
5. 使用 `CHECKLIST.md` 验证功能

### 贡献者
1. 理解所有技术文档
2. 遵循代码风格约定
3. 添加测试和文档
4. 提交前检查 `CHECKLIST.md`

## 📊 项目状态

**完成度**: 85%

✅ **已完成**:
- 设备扫描和配置
- 机器人连接和控制
- 键盘遥操作
- 多机位视频流
- 安全复位位置
- 步长等级控制
- 底盘松开停止

🚧 **进行中**:
- Xbox 手柄支持（框架已有）
- 性能优化
- 用户体验提升

📝 **计划中**:
- 录制和回放
- 数据集收集
- 更多控制模式

## 🤝 协作建议

### 给 AI 助手的建议
1. **优先参考参考代码**: 不要凭空想象，查看 lerobot 源码
2. **保持配置一致**: 不要修改已验证的参数
3. **充分测试**: 编译成功 ≠ 功能正常
4. **更新文档**: 修改代码后更新相关文档
5. **尊重历史**: 查看 git 历史和 fixes 文档了解为什么这样做

### 常用命令
```bash
# 编译检查
cd frontend && npm run build

# Linter 检查
cd frontend && npm run lint

# 类型检查
cd frontend && npx tsc --noEmit
```

---

**最后更新**: 2026-01-02  
**维护者**: AI Assistant  
**反馈**: 通过 GitHub Issues 或项目文档

