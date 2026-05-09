#!/usr/bin/env python3
"""Run XLeRobot Joy-Con teleoperation with custom reset-pose support."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LEROBOT_DIR = ROOT_DIR / "lerobot"
LEROBOT_SRC = LEROBOT_DIR / "src"
XLEROBOT_SOFTWARE = ROOT_DIR / "XLeRobot" / "software"
JOYCON_SCRIPT = LEROBOT_DIR / "examples" / "xlerobot" / "7_xlerobot_teleop_joycon.py"
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
    parser.add_argument(
        "--reset-pose",
        type=Path,
        default=Path(os.getenv("XLEROBOT_RESET_POSE", str(DEFAULT_RESET_POSE))),
        help="Path to reset_pose.json (default: config/reset_pose.json)",
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


def load_reset_pose(path: Path) -> dict | None:
    if not path.exists():
        print(f"[RESET] No reset pose file at {path}, using zero position")
        return None
    pose = json.loads(path.read_text())
    print(f"[RESET] Loaded reset pose from {path}")
    return pose


def compute_neutral_targets(module):
    """Joint angles when Joy-Con is in neutral position (all zeros)."""
    kin = module.SO101Kinematics()
    sl, ef = kin.inverse_kinematics(0.1629, 0.1131)
    wf = -sl - ef + 10  # pitch_wrist_base = 10
    return {
        "shoulder_pan": 0.0,
        "shoulder_lift": sl,
        "elbow_flex": ef,
        "wrist_flex": wf,
        "wrist_roll": 0.0,
    }


def compute_offsets(reset_pose, neutral):
    """Offset so that neutral Joy-Con maps to reset pose instead of default IK position."""
    offsets = {}
    for key in ("left_arm", "right_arm"):
        offsets[key] = {j: reset_pose[key][j] - neutral[j] for j in neutral}
    return offsets


IK_JOINTS = {"shoulder_lift", "elbow_flex", "wrist_flex"}


def apply_offsets(arm, offset):
    for j, v in offset.items():
        if j not in IK_JOINTS:
            arm.target_positions[j] += v


def converge_to_pose(arms, head_control, robot, reset_pose, time_mod, sleep_fn, fps=30, max_seconds=3, threshold=2.0):
    """Run P-control in a tight loop until all joints converge to the reset pose."""
    for arm, key in arms:
        arm.target_positions = reset_pose[key].copy()
        arm.current_x = 0.1629
        arm.current_y = 0.1131
        arm.pitch = 0.0
    if head_control and "head" in reset_pose:
        head_control.target_positions = reset_pose["head"].copy()

    max_iters = int(fps * max_seconds)
    for i in range(max_iters):
        t0 = time_mod.perf_counter()
        actions = {}
        for arm, _ in arms:
            actions.update(arm.p_control_action(robot))
        if head_control:
            actions.update(head_control.p_control_action(robot))
        robot.send_action(actions)

        # Check convergence every 10 frames
        if i > 0 and i % 10 == 0:
            obs = robot.get_observation()
            max_err = 0.0
            for arm, key in arms:
                for j, target in reset_pose[key].items():
                    current = obs.get(f"{arm.prefix}_arm_{j}.pos", 0.0)
                    max_err = max(max_err, abs(target - current))
            if head_control and "head" in reset_pose:
                for j, target in reset_pose["head"].items():
                    current = obs.get(f"{j}.pos", 0.0)
                    max_err = max(max_err, abs(target - current))
            if max_err < threshold:
                print(f"[RESET] Converged in {i + 1} frames (max error {max_err:.1f}°)")
                return
        sleep_fn(max(1 / fps - (time_mod.perf_counter() - t0), 0))
    print(f"[RESET] Reached {max_iters} frames, proceeding (may not be fully converged)")


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
        main_right_only(module, args.reset_pose)
    else:
        main_both(module, args.reset_pose)


def main_both(module, reset_pose_path: Path) -> None:
    fps = 30
    reset_pose = load_reset_pose(reset_pose_path)

    robot = module.XLerobot(module.XLerobotConfig())
    joycon_right = None
    joycon_left = None

    try:
        robot.connect()
        print("[MAIN] Successfully connected to robot")

        print("[MAIN] Initializing right Joy-Con controller...")
        joycon_right = module.FixedAxesJoyconRobotics("right", dof_speed=[2, 2, 2, 1, 1, 1])
        print("[MAIN] Right Joy-Con controller connected")
        print("[MAIN] Initializing left Joy-Con controller...")
        joycon_left = module.FixedAxesJoyconRobotics("left", dof_speed=[2, 2, 2, 1, 1, 1])
        print("[MAIN] Left Joy-Con controller connected")

        obs = robot.get_observation()
        kin_left = module.SO101Kinematics()
        kin_right = module.SO101Kinematics()
        left_arm = module.SimpleTeleopArm(module.LEFT_JOINT_MAP, obs, kin_left, prefix="left")
        right_arm = module.SimpleTeleopArm(module.RIGHT_JOINT_MAP, obs, kin_right, prefix="right")
        head_control = module.SimpleHeadControl(obs)

        # Compute pose offsets so neutral Joy-Con maps to reset pose
        offsets = None
        if reset_pose:
            neutral = compute_neutral_targets(module)
            offsets = compute_offsets(reset_pose, neutral)
            print(f"[RESET] Arm offsets computed (shoulder_lift L={offsets['left_arm']['shoulder_lift']:.1f}° R={offsets['right_arm']['shoulder_lift']:.1f}°)")

            print("[MAIN] Moving to reset pose on startup...")
            converge_to_pose(
                [(left_arm, "left_arm"), (right_arm, "right_arm")],
                head_control, robot, reset_pose,
                module.time, module.precise_sleep,
            )
            # Reset Joy-Con IMU so current orientation = neutral
            joycon_right.reset_joycon()
            joycon_left.reset_joycon()
        else:
            left_arm.move_to_zero_position(robot)
            right_arm.move_to_zero_position(robot)
            head_control.move_to_zero_position(robot)

        print("[MAIN] Starting teleoperation loop...")
        while True:
            loop_start = module.time.perf_counter()
            pose_right, gripper_right, control_button_right = joycon_right.get_control()
            pose_left, gripper_left, control_button_left = joycon_left.get_control()

            # Right Joy-Con + button → reset right arm only
            if control_button_right == 8:
                if reset_pose:
                    print("[MAIN] Right Joy-Con reset → right arm to reset pose")
                    converge_to_pose(
                        [(right_arm, "right_arm")], None, robot, reset_pose,
                        module.time, module.precise_sleep, max_seconds=2,
                    )
                    joycon_right.reset_joycon()
                else:
                    right_arm.move_to_zero_position(robot)
                continue

            # Left Joy-Con - button → reset left arm + head
            if joycon_left.reset_button == 1:
                if reset_pose:
                    print("[MAIN] Left Joy-Con reset → left arm + head to reset pose")
                    converge_to_pose(
                        [(left_arm, "left_arm")], head_control, robot, reset_pose,
                        module.time, module.precise_sleep, max_seconds=2,
                    )
                    joycon_left.reset_joycon()
                else:
                    left_arm.move_to_zero_position(robot)
                    head_control.move_to_zero_position(robot)
                continue

            right_arm.target_positions["gripper"] = gripper_right
            left_arm.target_positions["gripper"] = gripper_left

            precision_r = joycon_right.joycon.get_button_right_sr() == 1 or joycon_right.joycon.get_button_right_sl() == 1
            precision_l = joycon_left.joycon.get_button_left_sr() == 1 or joycon_left.joycon.get_button_left_sl() == 1

            right_arm.handle_joycon_input(pose_right, gripper_right, precision=precision_r)
            left_arm.handle_joycon_input(pose_left, gripper_left, precision=precision_l)

            # Apply reset pose offsets so neutral Joy-Con = reset pose
            if offsets:
                apply_offsets(right_arm, offsets["right_arm"])
                apply_offsets(left_arm, offsets["left_arm"])

            right_action = right_arm.p_control_action(robot)
            left_action = left_arm.p_control_action(robot)
            head_control.handle_joycon_input(joycon_left)
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
        if joycon_left is not None:
            joycon_left.disconnect()
        robot.disconnect()
        print("Teleoperation ended.")


def main_right_only(module, reset_pose_path: Path) -> None:
    fps = 30
    reset_pose = load_reset_pose(reset_pose_path)

    robot = module.XLerobot(module.XLerobotConfig())
    joycon_right = None

    try:
        robot.connect()
        print("[MAIN] Successfully connected to robot")

        print("[MAIN] Initializing right Joy-Con controller...")
        joycon_right = module.FixedAxesJoyconRobotics("right", dof_speed=[2, 2, 2, 1, 1, 1])
        print("[MAIN] Right Joy-Con controller connected")

        obs = robot.get_observation()
        kin_left = module.SO101Kinematics()
        kin_right = module.SO101Kinematics()
        left_arm = module.SimpleTeleopArm(module.LEFT_JOINT_MAP, obs, kin_left, prefix="left")
        right_arm = module.SimpleTeleopArm(module.RIGHT_JOINT_MAP, obs, kin_right, prefix="right")
        head_control = module.SimpleHeadControl(obs)

        offsets = None
        if reset_pose:
            neutral = compute_neutral_targets(module)
            offsets = compute_offsets(reset_pose, neutral)

            print("[MAIN] Moving to reset pose on startup...")
            converge_to_pose(
                [(left_arm, "left_arm"), (right_arm, "right_arm")],
                head_control, robot, reset_pose,
                module.time, module.precise_sleep,
            )
            joycon_right.reset_joycon()
        else:
            left_arm.move_to_zero_position(robot)
            right_arm.move_to_zero_position(robot)
            head_control.move_to_zero_position(robot)

        print("[MAIN] Starting teleoperation loop...")
        while True:
            loop_start = module.time.perf_counter()
            pose_right, gripper_right, control_button_right = joycon_right.get_control()

            if control_button_right == 8:
                if reset_pose:
                    print("[MAIN] Reset to reset pose!")
                    converge_to_pose(
                        [(left_arm, "left_arm"), (right_arm, "right_arm")],
                        head_control, robot, reset_pose,
                        module.time, module.precise_sleep, max_seconds=2,
                    )
                    joycon_right.reset_joycon()
                else:
                    right_arm.move_to_zero_position(robot)
                    left_arm.move_to_zero_position(robot)
                    head_control.move_to_zero_position(robot)
                continue

            right_arm.target_positions["gripper"] = gripper_right
            precision_r = joycon_right.joycon.get_button_right_sr() == 1 or joycon_right.joycon.get_button_right_sl() == 1
            right_arm.handle_joycon_input(pose_right, gripper_right, precision=precision_r)
            if offsets:
                apply_offsets(right_arm, offsets["right_arm"])

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
