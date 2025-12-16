"""机械臂管理 API"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models.robot import RobotConfig, RobotState
from ..services.robot_manager import robot_manager
from ..storage.database import RobotDatabase

router = APIRouter(prefix="/api/robots", tags=["robots"])
db = RobotDatabase()


@router.get("/", response_model=List[RobotState])
async def list_robots():
    """列出所有机械臂"""
    return robot_manager.list_robots()


@router.post("/", response_model=RobotState)
async def create_robot(config: RobotConfig):
    """添加新机械臂"""
    try:
        # 添加到管理器
        instance = robot_manager.add_robot(config)

        # 保存到数据库
        db.save_robot(config)

        return instance.get_state()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建机械臂失败: {str(e)}")


@router.get("/{robot_id}", response_model=RobotState)
async def get_robot(robot_id: str):
    """获取机械臂状态"""
    try:
        instance = robot_manager.get_robot(robot_id)
        return instance.get_state()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{robot_id}")
async def update_robot(
    robot_id: str,
    nickname: Optional[str] = None,
    notes: Optional[str] = None
):
    """更新机械臂信息（备注等）"""
    try:
        db.update_robot(robot_id, nickname=nickname, notes=notes)

        # 更新管理器中的配置
        if robot_manager.has_robot(robot_id):
            instance = robot_manager.get_robot(robot_id)
            if nickname is not None:
                instance.config.nickname = nickname
            if notes is not None:
                instance.config.notes = notes

        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/{robot_id}/connect")
async def connect_robot(robot_id: str, calibrate: bool = False):
    """连接机械臂"""
    try:
        await robot_manager.connect_robot(robot_id, calibrate)
        instance = robot_manager.get_robot(robot_id)
        return {
            "status": "connected",
            "is_calibrated": instance.robot.is_calibrated if instance.robot else False
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.post("/{robot_id}/disconnect")
async def disconnect_robot(robot_id: str):
    """断开机械臂"""
    try:
        await robot_manager.disconnect_robot(robot_id)
        return {"status": "disconnected"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开失败: {str(e)}")


@router.get("/{robot_id}/observation")
async def get_observation(robot_id: str):
    """获取当前观测"""
    try:
        instance = robot_manager.get_robot(robot_id)
        obs = await instance.get_observation()
        return obs
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取观测失败: {str(e)}")


@router.delete("/{robot_id}")
async def delete_robot(robot_id: str):
    """删除机械臂"""
    try:
        # 先断开连接
        if robot_manager.has_robot(robot_id):
            instance = robot_manager.get_robot(robot_id)
            if instance.status != "disconnected":
                await instance.disconnect()
            robot_manager.remove_robot(robot_id)

        # 从数据库删除
        db.delete_robot(robot_id)

        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
