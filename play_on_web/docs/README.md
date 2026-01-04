# 📚 文档索引

本目录包含项目的所有技术文档和指南。

## 📖 主要文档（项目根目录）

| 文档 | 说明 | 受众 |
|------|------|------|
| [README.md](../README.md) | 项目主文档 | 所有人 |
| [CURSOR.md](../CURSOR.md) | AI 助手指南 | AI/开发者 |
| [QUICKSTART.md](../QUICKSTART.md) | 快速开始 | 新用户 |
| [STATUS.md](../STATUS.md) | 项目状态 | 所有人 |

## 🎮 用户指南 (guides/)

| 文档 | 说明 | 重要性 |
|------|------|--------|
| [SAFE_RESET_POSITION_GUIDE.md](guides/SAFE_RESET_POSITION_GUIDE.md) | 安全复位位置使用指南 | ⭐⭐⭐⭐⭐ |
| [BASE_CONTROL_USAGE.md](guides/BASE_CONTROL_USAGE.md) | 底盘控制详细说明 | ⭐⭐⭐⭐ |

## 🔧 技术修复 (fixes/)

记录重要的技术问题和解决方案。

| 文档 | 问题 | 状态 |
|------|------|------|
| [SMOOTH_CONTROL_FIX.md](fixes/SMOOTH_CONTROL_FIX.md) | 机械臂运动抖动 | ✅ 已修复 |
| [BASE_CONTROL_FIX.md](fixes/BASE_CONTROL_FIX.md) | 底盘松开不停止 | ✅ 已修复 |
| [IK_CONTROL_EXPLANATION.md](fixes/IK_CONTROL_EXPLANATION.md) | IK 控制原理和多关节联动 | ✅ 已说明 |
| [SAFE_RESET_FEATURE_SUMMARY.md](fixes/SAFE_RESET_FEATURE_SUMMARY.md) | 安全复位功能实现 | ✅ 已实现 |
| [ROBOT_CONNECTION_TEST.md](fixes/ROBOT_CONNECTION_TEST.md) | 机器人连接测试 | ✅ 已解决 |

## 🛠️ 开发文档

| 文档 | 说明 | 重要性 |
|------|------|--------|
| [SETUP_CONDA.md](SETUP_CONDA.md) | Conda 环境配置详解 | ⭐⭐⭐⭐⭐ |
| [CHECKLIST.md](CHECKLIST.md) | 功能检查清单 | ⭐⭐⭐⭐ |
| [STRUCTURE.md](STRUCTURE.md) | 项目结构说明 | ⭐⭐⭐ |
| [CHANGES.md](CHANGES.md) | 更新日志 | ⭐⭐⭐ |

## 📦 平台特定文档

### Backend
- [backend/MACOS_PORTS.md](../backend/MACOS_PORTS.md) - macOS 串口设备处理
- [backend/README.md](../backend/README.md) - 后端说明

### Frontend
- [frontend/PORT_DETECTION_GUIDE.md](../frontend/PORT_DETECTION_GUIDE.md) - 端口检测指南
- [frontend/README.md](../frontend/README.md) - 前端说明

## 📂 历史文档 (archives/)

不再活跃但保留参考的文档。

| 文档 | 说明 |
|------|------|
| [CAMERA_OPTIONAL_FIX.md](archives/CAMERA_OPTIONAL_FIX.md) | 相机可选配置修复 |
| [FIX_SUMMARY_20260102.md](archives/FIX_SUMMARY_20260102.md) | 2026-01-02 修复总结 |
| [CONDA_SETUP_SUMMARY.md](archives/CONDA_SETUP_SUMMARY.md) | Conda 设置摘要 |
| [START_HERE.md](archives/START_HERE.md) | 旧的开始指南 |
| [GET_STARTED.md](archives/GET_STARTED.md) | 旧的快速开始 |
| [INDEX.md](archives/INDEX.md) | 旧的索引 |
| [QUICK_TEST.md](archives/QUICK_TEST.md) | 快速测试指南 |
| [TEST_GUIDE.md](archives/TEST_GUIDE.md) | 测试指南 |

## 📋 文档使用建议

### 👤 对于新用户
1. 从 [README.md](../README.md) 开始了解项目
2. 按照 [QUICKSTART.md](../QUICKSTART.md) 快速开始
3. 查看 [STATUS.md](../STATUS.md) 了解当前功能
4. 需要时参考 `guides/` 目录下的用户指南

### 👨‍💻 对于开发者
1. 阅读 [CURSOR.md](../CURSOR.md) 了解技术要点
2. 配置环境：[SETUP_CONDA.md](SETUP_CONDA.md)
3. 理解架构：[STRUCTURE.md](STRUCTURE.md)
4. 查看修复记录：`fixes/` 目录
5. 使用检查清单：[CHECKLIST.md](CHECKLIST.md)

### 🤖 对于 AI 助手
1. **必读**: [CURSOR.md](../CURSOR.md) - 包含所有关键技术要点
2. **参考**: `fixes/` 目录 - 了解已解决的问题和正确做法
3. **警告**: 文档中标记 ⚠️ 的配置不要随意修改

## 🔍 查找文档

### 按主题查找

**设备配置**:
- [QUICKSTART.md](../QUICKSTART.md) - 设备设置步骤
- [frontend/PORT_DETECTION_GUIDE.md](../frontend/PORT_DETECTION_GUIDE.md) - 端口检测
- [backend/MACOS_PORTS.md](../backend/MACOS_PORTS.md) - macOS 串口

**控制问题**:
- [fixes/SMOOTH_CONTROL_FIX.md](fixes/SMOOTH_CONTROL_FIX.md) - 运动平滑性
- [fixes/BASE_CONTROL_FIX.md](fixes/BASE_CONTROL_FIX.md) - 底盘控制
- [fixes/IK_CONTROL_EXPLANATION.md](fixes/IK_CONTROL_EXPLANATION.md) - IK 原理

**安全和复位**:
- [guides/SAFE_RESET_POSITION_GUIDE.md](guides/SAFE_RESET_POSITION_GUIDE.md) - 安全复位
- [fixes/SAFE_RESET_FEATURE_SUMMARY.md](fixes/SAFE_RESET_FEATURE_SUMMARY.md) - 技术实现

**环境配置**:
- [SETUP_CONDA.md](SETUP_CONDA.md) - Conda 环境
- [CHANGES.md](CHANGES.md) - 环境配置变更历史

## 📊 文档统计

- **核心文档**: 4 个（根目录）
- **用户指南**: 2 个
- **技术修复**: 5 个
- **开发文档**: 4 个
- **历史文档**: 8 个
- **平台文档**: 4 个

**总计**: 27 个文档

## 🔄 文档维护

### 更新优先级

1. **必须更新**: 核心文档（README, CURSOR, STATUS）
2. **建议更新**: 用户指南和技术修复文档
3. **可选更新**: 开发文档和历史文档

### 添加新文档

根据内容类型放置到对应目录：
- **用户指南** → `guides/`
- **技术修复** → `fixes/`
- **开发文档** → `docs/`（根）
- **过时文档** → `archives/`

### 文档规范

- 使用清晰的标题和结构
- 包含示例和代码片段
- 标注重要性（⭐）和状态（✅❌🚧）
- 添加"最后更新"日期

---

**最后更新**: 2026-01-02  
**维护**: 与代码同步更新

