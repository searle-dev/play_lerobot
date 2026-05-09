#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
XLEROBOT_DIR="${ROOT_DIR}/XLeRobot"
LEROBOT_DIR="${ROOT_DIR}/lerobot"

if [[ ! -d "${XLEROBOT_DIR}/software/src" ]]; then
  echo "Missing ${XLEROBOT_DIR}/software/src. Clone XLeRobot first." >&2
  exit 1
fi

if [[ ! -d "${LEROBOT_DIR}/src/lerobot" ]]; then
  echo "Missing ${LEROBOT_DIR}/src/lerobot. Clone LeRobot first." >&2
  exit 1
fi

mkdir -p \
  "${LEROBOT_DIR}/src/lerobot/robots/xlerobot" \
  "${LEROBOT_DIR}/src/lerobot/robots/xlerobot_2wheels" \
  "${LEROBOT_DIR}/src/lerobot/robots/xlerobot_mecanum" \
  "${LEROBOT_DIR}/src/lerobot/model" \
  "${LEROBOT_DIR}/src/joyconrobotics" \
  "${LEROBOT_DIR}/examples/xlerobot"

cp -R "${XLEROBOT_DIR}/software/src/robots/xlerobot/." \
  "${LEROBOT_DIR}/src/lerobot/robots/xlerobot/"
cp -R "${XLEROBOT_DIR}/software/src/robots/xlerobot_2wheels/." \
  "${LEROBOT_DIR}/src/lerobot/robots/xlerobot_2wheels/"
cp -R "${XLEROBOT_DIR}/software/src/robots/xlerobot_mecanum/." \
  "${LEROBOT_DIR}/src/lerobot/robots/xlerobot_mecanum/"
cp "${XLEROBOT_DIR}/software/src/model/SO101Robot.py" \
  "${LEROBOT_DIR}/src/lerobot/model/SO101Robot.py"
cp -R "${XLEROBOT_DIR}/software/joyconrobotics/." \
  "${LEROBOT_DIR}/src/joyconrobotics/"
cp "${XLEROBOT_DIR}/software/examples/5_xlerobot_teleop_xbox.py" \
  "${LEROBOT_DIR}/examples/xlerobot/5_xlerobot_teleop_xbox.py"
cp "${XLEROBOT_DIR}/software/examples/7_xlerobot_teleop_joycon.py" \
  "${LEROBOT_DIR}/examples/xlerobot/7_xlerobot_teleop_joycon.py"

echo "Synced XLeRobot sources into ${LEROBOT_DIR}"
