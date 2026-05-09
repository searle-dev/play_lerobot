#!/usr/bin/env python3
"""Local web dashboard for running XLeRobot LLM agent demos."""

from __future__ import annotations

import argparse
import glob
import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ROOT_DIR = Path(__file__).resolve().parents[1]
LLM_AGENT = ROOT_DIR / "programs" / "llm_agent.py"
ROBOCREW_CALIBRATION_DIR = Path.home() / ".cache" / "robocrew" / "calibrations" / "robots" / "so_follower"
RUNS_DIR = ROOT_DIR / "logs" / "dashboard_runs"
LOG_LIMIT = 1200

PRESETS = {
    "observe": {
        "label": "只观察",
        "risk": "只动头部和相机",
        "task": (
            "Use look_around exactly once, then summarize what you see. "
            "Do not move the base. Do not move forward, backward, strafe, "
            "turn the base, or manipulate objects."
        ),
    },
    "tiny_forward": {
        "label": "小步前进测试",
        "risk": "底盘最多前进 0.1 米",
        "task": (
            "Look around. If there is open space directly ahead, move forward "
            "at most 0.1 meters once, then stop. Do not manipulate objects."
        ),
    },
    "find_human": {
        "label": "寻找人",
        "risk": "允许小范围导航",
        "task": (
            "Look around to find a human. If a human is visible, turn to face "
            "them and move in small steps no larger than 0.2 meters. Stop before "
            "getting close. Do not manipulate objects."
        ),
    },
    "cautious_grasp": {
        "label": "谨慎抓取试验",
        "risk": "右臂小步试错",
        "task": (
            "Carefully observe the tabletop and find a cylindrical package. "
            "Use visual confirmation before every step. Use the right arm only. "
            "Use read_arm_pose, nudge_arm_joint, nudge_gripper, and capture_current_view "
            "in small increments to try to approach and gently grasp it. Stop if the "
            "gripper or target is not clearly visible."
        ),
    },
}

DASHBOARD_TASK_PREFIX = """
Dashboard safety rules:
1. Your first robot tool call for the whole task must be look_around(). Do not repeat look_around unless you need a wide scan.
2. Do not move, turn, strafe, switch mode, or move the arm before look_around has completed.
3. Before every movement or arm adjustment, use the latest visual observation to justify the action and keep changes small.
4. After every movement or arm adjustment, prefer capture_current_view() before taking another movement. Use look_around() only when you lost the target or need a wide scan.
5. For cautious non-VLA grasping, use read_arm_pose, nudge_arm_joint, and nudge_gripper only in small increments. Never jump to a large arm pose.
6. If you cannot visually confirm the gripper and target relationship, stop and explain what is missing.
7. Prefer visual confirmation over guessing. If unsure, call capture_current_view() or look_around() instead of moving blindly.
User task:
""".strip()


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        key = key.strip()
        values[key] = value
        os.environ.setdefault(key, value)
    return values


def mask_env(key: str, value: str | None) -> str:
    if value is None or value == "":
        return ""
    if "KEY" in key or "TOKEN" in key or "SECRET" in key:
        if len(value) <= 8:
            return "<set>"
        return f"{value[:4]}...{value[-4:]}"
    return value


def python_bin() -> str:
    local_python = ROOT_DIR / ".venv" / "bin" / "python"
    if local_python.exists():
        return str(local_python)
    return sys.executable


def vla_args_from_env() -> list[str]:
    policy_name = os.environ.get("XLEROBOT_VLA_POLICY_NAME", "").strip()
    if not policy_name:
        return []
    args = ["--vla-policy-name", policy_name]
    optional_map = {
        "XLEROBOT_VLA_POLICY_TYPE": "--vla-policy-type",
        "XLEROBOT_VLA_SERVER": "--vla-server",
        "XLEROBOT_VLA_TASK_PROMPT": "--vla-task-prompt",
        "XLEROBOT_RIGHT_CAMERA": "--right-camera",
        "XLEROBOT_POLICY_DEVICE": "--policy-device",
    }
    for env_key, cli_key in optional_map.items():
        value = os.environ.get(env_key, "").strip()
        if value:
            args.extend([cli_key, value])
    return args


