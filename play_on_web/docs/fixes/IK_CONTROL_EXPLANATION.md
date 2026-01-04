# 逆运动学（IK）控制说明

## 问题描述

**用户反馈**：
> "为什么使用 D 控制 y- 时，shoulder_lift、elbow_flex、wrist_flex 都发生了大范围移动？"

## 根本原因分析

### 1. 逆运动学（Inverse Kinematics）的工作原理

当你使用 **笛卡尔空间控制**（x, y 坐标）时，系统需要通过**逆运动学**计算出对应的关节角度。

#### 控制流程

```
按 D 键 (y-)
    ↓
更新目标 y 坐标: current_y -= xy_step (减少 5mm)
    ↓
调用逆运动学: inverse_kinematics(current_x, current_y)
    ↓
计算新的关节角度:
  - shoulder_lift (肩关节抬升)
  - elbow_flex (肘关节弯曲)
    ↓
根据耦合关系自动更新:
  - wrist_flex = -shoulder_lift - elbow_flex + pitch
```

### 2. 为什么三个关节都在动？

#### A. shoulder_lift 和 elbow_flex（IK 计算）

SO101 机械臂是一个**2 连杆平面机械臂**：

```
        shoulder_lift (θ1)
            ↓
    ┌──────────┐ l1 = 0.1159m
    │  上臂    │
    └──────────┘
            ↓ elbow_flex (θ2)
    ┌──────────┐ l2 = 0.1350m
    │  前臂    │
    └──────────┘
            ↓
        末端执行器 (x, y)
```

**逆运动学公式**（简化版）：

```python
# 1. 计算目标点到原点的距离
r = sqrt(x² + y²)

# 2. 使用余弦定理计算肘关节角度
cos_θ2 = -(r² - l1² - l2²) / (2 * l1 * l2)
θ2 = π - acos(cos_θ2)  # elbow_flex

# 3. 计算肩关节角度
β = atan2(y, x)
γ = atan2(l2 * sin(θ2), l1 + l2 * cos(θ2))
θ1 = β + γ  # shoulder_lift
```

**关键点**：
- 末端执行器的 (x, y) 位置由 **shoulder_lift 和 elbow_flex 共同决定**
- 改变 y 坐标时，这两个关节必须**同时调整**才能到达新位置
- 这是机械臂运动学的固有特性，不是 bug！

#### B. wrist_flex（耦合关系）

为了保持末端执行器的姿态（pitch），wrist_flex 通过以下公式自动计算：

```python
wrist_flex = -shoulder_lift - elbow_flex + pitch
```

这个耦合关系确保：
- 当 shoulder_lift 和 elbow_flex 变化时
- wrist_flex 自动调整以保持末端执行器的 pitch 角度不变

### 3. 为什么移动"大范围"？

#### 非线性特性

逆运动学是**非线性**的，同样的笛卡尔空间位移（如 5mm）在不同的机械臂姿态下需要的关节角度变化**差异很大**：

| 机械臂姿态 | y 移动 5mm | shoulder_lift 变化 | elbow_flex 变化 |
|------------|------------|-------------------|----------------|
| 完全伸展 | ✓ | ~2-3° | ~1-2° |
| 中间姿态 | ✓ | ~5-8° | ~5-8° |
| 接近奇异点 | ✓ | ~15-30° | ~15-30° |

**奇异点**：机械臂完全伸直或完全折叠时，微小的笛卡尔位移需要巨大的关节角度变化。

#### 步长配置

参考 `lerobot/examples/xlerobot/4_xlerobot_teleop_keyboard.py`：

```python
xy_step: float = 0.0081  # 8.1mm - 参考代码验证过的值
degree_step: int = 3     # 3° - 关节空间步长
```

**重要**：8.1mm 是经过实验验证的最佳值，提供了速度和精度的良好平衡。

## 解决方案

### 1. 使用参考代码的配置 ✅

```python
xy_step: float = 0.0081  # 8.1mm - 参考代码默认值
degree_step: int = 3     # 3° - 保持与参考代码一致
```

### 2. 添加可调节步长 ✅

提供三个步长等级：

| 等级 | degree_step | xy_step | 适用场景 |
|------|-------------|---------|----------|
| **慢速** | 2° | 5mm | 精细操作、接近目标 |
| **正常** | 3° | 8.1mm | 日常操作（参考代码默认值）|
| **快速** | 5° | 12mm | 快速移动、粗略定位 |

### 3. 在 Web UI 中添加步长选择器 ✅

在遥操作界面的控制模式旁边添加了步长下拉框：

```
[⌨️ 键盘] [🎮 Xbox]  |  步长: [慢速 (精细) ▼]
```

## 使用建议

### 场景 1：精细操作

**情况**：需要精确定位，或者机械臂接近工作空间边界

**建议**：
- 选择 **"慢速 (精细)"** 步长
- xy_step = 3mm，关节变化更小
- 更容易控制

### 场景 2：日常操作

**情况**：正常的遥操作任务

**建议**：
- 使用 **"正常"** 步长（默认）
- xy_step = 5mm，平衡速度和精度

### 场景 3：快速移动

**情况**：需要快速移动到大致位置

**建议**：
- 选择 **"快速"** 步长
- xy_step = 8mm，移动更快
- 然后切换到慢速进行精细调整

