"""
键位映射配置管理器

负责管理键盘和Xbox手柄的键位映射配置，包括：
- 加载和保存配置文件
- 管理多个配置预设
- 配置验证
- 构建反向键位映射（Key → Action）
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class KeymapManager:
    """键位映射配置管理器"""

    # 内置预设列表（不可删除）
    BUILTIN_PROFILES = ["default", "wasd", "arrows"]

    # 必需的动作列表
    REQUIRED_ACTIONS = {
        "left_arm": [
            "shoulder_pan+", "shoulder_pan-",
            "wrist_roll+", "wrist_roll-",
            "gripper+", "gripper-",
            "x+", "x-", "y+", "y-",
            "pitch+", "pitch-",
            "reset"
        ],
        "right_arm": [
            "shoulder_pan+", "shoulder_pan-",
            "wrist_roll+", "wrist_roll-",
            "gripper+", "gripper-",
            "x+", "x-", "y+", "y-",
            "pitch+", "pitch-",
            "reset"
        ],
        "base": [
            "forward", "backward",
            "left", "right",
            "rotate_left", "rotate_right"
        ]
    }

    def __init__(self):
        """初始化配置管理器"""
        self.config_path = Path.home() / ".cache" / "xlerobot_web" / "keymap_config.json"
        self.backup_path = self.config_path.with_suffix('.backup.json')
        self.config = self._load_config()
        self.current_profile = self.config["current_profile"]
        self.reverse_keymap = {}  # Key → (category, action) 映射
        self._build_reverse_keymap()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置（包含3个内置预设）"""
        return {
            "version": "1.0.0",
            "current_profile": "default",
            "profiles": {
                "default": {
                    "name": "默认配置",
                    "description": "原始键位配置",
                    "keyboard": {
                        "left_arm": {
                            "shoulder_pan+": "Q", "shoulder_pan-": "E",
                            "wrist_roll+": "R", "wrist_roll-": "F",
                            "gripper+": "T", "gripper-": "G",
                            "x+": "W", "x-": "S",
                            "y+": "A", "y-": "D",
                            "pitch+": "Z", "pitch-": "X",
                            "reset": "C"
                        },
                        "right_arm": {
                            "shoulder_pan+": "7", "shoulder_pan-": "9",
                            "wrist_roll+": "/", "wrist_roll-": "*",
                            "gripper+": "+", "gripper-": "-",
                            "x+": "8", "x-": "2",
                            "y+": "4", "y-": "6",
                            "pitch+": "1", "pitch-": "3",
                            "reset": "0"
                        },
                        "base": {
                            "forward": "I", "backward": "K",
                            "left": "J", "right": "L",
                            "rotate_left": "U", "rotate_right": "O"
                        }
                    }
                },
                "wasd": {
                    "name": "WASD方案",
                    "description": "使用WASD控制底盘，方向键控制左臂",
                    "keyboard": {
                        "left_arm": {
                            "shoulder_pan+": "Q", "shoulder_pan-": "E",
                            "wrist_roll+": "R", "wrist_roll-": "F",
                            "gripper+": "T", "gripper-": "G",
                            "x+": "ArrowUp", "x-": "ArrowDown",
                            "y+": "ArrowLeft", "y-": "ArrowRight",
                            "pitch+": "Z", "pitch-": "X",
                            "reset": "C"
                        },
                        "right_arm": {
                            "shoulder_pan+": "7", "shoulder_pan-": "9",
                            "wrist_roll+": "/", "wrist_roll-": "*",
                            "gripper+": "+", "gripper-": "-",
                            "x+": "8", "x-": "2",
                            "y+": "4", "y-": "6",
                            "pitch+": "1", "pitch-": "3",
                            "reset": "0"
                        },
                        "base": {
                            "forward": "W", "backward": "S",
                            "left": "A", "right": "D",
                            "rotate_left": "Q", "rotate_right": "E"
                        }
                    }
                },
                "arrows": {
                    "name": "方向键方案",
                    "description": "使用方向键控制底盘移动和旋转",
                    "keyboard": {
                        "left_arm": {
                            "shoulder_pan+": "Q", "shoulder_pan-": "E",
                            "wrist_roll+": "R", "wrist_roll-": "F",
                            "gripper+": "T", "gripper-": "G",
                            "x+": "W", "x-": "S",
                            "y+": "A", "y-": "D",
                            "pitch+": "Z", "pitch-": "X",
                            "reset": "C"
                        },
                        "right_arm": {
                            "shoulder_pan+": "7", "shoulder_pan-": "9",
                            "wrist_roll+": "/", "wrist_roll-": "*",
                            "gripper+": "+", "gripper-": "-",
                            "x+": "8", "x-": "2",
                            "y+": "4", "y-": "6",
                            "pitch+": "1", "pitch-": "3",
                            "reset": "0"
                        },
                        "base": {
                            "forward": "ArrowUp", "backward": "ArrowDown",
                            "left": "ArrowLeft", "right": "ArrowRight",
                            "rotate_left": "U", "rotate_right": "O"
                        }
                    }
                }
            }
        }

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件，失败则使用默认配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"成功加载键位配置: {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"加载键位配置失败: {e}，使用默认配置")
                return self._get_default_config()
        else:
            logger.info("配置文件不存在，创建默认配置")
            config = self._get_default_config()
            self._save_config(config)
            return config

    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置文件，先备份旧配置"""
        if config is None:
            config = self.config

        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 备份旧配置
            if self.config_path.exists():
                shutil.copy(self.config_path, self.backup_path)
                logger.info(f"已备份旧配置到: {self.backup_path}")

            # 保存新配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"成功保存键位配置: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存键位配置失败: {e}")
            return False

    def _build_reverse_keymap(self):
        """构建反向键位映射（Key → (category, action)）"""
        self.reverse_keymap = {}

        current_keymap = self.get_current_keymap()
        if not current_keymap:
            logger.warning("无法构建反向映射：当前配置无效")
            return

        keyboard = current_keymap.get("keyboard", {})

        # 遍历所有类别
        for category in ["left_arm", "right_arm", "base"]:
            category_map = keyboard.get(category, {})
            for action, key in category_map.items():
                key_upper = key.upper()
                self.reverse_keymap[key_upper] = (category, action)

        logger.info(f"已构建反向键位映射，共 {len(self.reverse_keymap)} 个按键")

    def get_key_action(self, key: str) -> Optional[Tuple[str, str]]:
        """
        根据按键获取对应的动作

        Args:
            key: 按键字符串（会自动转大写）

        Returns:
            (category, action) 元组，如 ("left_arm", "x+")
            如果按键未映射则返回 None
        """
        key_upper = key.upper()
        return self.reverse_keymap.get(key_upper)

    def get_all_profiles(self) -> Dict[str, Any]:
        """获取所有配置预设"""
        return self.config.get("profiles", {})

    def get_current_keymap(self) -> Optional[Dict[str, Any]]:
        """获取当前激活的键位配置"""
        profiles = self.config.get("profiles", {})
        current = self.config.get("current_profile", "default")
        return profiles.get(current)

    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """获取指定的配置预设"""
        profiles = self.config.get("profiles", {})
        return profiles.get(profile_name)

    def switch_profile(self, profile_name: str) -> Tuple[bool, str]:
        """
        切换配置预设

        Args:
            profile_name: 预设名称

        Returns:
            (成功, 消息) 元组
        """
        profiles = self.config.get("profiles", {})

        if profile_name not in profiles:
            return False, f"配置预设 '{profile_name}' 不存在"

        self.config["current_profile"] = profile_name
        self.current_profile = profile_name

        if self._save_config():
            self._build_reverse_keymap()
            return True, f"已切换到配置预设: {profile_name}"
        else:
            return False, "保存配置失败"

    def create_profile(self, profile_name: str, name: str, description: str,
                      keymap: Dict[str, Any]) -> Tuple[bool, str]:
        """
        创建新的配置预设

        Args:
            profile_name: 预设ID（英文标识符）
            name: 预设显示名称
            description: 预设描述
            keymap: 键位映射配置

        Returns:
            (成功, 消息) 元组
        """
        if profile_name in self.BUILTIN_PROFILES:
            return False, f"不能覆盖内置预设: {profile_name}"

        # 验证键位配置
        valid, msg = self.validate_keymap(keymap)
        if not valid:
            return False, f"配置验证失败: {msg}"

        # 创建新预设
        self.config["profiles"][profile_name] = {
            "name": name,
            "description": description,
            "keyboard": keymap
        }

        if self._save_config():
            return True, f"成功创建配置预设: {name}"
        else:
            return False, "保存配置失败"

    def update_profile(self, profile_name: str, keymap: Dict[str, Any]) -> Tuple[bool, str]:
        """
        更新配置预设的键位映射

        Args:
            profile_name: 预设名称
            keymap: 新的键位映射配置

        Returns:
            (成功, 消息) 元组
        """
        profiles = self.config.get("profiles", {})

        if profile_name not in profiles:
            return False, f"配置预设 '{profile_name}' 不存在"

        # 验证键位配置
        valid, msg = self.validate_keymap(keymap)
        if not valid:
            return False, f"配置验证失败: {msg}"

        # 更新键位映射
        self.config["profiles"][profile_name]["keyboard"] = keymap

        if self._save_config():
            # 如果更新的是当前预设，重建反向映射
            if profile_name == self.current_profile:
                self._build_reverse_keymap()
            return True, f"成功更新配置预设: {profile_name}"
        else:
            return False, "保存配置失败"

    def delete_profile(self, profile_name: str) -> Tuple[bool, str]:
        """
        删除配置预设（内置预设不可删除）

        Args:
            profile_name: 预设名称

        Returns:
            (成功, 消息) 元组
        """
        if profile_name in self.BUILTIN_PROFILES:
            return False, f"不能删除内置预设: {profile_name}"

        profiles = self.config.get("profiles", {})

        if profile_name not in profiles:
            return False, f"配置预设 '{profile_name}' 不存在"

        # 如果删除的是当前预设，切换到默认预设
        if profile_name == self.current_profile:
            self.config["current_profile"] = "default"
            self.current_profile = "default"

        # 删除预设
        del self.config["profiles"][profile_name]

        if self._save_config():
            self._build_reverse_keymap()
            return True, f"成功删除配置预设: {profile_name}"
        else:
            return False, "保存配置失败"

    def validate_keymap(self, keymap: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证键位配置的有效性

        Args:
            keymap: 键位映射配置

        Returns:
            (是否有效, 错误消息) 元组
        """
        # 检查必需的类别
        for category in ["left_arm", "right_arm", "base"]:
            if category not in keymap:
                return False, f"缺少必需的类别: {category}"

            category_map = keymap[category]

            # 检查必需的动作
            required = self.REQUIRED_ACTIONS[category]
            for action in required:
                if action not in category_map:
                    return False, f"缺少必需的动作: {category}.{action}"

        # 检查按键冲突
        all_keys = {}
        for category in ["left_arm", "right_arm", "base"]:
            category_map = keymap[category]
            for action, key in category_map.items():
                if not isinstance(key, str) or len(key) == 0:
                    return False, f"无效的按键: {category}.{action} = {key}"

                key_upper = key.upper()
                if key_upper in all_keys:
                    return False, f"按键冲突: '{key}' 被 {all_keys[key_upper]} 和 {category}.{action} 同时使用"

                all_keys[key_upper] = f"{category}.{action}"

        return True, "配置有效"

    def get_full_config(self) -> Dict[str, Any]:
        """获取完整的配置对象"""
        return self.config.copy()
