"""
机器人控制模块 - 核心控制逻辑
"""
import sys
import logging
import numpy as np
import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 复位位置配置文件路径
RESET_POSITION_CONFIG = Path.home() / ".cache" / "xlerobot_web" / "reset_positions.json"


@dataclass
class ArmState:
    """机械臂状态"""
    # 运动学状态
    current_x: float = 0.1629
    current_y: float = 0.1131
    pitch: float = 0.0
    
    # 目标位置
    target_positions: dict[str, float] = None
    
    # 控制参数（参考 4_xlerobot_teleop_keyboard.py）
    degree_step: int = 3  # 关节空间步长（度）
    xy_step: float = 0.0081  # 笛卡尔空间步长（米） - 8.1mm
    kp: float = 0.81  # P 控制增益
    
    # 步长等级（可选：slow, normal, fast）
    step_level: str = "normal"
    
    def __post_init__(self):
        if self.target_positions is None:
            self.target_positions = {
                "shoulder_pan": 0.0,
                "shoulder_lift": 0.0,
                "elbow_flex": 0.0,
                "wrist_flex": 0.0,
                "wrist_roll": 0.0,
                "gripper": 0.0,
            }


@dataclass
class HeadState:
    """头部状态"""
    target_positions: dict[str, float] = None
    degree_step: int = 1  # 参考 4_xlerobot_teleop_keyboard.py (第135行)
    kp: float = 0.81
    
    def __post_init__(self):
        if self.target_positions is None:
            self.target_positions = {
                "head_motor_1": 0.0,
                "head_motor_2": 0.0,
            }


