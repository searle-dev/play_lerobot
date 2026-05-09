#!/usr/bin/env python3
"""Run XLeRobot Joy-Con teleoperation from the local LeRobot checkout."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LEROBOT_DIR = ROOT_DIR / "lerobot"
LEROBOT_SRC = LEROBOT_DIR / "src"
XLEROBOT_SOFTWARE = ROOT_DIR / "XLeRobot" / "software"
JOYCON_SCRIPT = LEROBOT_DIR / "examples" / "xlerobot" / "7_xlerobot_teleop_joycon.py"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_args() -> argparse.Namespace:
    load_dotenv(ROOT_DIR / ".env")
    parser = argparse.ArgumentParser(description="XLeRobot Joy-Con teleoperation")
    parser.add_argument("--port1", default=os.getenv("XLEROBOT_PORT1") or os.getenv("XLEROBOT_LEFT_ARM", "/dev/ttyACM0"))
    parser.add_argument("--port2", default=os.getenv("XLEROBOT_PORT2") or os.getenv("XLEROBOT_RIGHT_ARM", "/dev/ttyACM1"))
    parser.add_argument("--robot-id", default=os.getenv("XLEROBOT_ID", "my_xlerobot"))
    parser.add_argument(
        "--mode",
        choices=("both", "right-only"),
        default=os.getenv("XLEROBOT_JOYCON_MODE", "both"),
        help="Use both Joy-Cons or only the right Joy-Con for bring-up/debugging.",
    )
    parser.add_argument(
        "--no-disable-torque-on-disconnect",
        action="store_true",
        help="Keep torque enabled when disconnecting.",
    )
    return parser.parse_args()


def load_official_joycon_module():
    if not JOYCON_SCRIPT.exists():
        raise FileNotFoundError(f"Missing official Joy-Con example: {JOYCON_SCRIPT}")

    sys.path.insert(0, str(ROOT_DIR))
    sys.path.insert(0, str(XLEROBOT_SOFTWARE))
    sys.path.insert(0, str(LEROBOT_SRC))
    sys.path.insert(0, str(LEROBOT_DIR))

    spec = importlib.util.spec_from_file_location("xlerobot_official_joycon", JOYCON_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {JOYCON_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    args = parse_args()
    module = load_official_joycon_module()
    original_config = module.XLerobotConfig

    def config_factory(*_args, **_kwargs):
        return original_config(
            id=args.robot_id,
            port1=args.port1,
            port2=args.port2,
            disable_torque_on_disconnect=not args.no_disable_torque_on_disconnect,
        )

    module.XLerobotConfig = config_factory
    if args.mode == "right-only":
        main_right_only(module)
    else:
        module.main()


def main_right_only(module) -> None:
    fps = 30
    robot = module.XLerobot(module.XLerobotConfig())
    joycon_right = None

    try:
        robot.connect()
        print("[MAIN] Successfully connected to robot")

        print("[MAIN] Initializing right Joy-Con controller...")
        joycon_right = module.FixedAxesJoyconRobotics(
            "right",
            dof_speed=[2, 2, 2, 1, 1, 1],
        )
        print("[MAIN] Right Joy-Con controller connected")

        obs = robot.get_observation()
        kin_left = module.SO101Kinematics()
        kin_right = module.SO101Kinematics()
        left_arm = module.SimpleTeleopArm(module.LEFT_JOINT_MAP, obs, kin_left, prefix="left")
        right_arm = module.SimpleTeleopArm(module.RIGHT_JOINT_MAP, obs, kin_right, prefix="right")
        head_control = module.SimpleHeadControl(obs)

        left_arm.move_to_zero_position(robot)
        right_arm.move_to_zero_position(robot)
        head_control.move_to_zero_position(robot)

        while True:
            loop_start = module.time.perf_counter()
            pose_right, gripper_right, control_button_right = joycon_right.get_control()
            print(
                f"pose_right: {pose_right}, "
                f"gripper_right: {gripper_right}, "
                f"control_button_right: {control_button_right}"
            )

            if control_button_right == 8:
                print("[MAIN] Reset to zero position!")
                right_arm.move_to_zero_position(robot)
                left_arm.move_to_zero_position(robot)
                head_control.move_to_zero_position(robot)
                continue

            right_arm.target_positions["gripper"] = gripper_right
            right_arm.handle_joycon_input(pose_right, gripper_right)

            right_action = right_arm.p_control_action(robot)
            left_action = left_arm.p_control_action(robot)
            head_action = head_control.p_control_action(robot)

            base_action = module.get_joycon_base_action(joycon_right, robot)
            speed_multiplier = module.get_joycon_speed_control(joycon_right)
            if base_action:
                for key in base_action:
                    if "vel" in key or "velocity" in key:
                        base_action[key] *= speed_multiplier

            action = {**left_action, **right_action, **head_action, **base_action}
            robot.send_action(action)
            module.precise_sleep(max(1 / fps - (module.time.perf_counter() - loop_start), 0))
    finally:
        if joycon_right is not None:
            joycon_right.disconnect()
        robot.disconnect()
        print("Teleoperation ended.")


if __name__ == "__main__":
    main()
