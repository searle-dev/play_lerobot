"""校准 WebSocket 端点"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.calibration_service import calibration_service
import json

router = APIRouter()


@router.websocket("/ws/calibration/{robot_id}")
async def calibration_websocket(websocket: WebSocket, robot_id: str):
    """
    校准 WebSocket 连接

    消息格式：
    - 客户端 -> 服务器：{"command": "start|confirm_center|finish"}
    - 服务器 -> 客户端：CalibrationStatus JSON
    """
    await websocket.accept()

    async def send_status(status):
        """发送状态到客户端"""
        await websocket.send_json(status.model_dump())

    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "start":
                # 开始校准
                await calibration_service.start_calibration(robot_id, send_status)

            elif command == "confirm_center":
                # 确认中心位置
                await calibration_service.confirm_center_position(robot_id, send_status)

            elif command == "finish":
                # 完成校准
                await calibration_service.finish_calibration(robot_id)
                await websocket.send_json({"status": "completed"})
                break

    except WebSocketDisconnect:
        print(f"校准 WebSocket 断开连接: {robot_id}")
    except Exception as e:
        print(f"校准 WebSocket 错误: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
