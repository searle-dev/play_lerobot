#!/usr/bin/env python3
"""Record the current XLeRobot pose used by the Xbox Back reset action."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LEROBOT_SRC = ROOT_DIR / "lerobot" / "src"
DEFAULT_RESET_POSE = ROOT_DIR / "config" / "reset_pose.json"


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
    parser = argparse.ArgumentParser(description="Record current XLeRobot reset pose")
    parser.add_argument("--port1", default=os.getenv("XLEROBOT_PORT1") or os.getenv("XLEROBOT_LEFT_ARM", "/dev/ttyACM0"))
    parser.add_argument("--port2", default=os.getenv("XLEROBOT_PORT2") or os.getenv("XLEROBOT_RIGHT_ARM", "/dev/ttyACM1"))
    parser.add_argument("--robot-id", default=os.getenv("XLEROBOT_ID", "my_xlerobot"))
    parser.add_argument("--output", type=Path, default=Path(os.getenv("XLEROBOT_RESET_POSE", DEFAULT_RESET_POSE)))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sys.path.insert(0, str(LEROBOT_SRC))

    from lerobot.robots.xlerobot import XLerobot, XLerobotConfig

    robot = XLerobot(XLerobotConfig(id=args.robot_id, port1=args.port1, port2=args.port2))
    print(f"Connecting with port1={args.port1}, port2={args.port2}")
    try:
        robot.connect(calibrate=False)
        obs = robot.get_observation()
        pose = {
            "left_arm": {
                "shoulder_pan": obs["left_arm_shoulder_pan.pos"],
                "shoulder_lift": obs["left_arm_shoulder_lift.pos"],
                "elbow_flex": obs["left_arm_elbow_flex.pos"],
                "wrist_flex": obs["left_arm_wrist_flex.pos"],
                "wrist_roll": obs["left_arm_wrist_roll.pos"],
                "gripper": obs["left_arm_gripper.pos"],
            },
            "right_arm": {
                "shoulder_pan": obs["right_arm_shoulder_pan.pos"],
                "shoulder_lift": obs["right_arm_shoulder_lift.pos"],
                "elbow_flex": obs["right_arm_elbow_flex.pos"],
                "wrist_flex": obs["right_arm_wrist_flex.pos"],
                "wrist_roll": obs["right_arm_wrist_roll.pos"],
                "gripper": obs["right_arm_gripper.pos"],
            },
            "head": {
                "head_motor_1": obs["head_motor_1.pos"],
                "head_motor_2": obs["head_motor_2.pos"],
            },
        }
    finally:
        if robot.is_connected:
            robot.disconnect()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pose, indent=2) + "\n")
    print(f"Reset pose saved to {args.output}")


if __name__ == "__main__":
    main()