class RobotController:
    """机器人控制器"""
    
    def __init__(self, config: dict[str, Any]):
        """
        初始化机器人控制器
        
        Args:
            config: 配置字典，包含 port1, port2 等信息
        """
        self.config = config
        self.robot = None
        self.kinematics_left = None
        self.kinematics_right = None
        
        # 机械臂和头部状态
        self.left_arm_state = ArmState()
        self.right_arm_state = ArmState()
        self.head_state = HeadState()
        
        # 关节映射
        self.left_joint_map = {
            "shoulder_pan": "left_arm_shoulder_pan",
            "shoulder_lift": "left_arm_shoulder_lift",
            "elbow_flex": "left_arm_elbow_flex",
            "wrist_flex": "left_arm_wrist_flex",
            "wrist_roll": "left_arm_wrist_roll",
            "gripper": "left_arm_gripper",
        }
        self.right_joint_map = {
            "shoulder_pan": "right_arm_shoulder_pan",
            "shoulder_lift": "right_arm_shoulder_lift",
            "elbow_flex": "right_arm_elbow_flex",
            "wrist_flex": "right_arm_wrist_flex",
            "wrist_roll": "right_arm_wrist_roll",
            "gripper": "right_arm_gripper",
        }
        self.head_motor_map = {
            "head_motor_1": "head_motor_1",
            "head_motor_2": "head_motor_2",
        }
        
        self._is_connected = False
        
        # 加载复位位置配置
        self.reset_positions = self._load_reset_positions()
    
    def connect(self) -> dict[str, Any]:
        """连接机器人"""
        try:
            # 动态导入 lerobot 模块
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lerobot" / "src"))
            
            from lerobot.robots.xlerobot import XLerobotConfig, XLerobot
            from lerobot.model.SO101Robot import SO101Kinematics
            
            # 创建机器人配置
            robot_config = XLerobotConfig(
                port1=self.config.get("port1"),
                port2=self.config.get("port2")
            )
            
            # 创建机器人实例
            self.robot = XLerobot(robot_config)
            
            # Monkey patch input() to automatically restore calibration from file
            # This is needed because XLerobot.connect() has an interactive prompt
            # that doesn't work in a non-interactive backend service
            import builtins
            original_input = builtins.input
            try:
                # Return empty string to automatically choose "restore from file"
                builtins.input = lambda *args, **kwargs: ""
                self.robot.connect()
            finally:
                # Restore original input function
                builtins.input = original_input
            
            # 初始化运动学模型
            self.kinematics_left = SO101Kinematics()
            self.kinematics_right = SO101Kinematics()
            
            # 获取初始观测值
            obs = self.robot.get_observation()
            
            # 初始化状态（从实际观测值）
            self._init_arm_state(self.left_arm_state, obs, "left")
            self._init_arm_state(self.right_arm_state, obs, "right")
            
            self._is_connected = True
            
            logger.info("机器人连接成功")
            return {
                "status": "success",
                "message": "机器人连接成功",
                "observation": obs
            }
        except Exception as e:
            logger.error(f"连接机器人时出错: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def disconnect(self) -> dict[str, Any]:
        """断开机器人连接"""
        try:
            if self.robot and self._is_connected:
                self.robot.disconnect()
                self._is_connected = False
                logger.info("机器人断开连接")
            
            return {
                "status": "success",
                "message": "机器人断开连接"
            }
        except Exception as e:
            logger.error(f"断开机器人时出错: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _init_arm_state(self, arm_state: ArmState, obs: dict, prefix: str):
        """初始化机械臂状态"""
        arm_state.target_positions = {
            "shoulder_pan": obs.get(f"{prefix}_arm_shoulder_pan.pos", 0.0),
            "shoulder_lift": obs.get(f"{prefix}_arm_shoulder_lift.pos", 0.0),
            "elbow_flex": obs.get(f"{prefix}_arm_elbow_flex.pos", 0.0),
            "wrist_flex": obs.get(f"{prefix}_arm_wrist_flex.pos", 0.0),
            "wrist_roll": obs.get(f"{prefix}_arm_wrist_roll.pos", 0.0),
            "gripper": obs.get(f"{prefix}_arm_gripper.pos", 0.0),
        }
    
    def move_to_zero_position(self, arm: str = "both") -> dict[str, Any]:
        """
        移动到零位
        
        Args:
            arm: "left", "right", 或 "both"
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "机器人未连接"}
            
            actions = {}
            
            if arm in ["left", "both"]:
                self.left_arm_state.current_x = 0.1629
                self.left_arm_state.current_y = 0.1131
                self.left_arm_state.pitch = 0.0
                self.left_arm_state.target_positions = {k: 0.0 for k in self.left_arm_state.target_positions}
                actions.update(self._get_arm_action(self.left_arm_state, "left"))
            
            if arm in ["right", "both"]:
                self.right_arm_state.current_x = 0.1629
                self.right_arm_state.current_y = 0.1131
                self.right_arm_state.pitch = 0.0
                self.right_arm_state.target_positions = {k: 0.0 for k in self.right_arm_state.target_positions}
                actions.update(self._get_arm_action(self.right_arm_state, "right"))
            
            # 发送动作
            self.robot.send_action(actions)
            
            return {
                "status": "success",
                "message": f"{arm} 移动到零位"
            }
        except Exception as e:
            logger.error(f"移动到零位时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_arm_action(self, arm_state: ArmState, prefix: str) -> dict[str, float]:
        """获取机械臂动作（P控制）"""
        obs = self.robot.get_observation()
        joint_map = self.left_joint_map if prefix == "left" else self.right_joint_map
        
        current = {j: obs[f"{prefix}_arm_{j}.pos"] for j in joint_map}
        action = {}
        
        for j in arm_state.target_positions:
            error = arm_state.target_positions[j] - current[j]
            control = arm_state.kp * error
            action[f"{joint_map[j]}.pos"] = current[j] + control
        
        return action
    
    def handle_keyboard_action(self, key_action: dict[str, Any]) -> dict[str, Any]:
        """
        处理键盘动作
        
        Args:
            key_action: 键盘动作字典，包含 arm, action, value 等
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "机器人未连接"}
            
            arm = key_action.get("arm")  # "left" 或 "right"
            action_type = key_action.get("action")
            value = key_action.get("value", 1.0)
            
            arm_state = self.left_arm_state if arm == "left" else self.right_arm_state
            kinematics = self.kinematics_left if arm == "left" else self.kinematics_right
            
            # 处理不同的动作类型
            if action_type == "shoulder_pan+":
                arm_state.target_positions["shoulder_pan"] += arm_state.degree_step
            elif action_type == "shoulder_pan-":
                arm_state.target_positions["shoulder_pan"] -= arm_state.degree_step
            elif action_type == "wrist_roll+":
                arm_state.target_positions["wrist_roll"] += arm_state.degree_step
            elif action_type == "wrist_roll-":
                arm_state.target_positions["wrist_roll"] -= arm_state.degree_step
            elif action_type == "gripper+":
                arm_state.target_positions["gripper"] += arm_state.degree_step
            elif action_type == "gripper-":
                arm_state.target_positions["gripper"] -= arm_state.degree_step
            elif action_type == "pitch+":
                arm_state.pitch += arm_state.degree_step
            elif action_type == "pitch-":
                arm_state.pitch -= arm_state.degree_step
            elif action_type == "x+":
                arm_state.current_x += arm_state.xy_step
                self._update_ik(arm_state, kinematics)
            elif action_type == "x-":
                arm_state.current_x -= arm_state.xy_step
                self._update_ik(arm_state, kinematics)
            elif action_type == "y+":
                arm_state.current_y += arm_state.xy_step
                self._update_ik(arm_state, kinematics)
            elif action_type == "y-":
                arm_state.current_y -= arm_state.xy_step
                self._update_ik(arm_state, kinematics)
            
            # 更新 wrist_flex（耦合关系）
            arm_state.target_positions["wrist_flex"] = (
                -arm_state.target_positions["shoulder_lift"]
                - arm_state.target_positions["elbow_flex"]
                + arm_state.pitch
            )
            
            # 获取动作并发送
            action = self._get_arm_action(arm_state, arm)
            self.robot.send_action(action)
            
            # 获取最新观测
            obs = self.robot.get_observation()
            
            return {
                "status": "success",
                "observation": obs
            }
        except Exception as e:
            logger.error(f"处理键盘动作时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def _update_ik(self, arm_state: ArmState, kinematics):
        """更新逆运动学解"""
        try:
            joint2, joint3 = kinematics.inverse_kinematics(arm_state.current_x, arm_state.current_y)
            arm_state.target_positions["shoulder_lift"] = joint2
            arm_state.target_positions["elbow_flex"] = joint3
            
            # 记录日志以便调试
            logger.debug(
                f"IK 更新: x={arm_state.current_x:.4f}, y={arm_state.current_y:.4f} "
                f"-> shoulder_lift={joint2:.2f}°, elbow_flex={joint3:.2f}°"
            )
        except Exception as e:
            logger.error(f"IK 计算失败: {e}")
    
    def set_step_level(self, arm: str, level: str) -> dict[str, Any]:
        """
        设置运动步长等级
        
        Args:
            arm: "left", "right", 或 "both"
            level: "slow", "normal", "fast"
        """
        try:
            # 参考 4_xlerobot_teleop_keyboard.py 的配置
            step_configs = {
                "slow": {"degree_step": 2, "xy_step": 0.005},      # 慢速：2°, 5mm
                "normal": {"degree_step": 3, "xy_step": 0.0081},   # 正常：3°, 8.1mm（参考代码默认值）
                "fast": {"degree_step": 5, "xy_step": 0.012}       # 快速：5°, 12mm
            }
            
            if level not in step_configs:
                return {"status": "error", "message": f"无效的步长等级: {level}"}
            
            config = step_configs[level]
            arms_updated = []
            
            if arm in ["left", "both"]:
                self.left_arm_state.degree_step = config["degree_step"]
                self.left_arm_state.xy_step = config["xy_step"]
                self.left_arm_state.step_level = level
                arms_updated.append("左臂")
            
            if arm in ["right", "both"]:
                self.right_arm_state.degree_step = config["degree_step"]
                self.right_arm_state.xy_step = config["xy_step"]
                self.right_arm_state.step_level = level
                arms_updated.append("右臂")
            
            message = f"{' 和 '.join(arms_updated)}步长已设置为 {level}"
            logger.info(message)
            
            return {
                "status": "success",
                "message": message,
                "config": config
            }
        except Exception as e:
            logger.error(f"设置步长等级时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_base_action(self, base_action: dict[str, Any]) -> dict[str, Any]:
        """
        处理底盘动作
        
        Args:
            base_action: 底盘动作字典，包含方向和速度
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "机器人未连接"}
            
            # 将底盘动作转换为键盘按键
            direction = base_action.get("direction")  # forward, backward, left, right, rotate_left, rotate_right
            
            key_map = {
                "forward": "i",
                "backward": "k",
                "left": "j",
                "right": "l",
                "rotate_left": "u",
                "rotate_right": "o",
            }
            
            pressed_keys = []
            if direction in key_map:
                pressed_keys.append(key_map[direction])
            
            # 转换为 numpy 数组并获取底盘动作
            keyboard_keys = np.array(pressed_keys)
            action = self.robot._from_keyboard_to_base_action(keyboard_keys) or {}
            
            if action:
                self.robot.send_action(action)
            
            # 获取最新观测
            obs = self.robot.get_observation()
            
            return {
                "status": "success",
                "observation": obs
            }
        except Exception as e:
            logger.error(f"处理底盘动作时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop_base(self) -> dict[str, Any]:
        """
        停止底盘运动
        发送速度为 0 的命令
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "机器人未连接"}
            
            # 发送速度为 0 的命令
            stop_action = {
                "x.vel": 0.0,
                "y.vel": 0.0,
                "theta.vel": 0.0
            }
            
            self.robot.send_action(stop_action)
            logger.debug("底盘已停止")
            
            return {
                "status": "success",
                "message": "底盘已停止"
            }
        except Exception as e:
            logger.error(f"停止底盘时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_observation(self) -> dict[str, Any]:
        """获取当前观测值"""
        try:
            if not self._is_connected:
                return {"status": "error", "message": "机器人未连接"}
            
            obs = self.robot.get_observation()
            
            return {
                "status": "success",
                "observation": obs
            }
        except Exception as e:
            logger.error(f"获取观测值时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def _load_reset_positions(self) -> dict[str, dict[str, float]]:
        """从配置文件加载复位位置"""
        try:
            if RESET_POSITION_CONFIG.exists():
                with open(RESET_POSITION_CONFIG, 'r', encoding='utf-8') as f:
                    positions = json.load(f)
                logger.info(f"已加载复位位置配置: {positions}")
                return positions
            else:
                # 默认使用零位作为初始复位位置
                logger.info("未找到复位位置配置，使用默认零位")
                return {
                    "left_arm": {
                        "shoulder_pan": 0.0,
                        "shoulder_lift": 0.0,
                        "elbow_flex": 0.0,
                        "wrist_flex": 0.0,
                        "wrist_roll": 0.0,
                        "gripper": 0.0,
                    },
                    "right_arm": {
                        "shoulder_pan": 0.0,
                        "shoulder_lift": 0.0,
                        "elbow_flex": 0.0,
                        "wrist_flex": 0.0,
                        "wrist_roll": 0.0,
                        "gripper": 0.0,
                    }
                }
        except Exception as e:
            logger.error(f"加载复位位置配置失败: {e}")
            return {}
    
    def _save_reset_positions(self) -> bool:
        """保存复位位置到配置文件"""
        try:
            # 确保目录存在
            RESET_POSITION_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            
            with open(RESET_POSITION_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(self.reset_positions, f, indent=2, ensure_ascii=False)
            
            logger.info(f"复位位置已保存到: {RESET_POSITION_CONFIG}")
            return True
        except Exception as e:
            logger.error(f"保存复位位置配置失败: {e}")
            return False
    
    def record_current_position_as_reset(self, arm: str = "both") -> dict[str, Any]:
        """
        记录当前位置作为复位位置
        
        Args:
            arm: "left", "right", 或 "both"
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "机器人未连接"}
            
            obs = self.robot.get_observation()
            recorded_arms = []
            
            if arm in ["left", "both"]:
                self.reset_positions["left_arm"] = {
                    "shoulder_pan": obs.get("left_arm_shoulder_pan.pos", 0.0),
                    "shoulder_lift": obs.get("left_arm_shoulder_lift.pos", 0.0),
                    "elbow_flex": obs.get("left_arm_elbow_flex.pos", 0.0),
                    "wrist_flex": obs.get("left_arm_wrist_flex.pos", 0.0),
                    "wrist_roll": obs.get("left_arm_wrist_roll.pos", 0.0),
                    "gripper": obs.get("left_arm_gripper.pos", 0.0),
                }
                recorded_arms.append("左臂")
            
            if arm in ["right", "both"]:
                self.reset_positions["right_arm"] = {
                    "shoulder_pan": obs.get("right_arm_shoulder_pan.pos", 0.0),
                    "shoulder_lift": obs.get("right_arm_shoulder_lift.pos", 0.0),
                    "elbow_flex": obs.get("right_arm_elbow_flex.pos", 0.0),
                    "wrist_flex": obs.get("right_arm_wrist_flex.pos", 0.0),
                    "wrist_roll": obs.get("right_arm_wrist_roll.pos", 0.0),
                    "gripper": obs.get("right_arm_gripper.pos", 0.0),
                }
                recorded_arms.append("右臂")
            
            # 保存到文件
            if self._save_reset_positions():
                message = f"已记录{' 和 '.join(recorded_arms)}当前位置作为复位位置"
                logger.info(message)
                return {
                    "status": "success",
                    "message": message,
                    "reset_positions": self.reset_positions
                }
            else:
                return {"status": "error", "message": "保存复位位置失败"}
                
        except Exception as e:
            logger.error(f"记录复位位置时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def move_to_reset_position(self, arm: str = "both") -> dict[str, Any]:
        """
        移动到复位位置（自定义的安全位置）
        
        Args:
            arm: "left", "right", 或 "both"
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "机器人未连接"}
            
            if not self.reset_positions:
                return {"status": "error", "message": "未设置复位位置，请先记录复位位置"}
            
            actions = {}
            moved_arms = []
            
            if arm in ["left", "both"] and "left_arm" in self.reset_positions:
                reset_pos = self.reset_positions["left_arm"]
                self.left_arm_state.target_positions = reset_pos.copy()
                actions.update(self._get_arm_action(self.left_arm_state, "left"))
                moved_arms.append("左臂")
            
            if arm in ["right", "both"] and "right_arm" in self.reset_positions:
                reset_pos = self.reset_positions["right_arm"]
                self.right_arm_state.target_positions = reset_pos.copy()
                actions.update(self._get_arm_action(self.right_arm_state, "right"))
                moved_arms.append("右臂")
            
            if not actions:
                return {"status": "error", "message": "未找到对应机械臂的复位位置"}
            
            # 发送动作
            self.robot.send_action(actions)
            
            message = f"{' 和 '.join(moved_arms)}正在移动到复位位置"
            logger.info(message)
            return {
                "status": "success",
                "message": message
            }
        except Exception as e:
            logger.error(f"移动到复位位置时出错: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_reset_positions(self) -> dict[str, Any]:
        """获取当前保存的复位位置"""
        return {
            "status": "success",
            "reset_positions": self.reset_positions
        }

