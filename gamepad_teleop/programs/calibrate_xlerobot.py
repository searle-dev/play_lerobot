#!/usr/bin/env python3
"""Run XLeRobot calibration without starting teleoperation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LEROBOT_SRC = ROOT_DIR / "lerobot" / "src"


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
    parser = argparse.ArgumentParser(description="Calibrate XLeRobot motors")
    parser.add_argument("--port1", default=os.getenv("XLEROBOT_PORT1") or os.getenv("XLEROBOT_LEFT_ARM", "/dev/ttyACM0"))
    parser.add_argument("--port2", default=os.getenv("XLEROBOT_PORT2") or os.getenv("XLEROBOT_RIGHT_ARM", "/dev/ttyACM1"))
    parser.add_argument("--robot-id", default=os.getenv("XLEROBOT_ID", "my_xlerobot"))
    parser.add_argument("--force", action="store_true", help="Run manual calibration even if a calibration file exists.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sys.path.insert(0, str(LEROBOT_SRC))

    from lerobot.robots.xlerobot import XLerobot, XLerobotConfig

    robot = XLerobot(
        XLerobotConfig(
            id=args.robot_id,
            port1=args.port1,
            port2=args.port2,
        )
    )

    print(f"Calibration file: {robot.calibration_fpath}")
    print(f"port1 left arm + head: {args.port1}")
    print(f"port2 right arm + base: {args.port2}")

    try:
        robot.bus1.connect()
        robot.bus2.connect()
        if args.force or not robot.calibration_fpath.is_file():
            robot.calibrate()
        else:
            print("Calibration file already exists. Use --force to recalibrate.")
    finally:
        if robot.bus1.is_connected:
            robot.bus1.disconnect()
        if robot.bus2.is_connected:
            robot.bus2.disconnect()


if __name__ == "__main__":
    main()
