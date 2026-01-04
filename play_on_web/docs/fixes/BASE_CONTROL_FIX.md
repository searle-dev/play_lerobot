# 底盘控制修复 - 松开按键自动停止

## 问题描述

**用户反馈**：
> "底盘控制时，一旦按了一个按键，需要按别的按键才能停止；我需要按一次按键动一次，长按则保持运动，松开按键则停止运动"

## 问题分析

### 当前行为 ❌

1. 按下底盘控制键（I/K/J/L/U/O）→ 机器人开始运动
2. 松开按键 → 机器人**继续运动**（不会停止）
3. 需要按其他按键才能改变或停止

### 期望行为 ✅

1. **按一次** → 动一次（短按）
2. **长按** → 持续运动（按住期间）
3. **松开** → 立即停止运动

## 根本原因

### 底盘控制使用速度命令

底盘控制与机械臂控制不同：

**机械臂控制**（位置命令）：
```python
# 设置目标位置
target_position = current_position + step
# 机械臂会移动到目标位置，然后停止
```

**底盘控制**（速度命令）：
```python
# 设置速度
{
    "x.vel": 0.2,      # 前进速度 0.2 m/s
    "y.vel": 0.0,
    "theta.vel": 0.0
}
# 机器人会以这个速度持续运动，直到接收到新的速度命令
```

### 参考代码分析

从 `lerobot/src/lerobot/robots/xlerobot/xlerobot.py` (第491-524行)：

```python
def _from_keyboard_to_base_action(self, pressed_keys: np.ndarray):
    x_cmd = 0.0  # 默认速度为 0
    y_cmd = 0.0
    theta_cmd = 0.0
    
    if self.teleop_keys["forward"] in pressed_keys:
        x_cmd += xy_speed  # 有按键 → 设置速度
    if self.teleop_keys["backward"] in pressed_keys:
        x_cmd -= xy_speed
    # ...
    
    return {
        "x.vel": x_cmd,    # 返回速度命令
        "y.vel": y_cmd,
        "theta.vel": theta_cmd,
    }
```

**关键点**：
- 如果 `pressed_keys` 包含按键 → 速度 = xy_speed
- 如果 `pressed_keys` 为空 → 速度 = 0.0

### 我们的实现缺少什么？

**问题**：
1. 前端在 `keydown` 时发送运动命令 ✅
2. 前端在 `keyup` 时**没有发送停止命令** ❌

**结果**：
- 底盘接收到速度命令后，会持续以该速度运动
- 即使按键松开，底盘不知道要停止

## 解决方案

### 实现架构

```
前端 KeyboardControl
    ↓
  keydown → 发送运动命令
    ↓
  keyup → 发送停止命令（新增）
    ↓
后端 WebSocket
    ↓
  base_stop → robot_controller.stop_base()
    ↓
发送速度为 0 的命令到机器人
```

### 1. 后端：添加停止底盘方法

**文件**：`backend/robot_controller.py`

```python
def stop_base(self) -> dict[str, Any]:
    """
    停止底盘运动
    发送速度为 0 的命令
    """
    try:
        if not self._is_connected:
            return {"status": "error", "message": "机器人未连接"}
        
        # 发送速度为 0 的命令
        stop_action = {
            "x.vel": 0.0,
            "y.vel": 0.0,
            "theta.vel": 0.0
        }
        
        self.robot.send_action(stop_action)
        logger.debug("底盘已停止")
        
        return {
            "status": "success",
            "message": "底盘已停止"
        }
    except Exception as e:
        logger.error(f"停止底盘时出错: {e}")
        return {"status": "error", "message": str(e)}
```

### 2. 后端：添加 API 端点

**文件**：`backend/main.py`

```python
@app.post("/api/robot/stop_base")
async def stop_base():
    """停止底盘运动"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.stop_base()
    return result
```

### 3. 后端：WebSocket 消息处理

**文件**：`backend/main.py`

```python
elif message_type == "base_stop":
    # 停止底盘
    if robot_controller:
        result = robot_controller.stop_base()
        await websocket.send_json({
            "type": "action_result",
            "data": result
        })
```

### 4. 前端：API 客户端

**文件**：`frontend/src/api/client.ts`

