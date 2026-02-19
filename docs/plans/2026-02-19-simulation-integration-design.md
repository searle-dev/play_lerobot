# play_on_web Simulation Integration Design

## Date: 2026-02-19

## Goal

Integrate MuJoCo-GS-Web as a browser-side simulation environment into play_on_web, enabling users to teleoperate a virtual robot with the same interface used for real hardware. First version focuses on simulation teleoperation and rendering; data collection and policy validation are deferred.

## Architecture

### RobotBackend Abstraction

A unified `RobotBackend` interface decouples control components from the underlying execution target.

```typescript
interface RobotBackend {
  connect(config: any): Promise<void>
  disconnect(): Promise<void>
  onKeyDown(key: string): void
  onKeyUp(key: string): void
  onGamepadInput(input: GamepadInput): void
  getObservation(): RobotObservation
  reset(arm?: string): void
}
```

Two implementations:

- **RealRobotBackend** — wraps existing WebSocket communication to FastAPI backend, unchanged logic.
- **SimRobotBackend** — wraps MuJoCo WASM engine running in browser, using MuJoCo-GS-Web's controllers directly.

```
KeyboardControl / XboxControl / (future: GestureControl)
        |
   RobotBackend (interface)
      |                  |
RealRobotBackend     SimRobotBackend
      |                  |
WebSocket→FastAPI    MuJoCo WASM + Three.js + 3DGS
→lerobot→Hardware    (all in browser)
```

### SimRobotBackend Internals

```
SimRobotBackend
├── SimEngine
│   ├── MuJoCo WASM loader (mujoco-js)
│   ├── Model + Data (qpos, qvel, ctrl)
│   ├── Physics loop (mj_step)
│   └── Scene management (XML composition)
├── Robot Controller (from MuJoCo-GS-Web)
│   ├── XLeRobotController
│   ├── SO101Controller
│   └── PandaController
├── SimRenderer
│   ├── Three.js scene + WebGL renderer
│   ├── OrbitControls (camera)
│   └── GaussianSplatController (optional 3DGS)
└── Observation adapter
    └── qpos[] → {left_arm_shoulder_pan.pos: ...} format
```

First version uses MuJoCo-GS-Web's control logic directly. Control model unification with real hardware is deferred to a second iteration.

### Page Flow

```
Home / Mode Selection
  ├─ "Real Robot" → DeviceSetup (ports/cameras/calibration) → TeleopControl
  └─ "Simulation" → SimSetup (robot/environment selection)  → TeleopControl
```

### TeleopControl Differences by Mode

| Area | Real Mode | Sim Mode |
|------|-----------|----------|
| Video area | CameraView (JPEG stream) | SimulationView (Three.js canvas + optional 3DGS) |
| Control input | KeyboardControl / XboxControl via RobotBackend | Same components, same interface |
| Status display | RobotStatus (from backend observation) | RobotStatus (from MuJoCo qpos, format-converted) |
| Step level | slow/normal/fast | Not supported in v1 |
| Reset | moveToZero / moveToReset | SimEngine.reset() |

### Zustand Store Extension

```typescript
interface RobotStore {
  // New fields
  mode: 'real' | 'sim'
  simConfig: { robot: string; environment: string } | null
  backend: RobotBackend | null

  // Existing fields unchanged
  isConnected: boolean
  observation: RobotObservation | null
  controlMode: 'keyboard' | 'xbox'
  keymapConfig: KeymapConfig | null
  // ...
}
```

## Code Organization

### New Directory Structure

```
play_on_web/frontend/src/
├── simulation/                     # Simulation module
│   ├── SimEngine.ts                # MuJoCo WASM loading + physics loop
│   ├── SimRenderer.ts              # Three.js rendering pipeline
│   ├── SimRobotBackend.ts          # RobotBackend implementation
│   ├── SceneManager.ts             # Scene composition (from MuJoCo-GS-Web)
│   ├── GaussianSplatController.ts  # 3DGS rendering control
│   ├── controllers/                # Robot controllers (from MuJoCo-GS-Web)
│   │   ├── BaseController.ts
│   │   ├── XLeRobotController.ts
│   │   ├── SO101Controller.ts
│   │   └── PandaController.ts
│   └── utils/
│       ├── mujocoUtils.ts          # Coordinate conversion, scene loading
│       ├── quaternion.ts
│       └── inverseKinematics.ts
├── backend/                        # RobotBackend abstraction
│   ├── types.ts                    # RobotBackend interface
│   ├── RealRobotBackend.ts         # Wraps existing WebSocket logic
│   └── SimRobotBackend.ts          # Re-exports from simulation/
├── components/
│   ├── SimulationView.tsx          # Three.js canvas component
│   ├── SimSetup.tsx                # Simulation config page
│   └── ...                         # Existing components unchanged
```

### New npm Dependencies

```json
{
  "mujoco-js": "^0.0.7",
  "three": "^0.178.0",
  "@types/three": "^0.178.0",
  "@sparkjsdev/spark": "^0.1.10"
}
```

### Static Assets

```
play_on_web/frontend/public/sim-assets/
├── robots/           # Robot XML + mesh files
│   ├── xlerobot/
│   ├── panda/
│   └── ...
├── environments/     # Scene XML + .spz files
│   ├── tabletop/
│   └── basic.xml
└── mujoco_wasm.wasm  # MuJoCo WASM binary
```

## Data Flow: Simulation Mode

```
User presses 'W'
→ KeyboardControl.tsx onKeyDown
→ backend.onKeyDown('w')
→ SimRobotBackend: keyStates['w'] = true
→ (next requestAnimationFrame)
→ XLeRobotController.step(keyStates, model, data, mujoco)
→ Updates data.ctrl[]
→ mujoco.mj_step(model, data) × N substeps
→ Update Three.js mesh positions from data.xpos/xquat
→ renderer.render(scene, camera)
→ SimulationView canvas updates
→ getObservation() extracts qpos → RobotStatus updates
```

## Scope

### v1 (this iteration)

- RobotBackend abstraction layer
- SimRobotBackend with MuJoCo WASM
- Three.js rendering (+ optional 3DGS)
- SimSetup page (robot/environment selection)
- SimulationView component
- Mode selection (real/sim)
- Store extension
- MuJoCo-GS-Web controller integration (XLeRobot, SO101)

### Deferred

- Data collection in simulation
- RL policy validation (ONNX)
- Step level control in sim mode
- Keymap unification between sim and real
- Control logic unification (common IK/P-control model)
- Gesture recognition input
