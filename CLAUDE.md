# CLAUDE.md - Project Guide for Claude Code

## Project Overview

**play_lerobot** is a collection of projects for the XLeRobot dual-arm mobile manipulator. The main active project is `play_on_web/` — a full-stack web teleoperation interface supporting both real hardware control and browser-based MuJoCo physics simulation.

## Repository Structure

```
play_lerobot/
├── play_on_web/
│   ├── backend/              # Python FastAPI backend (real robot control)
│   │   ├── main.py           # FastAPI app entry, REST + WebSocket endpoints
│   │   ├── robot_controller.py   # Core robot control with IK, P-control
│   │   ├── device_scanner.py     # Serial port + camera device scanning
│   │   ├── camera_manager.py     # Multi-camera stream management
│   │   ├── keymap_manager.py     # Keyboard/Xbox keymap profiles
│   │   └── config.py             # Pydantic settings
│   │
│   └── frontend/             # React + TypeScript frontend
│       ├── src/
│       │   ├── App.tsx           # Route switching (mode-select → setup → teleop)
│       │   ├── api/client.ts     # Axios HTTP + WebSocket factory
│       │   ├── stores/robotStore.ts  # Zustand state (mode, backend, config)
│       │   ├── backend/          # Backend abstraction layer
│       │   │   ├── types.ts          # RobotBackend interface
│       │   │   ├── RealRobotBackend.ts   # WebSocket + HTTP implementation
│       │   │   └── SimRobotBackend.ts    # MuJoCo simulation implementation
│       │   ├── simulation/       # MuJoCo simulation engine
│       │   │   ├── SimEngine.ts      # WASM physics wrapper
│       │   │   ├── SimRenderer.ts    # Three.js rendering
│       │   │   ├── controllers/      # Robot-specific controllers
│       │   │   └── utils/            # IK solver
│       │   ├── components/       # UI components
│       │   ├── pages/            # Page-level components
│       │   └── types/            # Shared TypeScript types
│       ├── public/sim-assets/    # MuJoCo robot/env assets (gitignored)
│       ├── vite.config.ts
│       ├── tsconfig.json
│       └── package.json
│
└── docs/plans/               # Design and implementation plan documents
```

## Tech Stack

- **Backend**: Python 3.8+, FastAPI, uvicorn, WebSocket, pydantic
- **Frontend**: React 18, TypeScript (strict), Vite 5, Zustand, Axios
- **Simulation**: MuJoCo-JS (WASM), Three.js, @sparkjsdev/spark
- **Hardware**: lerobot library (installed from /Users/ai/Project/lerobot)

## Quick Commands

```bash
# Frontend dev server (port 3000)
cd play_on_web/frontend && npm run dev

# Backend server (port 8000)
cd play_on_web/backend && conda activate lerobot && python main.py

# Frontend build + type check
cd play_on_web/frontend && npm run build

# Lint
cd play_on_web/frontend && npm run lint

# TypeScript check only
cd play_on_web/frontend && npx tsc --noEmit
```

## Architecture: Two Modes

The app supports two modes via the `RobotBackend` interface:

1. **Real mode** — connects to physical XLeRobot via FastAPI backend WebSocket. Keyboard/gamepad inputs go through WebSocket to Python robot_controller.
2. **Sim mode** — runs entirely in the browser. MuJoCo WASM handles physics, Three.js renders, `XLeRobotController` processes keyboard input. No backend server needed.

Both implement `RobotBackend` from `src/backend/types.ts`.

## Critical Configuration Values (DO NOT MODIFY)

```python
# In robot_controller.py — verified optimal values
xy_step = 0.0081      # Cartesian step (meters) — smaller causes jitter
degree_step = 3       # Joint step (degrees) — must be integer
kp = 0.81             # P-control gain
current_x = 0.1629    # Initial reference X
current_y = 0.1131    # Initial reference Y
```

Reference implementation: `lerobot/examples/xlerobot/4_xlerobot_teleop_keyboard.py`

## Important Technical Notes

### MuJoCo WASM Requirements
- `vite.config.ts` includes `assetsInclude: ['**/*.wasm']` and `optimizeDeps.exclude: ['mujoco-js']`
- COOP/COEP headers required for SharedArrayBuffer: `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Embedder-Policy: require-corp`

### Simulation Assets
- Robot meshes/XMLs live in `frontend/public/sim-assets/` — gitignored due to binary size
- Assets loaded at runtime via `index.json` manifests into MuJoCo's Emscripten VFS

### React + Three.js Timing
- `SimRobotBackend.connect()` loads the MuJoCo engine before the Three.js container mounts
- `setContainer()` must create the renderer if the engine is already initialized (see fix at commit 315619b)

### Base Chassis Control
- Uses velocity commands, not position commands
- `keyup` events MUST send explicit stop commands (vel=0) or the robot keeps moving

### macOS Serial Ports
- Each USB device creates both `/dev/tty.usbmodem*` and `/dev/cu.usbmodem*`
- Only `tty.*` devices should be used; filter out `cu.*` duplicates

## Code Conventions

- TypeScript strict mode throughout the frontend
- Python type annotations with pydantic models
- API responses use `{ status: "success" | "error", message?: string, data?: ... }`
- WebSocket messages use `{ type: string, data?: object }`
- Zustand for frontend state management (single `robotStore`)
- Component CSS files colocated with components

## Testing

- Backend: `test_device_scan.py`, `test_port_detection.py` (run directly with python)
- Frontend: No test suite currently configured
- Verification: `npm run build` (includes tsc) and `npm run lint` (zero warnings policy)

## Key Documentation

- `play_on_web/CURSOR.md` — Detailed AI assistant guide with control parameters and known issues
- `play_on_web/docs/fixes/` — Technical fixes with root cause analysis
- `play_on_web/docs/guides/` — User guides (safe reset, base control)
- `docs/plans/` — Design documents and implementation plans
