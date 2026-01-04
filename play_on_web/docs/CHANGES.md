# 🔄 更新日志 - Conda 环境支持

## 📅 更新时间
2026-01-01

## 🎯 更新目标
优化项目配置，支持复用已有的 `lerobot` conda 环境，避免重复安装依赖。

## ✨ 主要改进

### 1. 简化依赖管理 ⭐⭐⭐⭐⭐

**backend/requirements.txt** - 精简依赖列表

**修改前**:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0
opencv-python==4.9.0.80    ← 与 lerobot 重复
numpy==1.26.3              ← 与 lerobot 重复
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
```

**修改后**:
```txt
# lerobot 已提供: opencv-python, numpy, pyserial 等
# 只安装 Web 服务额外需要的依赖

fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
```

**好处**:
- ✅ 减少 2 个重复依赖
- ✅ 安装更快
- ✅ 磁盘占用更少
- ✅ 版本冲突风险降低

### 2. 新增 Conda 启动脚本 🚀

**start_conda.sh** - 自动化 Conda 环境启动

```bash
./start_conda.sh
```

**功能**:
- ✅ 自动检测 conda 安装
- ✅ 检查 lerobot 环境是否存在
- ✅ 自动激活 lerobot 环境
- ✅ 安装缺失的依赖
- ✅ 同时启动后端和前端

### 3. 新增环境检查工具 🔍

**backend/check_env.py** - Python 依赖检查脚本

```bash
conda activate lerobot
python backend/check_env.py
```

**检查内容**:
- ✅ lerobot 核心依赖
- ✅ Web 服务依赖
- ✅ 图像处理库
- ✅ 通信库

**输出示例**:
```
✅ lerobot - 已安装
✅ opencv-python - 已安装
✅ numpy - 已安装
✅ fastapi - 已安装
...
总计: 10 项检查
通过: 10 项 ✅
```

**verify_setup.sh** - Shell 环境验证脚本

```bash
./verify_setup.sh
```

**功能**:
- ✅ 检查 conda 安装
- ✅ 检查 lerobot 环境
- ✅ 检查 Python/Node.js 版本
- ✅ 运行 Python 依赖检查
- ✅ 提供清晰的错误提示

### 4. 简化配置文件 ⚙️

**backend/config.py** - 移除不必要的路径配置

**修改前**:
```python
lerobot_root: str = "../../lerobot"

@property
def lerobot_src_path(self) -> Path:
    return Path(__file__).parent / self.lerobot_root / "src"
