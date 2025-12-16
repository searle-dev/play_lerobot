"""FastAPI 主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import ports, robots, recording
from .websocket import calibration_ws, control_ws
from .config import CORS_ORIGINS
from .storage.database import RobotDatabase

# 创建应用
app = FastAPI(
    title="LeRobot 机械臂调试服务器",
    description="提供机械臂管理、校准、控制和录制回放功能",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 REST API 路由
app.include_router(ports.router)
app.include_router(robots.router)
app.include_router(recording.router)

# 注册 WebSocket 路由
app.include_router(calibration_ws.router)
app.include_router(control_ws.router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 初始化数据库
    db = RobotDatabase()
    print("✓ 数据库初始化完成")

    # 从数据库加载机械臂配置
    from .services.robot_manager import robot_manager
    saved_robots = db.list_robots()
    for config in saved_robots:
        try:
            robot_manager.add_robot(config)
            print(f"✓ 加载机械臂: {config.id}")
        except ValueError:
            # 机械臂已存在
            pass

    print(f"✓ LeRobot 调试服务器启动完成")
    print(f"  - API 文档: http://localhost:8000/docs")
    print(f"  - REST API: http://localhost:8000/api")
    print(f"  - WebSocket: ws://localhost:8000/ws")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "LeRobot 机械臂调试服务器",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    from .services.robot_manager import robot_manager
    return {
        "status": "healthy",
        "robots_count": len(robot_manager.robots)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