class AgentRunner:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.process: subprocess.Popen[str] | None = None
        self.started_at: float | None = None
        self.last_command: list[str] = []
        self.returncode: int | None = None
        self.run_id: str | None = None
        self.run_dir: Path | None = None
        self.logs: deque[dict[str, Any]] = deque(maxlen=LOG_LIMIT)

    def append_log(self, line: str, stream: str = "agent") -> None:
        with self.lock:
            self.logs.append({"time": time.time(), "stream": stream, "line": line.rstrip("\n")})

    def start(self, task: str, extra_args: list[str] | None = None) -> dict[str, Any]:
        if not task.strip():
            raise ValueError("Task cannot be empty.")
        with self.lock:
            if self.process and self.process.poll() is None:
                raise RuntimeError("An agent process is already running.")
            self.logs.clear()
            self.returncode = None
            self.run_id = time.strftime("%Y%m%d-%H%M%S")
            self.run_dir = RUNS_DIR / self.run_id
            self.run_dir.mkdir(parents=True, exist_ok=True)
            guarded_task = f"{DASHBOARD_TASK_PREFIX}\n{task.strip()}"
            cmd = [
                python_bin(),
                str(LLM_AGENT),
                "--task",
                guarded_task,
                "--dashboard-dir",
                str(self.run_dir),
            ]
            cmd.extend(vla_args_from_env())
            if extra_args:
                cmd.extend(extra_args)
            env = dict(os.environ)
            env["PYTHONUNBUFFERED"] = "1"
            self.process = subprocess.Popen(
                cmd,
                cwd=str(ROOT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                start_new_session=True,
            )
            self.started_at = time.time()
            self.last_command = cmd
            self.logs.append(
                {
                    "time": time.time(),
                    "stream": "dashboard",
                    "line": "已启动: " + " ".join(cmd),
                }
            )
            process = self.process
        threading.Thread(target=self._read_output, args=(process,), daemon=True).start()
        return self.status()

    def _read_output(self, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            self.append_log(line)
        returncode = process.wait()
        with self.lock:
            if self.process is process:
                self.returncode = returncode
                self.logs.append(
                    {
                        "time": time.time(),
                        "stream": "dashboard",
                        "line": f"进程退出，返回码 {returncode}。",
                    }
                )

    def stop(self) -> dict[str, Any]:
        with self.lock:
            process = self.process
            if not process or process.poll() is not None:
                process = None
        if process is None:
            return self.status()
        with self.lock:
            self.logs.append({"time": time.time(), "stream": "dashboard", "line": "正在停止 agent..."})
        try:
            os.killpg(process.pid, signal.SIGINT)
        except Exception:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except Exception:
                process.kill()
        return self.status()

    def status(self) -> dict[str, Any]:
        with self.lock:
            running = bool(self.process and self.process.poll() is None)
            returncode = self.process.poll() if self.process else self.returncode
            return {
                "running": running,
                "pid": self.process.pid if self.process and running else None,
                "started_at": self.started_at,
                "uptime_s": round(time.time() - self.started_at, 1) if running and self.started_at else None,
                "returncode": returncode,
                "last_command": self.last_command,
                "run_id": self.run_id,
            }

    def log_snapshot(self, after: int = 0) -> dict[str, Any]:
        with self.lock:
            logs = list(self.logs)
        return {"start": after, "logs": logs[after:], "next": len(logs)}

    def event_snapshot(self, after: int = 0) -> dict[str, Any]:
        with self.lock:
            run_id = self.run_id
            run_dir = self.run_dir
        if not run_dir:
            return {"run_id": run_id, "events": [], "next": 0}
        event_file = run_dir / "events.jsonl"
        if not event_file.exists():
            return {"run_id": run_id, "events": [], "next": 0}
        events = []
        for line in event_file.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return {"run_id": run_id, "events": events[after:], "next": len(events)}


RUNNER = AgentRunner()


def device_status(env_values: dict[str, str]) -> dict[str, Any]:
    devices = sorted(
        set(
            glob.glob("/dev/camera*")
            + glob.glob("/dev/arm*")
            + glob.glob("/dev/ttyACM*")
            + glob.glob("/dev/tty.usb*")
            + glob.glob("/dev/cu.usb*")
            + glob.glob("/dev/cu.usbmodem*")
            + glob.glob("/dev/tty.usbmodem*")
        )
    )
    keys = [
        "XLEROBOT_MAIN_CAMERA",
        "XLEROBOT_RIGHT_ARM",
        "XLEROBOT_LEFT_ARM",
        "XLEROBOT_LLM_PROVIDER",
        "XLEROBOT_LLM_BASE_URL",
        "XLEROBOT_LLM_API_KEY",
        "XLEROBOT_MODEL",
        "XLEROBOT_AGENT_HISTORY_LEN",
        "XLEROBOT_LLM_VISUAL_HISTORY",
        "XLEROBOT_THINKING_LEVEL",
        "XLEROBOT_VLA_POLICY_NAME",
        "XLEROBOT_VLA_POLICY_TYPE",
        "XLEROBOT_VLA_SERVER",
        "XLEROBOT_VLA_TASK_PROMPT",
        "XLEROBOT_RIGHT_CAMERA",
        "XLEROBOT_POLICY_DEVICE",
    ]
    config = {key: mask_env(key, env_values.get(key) or os.environ.get(key)) for key in keys}
    calibration = {
        "left_arm": (ROBOCREW_CALIBRATION_DIR / "left_arm.json").exists(),
        "right_arm": (ROBOCREW_CALIBRATION_DIR / "right_arm.json").exists(),
        "dir": str(ROBOCREW_CALIBRATION_DIR),
    }
    return {
        "devices": devices,
        "config": config,
        "calibration": calibration,
        "python": python_bin(),
        "llm_agent": str(LLM_AGENT),
    }


def json_response(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def file_response(handler: BaseHTTPRequestHandler, path: Path) -> None:
    try:
        resolved = path.resolve()
        base = RUNS_DIR.resolve()
        if base not in resolved.parents:
            raise FileNotFoundError
        data = resolved.read_bytes()
    except FileNotFoundError:
        json_response(handler, {"error": "Not found"}, status=404)
        return
    content_type = "image/jpeg" if resolved.suffix.lower() in {".jpg", ".jpeg"} else "application/octet-stream"
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "XLeRobotDashboard/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/status":
            json_response(
                self,
                {
                    "runner": RUNNER.status(),
                    "device": device_status(self.server.env_values),  # type: ignore[attr-defined]
                    "presets": PRESETS,
                },
            )
            return
        if parsed.path == "/api/logs":
            try:
                after = int(dict(part.split("=", 1) for part in parsed.query.split("&") if part).get("after", "0"))
            except ValueError:
                after = 0
            json_response(self, RUNNER.log_snapshot(after=max(0, after)))
            return
        if parsed.path == "/api/events":
            try:
                after = int(dict(part.split("=", 1) for part in parsed.query.split("&") if part).get("after", "0"))
            except ValueError:
                after = 0
            json_response(self, RUNNER.event_snapshot(after=max(0, after)))
            return
        if parsed.path.startswith("/media/"):
            rel = unquote(parsed.path.removeprefix("/media/"))
            file_response(self, RUNS_DIR / rel)
            return
        json_response(self, {"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            json_response(self, {"error": "Invalid JSON"}, status=400)
            return

        if parsed.path == "/api/start":
            preset = str(payload.get("preset") or "")
            task = str(payload.get("task") or "")
            if preset:
                if preset not in PRESETS:
                    json_response(self, {"error": f"Unknown preset: {preset}"}, status=400)
                    return
                task = PRESETS[preset]["task"]
            try:
                json_response(self, RUNNER.start(task))
            except (RuntimeError, ValueError) as exc:
                json_response(self, {"error": str(exc)}, status=409)
            return
        if parsed.path == "/api/stop":
            json_response(self, RUNNER.stop())
            return
        json_response(self, {"error": "Not found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>XLeRobot Agent Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f8;
      --panel: #ffffff;
      --text: #1d2329;
      --muted: #66717d;
      --line: #d9dee5;
      --accent: #0b6f6a;
      --accent-strong: #07534f;
      --danger: #b42318;
      --warn: #9a6700;
      --ok: #177245;
      --code: #111827;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 18px 22px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 { margin: 0; font-size: 20px; font-weight: 700; }
    h2 { margin: 0 0 12px; font-size: 15px; }
    main {
      max-width: 1320px;
      margin: 0 auto;
      padding: 18px;
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 16px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .stack { display: grid; gap: 16px; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 7px 11px;
      font-weight: 650;
      white-space: nowrap;
    }
    .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--muted); }
    .running .dot { background: var(--ok); }
    .stopped .dot { background: var(--muted); }
    dl { display: grid; grid-template-columns: 135px minmax(0, 1fr); gap: 8px 10px; margin: 0; }
    dt { color: var(--muted); }
    dd { margin: 0; min-width: 0; word-break: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .devices { display: grid; gap: 7px; margin: 0; padding: 0; list-style: none; }
    .device {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 9px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--code);
      word-break: break-all;
    }
    .empty { color: var(--muted); }
    .actions {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 7px;
      padding: 10px 11px;
      min-height: 42px;
      font-weight: 650;
      cursor: pointer;
    }
    button:hover { border-color: var(--accent); }
    button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
    button.primary:hover { background: var(--accent-strong); }
    button.danger { color: var(--danger); border-color: #efb5ae; }
    button:disabled { cursor: not-allowed; opacity: .52; }
    .preset {
      text-align: left;
      display: grid;
      gap: 5px;
      align-content: start;
    }
    .risk { color: var(--muted); font-size: 12px; font-weight: 500; }
    textarea {
      width: 100%;
      min-height: 118px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 10px;
      font: 14px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--code);
    }
    .row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .runbar { display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
    .log {
      height: 520px;
      overflow: auto;
      background: #111827;
      color: #d7dee8;
      border-radius: 8px;
      padding: 12px;
      font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .logline { display: block; }
    .logline[data-stream="dashboard"] { color: #9dd8d3; }
    .logtime { color: #8a96a6; }
    .hint { color: var(--muted); margin: 9px 0 0; line-height: 1.45; }
    .ok { color: var(--ok); font-weight: 650; }
    .warn { color: var(--warn); font-weight: 650; }
    @media (max-width: 920px) {
      main { grid-template-columns: 1fr; padding: 12px; }
      header { align-items: flex-start; flex-direction: column; }
      .actions { grid-template-columns: 1fr; }
      dl { grid-template-columns: 116px minmax(0, 1fr); }
      .log { height: 360px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>XLeRobot Agent Dashboard</h1>
      <div class="hint">Run the LLM agent, inspect the exact task, and watch stdout/stderr in one place.</div>
    </div>
    <div id="runState" class="status stopped"><span class="dot"></span><span>Stopped</span></div>
  </header>
  <main>
    <div class="stack">
      <section>
        <h2>Runtime</h2>
        <dl id="runtime"></dl>
      </section>
      <section>
        <h2>Device Config</h2>
        <dl id="config"></dl>
      </section>
      <section>
        <h2>Visible Devices</h2>
        <ul id="devices" class="devices"></ul>
      </section>
      <section>
        <h2>Calibration</h2>
        <dl id="calibration"></dl>
      </section>
    </div>
    <div class="stack">
      <section>
        <div class="row">
          <h2>Preset Runs</h2>
          <button id="refreshBtn" type="button">Refresh</button>
        </div>
        <div id="presets" class="actions"></div>
        <p class="hint">Start with Observe only. It should only turn the head and capture camera frames.</p>
      </section>
      <section>
        <h2>Custom Task</h2>
        <textarea id="taskInput" spellcheck="false">Use look_around exactly once, then summarize what you see. Do not move the base.</textarea>
        <div class="runbar">
          <button id="runCustom" class="primary" type="button">Run Custom Task</button>
          <button id="stopBtn" class="danger" type="button">Stop Agent</button>
        </div>
      </section>
      <section>
        <div class="row">
          <h2>Live Log</h2>
          <button id="clearLog" type="button">Clear View</button>
        </div>
        <div id="log" class="log" aria-live="polite"></div>
      </section>
    </div>
  </main>
  <script>
    let presets = {};
    let logCursor = 0;
    let running = false;

    const runState = document.getElementById('runState');
    const runtime = document.getElementById('runtime');
    const config = document.getElementById('config');
    const devices = document.getElementById('devices');
    const calibration = document.getElementById('calibration');
    const presetsNode = document.getElementById('presets');
    const logNode = document.getElementById('log');
    const taskInput = document.getElementById('taskInput');

    function dtRow(key, value) {
      return `<dt>${key}</dt><dd>${value || '<span class="empty">not set</span>'}</dd>`;
    }

    function setRunning(isRunning, status) {
      running = isRunning;
      runState.className = `status ${isRunning ? 'running' : 'stopped'}`;
      runState.innerHTML = `<span class="dot"></span><span>${isRunning ? 'Running' : 'Stopped'}</span>`;
      document.querySelectorAll('button[data-preset], #runCustom').forEach(btn => btn.disabled = isRunning);
      document.getElementById('stopBtn').disabled = !isRunning;
      runtime.innerHTML = [
        dtRow('PID', status.pid),
        dtRow('Uptime', status.uptime_s == null ? '' : `${status.uptime_s}s`),
        dtRow('Return code', status.returncode == null ? '' : status.returncode),
        dtRow('Command', status.last_command && status.last_command.length ? status.last_command.join(' ') : '')
      ].join('');
    }

    function renderStatus(data) {
      presets = data.presets || {};
      setRunning(Boolean(data.runner.running), data.runner);
      const cfg = data.device.config || {};
      config.innerHTML = Object.keys(cfg).map(key => dtRow(key, cfg[key])).join('');
      devices.innerHTML = '';
      if (!data.device.devices || !data.device.devices.length) {
        devices.innerHTML = '<li class="empty">No matching robot serial devices found.</li>';
      } else {
        for (const dev of data.device.devices) {
          const li = document.createElement('li');
          li.className = 'device';
          li.textContent = dev;
          devices.appendChild(li);
        }
      }
      const cal = data.device.calibration || {};
      calibration.innerHTML = [
        dtRow('Left arm', cal.left_arm ? '<span class="ok">present</span>' : '<span class="warn">missing</span>'),
        dtRow('Right arm', cal.right_arm ? '<span class="ok">present</span>' : '<span class="warn">missing</span>'),
        dtRow('Directory', cal.dir)
      ].join('');
      renderPresets();
    }

    function renderPresets() {
      presetsNode.innerHTML = '';
      for (const [id, preset] of Object.entries(presets)) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'preset';
        btn.dataset.preset = id;
        btn.disabled = running;
        btn.innerHTML = `<span>${preset.label}</span><span class="risk">${preset.risk}</span>`;
        btn.addEventListener('click', () => startPreset(id));
        presetsNode.appendChild(btn);
      }
    }

    async function refreshStatus() {
      const res = await fetch('/api/status');
      renderStatus(await res.json());
    }

    async function startPreset(id) {
      const res = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({preset: id})
      });
      const data = await res.json();
      if (data.error) appendLocal(`Error: ${data.error}`);
      await refreshStatus();
    }

    async function startCustom() {
      const res = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task: taskInput.value})
      });
      const data = await res.json();
      if (data.error) appendLocal(`Error: ${data.error}`);
      await refreshStatus();
    }

    async function stopAgent() {
      await fetch('/api/stop', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
      await refreshStatus();
    }

    function appendLocal(line) {
      appendLogLine({time: Date.now() / 1000, stream: 'dashboard', line});
    }

    function appendLogLine(item) {
      const span = document.createElement('span');
      span.className = 'logline';
      span.dataset.stream = item.stream || 'agent';
      const time = new Date(item.time * 1000).toLocaleTimeString();
      span.innerHTML = `<span class="logtime">${time}</span> [${item.stream}] ${escapeHtml(item.line)}`;
      logNode.appendChild(span);
      logNode.scrollTop = logNode.scrollHeight;
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
    }

    async function pollLogs() {
      try {
        const res = await fetch(`/api/logs?after=${logCursor}`);
        const data = await res.json();
        for (const item of data.logs || []) appendLogLine(item);
        logCursor = data.next;
      } catch (err) {
        appendLocal(`Log polling failed: ${err.message}`);
      }
    }

    document.getElementById('refreshBtn').addEventListener('click', refreshStatus);
    document.getElementById('runCustom').addEventListener('click', startCustom);
    document.getElementById('stopBtn').addEventListener('click', stopAgent);
    document.getElementById('clearLog').addEventListener('click', () => { logNode.innerHTML = ''; });

    refreshStatus();
    pollLogs();
    setInterval(refreshStatus, 2500);
    setInterval(pollLogs, 1000);
  </script>
</body>
</html>
"""

HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>XLeRobot Agent 控制台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f6f8;
      --panel: #ffffff;
      --text: #1d2329;
      --muted: #66717d;
      --line: #d9dee5;
      --accent: #0b6f6a;
      --accent-strong: #07534f;
      --danger: #b42318;
      --warn: #9a6700;
      --ok: #177245;
      --code: #111827;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 18px 22px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 { margin: 0; font-size: 20px; font-weight: 700; }
    h2 { margin: 0 0 12px; font-size: 15px; }
    main {
      max-width: 1440px;
      margin: 0 auto;
      padding: 18px;
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 16px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .stack { display: grid; gap: 16px; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 7px 11px;
      font-weight: 650;
      white-space: nowrap;
    }
    .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--muted); }
    .running .dot { background: var(--ok); }
    .stopped .dot { background: var(--muted); }
    dl { display: grid; grid-template-columns: 122px minmax(0, 1fr); gap: 8px 10px; margin: 0; }
    dt { color: var(--muted); }
    dd { margin: 0; min-width: 0; word-break: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .devices { display: grid; gap: 7px; margin: 0; padding: 0; list-style: none; }
    .device {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 9px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--code);
      word-break: break-all;
    }
    .empty { color: var(--muted); }
    .actions {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 7px;
      padding: 10px 11px;
      min-height: 42px;
      font-weight: 650;
      cursor: pointer;
    }
    button:hover { border-color: var(--accent); }
    button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
    button.primary:hover { background: var(--accent-strong); }
    button.danger { color: var(--danger); border-color: #efb5ae; }
    button:disabled { cursor: not-allowed; opacity: .52; }
    .preset {
      text-align: left;
      display: grid;
      gap: 5px;
      align-content: start;
    }
    .risk { color: var(--muted); font-size: 12px; font-weight: 500; }
    textarea {
      width: 100%;
      min-height: 116px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 10px;
      font: 14px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--code);
    }
    .row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .runbar { display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
    .grid2 { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; }
    .timeline {
      min-height: 300px;
      max-height: 520px;
      overflow: auto;
      display: grid;
      align-content: start;
      gap: 10px;
    }
    .event {
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 10px;
      display: grid;
      gap: 5px;
    }
    .eventTop { display: flex; justify-content: space-between; gap: 10px; color: var(--muted); font-size: 12px; }
    .eventTitle { font-weight: 700; }
    .eventCode { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--code); font-size: 12px; word-break: break-word; }
    .gallery {
      min-height: 300px;
      max-height: 520px;
      overflow: auto;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-content: start;
      gap: 10px;
    }
    figure {
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 7px;
      overflow: hidden;
      background: #fafafa;
    }
    figure img {
      display: block;
      width: 100%;
      aspect-ratio: 4 / 3;
      object-fit: cover;
      background: #e8ebef;
    }
    figcaption { padding: 7px 8px; color: var(--muted); font-size: 12px; }
    .log {
      height: 300px;
      overflow: auto;
      background: #111827;
      color: #d7dee8;
      border-radius: 8px;
      padding: 12px;
      font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .logline { display: block; }
    .logline[data-stream="dashboard"] { color: #9dd8d3; }
    .logtime { color: #8a96a6; }
    .hint { color: var(--muted); margin: 9px 0 0; line-height: 1.45; }
    .ok { color: var(--ok); font-weight: 650; }
    .warn { color: var(--warn); font-weight: 650; }
    @media (max-width: 1050px) {
      main { grid-template-columns: 1fr; padding: 12px; }
      header { align-items: flex-start; flex-direction: column; }
      .actions, .grid2 { grid-template-columns: 1fr; }
      dl { grid-template-columns: 108px minmax(0, 1fr); }
      .gallery { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>XLeRobot Agent 控制台</h1>
      <div class="hint">查看配置、启动任务、跟踪工具调用，并直接看到 agent 过程中拍到的图片。</div>
    </div>
    <div id="runState" class="status stopped"><span class="dot"></span><span>已停止</span></div>
  </header>
  <main>
    <div class="stack">
      <section>
        <h2>运行状态</h2>
        <dl id="runtime"></dl>
      </section>
      <section>
        <h2>设备配置</h2>
        <dl id="config"></dl>
      </section>
      <section>
        <h2>已发现设备</h2>
        <ul id="devices" class="devices"></ul>
      </section>
      <section>
        <h2>校准文件</h2>
        <dl id="calibration"></dl>
      </section>
    </div>
    <div class="stack">
      <section>
        <div class="row">
          <h2>预设任务</h2>
          <button id="refreshBtn" type="button">刷新</button>
        </div>
        <div id="presets" class="actions"></div>
        <p class="hint">建议先运行“只观察”。这个任务只会转头拍图，不会移动底盘。</p>
      </section>
      <section>
        <h2>自定义任务</h2>
        <textarea id="taskInput" spellcheck="false">Use look_around exactly once, then summarize what you see. Do not move the base.</textarea>
        <div class="runbar">
          <button id="runCustom" class="primary" type="button">运行自定义任务</button>
          <button id="stopBtn" class="danger" type="button">停止 Agent</button>
        </div>
      </section>
      <div class="grid2">
        <section>
          <div class="row">
            <h2>操作过程</h2>
            <button id="clearEvents" type="button">清空视图</button>
          </div>
          <div id="timeline" class="timeline"></div>
        </section>
        <section>
          <div class="row">
            <h2>过程图片</h2>
            <button id="clearImages" type="button">清空视图</button>
          </div>
          <div id="gallery" class="gallery"></div>
        </section>
      </div>
      <section>
        <div class="row">
          <h2>原始日志</h2>
          <button id="clearLog" type="button">清空视图</button>
        </div>
        <div id="log" class="log" aria-live="polite"></div>
      </section>
    </div>
  </main>
  <script>
    let presets = {};
    let logCursor = 0;
    let eventCursor = 0;
    let running = false;

    const runState = document.getElementById('runState');
    const runtime = document.getElementById('runtime');
    const config = document.getElementById('config');
    const devices = document.getElementById('devices');
    const calibration = document.getElementById('calibration');
    const presetsNode = document.getElementById('presets');
    const logNode = document.getElementById('log');
    const timelineNode = document.getElementById('timeline');
    const galleryNode = document.getElementById('gallery');
    const taskInput = document.getElementById('taskInput');

    const keyNames = {
      XLEROBOT_MAIN_CAMERA: '主相机',
      XLEROBOT_RIGHT_ARM: '右臂/底盘',
      XLEROBOT_LEFT_ARM: '左臂/头部',
      XLEROBOT_LLM_PROVIDER: '模型提供方',
      XLEROBOT_LLM_BASE_URL: '模型地址',
      XLEROBOT_LLM_API_KEY: 'API Key',
      XLEROBOT_MODEL: '模型',
      XLEROBOT_AGENT_HISTORY_LEN: '文本历史轮数',
      XLEROBOT_LLM_VISUAL_HISTORY: '保留图片轮数',
      XLEROBOT_THINKING_LEVEL: '思考级别',
      XLEROBOT_VLA_POLICY_NAME: 'VLA 策略',
      XLEROBOT_VLA_POLICY_TYPE: 'VLA 类型',
      XLEROBOT_VLA_SERVER: 'VLA 服务',
      XLEROBOT_VLA_TASK_PROMPT: 'VLA 任务',
      XLEROBOT_RIGHT_CAMERA: '右臂相机',
      XLEROBOT_POLICY_DEVICE: '推理设备'
    };

    function dtRow(key, value) {
      return `<dt>${key}</dt><dd>${value || '<span class="empty">未设置</span>'}</dd>`;
    }

    function setRunning(isRunning, status) {
      running = isRunning;
      runState.className = `status ${isRunning ? 'running' : 'stopped'}`;
      runState.innerHTML = `<span class="dot"></span><span>${isRunning ? '运行中' : '已停止'}</span>`;
      document.querySelectorAll('button[data-preset], #runCustom').forEach(btn => btn.disabled = isRunning);
      document.getElementById('stopBtn').disabled = !isRunning;
      runtime.innerHTML = [
        dtRow('进程 PID', status.pid),
        dtRow('运行时长', status.uptime_s == null ? '' : `${status.uptime_s}s`),
        dtRow('返回码', status.returncode == null ? '' : status.returncode),
        dtRow('运行编号', status.run_id || ''),
        dtRow('完整命令', status.last_command && status.last_command.length ? escapeHtml(status.last_command.join(' ')) : '')
      ].join('');
    }

    function renderStatus(data) {
      presets = data.presets || {};
      setRunning(Boolean(data.runner.running), data.runner);
      const cfg = data.device.config || {};
      config.innerHTML = Object.keys(cfg).map(key => dtRow(keyNames[key] || key, escapeHtml(cfg[key]))).join('');
      devices.innerHTML = '';
      if (!data.device.devices || !data.device.devices.length) {
        devices.innerHTML = '<li class="empty">没有发现匹配的机器人串口设备。</li>';
      } else {
        for (const dev of data.device.devices) {
          const li = document.createElement('li');
          li.className = 'device';
          li.textContent = dev;
          devices.appendChild(li);
        }
      }
      const cal = data.device.calibration || {};
      calibration.innerHTML = [
        dtRow('左臂', cal.left_arm ? '<span class="ok">已存在</span>' : '<span class="warn">缺失</span>'),
        dtRow('右臂', cal.right_arm ? '<span class="ok">已存在</span>' : '<span class="warn">缺失</span>'),
        dtRow('目录', escapeHtml(cal.dir || ''))
      ].join('');
      renderPresets();
    }

    function renderPresets() {
      presetsNode.innerHTML = '';
      for (const [id, preset] of Object.entries(presets)) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'preset';
        btn.dataset.preset = id;
        btn.disabled = running;
        btn.innerHTML = `<span>${escapeHtml(preset.label)}</span><span class="risk">${escapeHtml(preset.risk)}</span>`;
        btn.addEventListener('click', () => startPreset(id));
        presetsNode.appendChild(btn);
      }
    }

    async function refreshStatus() {
      const res = await fetch('/api/status');
      renderStatus(await res.json());
    }

    async function startPreset(id) {
      logCursor = 0;
      eventCursor = 0;
      timelineNode.innerHTML = '';
      galleryNode.innerHTML = '';
      logNode.innerHTML = '';
      const res = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({preset: id})
      });
      const data = await res.json();
      if (data.error) appendLocal(`错误：${data.error}`);
      await refreshStatus();
    }

    async function startCustom() {
      logCursor = 0;
      eventCursor = 0;
      timelineNode.innerHTML = '';
      galleryNode.innerHTML = '';
      logNode.innerHTML = '';
      const res = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task: taskInput.value})
      });
      const data = await res.json();
      if (data.error) appendLocal(`错误：${data.error}`);
      await refreshStatus();
    }

    async function stopAgent() {
      await fetch('/api/stop', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
      await refreshStatus();
    }

    function appendLocal(line) {
      appendLogLine({time: Date.now() / 1000, stream: 'dashboard', line});
    }

    function appendLogLine(item) {
      const span = document.createElement('span');
      span.className = 'logline';
      span.dataset.stream = item.stream || 'agent';
      const time = new Date(item.time * 1000).toLocaleTimeString();
      span.innerHTML = `<span class="logtime">${time}</span> [${escapeHtml(item.stream)}] ${escapeHtml(item.line)}`;
      logNode.appendChild(span);
      logNode.scrollTop = logNode.scrollHeight;
    }

    function appendEvent(item) {
      const div = document.createElement('div');
      div.className = 'event';
      const time = new Date(item.time * 1000).toLocaleTimeString();
      const title = eventTitle(item);
      const detail = [];
      if (item.tool) detail.push(`工具：${item.tool}`);
      if (item.duration_s != null) detail.push(`耗时：${item.duration_s}s`);
      if (item.args) detail.push(`参数：${JSON.stringify(item.args)}`);
      if (item.result) detail.push(`结果：${item.result}`);
      if (item.error) detail.push(`错误：${item.error}`);
      if (item.image_messages_total != null) detail.push(`图片消息：总 ${item.image_messages_total} / 保留 ${item.image_messages_kept} / 裁剪 ${item.image_messages_pruned}`);
      div.innerHTML = `<div class="eventTop"><span>${time}</span><span>${escapeHtml(item.type || '')}</span></div><div class="eventTitle">${escapeHtml(title)}</div><div class="eventCode">${escapeHtml(detail.join('\\n'))}</div>`;
      timelineNode.appendChild(div);
      timelineNode.scrollTop = timelineNode.scrollHeight;
      if (Array.isArray(item.images)) {
        for (const image of item.images) appendImage(image, item);
      }
    }

    function appendImage(image, event) {
      const fig = document.createElement('figure');
      const time = new Date(event.time * 1000).toLocaleTimeString();
      fig.innerHTML = `<img src="${escapeHtml(image.url)}" alt="${escapeHtml(image.label || '过程图片')}"><figcaption>${time} · ${escapeHtml(event.tool || '')} · ${escapeHtml(image.label || '')}</figcaption>`;
      galleryNode.appendChild(fig);
      galleryNode.scrollTop = galleryNode.scrollHeight;
    }

    function eventTitle(item) {
      if (item.message) return item.message;
      if (item.type === 'tool_start') return `开始执行工具：${item.tool}`;
      if (item.type === 'tool_end') return `工具完成：${item.tool}`;
      if (item.type === 'tool_error') return `工具失败：${item.tool}`;
      if (item.type === 'tool_blocked') return `工具被安全拦截：${item.tool}`;
      if (item.type === 'llm_request_start') return '开始请求 LLM';
      if (item.type === 'llm_request_end') return 'LLM 请求完成';
      if (item.type === 'agent_start') return 'Agent 已启动';
      return item.type || '事件';
    }

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
    }

    async function pollLogs() {
      try {
        const res = await fetch(`/api/logs?after=${logCursor}`);
        const data = await res.json();
        for (const item of data.logs || []) appendLogLine(item);
        logCursor = data.next;
      } catch (err) {
        appendLocal(`日志轮询失败：${err.message}`);
      }
    }

    async function pollEvents() {
      try {
        const res = await fetch(`/api/events?after=${eventCursor}`);
        const data = await res.json();
        for (const item of data.events || []) appendEvent(item);
        eventCursor = data.next;
      } catch (err) {
        appendLocal(`事件轮询失败：${err.message}`);
      }
    }

    document.getElementById('refreshBtn').addEventListener('click', refreshStatus);
    document.getElementById('runCustom').addEventListener('click', startCustom);
    document.getElementById('stopBtn').addEventListener('click', stopAgent);
    document.getElementById('clearLog').addEventListener('click', () => { logNode.innerHTML = ''; });
    document.getElementById('clearEvents').addEventListener('click', () => { timelineNode.innerHTML = ''; });
    document.getElementById('clearImages').addEventListener('click', () => { galleryNode.innerHTML = ''; });

    refreshStatus();
    pollLogs();
    pollEvents();
    setInterval(refreshStatus, 2500);
    setInterval(pollLogs, 1000);
    setInterval(pollEvents, 1000);
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local XLeRobot agent dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env_values = load_dotenv(ROOT_DIR / ".env")
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    server.env_values = env_values  # type: ignore[attr-defined]
    print(f"XLeRobot dashboard: http://{args.host}:{args.port}", flush=True)
    print("Press Ctrl-C to stop the dashboard.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        RUNNER.stop()
        server.server_close()


if __name__ == "__main__":
    main()
