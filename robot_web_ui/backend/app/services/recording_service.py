"""录制回放服务"""
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Callable, Optional
from ..models.recording import Recording, RecordingFrame, RecordingMetadata
from ..config import RECORDINGS_DIR, RECORDING_SAMPLE_RATE
from .robot_manager import robot_manager


class RecordingService:
    """录制回放服务"""

    def __init__(self):
        self.storage_dir = RECORDINGS_DIR
        self.active_recordings: Dict[str, List[RecordingFrame]] = {}
        self.recording_tasks: Dict[str, asyncio.Task] = {}

    async def start_recording(self, robot_id: str) -> str:
        """
        开始录制

        Args:
            robot_id: 机械臂 ID

        Returns:
            录制 ID
        """
        recording_id = f"{robot_id}_{int(time.time())}"
        self.active_recordings[recording_id] = []

        # 启动后台录制任务
        task = asyncio.create_task(self._record_loop(robot_id, recording_id))
        self.recording_tasks[recording_id] = task

        return recording_id

    async def _record_loop(self, robot_id: str, recording_id: str):
        """
        录制循环

        Args:
            robot_id: 机械臂 ID
            recording_id: 录制 ID
        """
        robot_instance = robot_manager.get_robot(robot_id)
        start_time = time.time()
        sample_interval = 1.0 / RECORDING_SAMPLE_RATE  # 采样间隔

        try:
            while recording_id in self.active_recordings:
                obs = await robot_instance.get_observation()

                # 只录制关节位置
                positions = {k: v for k, v in obs.items() if k.endswith('.pos')}

                frame = RecordingFrame(
                    timestamp=time.time() - start_time,
                    joint_positions=positions
                )
                self.active_recordings[recording_id].append(frame)

                await asyncio.sleep(sample_interval)
        except asyncio.CancelledError:
            # 任务被取消
            pass
        except Exception as e:
            print(f"录制循环出错: {e}")

    async def stop_recording(self, recording_id: str, name: str) -> Recording:
        """
        停止录制并保存

        Args:
            recording_id: 录制 ID
            name: 录制名称

        Returns:
            录制对象
        """
        if recording_id not in self.active_recordings:
            raise ValueError(f"录制 {recording_id} 不存在")

        # 取消录制任务
        if recording_id in self.recording_tasks:
            self.recording_tasks[recording_id].cancel()
            try:
                await self.recording_tasks[recording_id]
            except asyncio.CancelledError:
                pass
            del self.recording_tasks[recording_id]

        # 获取录制帧
        frames = self.active_recordings.pop(recording_id)

        # 创建录制对象
        recording = Recording(
            id=recording_id,
            robot_id=recording_id.split('_')[0],
            name=name,
            frames=frames,
            duration=frames[-1].timestamp if frames else 0,
            created_at=datetime.now()
        )

        # 保存到文件
        await self._save_recording(recording)

        return recording

    async def _save_recording(self, recording: Recording):
        """保存录制到文件"""
        robot_dir = self.storage_dir / recording.robot_id
        robot_dir.mkdir(parents=True, exist_ok=True)

        file_path = robot_dir / f"{recording.id}.json"

        # 异步写入文件
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: file_path.write_text(recording.model_dump_json(indent=2))
        )

    def list_recordings(self, robot_id: str) -> List[RecordingMetadata]:
        """
        列出所有录制

        Args:
            robot_id: 机械臂 ID

        Returns:
            录制元数据列表
        """
        robot_dir = self.storage_dir / robot_id
        if not robot_dir.exists():
            return []

        recordings = []
        for file_path in robot_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                metadata = RecordingMetadata(
                    id=data["id"],
                    robot_id=data["robot_id"],
                    name=data["name"],
                    duration=data["duration"],
                    frame_count=len(data["frames"]),
                    created_at=datetime.fromisoformat(data["created_at"])
                )
                recordings.append(metadata)
            except Exception as e:
                print(f"读取录制文件失败 {file_path}: {e}")

        return sorted(recordings, key=lambda x: x.created_at, reverse=True)

    async def load_recording(self, recording_id: str) -> Optional[Recording]:
        """
        加载录制

        Args:
            recording_id: 录制 ID

        Returns:
            录制对象
        """
        robot_id = recording_id.split('_')[0]
        file_path = self.storage_dir / robot_id / f"{recording_id}.json"

        if not file_path.exists():
            return None

        loop = asyncio.get_event_loop()
        data_str = await loop.run_in_executor(None, file_path.read_text)
        data = json.loads(data_str)

        return Recording(**data)

    async def playback(
        self,
        recording_id: str,
        on_frame: Optional[Callable] = None,
        speed: float = 1.0
    ):
        """
        回放录制

        Args:
            recording_id: 录制 ID
            on_frame: 帧回调函数
            speed: 回放速度（1.0 = 正常速度）
        """
        recording = await self.load_recording(recording_id)
        if not recording:
            raise ValueError(f"录制 {recording_id} 不存在")

        robot_instance = robot_manager.get_robot(recording.robot_id)

        for i, frame in enumerate(recording.frames):
            await robot_instance.send_action(frame.joint_positions)

            if on_frame:
                await on_frame(frame)

            # 等待到下一帧
            if i < len(recording.frames) - 1:
                next_frame = recording.frames[i + 1]
                delay = (next_frame.timestamp - frame.timestamp) / speed
                await asyncio.sleep(delay)


# 全局单例实例
recording_service = RecordingService()
