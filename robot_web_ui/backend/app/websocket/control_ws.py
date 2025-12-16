"""实时控制 WebSocket 端点"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.robot_manager import robot_manager
from ..config import WS_STATE_UPDATE_FREQ
import asyncio

router = APIRouter()


@router.websocket("/ws/control/{robot_id}")
async def control_websocket(websocket: WebSocket, robot_id: str):
    """
    实时控制 WebSocket 连接

    消息格式：
    - 服务器 -> 客户端：{"type": "state", "data": observation}
    - 客户端 -> 服务器：{"type": "action", "action": {joint: value}}
    """
    await websocket.accept()

    try:
        robot_instance = robot_manager.get_robot(robot_id)
    except ValueError as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
        return

    # 启动状态推送任务
    async def stream_state():
        """持续推送机械臂状态"""
        update_interval = 1.0 / WS_STATE_UPDATE_FREQ  # 20Hz
        try:
            while True:
                obs = await robot_instance.get_observation()
                await websocket.send_json({
                    "type": "state",
                    "data": obs
                })
                await asyncio.sleep(update_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"状态推送错误: {e}")

    stream_task = asyncio.create_task(stream_state())

    # 监听客户端动作指令
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "action":
                action = data.get("action")
                if action:
                    try:
                        await robot_instance.send_action(action)
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"发送动作失败: {str(e)}"
                        })

    except WebSocketDisconnect:
        print(f"控制 WebSocket 断开连接: {robot_id}")
    except Exception as e:
        print(f"控制 WebSocket 错误: {e}")
    finally:
        stream_task.cancel()
        try:
            await stream_task
        except asyncio.CancelledError:
            pass
