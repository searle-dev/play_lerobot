"""应用配置"""
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"
DATABASE_PATH = DATA_DIR / "robots.db"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
RECORDINGS_DIR.mkdir(exist_ok=True)

# CORS 配置
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite 开发服务器
    "http://localhost:3000",  # 备用端口
]

# WebSocket 配置
WS_HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）
WS_STATE_UPDATE_FREQ = 20   # 状态更新频率（Hz）

# 录制配置
RECORDING_SAMPLE_RATE = 50  # 录制采样率（Hz）
