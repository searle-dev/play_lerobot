"""
FastAPI 主应用 - Web 遥操作服务
"""
import asyncio
import logging
from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from pathlib import Path

from config import settings
from device_scanner import DeviceScanner
from robot_controller import RobotController
from camera_manager import CameraManager, CameraConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="XLerobot Web Teleop",
    description="XLerobot 机械臂小车网页遥操作系统",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
robot_controller: RobotController | None = None
camera_manager = CameraManager()
active_websockets: set[WebSocket] = set()


# ==================== Pydantic 模型 ====================

class PortDetectRequest(BaseModel):
    """端口检测请求"""
    ports_before: list[str]


class RobotConnectRequest(BaseModel):
    """机器人连接请求"""
    port1: str
    port2: str


class CameraAddRequest(BaseModel):
    """添加相机请求"""
    name: str
    camera_id: str
    camera_type: str
    width: int = 640
    height: int = 480
    fps: int = 30


class KeyboardActionRequest(BaseModel):
    """键盘动作请求"""
    arm: str  # "left" 或 "right"
    action: str  # 动作类型
    value: float = 1.0


class BaseActionRequest(BaseModel):
    """底盘动作请求"""
    direction: str  # forward, backward, left, right, rotate_left, rotate_right


class ZeroPositionRequest(BaseModel):
    """零位请求"""
    arm: str = "both"  # "left", "right", 或 "both"


class ResetPositionRequest(BaseModel):
    """复位位置请求"""
    arm: str = "both"  # "left", "right", 或 "both"


class StepLevelRequest(BaseModel):
    """步长等级请求"""
    arm: str = "both"  # "left", "right", 或 "both"
    level: str = "normal"  # "slow", "normal", "fast"


# ==================== HTTP 端点 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "XLerobot Web Teleop API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "robot_connected": robot_controller is not None and robot_controller._is_connected,
        "active_websockets": len(active_websockets)
    }


# ==================== 设备扫描端点 ====================

@app.get("/api/devices/ports")
async def get_ports():
    """获取所有可用串口"""
    ports = DeviceScanner.find_available_ports()
    return {
        "status": "success",
        "ports": ports
    }


@app.get("/api/devices/ports/detect/start")
async def start_port_detection():
    """开始端口检测（第一步：记录当前端口）"""
    result = DeviceScanner.find_port_by_disconnect()
    return result


@app.post("/api/devices/ports/detect/complete")
async def complete_port_detection(request: PortDetectRequest):
    """完成端口检测（第二步：检测断开后的端口）"""
    result = DeviceScanner.find_port_after_disconnect(request.ports_before)
    return result


@app.get("/api/devices/cameras")
async def get_cameras():
    """获取所有可用相机"""
    cameras = DeviceScanner.find_all_cameras()
    return {
        "status": "success",
        "cameras": cameras
    }


# ==================== 机器人控制端点 ====================

@app.post("/api/robot/connect")
async def connect_robot(request: RobotConnectRequest):
    """连接机器人"""
    global robot_controller
    
    try:
        config = {
            "port1": request.port1,
            "port2": request.port2
        }
        robot_controller = RobotController(config)
        result = robot_controller.connect()
        return result
    except Exception as e:
        logger.error(f"连接机器人时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/robot/disconnect")
async def disconnect_robot():
    """断开机器人连接"""
    global robot_controller
    
    if robot_controller:
        result = robot_controller.disconnect()
        robot_controller = None
        return result
    else:
        return {"status": "error", "message": "机器人未连接"}


@app.post("/api/robot/zero")
async def move_to_zero(request: ZeroPositionRequest):
    """移动到零位"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.move_to_zero_position(request.arm)
    return result


@app.post("/api/robot/record_reset_position")
async def record_reset_position(request: ResetPositionRequest):
    """记录当前位置作为复位位置"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.record_current_position_as_reset(request.arm)
    return result


@app.post("/api/robot/move_to_reset")
async def move_to_reset_position(request: ResetPositionRequest):
    """移动到复位位置（自定义的安全位置）"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.move_to_reset_position(request.arm)
    return result


@app.get("/api/robot/reset_positions")
async def get_reset_positions():
    """获取当前保存的复位位置"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.get_reset_positions()
    return result


