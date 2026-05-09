# XLeRobot Runtime

This directory contains a local XLeRobot runtime prepared from:

- XLeRobot docs: https://xlerobot.readthedocs.io/zh-cn/latest/software/index.html
- XLeRobot source: `robot/XLeRobot`
- LeRobot source with XLeRobot files synced in: `robot/lerobot`

## Setup

LeRobot `main` currently requires Python 3.12+. The setup script uses `python3.12` by default; override it with `PYTHON_BIN` if needed.

```bash
cd robot
./scripts/setup_env.sh
cp .env.example .env
```

Edit `.env` for the model provider key and stable device names. For Linux hardware, the XLeRobot docs recommend stable udev names and, when using raw serial devices, permissions such as `sudo chmod 666 /dev/ttyACM0 /dev/ttyACM1`.

## Program 1: Controller Teleoperation

```bash
cd robot
source .venv/bin/activate
python programs/xbox_teleop.py --port1 /dev/ttyACM0 --port2 /dev/ttyACM1
```

This runs the official `5_xlerobot_teleop_xbox.py` example from the local LeRobot checkout. Connect the Xbox controller before launch.

For Nintendo Switch Joy-Con teleoperation, pair both Joy-Cons with the host first, then run:

```bash
python programs/joycon_teleop.py --port1 /dev/ttyACM0 --port2 /dev/ttyACM1
```

This runs XLeRobot's official `7_xlerobot_teleop_joycon.py` example and the modified `joyconrobotics` package shipped under `XLeRobot/software/joyconrobotics`.

To bring up only the right Joy-Con first:

```bash
python programs/joycon_teleop.py --mode right-only --port1 /dev/ttyACM0 --port2 /dev/ttyACM1
```

## Program 2: LLM Agent

Basic navigation agent:

```bash
cd robot
source .venv/bin/activate
python programs/llm_agent.py --task "Approach a human."
```

Visual dashboard:

```bash
python programs/robot_dashboard.py
```

Open `http://127.0.0.1:8765` to use the Chinese dashboard. It shows device configuration, safe preset tasks, the agent's tool-call timeline, images captured during execution, stop controls, and raw logs.

OpenAI-compatible model providers are configured through `.env`:

```bash
XLEROBOT_LLM_PROVIDER=openai-compatible
XLEROBOT_LLM_BASE_URL=https://zenmux.ai/api/v1
XLEROBOT_LLM_API_KEY=your-api-key
XLEROBOT_MODEL=google/gemini-3.1-pro-preview
```

Run with the `.env` defaults:

```bash
python programs/llm_agent.py --task "Approach a human."
```

You can use any model id supported by the configured endpoint, for example `openai/gpt-5.2` or a Gemini/Claude model exposed by the provider.

Voice-command mode:

```bash
python programs/llm_agent.py --voice --sounddevice-index 2 --wakeword "hey robot" --tts
```

With a VLA manipulation policy:

```bash
python -m lerobot.async_inference.policy_server --host=0.0.0.0 --port=8080
python programs/llm_agent.py \
  --task "Grab the notebook and give it to a human." \
  --vla-policy-name "your-hf-user/your-policy" \
  --vla-task-prompt "Grab the notebook."
```

## Maintenance

If `robot/XLeRobot` is updated, resync the files into LeRobot:

```bash
cd robot
./scripts/sync_xlerobot_into_lerobot.sh
```
