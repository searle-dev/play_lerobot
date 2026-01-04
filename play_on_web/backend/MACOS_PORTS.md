# macOS 串口设备说明

## 🍎 macOS 串口特性

在 macOS 系统上，每个 USB 串口设备会创建**两个**设备文件：

### 1. TTY 设备 (Terminal)
```
/dev/tty.usbmodem*
```
- **推荐使用**
- 终端设备，会等待载波信号（carrier detect）
- 适合大多数应用场景

### 2. Callout 设备
```
/dev/cu.usbmodem*
```
- 拨出设备，不等待载波信号
- 适合直接通信，无需握手
- 与 tty 设备指向**同一个**物理 USB 设备

## 🔍 示例

当您插入一个 USB 串口设备时，会看到：

```bash
ls /dev/tty.usb* /dev/cu.usb*
/dev/tty.usbmodem5AB01574971    # TTY 设备
/dev/cu.usbmodem5AB01574971     # Callout 设备
```

**注意**：这是**同一个物理设备**！

## 🛠️ 我们的解决方案

### 问题
拔出一个 USB 时，两个设备文件都会消失，导致检测到"两个"端口变化。

### 解决方案

1. **显示端口列表时**：只显示 `tty.*` 设备
   - 避免用户看到重复的设备
   - 推荐使用 tty 版本

2. **自动检测时**：同时扫描 `tty.*` 和 `cu.*`
   - 检测端口变化
   - 识别成对消失的设备
   - 只返回 `tty.*` 版本

3. **代码实现**：
```python
# 检测到成对设备
if tty_name == cu_name:
    # 返回 tty 版本（推荐）
    return tty_device
```

## 📊 对比表格

| 特性 | tty.usb* | cu.usb* |
|-----|----------|---------|
| 类型 | Terminal | Callout |
| 载波检测 | 是 | 否 |
| 推荐使用 | ✅ | 🔄 |
| 物理设备 | 同一个 | 同一个 |

## 🎯 最佳实践

1. **优先使用** `/dev/tty.*` 设备
2. **只在端口列表中显示** tty 设备
3. **自动检测时处理**成对设备消失的情况
4. **用户无需关心**这个细节

## 🐛 常见问题

### Q: 为什么有两个设备？
A: 这是 macOS（和 BSD 系统）的设计，提供了两种不同的访问模式。

### Q: 应该用哪个？
A: 通常使用 `tty.*` 设备，它是推荐的标准接口。

### Q: 两个设备可以同时打开吗？
A: 不可以！它们指向同一个物理设备，同时打开会导致冲突。

### Q: 如何在代码中判断？
A: 看代码：
```python
if '/tty.' in device_path:
    print("这是 TTY 设备")
elif '/cu.' in device_path:
    print("这是 Callout 设备")
```

## 📚 参考资料

- [Apple Developer Documentation - Serial Port](https://developer.apple.com/documentation/)
- [Stack Overflow - Difference between /dev/tty and /dev/cu](https://stackoverflow.com/questions/8632586)

## 💡 对用户的影响

**现在用户体验**：
- ✅ 端口列表中只显示一个设备（不重复）
- ✅ 自动检测正常工作（识别成对设备）
- ✅ 无需了解 tty/cu 区别
- ✅ 选择任一端口都能正常工作

---

**总结**：这是 macOS 的特性，不是 bug！我们的代码已经妥善处理。

