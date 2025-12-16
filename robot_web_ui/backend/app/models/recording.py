"""录制回放相关数据模型"""
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class RecordingFrame(BaseModel):
    """录制帧"""
    timestamp: float
    joint_positions: Dict[str, float]


class Recording(BaseModel):
    """录制数据"""
    id: str
    robot_id: str
    name: str
    frames: List[RecordingFrame]
    duration: float
    created_at: datetime


class RecordingMetadata(BaseModel):
    """录制元数据"""
    id: str
    robot_id: str
    name: str
    duration: float
    frame_count: int
    created_at: datetime
