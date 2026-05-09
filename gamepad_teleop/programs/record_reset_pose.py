#!/usr/bin/env python3
"""Record the current XLeRobot pose with real-time preview."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LEROBOT_SRC = ROOT_DIR / "lerobot" / "src"
DEFAULT_RESET_POSE = ROOT_DIR / "config" / "reset_pose.json"

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


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


def read_pose(obs: dict) -> dict:
    return {
        "left_arm": {j: obs[f"left_arm_{j}.pos"] for j in JOINTS},
        "right_arm": {j: obs[f"right_arm_{j}.pos"] for j in JOINTS},
        "head": {
            "head_motor_1": obs["head_motor_1.pos"],
            "head_motor_2": obs["head_motor_2.pos"],
        },
    }


def print_pose(pose: dict) -> None:
    print("\033[2J\033[H", end="")  # clear screen
    print("=" * 70)
    print("  REAL-TIME JOINT ANGLES  —  adjust arms then press Enter to save")
    print("  Ctrl+C to quit without saving")
    print("=" * 70)
    print()
    print(f"  {'Joint':<16} {'Left':>10} {'Right':>10} {'Diff':>10}")
    print(f"  {'─' * 16} {'─' * 10} {'─' * 10} {'─' * 10}")
    for j in JOINTS:
        l = pose["left_arm"][j]
        r = pose["right_arm"][j]
        diff = abs(l - r)
        flag = " ⚠" if diff > 5 else ""
        print(f"  {j:<16} {l:>10.1f} {r:>10.1f} {diff:>10.1f}{flag}")
    print()
    h1 = pose["head"]["head_motor_1"]
    h2 = pose["head"]["head_motor_2"]
    print(f"  {'head_motor_1':<16} {h1:>10.1f}")
    print(f"  {'head_motor_2':<16} {h2:>10.1f}")
    print()
    print("  ⚠ = diff > 5°, check if arms are symmetric")
    print()


def main() -> None:
    args = parse_args()
    sys.path.insert(0, str(LEROBOT_SRC))

    from lerobot.robots.xlerobot import XLerobot, XLerobotConfig

    robot = XLerobot(XLerobotConfig(id=args.robot_id, port1=args.port1, port2=args.port2))
    print(f"Connecting with port1={args.port1}, port2={args.port2}")

    import select
    import termios
    import tty

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        robot.connect()
        tty.setcbreak(sys.stdin.fileno())

        pose = None
        while True:
            obs = robot.get_observation()
            pose = read_pose(obs)
            print_pose(pose)
            print("  >>> Press Enter to SAVE, Ctrl+C to cancel <<<")

            # Check for Enter key (non-blocking)
            if select.select([sys.stdin], [], [], 0.2)[0]:
                ch = sys.stdin.read(1)
                if ch in ("\n", "\r"):
                    break

        # Save
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(pose, indent=2) + "\n")
        print(f"\n  ✅ Reset pose saved to {args.output}\n")

    except KeyboardInterrupt:
        print("\n  Cancelled, nothing saved.\n")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        if robot.is_connected:
            robot.disconnect()


if __name__ == "__main__":
    main()
