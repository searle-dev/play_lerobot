# 🚀 立即开始使用

3 步开始使用 XLerobot Web Teleop！

## 📋 你需要什么

- ✅ 已配置的 `lerobot` conda 环境
- ✅ Node.js 16+
- ✅ XLerobot 机械臂小车硬件

## 🎯 3 步启动

### Step 1: 验证环境 ✅

```bash
cd /Users/ai/Project/play_lerobot/play_on_web
./verify_setup.sh
```

如果看到"✅ 所有依赖检查通过"，继续下一步。

### Step 2: 启动服务 🚀

```bash
./start_conda.sh
```

等待几秒，直到看到：
- ✅ 后端服务: `http://localhost:8000`
- ✅ 前端服务: `http://localhost:3000`

### Step 3: 打开浏览器 🌐

访问: `http://localhost:3000`

## 🎮 开始遥操作

### 1️⃣ 配置串口

![串口配置](https://via.placeholder.com/600x300/3b82f6/ffffff?text=Port+Configuration)

两种方式：
- **自动检测**: 点击"自动检测" → 拔USB → 点击"完成检测"
- **手动选择**: 从下拉菜单选择

### 2️⃣ 配置相机（可选）

![相机配置](https://via.placeholder.com/600x300/10b981/ffffff?text=Camera+Configuration)

为左手腕、右手腕、头部分配相机。

### 3️⃣ 校准

![校准](https://via.placeholder.com/600x300/f59e0b/ffffff?text=Calibration)

点击"开始遥操作"，机器人移动到安全零位。

### 4️⃣ 遥操作！

![遥操作](https://via.placeholder.com/600x300/ef4444/ffffff?text=Teleoperation)

**键盘控制:**
- 左臂: `Q` `W` `E` `R` `A` `S` `D` `F` `Z` `X` `C` `T` `G`
- 右臂: 数字键盘
- 底盘: `I` `J` `K` `L` `U` `O`

**Xbox 手柄:**
- 左摇杆 → 左臂
- 右摇杆 → 右臂
- 扳机 → 夹爪
- D-Pad → 底盘

## 💡 快速提示

| 功能 | 操作 |
|-----|------|
| 切换控制模式 | 点击顶部"键盘/Xbox"按钮 |
| 左臂归零 | 按 `C` 或点击"左臂归零" |
| 右臂归零 | 按 `0` 或点击"右臂归零" |
| 全部归零 | 点击"全部归零" |
| 查看多机位 | 点击"全部"标签 |
| 返回设置 | 点击"← 返回设置" |

## 🐛 遇到问题？

### 服务无法启动
```bash
# 检查环境
./verify_setup.sh

# 重新安装依赖
conda activate lerobot
pip install -r backend/requirements.txt
```

### 无法连接机器人
1. 检查 USB 连接
2. 确认机器人已通电
3. 验证串口选择正确

### 相机无法显示
1. 刷新浏览器
2. 检查相机权限
3. 重新配置相机

### 更多帮助
- 📖 完整文档: `README.md`
- 🐍 Conda 配置: `SETUP_CONDA.md`
- ✅ 功能检查: `CHECKLIST.md`

## 🎓 进阶使用

### 调整控制参数

编辑 `backend/robot_controller.py`:
```python
degree_step: float = 3.0    # 角度步进
xy_step: float = 0.0081     # XY 步进
kp: float = 0.81            # P 控制增益
```

### 自定义键位

编辑 `frontend/src/components/KeyboardControl.tsx`

### 查看 API

访问 `http://localhost:8000/docs`

## ✨ 特性预览

- ⌨️ **双模式控制** - 键盘和 Xbox 手柄自由切换
- 📹 **多机位视频** - 同时查看多个相机画面
- 📊 **实时状态** - 所有关节角度实时显示
- 🎯 **精确控制** - XY 平面逆运动学控制
- 🛡️ **安全保护** - 一键归零紧急停止

## 🎉 开始享受

现在您已经准备好了！

```bash
# 启动服务
./start_conda.sh

# 打开浏览器
open http://localhost:3000
```

**祝您遥操作愉快！** 🤖✨

---

**需要更多帮助？** 查看完整文档或运行 `./verify_setup.sh` 检查环境。

