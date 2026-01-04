# XLerobot Web Teleop - 前端

基于 React + TypeScript 的 XLerobot 机械臂小车网页遥操作前端。

## 功能特性

- 📱 **现代化 UI**: 精美的用户界面和流畅的交互体验
- 🎮 **多种控制**: 支持键盘和 Xbox 手柄
- 📹 **视频流**: 实时多机位视频显示
- 📊 **状态监控**: 实时机器人状态反馈
- 🔧 **设备配置**: 引导式设备配置流程

## 技术栈

- React 18
- TypeScript
- Vite
- Zustand (状态管理)
- Axios (HTTP 客户端)
- WebSocket (实时通信)

## 开发

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 项目结构

```
src/
├── components/         # React 组件
│   ├── DeviceSetup.tsx      # 设备配置向导
│   ├── TeleopControl.tsx    # 遥操作主界面
│   ├── KeyboardControl.tsx  # 键盘控制面板
│   ├── XboxControl.tsx      # Xbox 手柄控制
│   ├── CameraView.tsx       # 相机视图组件
│   └── RobotStatus.tsx      # 机器人状态显示
├── stores/            # Zustand 状态管理
│   └── robotStore.ts        # 机器人状态 store
├── api/              # API 客户端
│   └── client.ts            # HTTP 和 WebSocket 客户端
├── App.tsx           # 主应用组件
├── main.tsx          # 应用入口
└── index.css         # 全局样式
```

## 组件说明

### DeviceSetup
设备配置向导，包含三个步骤：
1. 串口配置
2. 相机配置
3. 校准和初始化

### TeleopControl
遥操作主控制界面，包含：
- 控制模式切换（键盘/Xbox）
- 归零按钮
- 相机视图
- 控制面板
- 状态侧边栏

### KeyboardControl
键盘控制面板，显示：
- 左臂控制键位
- 右臂控制键位
- 底盘控制键位
- 实时按键状态

### XboxControl
Xbox 手柄控制面板，显示：
- 手柄连接状态
- 摇杆位置可视化
- 按钮状态
- 控制映射说明

### CameraView
相机视图组件，支持：
- 多机位网格显示
- 单机位全屏显示
- 相机切换
- 实时视频流

### RobotStatus
机器人状态显示，包含：
- 左臂关节角度
- 右臂关节角度
- 头部电机位置
- 实时更新

## 状态管理

使用 Zustand 进行轻量级状态管理：

```typescript
interface RobotStore {
  isConnected: boolean         // 连接状态
  availablePorts: string[]     // 可用串口
  availableCameras: Camera[]   // 可用相机
  robotConfig: RobotConfig     // 机器人配置
  observation: RobotObservation // 实时观测值
  teleopWs: WebSocket | null   // 遥操作 WebSocket
  cameraWs: WebSocket | null   // 相机 WebSocket
  controlMode: 'keyboard' | 'xbox' // 控制模式
}
```

## API 通信

### HTTP API
使用 Axios 进行 HTTP 请求：
- 设备扫描
- 机器人连接/断开
- 相机管理

### WebSocket
实时双向通信：
- `/ws/teleop`: 遥操作控制和状态反馈
- `/ws/camera`: 视频流传输

## 样式设计

### 设计系统
- 主题色：蓝色系
- 圆角：8px
- 阴影：分层阴影系统
- 字体：系统默认字体栈

### 响应式设计
- 桌面优先
- 支持平板和手机
- 弹性网格布局
- 自适应组件

## 开发规范

### 代码风格
- TypeScript 严格模式
- ESLint + TypeScript ESLint
- 函数式组件 + Hooks
- Props 类型定义

### 命名规范
- 组件：PascalCase
- 文件：PascalCase.tsx
- 样式：PascalCase.css
- 函数：camelCase
- 常量：UPPER_SNAKE_CASE

### 组件结构
```typescript
// 1. 导入
import { useState } from 'react'
import './Component.css'

// 2. 类型定义
interface ComponentProps {
  prop1: string
}

// 3. 组件定义
function Component({ prop1 }: ComponentProps) {
  // 4. 状态和副作用
  const [state, setState] = useState()
  
  // 5. 事件处理
  const handleEvent = () => {}
  
  // 6. 渲染
  return <div>...</div>
}

// 7. 导出
export default Component
```

## 性能优化

- 使用 React.memo 避免不必要的重渲染
- WebSocket 消息节流
- 图像压缩传输
- 懒加载组件
- 代码分割

## 浏览器兼容性

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

注意：Xbox 手柄功能需要支持 Gamepad API 的浏览器。

## 故障排除

### WebSocket 连接失败
1. 检查后端服务是否运行
2. 确认代理配置正确
3. 查看浏览器控制台错误

### 视频流卡顿
1. 降低视频质量
2. 减少同时显示的相机数量
3. 检查网络带宽

### 手柄无响应
1. 确认手柄已连接
2. 按任意键激活
3. 使用 Chrome/Edge 浏览器

## 调试技巧

### React DevTools
安装 React DevTools 浏览器扩展查看组件树和状态。

### 网络调试
使用浏览器开发者工具的 Network 标签查看 WebSocket 消息。

### 日志输出
关键操作都有 console.log 输出，便于调试。

---

Happy Coding! 🚀

