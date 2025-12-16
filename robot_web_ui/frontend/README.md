# LeRobot 机械臂调试平台 - 前端

基于 React + TypeScript + Ant Design 的现代化Web应用。

## 功能特性

- 🤖 机械臂管理（添加、连接、断开、删除）
- 📊 实时状态监控
- ⚙️ 交互式校准向导（WebSocket）
- 🎮 实时控制面板
- 📹 动作录制和回放
- 🔌 端口扫描和识别

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 库**: Ant Design 5
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **实时通信**: WebSocket

## 项目结构

```
frontend/
├── src/
│   ├── components/      # React 组件
│   ├── pages/           # 页面组件
│   ├── store/           # Zustand 状态管理
│   ├── services/        # API 服务层
│   ├── hooks/           # 自定义 Hooks
│   ├── types/           # TypeScript 类型
│   ├── App.tsx          # 根组件
│   └── main.tsx         # 入口文件
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

## API 配置

默认连接到 `http://localhost:8000`

修改 `src/services/api.ts` 更改后端地址：

```typescript
export const api = axios.create({
  baseURL: 'http://localhost:8000',  // 修改这里
  timeout: 10000,
});
```

## 开发说明

### 状态管理

使用 Zustand 进行全局状态管理：

```typescript
import { useRobotStore } from './store/robotStore';

const { robots, fetchRobots } = useRobotStore();
```

### WebSocket Hook

```typescript
import { useWebSocket } from './hooks/useWebSocket';

const { sendMessage, lastMessage } = useWebSocket(
  'ws://localhost:8000/ws/control/robot1'
);
```

### API 调用

```typescript
import { robotApi } from './services/robotApi';

await robotApi.connectRobot('robot1');
```

## 扩展开发

### 添加新页面

1. 在 `src/pages/` 创建新组件
2. 在 `App.tsx` 中引入和使用

### 添加新 API

1. 在 `src/services/` 添加 API 函数
2. 在组件中使用

## 浏览器兼容性

- Chrome/Edge ≥ 90
- Firefox ≥ 88
- Safari ≥ 14

## 许可证

MIT
