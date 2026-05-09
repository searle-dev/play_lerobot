#!/usr/bin/env python3
"""Run XLeRobot Xbox teleoperation from the local LeRobot checkout."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LEROBOT_DIR = ROOT_DIR / "lerobot"
LEROBOT_SRC = LEROBOT_DIR / "src"
XBOX_SCRIPT = LEROBOT_DIR / "examples" / "xlerobot" / "5_xlerobot_teleop_xbox.py"


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
    parser = argparse.ArgumentParser(description="XLeRobot Xbox controller teleoperation")
    parser.add_argument("--port1", default=os.getenv("XLEROBOT_PORT1") or os.getenv("XLEROBOT_LEFT_ARM", "/dev/ttyACM0"))
    parser.add_argument("--port2", default=os.getenv("XLEROBOT_PORT2") or os.getenv("XLEROBOT_RIGHT_ARM", "/dev/ttyACM1"))
    parser.add_argument("--robot-id", default=os.getenv("XLEROBOT_ID", "my_xlerobot"))
    parser.add_argument(
        "--no-disable-torque-on-disconnect",
        action="store_true",
        help="Keep torque enabled when disconnecting.",
    )
    return parser.parse_args()


def load_official_xbox_module():
    if not XBOX_SCRIPT.exists():
        raise FileNotFoundError(f"Missing official Xbox example: {XBOX_SCRIPT}")

    sys.path.insert(0, str(LEROBOT_SRC))
    sys.path.insert(0, str(LEROBOT_DIR))

    spec = importlib.util.spec_from_file_location("xlerobot_official_xbox", XBOX_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {XBOX_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    args = parse_args()
    module = load_official_xbox_module()
    original_config = module.XLerobotConfig

    def config_factory():
        return original_config(
            id=args.robot_id,
            port1=args.port1,
            port2=args.port2,
            disable_torque_on_disconnect=not args.no_disable_torque_on_disconnect,
        )

    module.XLerobotConfig = config_factory
    module.main()


if __name__ == "__main__":
    main()