@app.post("/api/robot/set_step_level")
async def set_step_level(request: StepLevelRequest):
    """设置运动步长等级（slow/normal/fast）"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.set_step_level(request.arm, request.level)
    return result


@app.post("/api/robot/stop_base")
async def stop_base():
    """停止底盘运动"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.stop_base()
    return result


@app.get("/api/robot/observation")
async def get_observation():
    """获取机器人观测值"""
    if not robot_controller:
        raise HTTPException(status_code=400, detail="机器人未连接")
    
    result = robot_controller.get_observation()
    return result


# ==================== 相机管理端点 ====================

@app.post("/api/cameras/add")
async def add_camera(request: CameraAddRequest):
    """添加相机"""
    config = CameraConfig(
        camera_id=request.camera_id,
        camera_type=request.camera_type,
        width=request.width,
        height=request.height,
        fps=request.fps
    )
    result = camera_manager.add_camera(request.name, config)
    return result


@app.delete("/api/cameras/{camera_name}")
async def remove_camera(camera_name: str):
    """移除相机"""
    result = camera_manager.remove_camera(camera_name)
    return result


@app.get("/api/cameras/{camera_name}/frame")
async def get_camera_frame(camera_name: str):
    """获取单帧图像"""
    frame_bytes = camera_manager.get_frame(camera_name)
    if frame_bytes:
        return StreamingResponse(
            iter([frame_bytes]),
            media_type="image/jpeg"
        )
    else:
        raise HTTPException(status_code=404, detail="相机不存在或无法获取帧")


# ==================== WebSocket 端点 ====================

@app.websocket("/ws/teleop")
async def websocket_teleop(websocket: WebSocket):
    """
    WebSocket 遥操作端点
    支持实时控制和状态反馈
    """
    await websocket.accept()
    active_websockets.add(websocket)
    logger.info(f"WebSocket 连接建立，当前活跃连接数: {len(active_websockets)}")
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            # 处理不同类型的消息
            if message_type == "keyboard_action":
                # 键盘动作
                if robot_controller:
                    result = robot_controller.handle_keyboard_action(data.get("data"))
                    await websocket.send_json({
                        "type": "action_result",
                        "data": result
                    })
            
            elif message_type == "base_action":
                # 底盘动作
                if robot_controller:
                    result = robot_controller.handle_base_action(data.get("data"))
                    await websocket.send_json({
                        "type": "action_result",
                        "data": result
                    })
            
            elif message_type == "base_stop":
                # 停止底盘
                if robot_controller:
                    result = robot_controller.stop_base()
                    await websocket.send_json({
                        "type": "action_result",
                        "data": result
                    })
            
            elif message_type == "get_observation":
                # 获取观测值
                if robot_controller:
                    result = robot_controller.get_observation()
                    await websocket.send_json({
                        "type": "observation",
                        "data": result
                    })
            
            elif message_type == "ping":
                # 心跳
                await websocket.send_json({
                    "type": "pong"
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"未知消息类型: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        active_websockets.discard(websocket)
        logger.info(f"WebSocket 连接关闭，当前活跃连接数: {len(active_websockets)}")


@app.websocket("/ws/camera")
async def websocket_camera(websocket: WebSocket):
    """
    WebSocket 相机流端点
    实时传输多路相机画面
    """
    await websocket.accept()
    logger.info("相机流 WebSocket 连接建立")
    
    try:
        # 等待客户端发送相机列表
        data = await websocket.receive_json()
        camera_names = data.get("cameras", [])
        
        logger.info(f"开始流式传输相机: {camera_names}")
        
        # 开始流式传输
        await camera_manager.stream_frames(websocket, camera_names)
    
    except WebSocketDisconnect:
        logger.info("相机流 WebSocket 连接断开")
    except Exception as e:
        logger.error(f"相机流 WebSocket 错误: {e}")
    finally:
        camera_manager.stop_streaming()
        logger.info("相机流 WebSocket 连接关闭")


# ==================== 启动和关闭事件 ====================

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("XLerobot Web Teleop 服务启动")
    logger.info(f"CORS 允许的源: {settings.cors_origins_list}")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("XLerobot Web Teleop 服务关闭")
    
    # 断开机器人
    if robot_controller:
        robot_controller.disconnect()
    
    # 断开所有相机
    camera_manager.disconnect_all()
    
    # 关闭所有 WebSocket 连接
    for ws in active_websockets:
        await ws.close()


# ==================== 主函数 ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level="info"
    )

