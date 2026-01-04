# 安全复位位置使用指南

## 📋 功能概述

**安全复位位置**是一个可自定义的机械臂姿态，用于在以下场景下保护机械臂：
- ✅ 开机初始化时的复位
- ✅ 断电前的安全归位
- ✅ 紧急情况下的快速归位

### 为什么需要安全复位位置？

**问题**：传统的"归零"（所有关节角度为 0°）可能不是一个安全的位置。当机械臂处于零位时：
- ⚠️ 前臂可能完全伸直或处于不稳定的姿态
- ⚠️ 如果此时断电，前臂会因重力而快速掉落
- ⚠️ 可能造成机械臂损坏或伤害周围人员

**解决方案**：设置一个**安全复位位置**，让机械臂在断电时也能保持相对稳定的姿态。

## 🎯 推荐的安全姿态

根据 SO101 机械臂的特点，推荐的安全复位位置应该：

### 左臂 / 右臂
1. **shoulder_lift (肩关节抬升)**：约 30° ~ 45°
   - 目的：让前臂略微向上，减少重力造成的力矩
   
2. **elbow_flex (肘关节弯曲)**：约 45° ~ 60°
   - 目的：弯曲肘关节，降低前臂质心
   
3. **shoulder_pan (肩关节旋转)**：0° ~ 10°
   - 目的：保持平衡，避免侧翻
   
4. **wrist_flex (腕关节)**：根据耦合关系自动调整
   - 自动计算：`wrist_flex = -shoulder_lift - elbow_flex + pitch`
   
5. **wrist_roll (腕旋转)**：0°
   - 目的：保持简单姿态
   
6. **gripper (夹爪)**：50 (半开)
   - 目的：保持夹爪在中立位置

### 示例安全位置

```json
{
  "left_arm": {
    "shoulder_pan": 0.0,
    "shoulder_lift": 35.0,
    "elbow_flex": 50.0,
    "wrist_flex": -85.0,
    "wrist_roll": 0.0,
    "gripper": 50.0
  },
  "right_arm": {
    "shoulder_pan": 0.0,
    "shoulder_lift": 35.0,
    "elbow_flex": 50.0,
    "wrist_flex": -85.0,
    "wrist_roll": 0.0,
    "gripper": 50.0
  }
}
```

## 🚀 使用步骤

### 方法 1: 在设备设置-校准页面设置（推荐）

1. **完成设备配置**
   - 配置串口 1 和串口 2
   - （可选）配置相机

2. **进入校准与初始化页面**
   - 系统会显示"校准与初始化"界面
   - 可以看到复位位置设置区域

3. **设置安全复位位置**
   
   **方法 A：从零位开始调整**
   ```
   a. 点击 "📍 移动到零位" 按钮
   b. 使用键盘或手柄手动调整机械臂到安全姿态
      - 建议：肩关节和肘关节适当向上弯曲
      - 确认断电时前臂不会快速掉落
   c. 点击 "💾 记录当前位置为复位位置"
   d. 系统会提示 "✅ 已记录左臂和右臂当前位置作为复位位置"
   ```
   
   **方法 B：手动调整到理想位置**
   ```
   a. 直接使用键盘或手柄调整机械臂
   b. 找到一个稳定、安全的姿态
   c. 点击 "💾 记录当前位置为复位位置"
   ```

4. **测试复位位置**
   ```
   a. 移动机械臂到其他位置
   b. 点击 "🔄 测试复位位置"
   c. 观察机械臂是否平稳地移动到记录的位置
   d. 验证该位置是否安全稳定
   ```

5. **完成设置**
   ```
   点击 "完成设置，开始遥操作" 进入控制界面
   ```

### 方法 2: 在遥操作页面使用快捷复位

1. **进入遥操作界面**
   - 完成设备设置后进入主控制界面

2. **使用安全复位功能**
   - 在页面右上角找到控制按钮组
   - 点击 "🏠 安全复位" 按钮
   - 机械臂会平稳移动到预设的安全位置

3. **其他相关按钮**
   - "左臂归零" - 只让左臂归零
   - "右臂归零" - 只让右臂归零
   - "全部归零" - 让两个机械臂都归零
   - "🏠 安全复位" - 移动到安全复位位置（推荐）

## 📁 配置文件位置

复位位置配置保存在：
```
~/.cache/xlerobot_web/reset_positions.json
```

### 配置文件格式

```json
{
  "left_arm": {
    "shoulder_pan": 0.0,
    "shoulder_lift": 35.0,
    "elbow_flex": 50.0,
    "wrist_flex": -85.0,
    "wrist_roll": 0.0,
    "gripper": 50.0
  },
  "right_arm": {
    "shoulder_pan": 0.0,
    "shoulder_lift": 35.0,
    "elbow_flex": 50.0,
    "wrist_flex": -85.0,
    "wrist_roll": 0.0,
    "gripper": 50.0
  }
}
```

