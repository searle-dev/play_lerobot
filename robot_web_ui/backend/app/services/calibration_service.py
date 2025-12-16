"""校准服务 - 将交互式校准改造为异步流程"""
import asyncio
from typing import Dict, Callable, Optional
from ..models.calibration import CalibrationStep, CalibrationStatus
from .robot_manager import robot_manager


class CalibrationService:
    """校准服务"""

    def __init__(self):
        self.calibration_sessions: Dict[str, CalibrationStatus] = {}
        self.streaming_tasks: Dict[str, asyncio.Task] = {}

    async def start_calibration(
        self,
        robot_id: str,
        on_status_update: Callable
    ):
        """
        启动校准流程

        Args:
            robot_id: 机械臂 ID
            on_status_update: 状态更新回调（WebSocket 推送）
        """
        robot_instance = robot_manager.get_robot(robot_id)

        # 设置校准状态
        robot_instance.status = "calibrating"

        # 初始化校准会话
        status = CalibrationStatus(
            robot_id=robot_id,
            step=CalibrationStep.MOVE_TO_CENTER,
            message="请将机械臂移动到所有关节的中间位置，然后点击'确认中心位置'"
        )
        self.calibration_sessions[robot_id] = status

        await on_status_update(status)

    async def confirm_center_position(
        self,
        robot_id: str,
        on_status_update: Callable
    ):
        """
        确认中心位置

        Args:
            robot_id: 机械臂 ID
            on_status_update: 状态更新回调
        """
        robot_instance = robot_manager.get_robot(robot_id)
        loop = asyncio.get_event_loop()

        # 设置半圈归位
        with robot_instance.lock:
            homing_offsets = await loop.run_in_executor(
                None,
                robot_instance.robot.bus.set_half_turn_homings
            )

        # 进入下一步：记录运动范围
        status = self.calibration_sessions[robot_id]
        status.step = CalibrationStep.RECORDING_RANGE
        status.message = "请依次移动每个关节到其完整的运动范围，然后点击'完成录制'"
        await on_status_update(status)

        # 启动后台任务持续读取当前位置
        task = asyncio.create_task(self._stream_positions(robot_id, on_status_update))
        self.streaming_tasks[robot_id] = task

    async def _stream_positions(self, robot_id: str, on_status_update: Callable):
        """
        持续推送当前关节位置

        Args:
            robot_id: 机械臂 ID
            on_status_update: 状态更新回调
        """
        robot_instance = robot_manager.get_robot(robot_id)
        status = self.calibration_sessions[robot_id]

        try:
            while status.step == CalibrationStep.RECORDING_RANGE:
                obs = await robot_instance.get_observation()

                # 提取关节位置
                positions = {
                    k.replace('.pos', ''): v
                    for k, v in obs.items()
                    if k.endswith('.pos')
                }

                # 更新 min/max
                if status.range_mins is None:
                    status.range_mins = positions.copy()
                    status.range_maxes = positions.copy()
                else:
                    for motor, pos in positions.items():
                        status.range_mins[motor] = min(status.range_mins[motor], pos)
                        status.range_maxes[motor] = max(status.range_maxes[motor], pos)

                status.current_positions = positions
                await on_status_update(status)

                await asyncio.sleep(0.1)  # 10Hz 更新
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"位置流出错: {e}")

    async def finish_calibration(self, robot_id: str):
        """
        完成校准并保存

        Args:
            robot_id: 机械臂 ID
        """
        status = self.calibration_sessions.get(robot_id)
        if not status:
            raise ValueError(f"未找到机械臂 {robot_id} 的校准会话")

        # 取消流任务
        if robot_id in self.streaming_tasks:
            self.streaming_tasks[robot_id].cancel()
            try:
                await self.streaming_tasks[robot_id]
            except asyncio.CancelledError:
                pass
            del self.streaming_tasks[robot_id]

        robot_instance = robot_manager.get_robot(robot_id)

        # 构造校准数据
        from lerobot.motors import MotorCalibration
        calibration = {}

        for motor, m in robot_instance.robot.bus.motors.items():
            calibration[motor] = MotorCalibration(
                id=m.id,
                drive_mode=0,
                homing_offset=0,  # 已在 set_half_turn_homings 中设置
                range_min=int(status.range_mins[motor]),
                range_max=int(status.range_maxes[motor])
            )

        # 保存校准
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            robot_instance.robot.bus.write_calibration,
            calibration
        )
        await loop.run_in_executor(
            None,
            robot_instance.robot._save_calibration
        )

        # 更新状态
        status.step = CalibrationStep.COMPLETED
        robot_instance.status = "ready"

        # 清理会话
        del self.calibration_sessions[robot_id]

    def get_calibration_status(self, robot_id: str) -> Optional[CalibrationStatus]:
        """获取校准状态"""
        return self.calibration_sessions.get(robot_id)


# 全局单例实例
calibration_service = CalibrationService()
