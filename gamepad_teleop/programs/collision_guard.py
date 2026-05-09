"""Collision detection for STS3215 servo-based arms.

Detects when a joint is stuck: high load but the actual position is not
changing.  During normal movement, even under high load, the actual joint
position changes every frame.  During a collision, the motor fights but
the joint doesn't move.
"""

from __future__ import annotations

import csv
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


class CollisionGuard:
    WARMUP_ERROR = 5.0

    def __init__(
        self,
        robot: Any,
        *,
        load_threshold: int = 300,
        stuck_velocity_threshold: float = 0.5,
        stall_error_threshold: float = 8.0,
        sustain_frames: int = 6,
        freeze_frames: int = 10,
        monitor_only: bool = False,
    ):
        """
        Args:
            robot: XLerobot instance.
            load_threshold: Present_Load magnitude (0-1000).
            stuck_velocity_threshold: If actual position changes less than
                this many degrees per frame, the joint is considered stuck.
            stall_error_threshold: Minimum goal-vs-actual error (degrees)
                to care about.  If the joint is near its goal, high load
                is just holding position (gravity), not a collision.
            sustain_frames: Consecutive stuck frames before confirming
                collision.  At 30 FPS, 6 ≈ 200 ms.
            freeze_frames: Frames to hold joint still after collision.
            monitor_only: Only log, never freeze.
        """
        self.robot = robot
        self.load_threshold = load_threshold
        self.stuck_velocity_threshold = stuck_velocity_threshold
        self.stall_error_threshold = stall_error_threshold
        self.sustain_frames = sustain_frames
        self.freeze_frames = freeze_frames
        self.monitor_only = monitor_only

        self._prev_actual: dict[str, float] = {}
        self._stall_count: dict[str, int] = defaultdict(int)
        self._frozen: dict[str, int] = {}
        self._armed = False
        self._log_file = self._init_log()

    # -- logging --------------------------------------------------------

    def _init_log(self) -> Path:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = log_dir / f"collision_{stamp}.csv"
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow([
                "time", "motor", "load", "pos_error", "actual_delta", "event",
            ])
        print(f"[COLLISION] Logging to {path}")
        return path

    def _log(self, motor: str, load: int, err: float, adelta: float, event: str) -> None:
        with open(self._log_file, "a", newline="") as f:
            csv.writer(f).writerow([
                f"{time.time():.3f}", motor, load,
                f"{err:.1f}", f"{adelta:.2f}", event,
            ])

    # -- helpers --------------------------------------------------------

    @staticmethod
    def decode_load(raw: int) -> int:
        sign = -1 if raw & 0x400 else 1
        return sign * (raw & 0x3FF)

    def read_loads(self) -> dict[str, int]:
        left = self.robot.bus1.sync_read(
            "Present_Load", self.robot.left_arm_motors, normalize=False
        )
        right = self.robot.bus2.sync_read(
            "Present_Load", self.robot.right_arm_motors, normalize=False
        )
        return {**left, **right}

    def reset(self) -> None:
        self._armed = False
        self._frozen.clear()
        self._stall_count.clear()
        self._prev_actual.clear()

    # -- main entry -----------------------------------------------------

    def check(self, action: dict[str, Any], obs: dict[str, Any]) -> dict[str, Any]:
        arm_motors = list(self.robot.left_arm_motors) + list(self.robot.right_arm_motors)

        actuals: dict[str, float] = {}
        errors: dict[str, float] = {}
        for motor in arm_motors:
            goal = action.get(f"{motor}.pos")
            actual = obs.get(f"{motor}.pos")
            actuals[motor] = actual if actual is not None else 0.0
            errors[motor] = abs(goal - actual) if (goal is not None and actual is not None) else 0.0

        # Wait for startup settling
        if not self._armed:
            max_err = max(errors.values()) if errors else 0.0
            if max_err < self.WARMUP_ERROR:
                self._armed = True
                self._prev_actual = dict(actuals)
                print(f"[COLLISION] Armed (max_err={max_err:.1f}°)")
            return action

        raw_loads = self.read_loads()
        filtered = dict(action)

        for motor, raw in raw_loads.items():
            load = abs(self.decode_load(raw))
            err = errors.get(motor, 0.0)
            actual = actuals.get(motor, 0.0)
            prev = self._prev_actual.get(motor, actual)
            actual_delta = abs(actual - prev)

            if self.monitor_only:
                if load > 50:
                    print(f"[LOAD] {motor:30s}  load={load:4d}  err={err:6.1f}°  Δact={actual_delta:.2f}°")
                    self._log(motor, load, err, actual_delta, "monitor")
                self._prev_actual[motor] = actual
                continue

            # Already frozen
            if motor in self._frozen:
                obs_actual = obs.get(f"{motor}.pos")
                if self._frozen[motor] > 0:
                    if f"{motor}.pos" in filtered and obs_actual is not None:
                        filtered[f"{motor}.pos"] = obs_actual
                    self._frozen[motor] -= 1
                else:
                    del self._frozen[motor]
                    print(f"[COLLISION] {motor} unfrozen")
                self._prev_actual[motor] = actual
                continue

            # Collision = high load + not near goal + actual position not moving
            is_stuck = (
                load > self.load_threshold
                and err > self.stall_error_threshold
                and actual_delta < self.stuck_velocity_threshold
            )

            if is_stuck:
                self._stall_count[motor] += 1
                n = self._stall_count[motor]
                print(f"[SUSPECT] {motor} load={load} err={err:.1f}° Δact={actual_delta:.2f}° ({n}/{self.sustain_frames})")
                self._log(motor, load, err, actual_delta, f"suspect({n}/{self.sustain_frames})")
            else:
                if self._stall_count[motor] > 0:
                    self._log(motor, load, err, actual_delta, "cleared")
                self._stall_count[motor] = 0

            if self._stall_count[motor] >= self.sustain_frames:
                self._frozen[motor] = self.freeze_frames
                self._stall_count[motor] = 0
                obs_actual = obs.get(f"{motor}.pos")
                if f"{motor}.pos" in filtered and obs_actual is not None:
                    filtered[f"{motor}.pos"] = obs_actual
                print(f"[COLLISION] {motor} load={load} err={err:.1f}° → frozen {self.freeze_frames}f")
                self._log(motor, load, err, actual_delta, "collision")

            self._prev_actual[motor] = actual

        return filtered

    @property
    def any_frozen(self) -> bool:
        return bool(self._frozen)
