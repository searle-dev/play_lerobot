"""机械臂相关数据模型"""
from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime


class RobotType(str, Enum):
    """机械臂类型"""
    SO100_FOLLOWER = "so100_follower"
    SO101_FOLLOWER = "so101_follower"
    KOCH_FOLLOWER = "koch_follower"
    LEKIWI = "lekiwi"


class RobotStatus(str, Enum):
    """机械臂状态"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    CALIBRATING = "calibrating"
    READY = "ready"
    ERROR = "error"


class PortInfo(BaseModel):
    """端口信息"""
    port: str
    description: str
    hwid: str


class ScanResult(BaseModel):
    """端口扫描结果"""
    port: str
    baudrate: int
    motor_ids: List[int]


class RobotConfig(BaseModel):
    """机械臂配置"""
    id: str
    robot_type: RobotType
    port: str
    nickname: Optional[str] = None
    notes: Optional[str] = None


class RobotState(BaseModel):
    """机械臂状态"""
    id: str
    robot_type: RobotType
    port: str
    status: RobotStatus
    nickname: Optional[str] = None
    is_calibrated: bool
    joint_positions: Optional[Dict[str, float]] = None
    last_updated: Optional[str] = None


class JointPosition(BaseModel):
    """关节位置"""
    positions: Dict[str, float]


class RobotAction(BaseModel):
    """机械臂动作"""
    robot_id: str
    action: Dict[str, float]
