#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="${PYTHON_BIN}"
elif command -v python3.13 >/dev/null 2>&1; then
  PYTHON_BIN="python3.13"
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="python3.12"
else
  PYTHON_BIN="python3"
fi

cd "${ROOT_DIR}"

if [[ ! -d "XLeRobot" ]]; then
  git clone --depth 1 https://github.com/Vector-Wangel/XLeRobot.git XLeRobot
fi

if [[ ! -d "lerobot" ]]; then
  git clone --depth 1 https://github.com/huggingface/lerobot.git lerobot
fi

"${ROOT_DIR}/scripts/sync_xlerobot_into_lerobot.sh"

if [[ ! -d "${VENV_DIR}" ]]; then
  if command -v uv >/dev/null 2>&1; then
    uv venv --python "${PYTHON_BIN}" "${VENV_DIR}"
  else
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi
fi

source "${VENV_DIR}/bin/activate"

if command -v uv >/dev/null 2>&1; then
  uv pip install --python "${VENV_DIR}/bin/python" -r requirements-runtime.txt
  uv pip install --python "${VENV_DIR}/bin/python" -e "./lerobot[feetech,gamepad,core_scripts,async]" --reinstall-package lerobot
else
  python -m ensurepip --upgrade
  python -m pip install --upgrade pip
  python -m pip install -r requirements-runtime.txt
  python -m pip install -e "./lerobot[feetech,gamepad,core_scripts,async]" --force-reinstall
fi

echo
echo "Environment ready."
echo "Activate with: source ${VENV_DIR}/bin/activate"
echo "Xbox teleop:   python programs/xbox_teleop.py"
echo "LLM agent:     python programs/llm_agent.py --task 'Approach a human.'"
