# 🧪 测试指南

## ✅ 修复完成

所有 TypeScript 编译错误已修复！

### 修复的问题
1. ✅ `DeviceSetup.tsx` - 类型错误（setAvailablePorts）
2. ✅ `CameraView.tsx` - 未使用的变量（cameraWs）
3. ✅ `client.ts` - import.meta.env 类型错误

## 🚀 如何测试

### 步骤 1: 重启前端服务

```bash
# 停止当前前端服务（Ctrl+C）
cd /Users/ai/Project/play_lerobot/play_on_web/frontend
npm run dev
```

或者完全重启：

```bash
cd /Users/ai/Project/play_lerobot/play_on_web
./start_conda.sh
```

### 步骤 2: 打开浏览器

访问: `http://localhost:3000`

### 步骤 3: 测试串口自动检测

#### 测试串口 1

1. **点击"自动检测"按钮**（串口 1 旁边）
   - 应该看到提示："👉 请拔出 USB 线缆，然后点击'完成检测'"

2. **拔出 USB 设备**
   - 物理拔出一个 USB 串口设备
   - 例如：`/dev/tty.usbmodem5AB01574971`

3. **点击"完成检测"按钮**
   - ✅ 应该自动识别并填充端口
   - ✅ 下拉框中应该显示检测到的端口
   - ✅ 端口应该被自动选中

4. **检查结果**
   - 打开浏览器控制台（F12）
   - 应该看到：`✅ 成功识别端口: /dev/tty.usbmodem...`

5. **重新插入 USB**（可选）
   - 插回 USB 设备

6. **点击"🔄 刷新列表"**（可选）
   - 验证端口仍在列表中

#### 测试串口 2

重复上述步骤，测试串口 2 的自动检测。

### 步骤 4: 测试手动选择

1. **确保两个 USB 都已连接**

2. **点击"🔄 刷新列表"**
   - 应该看到 "选择串口 (2 个可用)"

3. **从下拉菜单手动选择**
   - 串口 1: 选择第一个端口
   - 串口 2: 选择第二个端口

4. **点击"连接机器人"**
   - 测试连接功能

## 🔍 检查点

### 浏览器控制台（F12 → Console）

应该看到：
```
✅ 已加载 2 个串口
✅ 成功识别端口: /dev/tty.usbmodem5A7C1163141
```

不应该看到：
```
❌ TypeError: ...
❌ Uncaught Error: ...
❌ 任何红色错误信息
```

### 后端日志

应该看到：
```
INFO:device_scanner:找到 2 个串口: [...]
INFO:device_scanner:断开前的端口: [...]
INFO:device_scanner:断开后的端口: [...]
INFO:device_scanner:检测到成对的 tty/cu 设备，使用: /dev/tty.xxx
INFO:device_scanner:成功识别端口: /dev/tty.xxx
```

### 前端界面

✅ **正常状态**：
- 页面正常显示
- 可以看到"选择串口"标题
- 可以看到两个串口选择区域
- 可以看到"自动检测"按钮
- 可以看到"🔄 刷新列表"按钮
- 下拉菜单可以正常打开

❌ **白屏状态**（已修复）：
- 页面完全空白
- 浏览器控制台有红色错误
- 无法看到任何内容

## 🐛 如果还有问题

### 问题 1: 仍然白屏

**检查**：
```bash
# 1. 确认前端已重启
ps aux | grep "vite\|npm"

# 2. 查看编译错误
cd /Users/ai/Project/play_lerobot/play_on_web/frontend
npm run build
```

**解决**：
```bash
# 清除缓存并重新安装
rm -rf node_modules dist
npm install
npm run dev
```

### 问题 2: 端口检测不工作

**检查**：
```bash
# 测试后端 API
curl http://localhost:8000/api/devices/ports
```

**解决**：
- 查看后端日志
- 运行 `backend/test_port_detection.py`

### 问题 3: 端口未自动填充

**检查**：
- 打开浏览器控制台
- 查看是否有 JavaScript 错误
- 查看网络请求是否成功

**解决**：
- 点击"🔄 刷新列表"
- 重新进行自动检测

## 📊 测试清单

### 基础功能
- [ ] 页面正常加载（无白屏）
- [ ] 可以看到串口选择界面
- [ ] 可以看到端口数量显示
- [ ] "🔄 刷新列表"按钮可用

### 自动检测功能
- [ ] 点击"自动检测"显示提示
- [ ] 拔出 USB 后点击"完成检测"
- [ ] 端口自动填充到选择框
- [ ] 端口在下拉菜单中可见
- [ ] 端口被自动选中

### 手动选择功能
- [ ] 下拉菜单显示所有端口
- [ ] 可以手动选择端口
- [ ] 刷新按钮更新端口列表

### macOS 特性
- [ ] 只显示 tty.usb* 设备（不重复）
- [ ] 自动识别成对的 tty/cu 设备
- [ ] 返回 tty 版本（不是 cu）

### 错误处理
- [ ] 未拔出 USB 时显示错误提示
- [ ] 拔出多个 USB 时显示错误提示
- [ ] 错误提示可以关闭

## 🎯 预期结果

### 成功场景

```
用户操作：
1. 点击"自动检测" ✅
2. 拔出 USB ✅
3. 点击"完成检测" ✅

系统响应：
1. 后端识别端口 ✅
2. 前端接收结果 ✅
3. 端口添加到列表 ✅
4. 端口自动选中 ✅
5. 界面正常显示 ✅
```

### 之前的问题（已修复）

```
用户操作：
1. 点击"自动检测" ✅
2. 拔出 USB ✅
3. 点击"完成检测" ✅

系统响应：
1. 后端识别端口 ✅
2. 前端接收结果 ✅
3. TypeScript 类型错误 ❌ ← 已修复
4. 页面白屏 ❌ ← 已修复
```

## 💡 调试技巧

### 1. 查看浏览器控制台
```
F12 → Console 标签
查看是否有错误信息
```

### 2. 查看网络请求
```
F12 → Network 标签
查看 API 请求是否成功
```

### 3. 查看后端日志
```
后端终端窗口
查看 device_scanner 的日志
```

### 4. 使用测试脚本
```bash
cd backend
python test_port_detection.py
```

## 📚 相关文档

- **使用指南**: `frontend/PORT_DETECTION_GUIDE.md`
- **macOS 特性**: `backend/MACOS_PORTS.md`
- **项目文档**: `README.md`

---

**现在重启前端服务，应该一切正常了！** 🎉

如有任何问题，查看浏览器控制台和后端日志。