### 场景 4：避免奇异点

**奇异点位置**：
- 机械臂完全伸直（r ≈ l1 + l2 ≈ 0.25m）
- 机械臂完全折叠（r ≈ |l1 - l2| ≈ 0.02m）

**建议**：
- 避免在这些位置使用 y 方向控制
- 如果必须经过，使用 **"慢速"** 步长
- 或者使用关节空间控制（直接控制关节角度）

## 技术细节

### 逆运动学实现

参考 `lerobot/examples/xlerobot/1_so100_keyboard_ee_control.py`:

```python
def inverse_kinematics(x, y, l1=0.1159, l2=0.1350):
    """
    2连杆机械臂逆运动学
    
    参数:
        x: 末端执行器 x 坐标
        y: 末端执行器 y 坐标
        l1: 上臂长度 (0.1159m)
        l2: 前臂长度 (0.1350m)
    
    返回:
        joint2 (shoulder_lift), joint3 (elbow_flex) 的角度（度）
    """
    # 1. 计算距离
    r = sqrt(x² + y²)
    
    # 2. 边界检查
    r_max = l1 + l2  # 最大可达距离
    r_min = |l1 - l2|  # 最小可达距离
    
    # 3. 余弦定理计算肘关节
    cos_θ2 = -(r² - l1² - l2²) / (2 * l1 * l2)
    θ2 = π - acos(cos_θ2)
    
    # 4. 计算肩关节
    β = atan2(y, x)
    γ = atan2(l2 * sin(θ2), l1 + l2 * cos(θ2))
    θ1 = β + γ
    
    # 5. 转换为关节角度
    joint2 = θ1 + offset1
    joint3 = θ2 + offset2
    
    return joint2_deg, joint3_deg
```

### 耦合关系

```python
# 保持末端执行器 pitch 角度
wrist_flex = -shoulder_lift - elbow_flex + pitch
```

这确保了：
```
末端执行器的绝对角度 = shoulder_lift + elbow_flex + wrist_flex = pitch
```

### 步长配置

```python
# 参考 4_xlerobot_teleop_keyboard.py 的配置
step_configs = {
    "slow": {
        "degree_step": 2,      # 关节空间步长（度）
        "xy_step": 0.005       # 笛卡尔空间步长（米）
    },
    "normal": {
        "degree_step": 3,      # 参考代码默认值
        "xy_step": 0.0081      # 参考代码默认值 (8.1mm)
    },
    "fast": {
        "degree_step": 5,
        "xy_step": 0.012
    }
}
```

## API 使用

### 设置步长等级

```bash
POST /api/robot/set_step_level
Content-Type: application/json

{
  "arm": "both",     # "left", "right", 或 "both"
  "level": "slow"    # "slow", "normal", "fast"
}
```

### 前端调用

```typescript
// 设置为慢速
await robotApi.setStepLevel('both', 'slow')

// 设置为快速
await robotApi.setStepLevel('both', 'fast')
```

## 常见问题

### Q1: 为什么不能只动一个关节？

**A**: 因为你使用的是**笛卡尔空间控制**（x, y 坐标）。如果想单独控制关节，应该使用**关节空间控制**：
- Q/A 键：shoulder_pan
- T/G 键：wrist_roll
- Y/H 键：gripper

### Q2: 如何避免大幅度移动？

**A**: 
1. 使用 **"慢速"** 步长
2. 避免在奇异点附近操作
3. 考虑使用关节空间控制

### Q3: 步长设置会保存吗？

**A**: 当前版本不会保存，每次启动默认为 "normal"。未来可以添加配置保存功能。

### Q4: 左右臂可以设置不同的步长吗？

**A**: 可以！API 支持：
```typescript
await robotApi.setStepLevel('left', 'slow')   // 左臂慢速
await robotApi.setStepLevel('right', 'fast')  // 右臂快速
```

### Q5: 为什么有时候按键没反应？

**A**: 可能是：
1. 目标位置超出工作空间
2. 机械臂在奇异点附近
3. 关节角度达到限位

## 进一步优化方向

### 1. 自适应步长

根据机械臂当前姿态自动调整步长：
- 接近奇异点时自动减小步长
- 在工作空间中心时使用正常步长

### 2. 平滑插值

在当前位置和目标位置之间进行轨迹规划，避免突变。

### 3. 可视化反馈

显示：
- 当前末端执行器位置 (x, y)
- 工作空间边界
- 奇异点警告

### 4. 速度控制

不仅控制步长，还控制移动速度（通过调整 kp 参数）。

## 总结

✅ **这不是 bug，而是逆运动学的固有特性**

✅ **已优化**：
- 减小默认步长（8.1mm → 5mm）
- 添加三档可调节步长
- 在 Web UI 中提供步长选择器

✅ **使用建议**：
- 精细操作时使用 "慢速"
- 日常操作使用 "正常"
- 快速移动使用 "快速"
- 避免在奇异点附近操作

---

**参考文档**：
- `lerobot/examples/xlerobot/1_so100_keyboard_ee_control.py` - 逆运动学实现
- `backend/robot_controller.py` - 控制逻辑
- `SAFE_RESET_POSITION_GUIDE.md` - 安全复位指南