```

**修改后**:
```python
# 不需要配置路径
# lerobot 通过 pip install -e . 安装后可直接 import
```

**好处**:
- ✅ 配置更简单
- ✅ 不依赖相对路径
- ✅ 支持任意安装位置

### 5. 新增详细文档 📚

#### SETUP_CONDA.md
完整的 Conda 环境配置指南：
- 📖 为什么使用 conda 环境
- 🚀 详细配置步骤
- 🔍 依赖树和版本说明
- 🐛 常见问题解答
- ✅ 完整的验证清单

#### CONDA_SETUP_SUMMARY.md
配置变更总结：
- 📝 修改内容对比
- 📊 依赖对比表格
- 💡 快速开始指南
- ❓ FAQ

#### GET_STARTED.md
3 步快速上手：
1. 验证环境
2. 启动服务
3. 开始遥操作

### 6. 更新现有文档 📝

所有文档都已更新，优先推荐 conda 方式：

- ✅ **README.md** - 添加 conda 使用说明
- ✅ **QUICKSTART.md** - conda 作为首选方式
- ✅ **backend/README.md** - 更新安装说明

## 📊 对比表格

| 特性 | 使用 Conda 环境 | 独立虚拟环境 |
|-----|----------------|-------------|
| **安装时间** | ⚡⚡⚡ 快（~10秒） | ⚡⚡ 慢（~2分钟） |
| **磁盘占用** | 💾 小（~50MB） | 💾💾 大（~500MB） |
| **依赖冲突** | ✅ 极少 | ⚠️ 可能 |
| **维护成本** | 🛠️ 低 | 🛠️🛠️ 高 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🔄 迁移指南

### 从独立虚拟环境迁移到 Conda

#### Step 1: 删除旧的虚拟环境
```bash
cd backend
rm -rf venv  # 或 deactivate && rm -rf venv
```

#### Step 2: 激活 lerobot 环境
```bash
conda activate lerobot
```

#### Step 3: 安装依赖
```bash
pip install -r requirements.txt
```

#### Step 4: 测试
```bash
python check_env.py
```

#### Step 5: 使用新脚本启动
```bash
cd ..
./start_conda.sh
```

### 保持独立虚拟环境

如果您仍想使用独立虚拟环境，可以继续使用 `./start.sh`。
但需要注意可能的依赖版本冲突。

## 📋 文件清单

### 新增文件
- ✅ `start_conda.sh` - Conda 环境启动脚本
- ✅ `verify_setup.sh` - 环境验证脚本
- ✅ `backend/check_env.py` - Python 依赖检查
- ✅ `SETUP_CONDA.md` - Conda 配置详细指南
- ✅ `CONDA_SETUP_SUMMARY.md` - 配置变更总结
- ✅ `GET_STARTED.md` - 快速上手指南
- ✅ `CHANGES.md` - 本文件

### 修改文件
- ✏️ `backend/requirements.txt` - 精简依赖
- ✏️ `backend/config.py` - 移除路径配置
- ✏️ `README.md` - 添加 conda 说明
- ✏️ `QUICKSTART.md` - conda 作为首选
- ✏️ `.env.example` - 更新注释

### 保留文件
- ✅ `start.sh` - 独立环境启动（仍可用）
- ✅ 所有其他文件保持不变

## 🎯 使用建议

### 推荐方式（Conda）
```bash
# 1. 验证环境
./verify_setup.sh

# 2. 启动服务
./start_conda.sh

# 3. 打开浏览器
open http://localhost:3000
```

### 替代方式（Venv）
```bash
# 如果不想用 conda
./start.sh
```

## ✅ 验证清单

完成配置后，确认这些项：

- [ ] conda 已安装
- [ ] lerobot 环境已创建
- [ ] lerobot 库已安装（`pip install -e .[all]`）
- [ ] Web 依赖已安装（`pip install -r requirements.txt`）
- [ ] 可以导入 lerobot（`python -c "import lerobot"`）
- [ ] 可以导入 fastapi（`python -c "import fastapi"`）
- [ ] verify_setup.sh 通过
- [ ] check_env.py 全部通过
- [ ] 后端可以启动
- [ ] 前端可以启动
- [ ] 可以访问 http://localhost:3000

## 🐛 故障排除

### 问题 1: 找不到 lerobot 模块

**解决方案**:
```bash
conda activate lerobot
cd /path/to/lerobot
pip install -e .[all]
```

### 问题 2: FastAPI 导入错误

**解决方案**:
```bash
conda activate lerobot
cd /path/to/play_on_web/backend
pip install -r requirements.txt
```

### 问题 3: 版本冲突

**解决方案**:
```bash
# 如果 pydantic 版本冲突
pip install pydantic>=2.0.0 --upgrade
```

### 问题 4: 想回到独立环境

**解决方案**:
```bash
# 删除 venv（如果存在）
rm -rf backend/venv

# 使用独立环境脚本
./start.sh
```

## 📞 获取帮助

- 📖 详细文档: [SETUP_CONDA.md](SETUP_CONDA.md)
- 🚀 快速上手: [GET_STARTED.md](GET_STARTED.md)
- 📁 项目结构: [STRUCTURE.md](STRUCTURE.md)
- ✅ 功能检查: [CHECKLIST.md](CHECKLIST.md)

## 🎉 总结

通过这次更新：

✅ **简化了配置** - 只需几个命令即可启动
✅ **提高了效率** - 复用环境，节省时间和空间
✅ **降低了复杂度** - 自动化脚本处理一切
✅ **增强了文档** - 完善的指南和检查清单
✅ **保持了兼容** - 仍支持独立虚拟环境

**现在您可以更轻松地使用 XLerobot Web Teleop 了！** 🎊

---

**更新日期**: 2026-01-01
**版本**: 1.1.0
**作者**: XLerobot Team

