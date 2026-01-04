"""
配置管理模块

注意: 本项目设计为在 lerobot conda 环境中运行
当 lerobot 通过 `pip install -e .` 安装后，可以直接 import lerobot
不需要手动添加 sys.path
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务器配置
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # 机器人配置
    robot_id: str = "my_xlerobot"
    robot_fps: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list[str]:
        """获取 CORS 源列表"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()

