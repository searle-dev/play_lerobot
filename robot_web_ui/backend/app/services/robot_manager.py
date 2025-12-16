"""机械臂管理器 - 核心服务"""
import asyncio
import threading
from typing import Dict, Optional, Any
from datetime import datetime
from ..models.robot import RobotConfig, RobotState, RobotStatus


class RobotInstance:
    """
    机械臂实例封装

    封装单个机械臂，提供异步接口并确保线程安全
    """

    def __init__(self, config: RobotConfig):
        self.config = config
        self.robot = None  # LeRobot 机械臂实例
        self.status = RobotStatus.DISCONNECTED
        self.lock = threading.Lock()  # 线程锁，确保并发安全
        self.last_observation = {}
        self.last_updated = None

    async def connect(self, calibrate: bool = True):
        """
        连接机械臂（异步）

        Args:
            calibrate: 是否自动校准
        """
        loop = asyncio.get_event_loop()

        with self.lock:
            if self.robot is None:
                # 在线程池中创建 LeRobot 实例
                self.robot = await loop.run_in_executor(None, self._create_robot)

            # 连接机械臂
            try:
                await loop.run_in_executor(None, self.robot.connect, calibrate)
                self.status = RobotStatus.READY if self.robot.is_calibrated else RobotStatus.CONNECTED
            except Exception as e:
                self.status = RobotStatus.ERROR
                raise RuntimeError(f"连接机械臂失败: {e}")

    def _create_robot(self):
        """
        创建 LeRobot 实例（同步）

        根据 robot_type 创建相应的配置和实例
        """
        from lerobot.robots.utils import make_robot_from_config

        # 根据类型导入配置
        if self.config.robot_type == "so100_follower":
            from lerobot.robots.so100_follower import SO100FollowerConfig
            lerobot_config = SO100FollowerConfig(
                id=self.config.id,
                port=self.config.port
            )
        elif self.config.robot_type == "so101_follower":
            from lerobot.robots.so101_follower import SO101FollowerConfig
            lerobot_config = SO101FollowerConfig(
                id=self.config.id,
                port=self.config.port
            )
        elif self.config.robot_type == "koch_follower":
            from lerobot.robots.koch_follower import KochFollowerConfig
            lerobot_config = KochFollowerConfig(
                id=self.config.id,
                port=self.config.port
            )
        elif self.config.robot_type == "lekiwi":
            from lerobot.robots.lekiwi import LeKiwiConfig
            lerobot_config = LeKiwiConfig(
                id=self.config.id,
                port=self.config.port
            )
        else:
            raise ValueError(f"不支持的机械臂类型: {self.config.robot_type}")

        return make_robot_from_config(lerobot_config)

    async def disconnect(self):
        """断开机械臂连接"""
        if not self.robot:
            return

        loop = asyncio.get_event_loop()
        with self.lock:
            try:
                await loop.run_in_executor(None, self.robot.disconnect)
            except Exception as e:
                print(f"断开连接时出错: {e}")
            finally:
                self.status = RobotStatus.DISCONNECTED

    async def get_observation(self) -> Dict[str, Any]:
        """
        获取当前观测（关节位置和相机图像）

        Returns:
            观测字典
        """
        if not self.robot or not self.robot.is_connected:
            raise ValueError(f"机械臂 {self.config.id} 未连接")

        loop = asyncio.get_event_loop()
        with self.lock:
            obs = await loop.run_in_executor(None, self.robot.get_observation)
            self.last_observation = obs
            self.last_updated = datetime.now().isoformat()
        return obs

    async def send_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送动作指令

        Args:
            action: 动作字典 {joint_name.pos: value}

        Returns:
            实际发送的动作
        """
        if not self.robot or not self.robot.is_connected:
            raise ValueError(f"机械臂 {self.config.id} 未连接")

        loop = asyncio.get_event_loop()
        with self.lock:
            sent_action = await loop.run_in_executor(
                None,
                self.robot.send_action,
                action
            )
        return sent_action

    def get_state(self) -> RobotState:
        """获取机械臂状态"""
        joint_positions = None
        if self.last_observation:
            joint_positions = {
                k: v for k, v in self.last_observation.items()
                if k.endswith('.pos')
            }

        return RobotState(
            id=self.config.id,
            robot_type=self.config.robot_type,
            port=self.config.port,
            status=self.status,
            nickname=self.config.nickname,
            is_calibrated=self.robot.is_calibrated if self.robot else False,
            joint_positions=joint_positions,
            last_updated=self.last_updated
        )


class RobotManager:
    """
    全局机械臂管理器（单例模式）

    管理所有机械臂实例，提供统一的访问接口
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.robots: Dict[str, RobotInstance] = {}
        return cls._instance

    def add_robot(self, config: RobotConfig) -> RobotInstance:
        """
        添加机械臂

        Args:
            config: 机械臂配置

        Returns:
            机械臂实例
        """
        if config.id in self.robots:
            raise ValueError(f"机械臂 {config.id} 已存在")

        robot_instance = RobotInstance(config)
        self.robots[config.id] = robot_instance
        return robot_instance

    def get_robot(self, robot_id: str) -> RobotInstance:
        """
        获取机械臂实例

        Args:
            robot_id: 机械臂 ID

        Returns:
            机械臂实例
        """
        if robot_id not in self.robots:
            raise ValueError(f"机械臂 {robot_id} 不存在")
        return self.robots[robot_id]

    def has_robot(self, robot_id: str) -> bool:
        """检查机械臂是否存在"""
        return robot_id in self.robots

    def list_robots(self) -> list[RobotState]:
        """列出所有机械臂状态"""
        return [instance.get_state() for instance in self.robots.values()]

    async def connect_robot(self, robot_id: str, calibrate: bool = True):
        """连接机械臂"""
        instance = self.get_robot(robot_id)
        await instance.connect(calibrate)

    async def disconnect_robot(self, robot_id: str):
        """断开机械臂"""
        instance = self.get_robot(robot_id)
        await instance.disconnect()

    def remove_robot(self, robot_id: str):
        """移除机械臂"""
        if robot_id in self.robots:
            del self.robots[robot_id]


# 全局单例实例
robot_manager = RobotManager()