```typescript
export const robotApi = {
  // ... 其他方法
  stopBase: () => apiClient.post('/robot/stop_base'),
}
```

### 5. 前端：KeyboardControl 组件

**文件**：`frontend/src/components/KeyboardControl.tsx`

#### 添加停止方法

```typescript
const sendBaseStop = () => {
  if (teleopWs && teleopWs.readyState === WebSocket.OPEN) {
    teleopWs.send(JSON.stringify({
      type: 'base_stop'
    }))
  }
}
```

#### 修改 keyup 处理

```typescript
const handleKeyUp = (e: KeyboardEvent) => {
  const key = e.key.toUpperCase()
  setPressedKeys((prev) => {
    const newSet = new Set(prev)
    newSet.delete(key)
    return newSet
  })
  
  // 检查是否是底盘控制键，如果是则发送停止命令
  for (const [, mappedKey] of Object.entries(BASE_KEYMAP)) {
    if (key === mappedKey) {
      sendBaseStop()  // 🎯 关键：松开底盘按键时停止
      e.preventDefault()
      return
    }
  }
}
```

## 工作流程

### 场景 1：短按（按一次动一次）

```
1. 用户按下 I 键
   ↓
2. keydown 事件 → 发送 forward 命令
   ↓
3. 底盘开始前进（速度 = 0.2 m/s）
   ↓
4. 用户松开 I 键（很快）
   ↓
5. keyup 事件 → 发送 stop 命令
   ↓
6. 底盘停止（速度 = 0.0 m/s）

结果：机器人短暂前进后停止 ✅
```

### 场景 2：长按（持续运动）

```
1. 用户按住 I 键
   ↓
2. keydown 事件 → 发送 forward 命令
   ↓
3. 底盘开始前进（速度 = 0.2 m/s）
   ↓
4. （用户持续按住，可能触发多次 keydown）
   ↓
5. 每次 keydown → 重新发送 forward 命令
   ↓
6. 底盘持续前进
   ↓
7. 用户松开 I 键
   ↓
8. keyup 事件 → 发送 stop 命令
   ↓
9. 底盘停止

结果：机器人持续前进，松开后停止 ✅
```

### 场景 3：切换方向

```
1. 用户按住 I 键（前进）
   ↓
2. 底盘前进
   ↓
3. 用户松开 I 键
   ↓
4. keyup → 发送 stop → 底盘停止
   ↓
5. 用户按下 K 键（后退）
   ↓
6. keydown → 发送 backward → 底盘后退
   ↓
7. 用户松开 K 键
   ↓
8. keyup → 发送 stop → 底盘停止

结果：方向切换平滑，每次松开都停止 ✅
```

## 底盘按键映射

```typescript
const BASE_KEYMAP = {
  'forward': 'I',       // 前进
  'backward': 'K',      // 后退
  'left': 'J',          // 左移
  'right': 'L',         // 右移
  'rotate_left': 'U',   // 左转
  'rotate_right': 'O',  // 右转
}
```

所有这些按键在松开时都会触发停止命令。

## 技术细节

### 速度命令 vs 位置命令

| 特性 | 位置命令（机械臂）| 速度命令（底盘）|
|------|-----------------|----------------|
| 命令类型 | `.pos` | `.vel` |
| 行为 | 移动到目标位置后停止 | 以设定速度持续运动 |
| 停止方式 | 自动停止 | 需要发送速度 = 0 |
| 例子 | `shoulder_pan.pos: 10.0` | `x.vel: 0.2` |

### 为什么机械臂不需要停止命令？

机械臂使用 **P 控制 + 目标位置**：

```python
# 每次按键只是更新目标位置
target_position += step

# P 控制会让机械臂平滑移动到目标
error = target_position - current_position
control = kp * error
new_position = current_position + control

# 当到达目标位置时，error → 0，自动停止
```

### 底盘为什么使用速度命令？

底盘是**轮式移动**，适合用速度控制：

1. **连续运动**：底盘通常需要连续移动
2. **实时响应**：速度命令可以实时调整方向
3. **平滑控制**：避免突然的位置跳变

## 测试验证

### 测试 1：短按测试