### 手动编辑配置文件

你也可以直接编辑配置文件：

```bash
# 查看当前配置
cat ~/.cache/xlerobot_web/reset_positions.json

# 编辑配置
nano ~/.cache/xlerobot_web/reset_positions.json
```

编辑后，重启后端服务即可生效。

## 🔧 API 接口

如果需要通过程序控制，可以使用以下 API：

### 1. 记录当前位置为复位位置
```bash
POST /api/robot/record_reset_position
Content-Type: application/json

{
  "arm": "both"  # "left", "right", 或 "both"
}
```

### 2. 移动到复位位置
```bash
POST /api/robot/move_to_reset
Content-Type: application/json

{
  "arm": "both"  # "left", "right", 或 "both"
}
```

### 3. 获取当前复位位置
```bash
GET /api/robot/reset_positions
```

响应：
```json
{
  "status": "success",
  "reset_positions": {
    "left_arm": { ... },
    "right_arm": { ... }
  }
}
```

## 🛡️ 安全建议

### ⚠️ 设置复位位置时

1. **确保周围无障碍物**
   - 机械臂移动路径上不应有障碍物
   - 留出足够的安全距离

2. **逐步调整**
   - 从零位开始，逐步调整每个关节
   - 每次调整后观察机械臂稳定性

3. **测试断电情况**（可选，需谨慎）
   - 在安全环境下，可以测试断电时机械臂的表现
   - 确保前臂不会快速掉落

4. **记录多个预设位置**
   - 可以为不同的应用场景设置不同的复位位置
   - 当前版本支持一个复位位置，未来可扩展

### 🔥 使用时注意事项

1. **断电前使用复位**
   - 在关闭机器人电源前，先点击"安全复位"
   - 等待机械臂移动到位后再断电

2. **紧急情况**
   - 如果机械臂处于危险姿态，立即使用"安全复位"
   - 复位过程是平滑的，不会突然移动

3. **定期检查**
   - 定期检查复位位置是否仍然合适
   - 根据机械臂磨损情况调整

## 📊 技术实现

### 后端

- **配置管理**：`backend/robot_controller.py`
  - `_load_reset_positions()` - 加载配置
  - `_save_reset_positions()` - 保存配置
  - `record_current_position_as_reset()` - 记录当前位置
  - `move_to_reset_position()` - 移动到复位位置

- **API 端点**：`backend/main.py`
  - `POST /api/robot/record_reset_position`
  - `POST /api/robot/move_to_reset`
  - `GET /api/robot/reset_positions`

### 前端

- **校准页面**：`frontend/src/components/DeviceSetup.tsx`
  - 复位位置设置 UI
  - 操作指南和安全提示

- **控制页面**：`frontend/src/components/TeleopControl.tsx`
  - "安全复位" 快捷按钮
  - 一键快速复位功能

- **API 客户端**：`frontend/src/api/client.ts`
  - `robotApi.recordResetPosition()`
  - `robotApi.moveToResetPosition()`
  - `robotApi.getResetPositions()`

## ❓ 常见问题

### Q1: 复位位置丢失了怎么办？

**A**: 配置文件保存在 `~/.cache/xlerobot_web/reset_positions.json`。如果文件丢失：
1. 系统会自动使用默认零位
2. 你需要重新设置复位位置

**建议**：定期备份配置文件：
```bash
cp ~/.cache/xlerobot_web/reset_positions.json ~/reset_positions_backup.json
```

### Q2: 可以为左右臂设置不同的复位位置吗？

**A**: 可以。在记录复位位置时：
- 选择 `arm="left"` 只记录左臂
- 选择 `arm="right"` 只记录右臂
- 选择 `arm="both"` 记录两个臂

### Q3: 复位过程太慢/太快？

**A**: 复位速度由 P 控制的 `kp` 参数控制：
- 当前默认 `kp=0.81`
- 如需调整，修改 `robot_controller.py` 中的 `ArmState` 类

### Q4: 复位位置不够稳定？

**A**: 重新调整并记录更稳定的位置：
1. 增大 `shoulder_lift` 和 `elbow_flex` 角度
2. 确保机械臂质心在支撑范围内
3. 测试不同姿态，选择最稳定的

### Q5: 如何恢复到默认设置？

**A**: 删除配置文件：
```bash
rm ~/.cache/xlerobot_web/reset_positions.json
```

重启后端服务，系统会使用默认零位。

## 📝 更新日志

- **2026-01-02**: 初始版本发布
  - 添加自定义复位位置功能
  - 支持左臂、右臂独立设置
  - Web UI 集成

## 🔗 相关文档

- `STATUS.md` - 项目状态和功能列表
- `QUICK_TEST.md` - 快速测试指南
- `START_HERE.md` - 快速开始
- `ROBOT_CONNECTION_TEST.md` - 机器人连接测试

---

**安全第一！** 在设置和使用复位位置时，始终将安全放在首位。

