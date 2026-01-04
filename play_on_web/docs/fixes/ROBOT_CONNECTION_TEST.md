# 机器人连接测试指南

本文档说明如何测试最新修复的机器人连接问题。

## 修复的问题

### 1. 交互式输入问题
- **问题描述**: 连接机器人时出现 `EOF when reading a line` 错误
- **根本原因**: XLerobot.connect() 包含交互式校准提示，在后台服务中无法处理
- **解决方案**: 使用 monkey patch 自动选择恢复校准文件选项

### 2. RealSense 相机扫描错误
- **问题描述**: 扫描相机时出现 `name 'rs' is not defined` 错误
- **根本原因**: pyrealsense2 库未安装或导入失败
- **解决方案**: 添加 pyrealsense2 可用性检查，如果不可用则跳过 RealSense 扫描

## 测试步骤

### 准备工作

1. **确保后端服务已停止**
   ```bash
   # 如果后端正在运行，按 Ctrl+C 停止
   ```

2. **检查校准文件是否存在**
   ```bash
   ls -la ~/.cache/huggingface/lerobot/calibration/robots/xlerobot/
   ```
   
   应该能看到校准文件（例如 `None.json`）。这是自动恢复校准所必需的。

3. **连接硬件**
   - 确保两个串口设备已连接到计算机
   - 确保机器人已上电

### 测试 1: 设备扫描（无需硬件）

1. **启动后端服务**
   ```bash
   cd /Users/ai/Project/play_lerobot/play_on_web
   ./start_conda.sh backend
   ```

2. **启动前端**（在新终端）
   ```bash
   cd /Users/ai/Project/play_lerobot/play_on_web
   ./start_conda.sh frontend
   ```

3. **打开浏览器访问** http://localhost:3000

4. **测试串口扫描**
   - 点击"设备设置"标签
   - 点击"扫描串口"按钮
   - ✅ **预期**: 应该看到可用串口列表（如果有 USB 设备连接）
   - ✅ **预期**: 不应该出现 Python 错误

5. **测试相机扫描**
   - 点击"扫描相机"按钮
   - ✅ **预期**: 应该看到可用相机列表（如果有相机连接）
   - ✅ **预期**: 不应该出现 `rs is not defined` 错误
   - ⚠️ **注意**: 如果 pyrealsense2 未安装，后端日志会显示警告，但不会报错

### 测试 2: 机器人连接（需要硬件）

1. **完成设备设置**
   - 在"设备设置"页面选择或自动检测 串口1 和 串口2
   - 点击"保存配置"

2. **连接机器人**
   - 切换到"机器人控制"标签
   - 点击"连接机器人"按钮
   - ⏳ **等待**: 连接过程可能需要几秒钟

3. **检查结果**
   - ✅ **预期**: 按钮变为"断开连接"
   - ✅ **预期**: 状态显示"已连接"
   - ✅ **预期**: 后端日志显示"机器人连接成功"
   - ❌ **不应该**: 出现 `EOF when reading a line` 错误

4. **查看后端日志**
   应该看到类似以下的日志：
   ```
   INFO - Calibration file found at /Users/ai/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json
   INFO - Attempting to restore calibration from file...
   INFO - Calibration data loaded into bus memory successfully!
   INFO - Calibration restored successfully from file!
   INFO - 机器人连接成功
   ```

5. **测试基本控制**
   - 点击"移动到零位"按钮
   - ✅ **预期**: 机器人应该移动到零位
   - ✅ **预期**: 不应该出现错误

### 测试 3: 错误处理

1. **测试无校准文件的情况**
   ```bash
   # 临时重命名校准文件
   mv ~/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json \
      ~/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json.bak
   ```

2. **尝试连接**
   - 点击"连接机器人"
   - ✅ **预期**: 应该能够连接（可能会触发自动校准）
   - ⚠️ **注意**: 自动校准可能需要较长时间

3. **恢复校准文件**
   ```bash
   mv ~/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json.bak \
      ~/.cache/huggingface/lerobot/calibration/robots/xlerobot/None.json
   ```

## 常见问题

### Q: 仍然看到 "EOF when reading a line" 错误
**A**: 检查以下内容：
1. 确保使用的是最新版本的 `robot_controller.py`
2. 检查 monkey patch 代码是否正确应用
3. 查看完整的堆栈跟踪以确定错误来源

### Q: 看到 "pyrealsense2 未安装" 警告
**A**: 这是正常的，如果你没有 RealSense 相机。系统会自动跳过 RealSense 扫描。
如果你需要使用 RealSense 相机，请安装：
```bash
conda activate lerobot
pip install pyrealsense2
```

### Q: 机器人连接后无法控制
**A**: 检查：
1. 串口是否正确配置
2. 机器人是否已上电
3. 后端日志中是否有错误信息

## 技术细节

### Monkey Patch 实现

```python
import builtins
original_input = builtins.input
try:
    # 自动返回空字符串，选择"从文件恢复校准"
    builtins.input = lambda *args, **kwargs: ""
    self.robot.connect()
finally:
    # 恢复原始 input 函数
    builtins.input = original_input
```

这个方法的优点：
- ✅ 不需要修改 lerobot 源代码
- ✅ 只影响 connect() 调用期间的 input()
- ✅ 使用 finally 确保总是恢复原始函数
- ✅ 适用于非交互式环境（FastAPI 后台服务）

### RealSense 检查

```python
try:
    import pyrealsense2 as rs
except ImportError:
    logger.warning("pyrealsense2 未安装，跳过 RealSense 相机扫描")
    return all_cameras
```

这个方法的优点：
- ✅ 优雅地处理缺失的依赖
- ✅ 不会中断整体扫描流程
- ✅ 提供清晰的日志信息

## 下一步

如果所有测试通过，你可以：
1. ✅ 开始使用网页进行机器人控制
2. ✅ 配置相机并查看实时视频
3. ✅ 测试键盘和 Xbox 手柄控制

如果遇到问题，请检查：
- 后端日志中的详细错误信息
- 浏览器控制台中的前端错误
- 网络连接状态（WebSocket）