1. 快速按下并松开 `I` 键
2. **预期**：机器人短暂前进（< 0.5秒）后停止
3. **验证**：机器人是否立即停止

### 测试 2：长按测试

1. 按住 `I` 键 3 秒
2. **预期**：机器人持续前进 3 秒
3. 松开 `I` 键
4. **预期**：机器人立即停止
5. **验证**：停止是否及时

### 测试 3：方向切换

1. 按住 `I` 键 2 秒（前进）
2. 松开，机器人应停止
3. 按住 `K` 键 2 秒（后退）
4. 松开，机器人应停止
5. **验证**：每次切换是否平滑

### 测试 4：旋转控制

1. 按住 `U` 键（左转）
2. **预期**：机器人持续左转
3. 松开
4. **预期**：机器人停止旋转

### 测试 5：组合控制

1. 同时按住 `I` + `J`（前进 + 左移）
2. **预期**：机器人斜向移动
3. 松开一个键
4. **预期**：停止（因为任一底盘键松开都触发停止）

## 潜在改进

### 选项 1：持续状态追踪

当前实现：每次 keydown/keyup 都发送命令

**改进**：持续追踪所有按下的底盘键

```typescript
// 维护底盘按键状态
const [baseKeysPressed, setBaseKeysPressed] = useState<Set<string>>(new Set())

// 定时发送底盘命令（例如 30Hz）
useEffect(() => {
  const interval = setInterval(() => {
    if (baseKeysPressed.size > 0) {
      // 发送当前按键状态对应的速度命令
      sendBaseActionFromKeys(baseKeysPressed)
    } else {
      // 没有按键 → 发送停止
      sendBaseStop()
    }
  }, 33)  // ~30Hz
  
  return () => clearInterval(interval)
}, [baseKeysPressed])
```

**优点**：
- 更精确的控制
- 可以同时处理多个底盘按键

**缺点**：
- 增加网络流量
- 更复杂的实现

### 选项 2：只在必要时停止

当前实现：任何底盘键松开都发送停止

**改进**：追踪多个底盘键，只在所有键都松开时停止

```typescript
// 只在没有任何底盘键被按住时才停止
if (baseKeysPressed.size === 0) {
  sendBaseStop()
}
```

## 常见问题

### Q1: 为什么松开按键后机器人还动了一小段？

**A**: 这是正常的物理惯性。机器人不能瞬间停止，会有短暂的滑行。这是机械系统的固有特性。

### Q2: 可以同时控制前进和旋转吗？

**A**: 理论上可以，但当前实现在松开任一底盘键时都会停止。如果需要组合控制，建议使用"选项 1"的改进方案。

### Q3: 机械臂按键会触发底盘停止吗？

**A**: 不会。代码明确检查是否是底盘控制键（BASE_KEYMAP），只有底盘键才触发停止。

### Q4: 如何紧急停止机器人？

**A**: 
1. 松开所有底盘按键
2. 或按任意底盘键再松开
3. 未来可以添加专门的紧急停止键（如 Space）

## 文件变更摘要

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/robot_controller.py` | 新增方法 | `stop_base()` - 停止底盘 |
| `backend/main.py` | 新增端点 | `POST /api/robot/stop_base` |
| `backend/main.py` | WebSocket | 添加 `base_stop` 消息处理 |
| `frontend/src/api/client.ts` | 新增方法 | `robotApi.stopBase()` |
| `frontend/src/components/KeyboardControl.tsx` | 修改 | 添加 `sendBaseStop()` 方法 |
| `frontend/src/components/KeyboardControl.tsx` | 修改 | keyup 时检查并停止底盘 |

## 总结

✅ **问题已修复**：松开底盘控制键现在会立即停止机器人

✅ **实现方式**：
- 后端：添加 `stop_base()` 方法发送速度为 0 的命令
- 前端：keyup 时检测底盘按键并发送停止命令

✅ **用户体验**：
- 短按：按一次动一次
- 长按：持续运动
- 松开：立即停止

✅ **参考代码一致性**：遵循 lerobot 的速度命令机制

---

**修复日期**: 2026-01-02  
**参考代码**: `lerobot/src/lerobot/robots/xlerobot/xlerobot.py`  
**状态**: ✅ 已实现并编译成功

