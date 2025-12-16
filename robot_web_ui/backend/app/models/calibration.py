"""校准相关数据模型"""
from pydantic import BaseModel
from typing import Dict, Optional
from enum import Enum


class CalibrationStep(str, Enum):
    """校准步骤"""
    NOT_STARTED = "not_started"
    MOVE_TO_CENTER = "move_to_center"
    RECORDING_RANGE = "recording_range"
    COMPLETED = "completed"


class CalibrationData(BaseModel):
    """电机校准数据"""
    robot_id: str
    motor_name: str
    id: int
    drive_mode: int
    homing_offset: int
    range_min: int
    range_max: int


class CalibrationStatus(BaseModel):
    """校准状态"""
    robot_id: str
    step: CalibrationStep
    current_positions: Dict[str, float] = {}
    range_mins: Optional[Dict[str, float]] = None
    range_maxes: Optional[Dict[str, float]] = None
    message: str = ""
