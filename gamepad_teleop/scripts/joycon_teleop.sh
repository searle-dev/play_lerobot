#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Error: venv not found at ${VENV_DIR}"
  echo "Run scripts/setup_env.sh first."
  exit 1
fi

source "${VENV_DIR}/bin/activate"

exec python "${ROOT_DIR}/programs/joycon_teleop.py" "$@"
