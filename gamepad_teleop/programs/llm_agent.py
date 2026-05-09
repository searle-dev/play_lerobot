#!/usr/bin/env python3
"""Run a RoboCrew LLM Agent for XLeRobot."""

from __future__ import annotations

import argparse
import base64
import json
import importlib
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


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

    parser = argparse.ArgumentParser(description="XLeRobot RoboCrew LLM Agent")
    parser.add_argument("--provider", default=os.getenv("XLEROBOT_LLM_PROVIDER", "openai-compatible"))
    parser.add_argument("--model", default=os.getenv("XLEROBOT_MODEL", "google/gemini-3.1-pro-preview"))
    parser.add_argument("--base-url", default=os.getenv("XLEROBOT_LLM_BASE_URL"))
    parser.add_argument("--api-key", default=os.getenv("XLEROBOT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--task", default=os.getenv("XLEROBOT_TASK", "Approach a human."))
    parser.add_argument("--camera", default=os.getenv("XLEROBOT_MAIN_CAMERA", "/dev/camera_center"))
    parser.add_argument("--right-arm", default=os.getenv("XLEROBOT_RIGHT_ARM", "/dev/arm_right"))
    parser.add_argument("--left-arm", default=os.getenv("XLEROBOT_LEFT_ARM", "/dev/arm_left"))
    parser.add_argument("--voice", action="store_true", help="Wait for microphone voice commands.")
    parser.add_argument("--sounddevice-index", type=int, default=None)
    parser.add_argument("--wakeword", default="hey robot")
    parser.add_argument("--tts", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--dashboard-dir", type=Path, default=None, help="Directory for dashboard events and images.")
    parser.add_argument("--agent-history-len", type=int, default=int(os.getenv("XLEROBOT_AGENT_HISTORY_LEN", "6")))
    parser.add_argument("--llm-visual-history", type=int, default=int(os.getenv("XLEROBOT_LLM_VISUAL_HISTORY", "1")))
    parser.add_argument("--thinking-level", default=os.getenv("XLEROBOT_THINKING_LEVEL"))

    parser.add_argument("--vla-policy-name", default=None)
    parser.add_argument("--vla-policy-type", default="act")
    parser.add_argument("--vla-server", default="0.0.0.0:8080")
    parser.add_argument("--vla-tool-name", default="Manipulate_object")
    parser.add_argument("--vla-tool-description", default="Manipulation tool for the configured XLeRobot VLA policy.")
    parser.add_argument("--vla-task-prompt", default=None)
    parser.add_argument("--right-camera", default=os.getenv("XLEROBOT_RIGHT_CAMERA", "/dev/camera_right"))
    parser.add_argument("--policy-device", default="cpu")
    return parser.parse_args()


def camera_ref(value: str) -> int | str:
    return int(value) if value.isdigit() else value


def configure_robocrew_llm(args: argparse.Namespace) -> type:
    """Patch RoboCrew's hardcoded model factory for configurable providers."""
    llm_agent_module = importlib.import_module("robocrew.core.LLMAgent")
    original_init_chat_model = llm_agent_module.init_chat_model

    provider = args.provider.lower().replace("_", "-")
    model = args.model

    if provider in {"openai-compatible", "openai-compatible-api"}:
        base_url = args.base_url
        api_key = args.api_key
        if not base_url:
            raise SystemExit("Missing XLEROBOT_LLM_BASE_URL. Put it in robot/.env or pass --base-url.")
        if not api_key:
            raise SystemExit("Missing XLEROBOT_LLM_API_KEY or OPENAI_API_KEY. Put one in robot/.env.")

        def init_chat_model_override(*_factory_args: Any, **_factory_kwargs: Any):
            return original_init_chat_model(
                model=model,
                model_provider="openai",
                base_url=base_url,
                api_key=api_key,
            )

    elif provider == "openai":
        model_name = model if model.startswith("openai:") else f"openai:{model}"

        def init_chat_model_override(*_factory_args: Any, **_factory_kwargs: Any):
            return original_init_chat_model(model_name)

    elif provider in {"google", "google-genai", "google_genai"}:
        model_name = model if model.startswith("google_genai:") else f"google_genai:{model}"

        def init_chat_model_override(*_factory_args: Any, **_factory_kwargs: Any):
            return original_init_chat_model(model_name)

    else:
        def init_chat_model_override(*_factory_args: Any, **_factory_kwargs: Any):
            return original_init_chat_model(model)

    llm_agent_module.init_chat_model = init_chat_model_override
    return llm_agent_module.LLMAgent


def dashboard_event(dashboard_dir: Path | None, event: dict[str, Any]) -> None:
    if dashboard_dir is None:
        return
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    payload = {"time": time.time(), **event}
    with (dashboard_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def message_has_image(message: Any) -> bool:
    def visit(value: Any) -> bool:
        if isinstance(value, dict):
            if value.get("type") == "image_url" or "image_url" in value:
                return True
            return any(visit(child) for child in value.values())
        if isinstance(value, (list, tuple)):
            return any(visit(child) for child in value)
        return False

    return visit(getattr(message, "content", None))


def strip_images(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("type") == "image_url" or "image_url" in value:
            return {"type": "text", "text": "[历史图片已裁剪，dashboard 中仍可查看原图]"}
        return {key: strip_images(child) for key, child in value.items()}
    if isinstance(value, list):
        return [strip_images(child) for child in value]
    if isinstance(value, tuple):
        return tuple(strip_images(child) for child in value)
    return value


class ImagePruningLLM:
    """Delegate to a bound LLM while pruning old images from each request."""

    def __init__(self, llm: Any, *, keep_recent_image_messages: int, dashboard_dir: Path | None) -> None:
        self.llm = llm
        self.keep_recent_image_messages = max(0, keep_recent_image_messages)
        self.dashboard_dir = dashboard_dir

    def __getattr__(self, name: str) -> Any:
        return getattr(self.llm, name)

    def invoke(self, messages: list[Any], *args: Any, **kwargs: Any) -> Any:
        pruned_messages, stats = self._prune(messages)
        dashboard_event(
            self.dashboard_dir,
            {
                "type": "llm_request_start",
                "message": "开始请求 LLM",
                **stats,
            },
        )
        started_at = time.time()
        response = self.llm.invoke(pruned_messages, *args, **kwargs)
        dashboard_event(
            self.dashboard_dir,
            {
                "type": "llm_request_end",
                "message": "LLM 请求完成",
                "duration_s": round(time.time() - started_at, 3),
                **stats,
            },
        )
        return response

    def _prune(self, messages: list[Any]) -> tuple[list[Any], dict[str, int]]:
        image_indices = [index for index, message in enumerate(messages) if message_has_image(message)]
        keep = set(image_indices[-self.keep_recent_image_messages :]) if self.keep_recent_image_messages else set()
        pruned: list[Any] = []
        for index, message in enumerate(messages):
            if index in keep or not message_has_image(message):
                pruned.append(message)
                continue
            copied = message.copy(deep=True) if hasattr(message, "copy") else message
            try:
                copied.content = strip_images(getattr(message, "content", None))
            except Exception:
                copied = message
            pruned.append(copied)
        return pruned, {
            "image_messages_total": len(image_indices),
            "image_messages_kept": len(keep),
            "image_messages_pruned": max(0, len(image_indices) - len(keep)),
        }


def save_dashboard_images(dashboard_dir: Path | None, tool_name: str, result: Any) -> list[dict[str, Any]]:
    if dashboard_dir is None:
        return []
    images_dir = dashboard_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    saved: list[dict[str, Any]] = []

    def visit(value: Any, label: str = "") -> None:
        if isinstance(value, dict):
            image_url = value.get("image_url")
            if isinstance(image_url, dict):
                url = str(image_url.get("url", ""))
                prefix = "data:image/jpeg;base64,"
                if url.startswith(prefix):
                    index = len(saved) + 1
                    file_name = f"{int(time.time() * 1000)}-{tool_name}-{index}.jpg"
                    target = images_dir / file_name
                    target.write_bytes(base64.b64decode(url[len(prefix) :]))
                    saved.append(
                        {
                            "label": label or f"图片 {index}",
                            "path": f"images/{file_name}",
                            "url": f"/media/{dashboard_dir.name}/images/{file_name}",
                        }
                    )
            text = value.get("text")
            next_label = str(text) if isinstance(text, str) and text else label
            for child in value.values():
                visit(child, next_label)
        elif isinstance(value, (list, tuple)):
            current_label = label
            for child in value:
                if isinstance(child, dict) and isinstance(child.get("text"), str):
                    current_label = child["text"]
                visit(child, current_label)

    visit(result)
    return saved


def instrument_tool(tool: Any, dashboard_dir: Path | None) -> Any:
    if dashboard_dir is None or not hasattr(tool, "func"):
        return tool
    original_func = tool.func
    tool_name = getattr(tool, "name", "tool")

    def wrapped_tool(*args: Any, **kwargs: Any) -> Any:
        dashboard_event(
            dashboard_dir,
            {
                "type": "tool_start",
                "tool": tool_name,
                "args": kwargs or list(args),
                "message": f"开始执行工具：{tool_name}",
            },
        )
        started_at = time.time()
        try:
            result = original_func(*args, **kwargs)
        except Exception as exc:
            dashboard_event(
                dashboard_dir,
                {
                    "type": "tool_error",
                    "tool": tool_name,
                    "duration_s": round(time.time() - started_at, 3),
                    "error": repr(exc),
                    "message": f"工具失败：{tool_name}",
                },
            )
            raise
        images = save_dashboard_images(dashboard_dir, tool_name, result)
        dashboard_event(
            dashboard_dir,
            {
                "type": "tool_end",
                "tool": tool_name,
                "duration_s": round(time.time() - started_at, 3),
                "result": summarize_result(result),
                "images": images,
                "message": f"工具完成：{tool_name}",
            },
        )
        return result

    tool.func = wrapped_tool
    return tool


class DashboardToolMonitor:
    """Track and constrain dashboard-launched tool calls."""

    MOTION_TOOLS = {
        "move_forward",
        "move_backward",
        "strafe_left",
        "strafe_right",
        "turn_left",
        "turn_right",
        "go_to_precision_mode",
        "go_to_normal_mode",
        "nudge_arm_joint",
        "nudge_gripper",
        "set_gripper_position",
        "Manipulate_object",
    }
    VISUAL_TOOLS = {"look_around", "capture_current_view"}

    def __init__(self, dashboard_dir: Path | None) -> None:
        self.dashboard_dir = dashboard_dir
        self.has_visual_confirmation = False

    def wrap(self, tool: Any) -> Any:
        if self.dashboard_dir is None or not hasattr(tool, "func"):
            return tool
        original_func = tool.func
        tool_name = getattr(tool, "name", "tool")

        def wrapped_tool(*args: Any, **kwargs: Any) -> Any:
            if tool_name in self.MOTION_TOOLS and not self.has_visual_confirmation:
                message = (
                    f"已拦截工具：{tool_name}。原因：还没有完成最新视觉确认，"
                    "dashboard 安全模式要求先执行 look_around() 或 capture_current_view()。"
                )
                dashboard_event(
                    self.dashboard_dir,
                    {
                        "type": "tool_blocked",
                        "tool": tool_name,
                        "args": kwargs or list(args),
                        "message": message,
                    },
                )
                return message

            dashboard_event(
                self.dashboard_dir,
                {
                    "type": "tool_start",
                    "tool": tool_name,
                    "args": kwargs or list(args),
                    "message": f"开始执行工具：{tool_name}",
                },
            )
            started_at = time.time()
            try:
                result = original_func(*args, **kwargs)
            except Exception as exc:
                dashboard_event(
                    self.dashboard_dir,
                    {
                        "type": "tool_error",
                        "tool": tool_name,
                        "duration_s": round(time.time() - started_at, 3),
                        "error": repr(exc),
                        "message": f"工具失败：{tool_name}",
                    },
                )
                raise
            images = save_dashboard_images(self.dashboard_dir, tool_name, result)
            if tool_name in self.VISUAL_TOOLS:
                self.has_visual_confirmation = True
            elif tool_name in self.MOTION_TOOLS:
                self.has_visual_confirmation = False
            dashboard_event(
                self.dashboard_dir,
                {
                    "type": "tool_end",
                    "tool": tool_name,
                    "duration_s": round(time.time() - started_at, 3),
                    "result": summarize_result(result),
                    "images": images,
                    "message": f"工具完成：{tool_name}",
                },
            )
            return result

        tool.func = wrapped_tool
        return tool


def summarize_result(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, tuple) and result and isinstance(result[0], str):
        return result[0]
    text_parts: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            text = value.get("text")
            if isinstance(text, str):
                text_parts.append(text)
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(result)
    return " / ".join(text_parts[:8]) or type(result).__name__


ARM_JOINT_LIMITS = {
    "shoulder_pan": (-120.0, 120.0),
    "shoulder_lift": (-130.0, 130.0),
    "elbow_flex": (-30.0, 150.0),
    "wrist_flex": (-130.0, 130.0),
    "wrist_roll": (-180.0, 180.0),
    "gripper": (0.0, 100.0),
}
ARM_SIDES = {"left", "right"}
MAX_JOINT_DELTA = 5.0
MAX_GRIPPER_DELTA = 5.0


def clamp_float(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def create_capture_current_view(main_camera: Any):
    from langchain_core.tools import tool

    @tool
    def capture_current_view(note: str = "") -> list:
        """Capture one image from the current camera/head view for visual confirmation before the next action."""
        image = main_camera.capture_image(center_angle=0)
        image_64 = base64.b64encode(image).decode("utf-8")
        label = note or "Current view"
        return "Captured current view", [
            {"type": "text", "text": label},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_64}"}},
        ]

    return capture_current_view


def create_read_arm_pose(servo_controler: Any):
    from langchain_core.tools import tool

    @tool
    def read_arm_pose(arm_side: str = "right") -> str:
        """Read current arm joint positions. arm_side must be 'left' or 'right'."""
        side = arm_side.lower().strip()
        if side not in ARM_SIDES:
            return "Invalid arm_side. Use 'left' or 'right'."
        pose = servo_controler.read_arm_present_position(side)
        return json.dumps({"arm_side": side, "pose": pose}, ensure_ascii=False)

    return read_arm_pose


def create_nudge_arm_joint(servo_controler: Any):
    from langchain_core.tools import tool

    @tool
    def nudge_arm_joint(arm_side: str, joint: str, delta: float) -> str:
        """Move one arm joint by a small delta. Requires visual confirmation before each call."""
        side = arm_side.lower().strip()
        joint_name = joint.lower().strip()
        if side not in ARM_SIDES:
            return "Invalid arm_side. Use 'left' or 'right'."
        if joint_name not in ARM_JOINT_LIMITS:
            return f"Invalid joint. Use one of: {', '.join(ARM_JOINT_LIMITS)}."
        bounded_delta = clamp_float(float(delta), -MAX_JOINT_DELTA, MAX_JOINT_DELTA)
        pose = servo_controler.read_arm_present_position(side)
        current = float(pose.get(joint_name, 0.0))
        low, high = ARM_JOINT_LIMITS[joint_name]
        target = clamp_float(current + bounded_delta, low, high)
        servo_controler.set_arm_position({joint_name: target}, side)
        time.sleep(0.35)
        return json.dumps(
            {
                "arm_side": side,
                "joint": joint_name,
                "requested_delta": float(delta),
                "applied_delta": round(target - current, 3),
                "from": round(current, 3),
                "to": round(target, 3),
                "next_step_required": "Call capture_current_view or look_around before any further movement.",
            },
            ensure_ascii=False,
        )

    return nudge_arm_joint


def create_nudge_gripper(servo_controler: Any):
    from langchain_core.tools import tool

    @tool
    def nudge_gripper(arm_side: str, delta: float) -> str:
        """Open or close the gripper by a small delta. Use repeated visual confirmation to determine direction."""
        side = arm_side.lower().strip()
        if side not in ARM_SIDES:
            return "Invalid arm_side. Use 'left' or 'right'."
        bounded_delta = clamp_float(float(delta), -MAX_GRIPPER_DELTA, MAX_GRIPPER_DELTA)
        pose = servo_controler.read_arm_present_position(side)
        current = float(pose.get("gripper", 0.0))
        low, high = ARM_JOINT_LIMITS["gripper"]
        target = clamp_float(current + bounded_delta, low, high)
        servo_controler.set_arm_position({"gripper": target}, side)
        time.sleep(0.25)
        return json.dumps(
            {
                "arm_side": side,
                "joint": "gripper",
                "requested_delta": float(delta),
                "applied_delta": round(target - current, 3),
                "from": round(current, 3),
                "to": round(target, 3),
                "next_step_required": "Call capture_current_view or look_around before any further movement.",
            },
            ensure_ascii=False,
        )

    return nudge_gripper


def create_set_gripper_position(servo_controler: Any):
    from langchain_core.tools import tool

    @tool
    def set_gripper_position(arm_side: str, position: float) -> str:
        """Set gripper to a bounded position from 0 to 100. Prefer nudge_gripper for cautious grasping."""
        side = arm_side.lower().strip()
        if side not in ARM_SIDES:
            return "Invalid arm_side. Use 'left' or 'right'."
        target = clamp_float(float(position), *ARM_JOINT_LIMITS["gripper"])
        pose = servo_controler.read_arm_present_position(side)
        current = float(pose.get("gripper", 0.0))
        servo_controler.set_arm_position({"gripper": target}, side)
        time.sleep(0.25)
        return json.dumps(
            {
                "arm_side": side,
                "joint": "gripper",
                "from": round(current, 3),
                "to": round(target, 3),
                "next_step_required": "Call capture_current_view or look_around before any further movement.",
            },
            ensure_ascii=False,
        )

    return set_gripper_position


def main() -> None:
    args = parse_args()
    sys.path.insert(0, str(ROOT_DIR / "lerobot" / "src"))

    try:
        from robocrew.core.camera import RobotCamera
        from robocrew.robots.XLeRobot.servo_controls import ServoControler
        from robocrew.robots.XLeRobot.tools import (
            create_go_to_normal_mode,
            create_go_to_precision_mode,
            create_look_around,
            create_move_backward,
            create_move_forward,
            create_strafe_left,
            create_strafe_right,
            create_turn_left,
            create_turn_right,
        )
    except ImportError as exc:
        raise SystemExit(
            "Missing RoboCrew runtime. Run: cd robot && ./scripts/setup_env.sh"
        ) from exc

    LLMAgent = configure_robocrew_llm(args)
    main_camera = RobotCamera(camera_ref(args.camera))
    servo_controler = ServoControler(args.right_arm, args.left_arm)

    dashboard_monitor = DashboardToolMonitor(args.dashboard_dir)
    tools = [
        create_move_forward(servo_controler),
        create_move_backward(servo_controler),
        create_strafe_left(servo_controler),
        create_strafe_right(servo_controler),
        create_turn_left(servo_controler),
        create_turn_right(servo_controler),
        create_look_around(servo_controler, main_camera),
        create_capture_current_view(main_camera),
        create_go_to_precision_mode(servo_controler),
        create_go_to_normal_mode(servo_controler),
        create_read_arm_pose(servo_controler),
        create_nudge_arm_joint(servo_controler),
        create_nudge_gripper(servo_controler),
        create_set_gripper_position(servo_controler),
    ]
    tools = [dashboard_monitor.wrap(tool) for tool in tools]

    if args.vla_policy_name:
        from robocrew.robots.XLeRobot.tools import create_vla_single_arm_manipulation

        tools.append(
            dashboard_monitor.wrap(
                create_vla_single_arm_manipulation(
                tool_name=args.vla_tool_name,
                tool_description=args.vla_tool_description,
                task_prompt=args.vla_task_prompt or args.task,
                server_address=args.vla_server,
                policy_name=args.vla_policy_name,
                policy_type=args.vla_policy_type,
                arm_port=args.right_arm,
                servo_controler=servo_controler,
                camera_config={
                    "main": {"index_or_path": camera_ref(args.camera)},
                    "right_arm": {"index_or_path": camera_ref(args.right_camera)},
                },
                main_camera_object=main_camera,
                policy_device=args.policy_device,
                ),
                args.dashboard_dir,
            )
        )

    agent_kwargs = {
        "model": args.model,
        "tools": tools,
        "main_camera": main_camera,
        "servo_controler": servo_controler,
        "history_len": args.agent_history_len,
    }
    if args.thinking_level:
        agent_kwargs["thinking_level"] = args.thinking_level

    if args.voice:
        agent_kwargs.update(
            sounddevice_index_or_alias=args.sounddevice_index,
            wakeword=args.wakeword,
            tts=args.tts,
        )

    agent = LLMAgent(**agent_kwargs)
    agent.llm = ImagePruningLLM(
        agent.llm,
        keep_recent_image_messages=args.llm_visual_history,
        dashboard_dir=args.dashboard_dir,
    )
    agent.task = "Wait for the voice commands and execute." if args.voice else args.task
    dashboard_event(
        args.dashboard_dir,
        {
            "type": "agent_start",
            "task": agent.task,
            "message": "Agent 已启动",
        },
    )
    agent.go()


if __name__ == "__main__":
    main()
