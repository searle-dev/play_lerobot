# Simulation Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate MuJoCo-GS-Web as a browser-side simulation environment into play_on_web, sharing the same UI and control interface used for real hardware.

**Architecture:** A `RobotBackend` abstraction decouples input components from execution targets. `RealRobotBackend` wraps existing WebSocket logic; `SimRobotBackend` wraps MuJoCo WASM + Three.js running in-browser. Mode selection at startup routes all control flow to the chosen backend.

**Tech Stack:** React 18 + TypeScript + Vite, MuJoCo WASM (mujoco-js), Three.js, @sparkjsdev/spark (3DGS), Zustand

**Reference:** Design document at `docs/plans/2026-02-19-simulation-integration-design.md`

---

### Task 1: Install Dependencies and Configure Vite

**Files:**
- Modify: `play_on_web/frontend/package.json`
- Modify: `play_on_web/frontend/vite.config.ts`
- Modify: `play_on_web/frontend/tsconfig.json`

**Step 1: Install npm packages**

Run:
```bash
cd play_on_web/frontend
npm install mujoco-js@^0.0.7 three@^0.178.0 @sparkjsdev/spark@^0.1.10
npm install -D @types/three@^0.178.0
```

**Step 2: Configure Vite for WASM**

Modify `play_on_web/frontend/vite.config.ts` — add `optimizeDeps` and `assetsInclude` for WASM files:

```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  assetsInclude: ['**/*.wasm'],
  optimizeDeps: {
    exclude: ['mujoco-js'],
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
```

Note: The COOP/COEP headers are required for `SharedArrayBuffer` which MuJoCo WASM may need.

**Step 3: Verify build works**

Run: `cd play_on_web/frontend && npm run build`
Expected: Build succeeds (may have warnings, no errors)

**Step 4: Commit**

```bash
git add play_on_web/frontend/package.json play_on_web/frontend/package-lock.json play_on_web/frontend/vite.config.ts
git commit -m "chore: add mujoco-js, three.js, spark dependencies for simulation"
```

---

### Task 2: Copy Static Assets from MuJoCo-GS-Web

**Files:**
- Create: `play_on_web/frontend/public/sim-assets/` (directory with robot/environment assets)

**Step 1: Copy WASM and robot/environment assets**

```bash
# Create target directory
mkdir -p play_on_web/frontend/public/sim-assets

# Copy MuJoCo WASM files from node_modules after install
cp -r node_modules/mujoco-js/dist/mujoco_wasm.* play_on_web/frontend/public/sim-assets/

# Copy robot assets from MuJoCo-GS-Web
cp -r ~/Project/MuJoCo-GS-Web/assets/robots play_on_web/frontend/public/sim-assets/
cp -r ~/Project/MuJoCo-GS-Web/assets/environments play_on_web/frontend/public/sim-assets/
```

**Step 2: Add sim-assets to .gitignore (large binary files)**

Add to `play_on_web/frontend/.gitignore`:
```
public/sim-assets/
```

Note: These binary assets (mesh STL files, .spz Gaussian splat files, WASM) are too large for git. They should be downloaded or symlinked during setup. For now, we copy them locally for development.

**Step 3: Verify assets are accessible**

Run: `cd play_on_web/frontend && npm run dev`
Then check: `curl -s http://localhost:3000/sim-assets/environments/basic.xml | head -5`
Expected: XML content of the basic environment file

**Step 4: Commit**

```bash
git add play_on_web/frontend/.gitignore
git commit -m "chore: add sim-assets gitignore for large binary simulation files"
```

---

### Task 3: Create RobotBackend Interface and Types

**Files:**
- Create: `play_on_web/frontend/src/backend/types.ts`

**Step 1: Define the RobotBackend interface**

```typescript
// play_on_web/frontend/src/backend/types.ts

import type { RobotObservation } from '../stores/robotStore'

export interface GamepadInput {
  axes: number[]       // Stick values [-1, 1]
  buttons: boolean[]   // Button pressed states
}

export interface RobotBackend {
  /** Connect to robot (real or simulated) */
  connect(config: Record<string, unknown>): Promise<void>

  /** Disconnect and clean up */
  disconnect(): Promise<void>

  /** Handle keyboard key down (uses event.code, e.g. 'KeyW') */
  onKeyDown(code: string): void

  /** Handle keyboard key up */
  onKeyUp(code: string): void

  /** Handle gamepad input (called at poll rate) */
  onGamepadInput(input: GamepadInput): void

  /** Get current robot observation */
  getObservation(): RobotObservation

  /** Reset robot to initial state */
  reset(): void

  /** Whether the backend is currently connected */
  readonly isConnected: boolean
}

export type RobotMode = 'real' | 'sim'

export interface SimConfig {
  robot: string
  environment: string
}
```

**Step 2: Commit**

```bash
git add play_on_web/frontend/src/backend/types.ts
git commit -m "feat: add RobotBackend interface types"
```

---

### Task 4: Create RealRobotBackend

Wraps existing WebSocket + HTTP logic into the `RobotBackend` interface. This is a refactor — no behavior changes.

**Files:**
- Create: `play_on_web/frontend/src/backend/RealRobotBackend.ts`

**Step 1: Implement RealRobotBackend**

```typescript
// play_on_web/frontend/src/backend/RealRobotBackend.ts

import type { RobotBackend, GamepadInput } from './types'
import type { RobotObservation } from '../stores/robotStore'
import { createTeleopWebSocket, robotApi, keymapApi } from '../api/client'
import type { KeyboardKeymap } from '../types/keymap'

export class RealRobotBackend implements RobotBackend {
  private ws: WebSocket | null = null
  private _isConnected = false
  private _observation: RobotObservation = {}
  private keymap: KeyboardKeymap | null = null
  private reverseKeymap: Record<string, { category: 'left' | 'right' | 'base'; action: string }> = {}
  private onObservationUpdate: ((obs: RobotObservation) => void) | null = null

  constructor(onObservationUpdate?: (obs: RobotObservation) => void) {
    this.onObservationUpdate = onObservationUpdate ?? null
  }

  get isConnected() { return this._isConnected }

  async connect(config: Record<string, unknown>): Promise<void> {
    // Load keymap
    try {
      const resp = await keymapApi.getCurrentKeymap()
      if (resp.data.status === 'success') {
        this.keymap = resp.data.keymap.keyboard
        this._buildReverseKeymap()
      }
    } catch {
      // Use default if keymap fails to load
    }

    // Connect WebSocket
    this.ws = createTeleopWebSocket(
      (data: any) => {
        if (data.type === 'observation' || data.type === 'action_result') {
          const obs = data.data?.observation ?? data.data
          if (obs) {
            this._observation = obs
            this.onObservationUpdate?.(obs)
          }
        }
      },
      (error: Event) => console.error('Teleop WebSocket error:', error),
      () => { this.ws = null }
    )
    this._isConnected = true
  }

  async disconnect(): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.close()
    }
    this.ws = null
    this._isConnected = false
  }

  onKeyDown(code: string): void {
    // Convert event.code to key character for lookup
    const key = this._codeToKey(code)
    const mapping = this.reverseKeymap[key]
    if (!mapping) return

    if (mapping.category === 'base') {
      this._send({ type: 'base_action', data: { direction: mapping.action } })
    } else {
      this._send({ type: 'keyboard_action', data: { arm: mapping.category, action: mapping.action } })
    }
  }

  onKeyUp(code: string): void {
    const key = this._codeToKey(code)
    const mapping = this.reverseKeymap[key]
    if (mapping && mapping.category === 'base') {
      this._send({ type: 'base_stop' })
    }
  }

  onGamepadInput(input: GamepadInput): void {
    // Forward gamepad as arm actions (same logic as current XboxControl)
    const { axes } = input
    const deadzone = 0.5

    if (Math.abs(axes[0]) > deadzone) {
      this._send({ type: 'keyboard_action', data: { arm: 'left', action: axes[0] > 0 ? 'y+' : 'y-' } })
    }
    if (Math.abs(axes[1]) > deadzone) {
      this._send({ type: 'keyboard_action', data: { arm: 'left', action: axes[1] > 0 ? 'x-' : 'x+' } })
    }
    if (Math.abs(axes[2]) > deadzone) {
      this._send({ type: 'keyboard_action', data: { arm: 'right', action: axes[2] > 0 ? 'y+' : 'y-' } })
    }
    if (Math.abs(axes[3]) > deadzone) {
      this._send({ type: 'keyboard_action', data: { arm: 'right', action: axes[3] > 0 ? 'x-' : 'x+' } })
    }
  }

  getObservation(): RobotObservation {
    return this._observation
  }

  reset(): void {
    robotApi.moveToZero('both').catch(console.error)
  }

  private _send(msg: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg))
    }
  }

  private _codeToKey(code: string): string {
    // Convert KeyboardEvent.code to the key character used in keymap
    // e.g. 'KeyW' → 'W', 'Digit7' → '7', 'Slash' → '/'
    if (code.startsWith('Key')) return code.slice(3)
    if (code.startsWith('Digit')) return code.slice(5)
    const codeMap: Record<string, string> = {
      'Slash': '/', 'Minus': '-', 'Equal': '+',
      'BracketLeft': '[', 'BracketRight': ']',
      'Semicolon': ';', 'Quote': "'", 'Comma': ',',
      'Period': '.', 'Backquote': '`',
      'NumpadMultiply': '*', 'NumpadAdd': '+', 'NumpadSubtract': '-',
      'Numpad0': '0', 'Numpad1': '1', 'Numpad2': '2', 'Numpad3': '3',
      'Numpad4': '4', 'Numpad5': '5', 'Numpad6': '6', 'Numpad7': '7',
      'Numpad8': '8', 'Numpad9': '9',
    }
    return codeMap[code] ?? code
  }

  private _buildReverseKeymap(): void {
    if (!this.keymap) return
    this.reverseKeymap = {}
    for (const [action, key] of Object.entries(this.keymap.left_arm)) {
      this.reverseKeymap[key.toUpperCase()] = { category: 'left', action }
    }
    for (const [action, key] of Object.entries(this.keymap.right_arm)) {
      this.reverseKeymap[key.toUpperCase()] = { category: 'right', action }
    }
    for (const [action, key] of Object.entries(this.keymap.base)) {
      this.reverseKeymap[key.toUpperCase()] = { category: 'base', action }
    }
  }
}
```

**Step 2: Verify it compiles**

Run: `cd play_on_web/frontend && npx tsc --noEmit`
Expected: No errors from RealRobotBackend.ts (may have pre-existing errors elsewhere)

**Step 3: Commit**

```bash
git add play_on_web/frontend/src/backend/RealRobotBackend.ts
git commit -m "feat: add RealRobotBackend wrapping existing WebSocket logic"
```

---

### Task 5: Port Simulation Core from MuJoCo-GS-Web

Port the minimal set of MuJoCo-GS-Web modules to TypeScript. These are ported as `.js` files with JSDoc types initially (the originals are plain JS), placed in `src/simulation/`.

**Files:**
- Create: `play_on_web/frontend/src/simulation/utils/inverseKinematics.ts`
- Create: `play_on_web/frontend/src/simulation/controllers/BaseController.ts`
- Create: `play_on_web/frontend/src/simulation/controllers/XLeRobotController.ts`
- Create: `play_on_web/frontend/src/simulation/controllers/index.ts`

**Step 1: Port inverseKinematics**

Copy from `/Users/ai/Project/MuJoCo-GS-Web/src/utils/math/inverseKinematics.js` and add TypeScript types. The function body is pure math with no external dependencies.

```typescript
// play_on_web/frontend/src/simulation/utils/inverseKinematics.ts

export function inverseKinematics2Link(
  x: number, y: number,
  l1 = 0.1159, l2 = 0.1350
): [number, number] {
  // (Copy the exact function body from MuJoCo-GS-Web/src/utils/math/inverseKinematics.js)
  // Lines 13-56 of that file
}
```

**Step 2: Port BaseController**

```typescript
// play_on_web/frontend/src/simulation/controllers/BaseController.ts

export interface KeyStates {
  [code: string]: boolean
}

export abstract class BaseController {
  initialized = false

  abstract initialize(model: any, data: any, mujoco: any): Promise<void>
  abstract reset(model: any, data: any): void
  abstract step(keyStates: KeyStates, model: any, data: any, mujoco: any): Promise<void>
  abstract getControlKeys(): string[]
  abstract getDescription(): string
}
```

**Step 3: Port XLeRobotController**

Copy from `/Users/ai/Project/MuJoCo-GS-Web/src/utils/controllers/XLeRobotController.js` — keep exact same logic, add TypeScript types. Import `inverseKinematics2Link` from the local port.

```typescript
// play_on_web/frontend/src/simulation/controllers/XLeRobotController.ts

import { BaseController, type KeyStates } from './BaseController'
import { inverseKinematics2Link } from '../utils/inverseKinematics'

// (Port the full class from MuJoCo-GS-Web with TypeScript annotations)
// Source: /Users/ai/Project/MuJoCo-GS-Web/src/utils/controllers/XLeRobotController.js
```

**Step 4: Create controllers index**

```typescript
// play_on_web/frontend/src/simulation/controllers/index.ts
export { BaseController } from './BaseController'
export { XLeRobotController } from './XLeRobotController'
```

**Step 5: Verify types compile**

Run: `cd play_on_web/frontend && npx tsc --noEmit`

**Step 6: Commit**

```bash
git add play_on_web/frontend/src/simulation/
git commit -m "feat: port MuJoCo-GS-Web controllers and IK to TypeScript"
```

---

### Task 6: Create SimEngine (MuJoCo WASM Wrapper)

The core simulation engine that loads MuJoCo WASM, manages the virtual filesystem, loads scenes, and runs physics steps.

**Files:**
- Create: `play_on_web/frontend/src/simulation/SimEngine.ts`

**Step 1: Implement SimEngine**

Reference files:
- `/Users/ai/Project/MuJoCo-GS-Web/src/main.js` lines 18-23 (WASM loading)
- `/Users/ai/Project/MuJoCo-GS-Web/src/utils/SceneManager.js` (scene composition)
- `/Users/ai/Project/MuJoCo-GS-Web/src/mujocoUtils.js` (downloadRobotAssets, loadSceneFromURL)

```typescript
// play_on_web/frontend/src/simulation/SimEngine.ts

import { XLeRobotController } from './controllers/XLeRobotController'
import type { BaseController, KeyStates } from './controllers/BaseController'

// MuJoCo types (from mujoco-js, loosely typed)
type MuJoCoModule = any
type MjModel = any
type MjData = any

export interface SimConfig {
  robot: string
  environment: string
}

const ROBOT_CONTROLLERS: Record<string, new () => BaseController> = {
  'xlerobot': XLeRobotController,
}

const ASSET_BASE = '/sim-assets'

export class SimEngine {
  private mujoco: MuJoCoModule | null = null
  private model: MjModel | null = null
  private data: MjData | null = null
  private controller: BaseController | null = null
  private keyStates: KeyStates = {}
  private _initialized = false

  get initialized() { return this._initialized }

  /** Load MuJoCo WASM module */
  async loadMuJoCo(): Promise<void> {
    if (this.mujoco) return
    // Dynamic import of mujoco-js WASM module
    const loadModule = (await import('mujoco-js')).default
    this.mujoco = await loadModule()
    this.mujoco.FS.mkdir('/working')
    this.mujoco.FS.mount(this.mujoco.MEMFS, { root: '.' }, '/working')
  }

  /** Download and write asset files to virtual filesystem */
  async downloadAssets(robot: string, environment: string): Promise<void> {
    // Fetch robot and environment XML/mesh files from public/sim-assets/
    // and write them to Emscripten virtual filesystem
    // This mirrors MuJoCo-GS-Web's downloadRobotAssets() logic
    // (Implementation will fetch files and write to mujoco.FS)
  }

  /** Load scene (environment + robot) and create model/data */
  async loadScene(config: SimConfig): Promise<void> {
    await this.loadMuJoCo()
    await this.downloadAssets(config.robot, config.environment)

    // Compose scene XML with <include> directives
    // (Mirror SceneManager.loadModularScene logic)

    // Load model and create data
    // this.model = this.mujoco.MjModel.loadFromXML('/working/scene.xml')
    // this.data = new this.mujoco.MjData(this.model)

    // Initialize controller
    const ControllerClass = ROBOT_CONTROLLERS[config.robot]
    if (ControllerClass) {
      this.controller = new ControllerClass()
      await this.controller.initialize(this.model, this.data, this.mujoco)
      for (const key of this.controller.getControlKeys()) {
        this.keyStates[key] = false
      }
    }

    this._initialized = true
  }

  /** Run one frame of physics simulation (multiple substeps) */
  step(): void {
    if (!this.model || !this.data || !this.mujoco) return

    // Run controller step (reads keyStates, writes ctrl[])
    this.controller?.step(this.keyStates, this.model, this.data, this.mujoco)

    // Run physics substeps
    const timestep = this.model.opt.timestep
    const stepsPerFrame = Math.round(1 / (60 * timestep))  // e.g. ~8 steps at 500Hz/60fps
    for (let i = 0; i < stepsPerFrame; i++) {
      this.mujoco.mj_step(this.model, this.data)
    }
  }

  /** Update key state */
  setKeyState(code: string, pressed: boolean): void {
    if (code in this.keyStates) {
      this.keyStates[code] = pressed
    }
  }

  /** Get model (for renderer to read body count, names, etc.) */
  getModel(): MjModel | null { return this.model }

  /** Get data (for renderer to read xpos, xquat) */
  getData(): MjData | null { return this.data }

  /** Get MuJoCo module ref */
  getMuJoCo(): MuJoCoModule | null { return this.mujoco }

  /** Get observation in play_on_web format */
  getObservation(): Record<string, number> {
    if (!this.model || !this.data) return {}
    const obs: Record<string, number> = {}
    // Read qpos values and map to named joints
    // This mapping depends on the robot's joint names in the XML
    for (let i = 0; i < this.model.nq; i++) {
      obs[`qpos_${i}`] = this.data.qpos[i]
    }
    return obs
  }

  /** Reset simulation to initial state */
  reset(): void {
    if (!this.model || !this.data || !this.mujoco) return
    this.mujoco.mj_resetData(this.model, this.data)
    this.controller?.reset(this.model, this.data)
  }

  /** Clean up resources */
  dispose(): void {
    this.model = null
    this.data = null
    this.controller = null
    this.keyStates = {}
    this._initialized = false
  }
}
```

Note: The `downloadAssets` and `loadScene` methods will need full implementation — they need to fetch files from `/sim-assets/` via HTTP and write them to MuJoCo's Emscripten virtual filesystem. This mirrors the logic in MuJoCo-GS-Web's `mujocoUtils.js::downloadRobotAssets()` and `SceneManager.js::loadModularScene()`. The implementer should reference those files directly when filling in the bodies.

**Step 2: Verify types**

Run: `cd play_on_web/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add play_on_web/frontend/src/simulation/SimEngine.ts
git commit -m "feat: add SimEngine wrapping MuJoCo WASM physics"
```

---

### Task 7: Create SimRenderer (Three.js Rendering)

**Files:**
- Create: `play_on_web/frontend/src/simulation/SimRenderer.ts`

**Step 1: Implement SimRenderer**

Reference: `/Users/ai/Project/MuJoCo-GS-Web/src/main.js` constructor (lines 60-143) and render loop (lines 451-483).

```typescript
// play_on_web/frontend/src/simulation/SimRenderer.ts

import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export class SimRenderer {
  private renderer: THREE.WebGLRenderer
  private scene: THREE.Scene
  private camera: THREE.PerspectiveCamera
  private controls: OrbitControls
  private bodies: Record<number, THREE.Object3D> = {}
  private animationId: number | null = null

  constructor(container: HTMLElement) {
    // Scene
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color(0.15, 0.25, 0.35)

    // Camera
    this.camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.001, 100)
    this.camera.position.set(0.5, 1.7, -3)
    this.scene.add(this.camera)

    // Lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.1 * Math.PI)
    this.scene.add(ambient)

    const spot = new THREE.SpotLight()
    spot.angle = 1.11
    spot.penumbra = 0.5
    spot.castShadow = true
    spot.intensity = spot.intensity * Math.PI * 10
    spot.position.set(0, 3, 3)
    this.scene.add(spot)

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    this.renderer.setPixelRatio(window.devicePixelRatio)
    this.renderer.setSize(container.clientWidth, container.clientHeight)
    this.renderer.shadowMap.enabled = true
    container.appendChild(this.renderer.domElement)

    // Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement)
    this.controls.target.set(0, 0.7, 0)
    this.controls.enableDamping = true
    this.controls.dampingFactor = 0.1
    this.controls.update()
  }

  /** Build Three.js meshes from loaded MuJoCo scene.
   *  Reference: mujocoUtils.js loadSceneFromURL() which creates
   *  THREE geometries from MuJoCo geom types (box, sphere, capsule, mesh). */
  buildScene(model: any, data: any, mujoco: any): void {
    // Iterate over model.ngeom geometries
    // Create appropriate THREE.Mesh for each (Box, Sphere, Capsule, loaded STL mesh)
    // Store body references in this.bodies for animation
    // This mirrors the logic in mujocoUtils.js::loadSceneFromURL()
  }

  /** Update mesh transforms from MuJoCo simulation state */
  updateFromPhysics(model: any, data: any): void {
    for (let b = 0; b < model.nbody; b++) {
      const body = this.bodies[b]
      if (!body) continue
      // Read position from data.xpos
      body.position.set(
        data.xpos[b * 3],
        data.xpos[b * 3 + 2],   // MuJoCo Y → Three.js Y (up)
        -data.xpos[b * 3 + 1]   // MuJoCo Z → Three.js -Z
      )
      // Read quaternion from data.xquat
      body.quaternion.set(
        data.xquat[b * 4 + 1],
        data.xquat[b * 4 + 3],
        -data.xquat[b * 4 + 2],
        data.xquat[b * 4 + 0]   // MuJoCo w,x,y,z → Three.js x,y,z,w with coord swap
      )
    }
  }

  /** Render one frame */
  render(): void {
    this.controls.update()
    this.renderer.render(this.scene, this.camera)
  }

  /** Handle container resize */
  resize(width: number, height: number): void {
    this.camera.aspect = width / height
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(width, height)
  }

  /** Get the Three.js scene (for GaussianSplatController to add SplatMesh) */
  getScene(): THREE.Scene { return this.scene }

  /** Clean up WebGL resources */
  dispose(): void {
    this.renderer.dispose()
    this.controls.dispose()
    this.bodies = {}
  }
}
```

Note: The `buildScene` method is the most complex part. It must replicate `mujocoUtils.js::loadSceneFromURL()` which creates Three.js geometry from MuJoCo geom types. The implementer should port this from the 800+ line function in mujocoUtils.js, starting with basic geom types (box, sphere, capsule, mesh) and adding visual fidelity later.

**Step 2: Commit**

```bash
git add play_on_web/frontend/src/simulation/SimRenderer.ts
git commit -m "feat: add SimRenderer for Three.js rendering of MuJoCo scenes"
```

---

### Task 8: Create SimRobotBackend

Ties SimEngine + SimRenderer together behind the RobotBackend interface.

**Files:**
- Create: `play_on_web/frontend/src/backend/SimRobotBackend.ts`

**Step 1: Implement SimRobotBackend**

```typescript
// play_on_web/frontend/src/backend/SimRobotBackend.ts

import type { RobotBackend, GamepadInput, SimConfig } from './types'
import type { RobotObservation } from '../stores/robotStore'
import { SimEngine } from '../simulation/SimEngine'
import { SimRenderer } from '../simulation/SimRenderer'

export class SimRobotBackend implements RobotBackend {
  private engine: SimEngine
  private renderer: SimRenderer | null = null
  private container: HTMLElement | null = null
  private animationId: number | null = null
  private _isConnected = false
  private onObservationUpdate: ((obs: RobotObservation) => void) | null = null

  constructor(onObservationUpdate?: (obs: RobotObservation) => void) {
    this.engine = new SimEngine()
    this.onObservationUpdate = onObservationUpdate ?? null
  }

  get isConnected() { return this._isConnected }

  /** Attach a DOM container for rendering. Must be called before connect(). */
  setContainer(container: HTMLElement): void {
    this.container = container
  }

  async connect(config: Record<string, unknown>): Promise<void> {
    const simConfig = config as unknown as SimConfig
    await this.engine.loadScene(simConfig)

    if (this.container) {
      this.renderer = new SimRenderer(this.container)
      this.renderer.buildScene(
        this.engine.getModel(),
        this.engine.getData(),
        this.engine.getMuJoCo()
      )
    }

    this._isConnected = true
    this._startLoop()
  }

  async disconnect(): Promise<void> {
    this._stopLoop()
    this.renderer?.dispose()
    this.renderer = null
    this.engine.dispose()
    this._isConnected = false
  }

  onKeyDown(code: string): void {
    this.engine.setKeyState(code, true)
  }

  onKeyUp(code: string): void {
    this.engine.setKeyState(code, false)
  }

  onGamepadInput(_input: GamepadInput): void {
    // TODO: Map gamepad axes/buttons to key states for controller
  }

  getObservation(): RobotObservation {
    return this.engine.getObservation()
  }

  reset(): void {
    this.engine.reset()
  }

  private _startLoop(): void {
    const loop = () => {
      if (!this._isConnected) return

      // Physics step
      this.engine.step()

      // Update rendering
      if (this.renderer) {
        this.renderer.updateFromPhysics(this.engine.getModel(), this.engine.getData())
        this.renderer.render()
      }

      // Emit observation
      const obs = this.engine.getObservation()
      this.onObservationUpdate?.(obs)

      this.animationId = requestAnimationFrame(loop)
    }
    this.animationId = requestAnimationFrame(loop)
  }

  private _stopLoop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId)
      this.animationId = null
    }
  }
}
```

**Step 2: Commit**

```bash
git add play_on_web/frontend/src/backend/SimRobotBackend.ts
git commit -m "feat: add SimRobotBackend bridging MuJoCo sim to RobotBackend interface"
```

---

### Task 9: Extend Zustand Store with Mode and Backend

**Files:**
- Modify: `play_on_web/frontend/src/stores/robotStore.ts`

**Step 1: Add mode, simConfig, backend fields**

Add to the `RobotStore` interface and initial state:

```typescript
import type { RobotBackend, RobotMode, SimConfig } from '../backend/types'

// Add to interface:
mode: RobotMode
setMode: (mode: RobotMode) => void
simConfig: SimConfig | null
setSimConfig: (config: SimConfig | null) => void
backend: RobotBackend | null
setBackend: (backend: RobotBackend | null) => void

// Add to create() initial state:
mode: 'real',
setMode: (mode) => set({ mode }),
simConfig: null,
setSimConfig: (config) => set({ simConfig: config }),
backend: null,
setBackend: (backend) => set({ backend }),
```

**Step 2: Verify types**

Run: `cd play_on_web/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add play_on_web/frontend/src/stores/robotStore.ts
git commit -m "feat: extend store with mode, simConfig, and backend fields"
```

---

### Task 10: Create SimulationView Component

**Files:**
- Create: `play_on_web/frontend/src/components/SimulationView.tsx`
- Create: `play_on_web/frontend/src/components/SimulationView.css`

**Step 1: Implement SimulationView**

```tsx
// play_on_web/frontend/src/components/SimulationView.tsx

import { useEffect, useRef } from 'react'
import { useRobotStore } from '../stores/robotStore'
import { SimRobotBackend } from '../backend/SimRobotBackend'
import './SimulationView.css'

function SimulationView() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { backend } = useRobotStore()

  useEffect(() => {
    if (!containerRef.current || !backend) return

    // If backend is SimRobotBackend, attach the container for rendering
    if (backend instanceof SimRobotBackend) {
      backend.setContainer(containerRef.current)
    }

    const handleResize = () => {
      if (!containerRef.current) return
      // Renderer handles its own resize via ResizeObserver or manual call
    }

    const observer = new ResizeObserver(handleResize)
    observer.observe(containerRef.current)

    return () => {
      observer.disconnect()
    }
  }, [backend])

  return (
    <div className="simulation-view" ref={containerRef}>
      <div className="sim-overlay">
        <span className="sim-badge">Simulation Mode</span>
      </div>
    </div>
  )
}

export default SimulationView
```

**Step 2: Add basic CSS**

```css
/* play_on_web/frontend/src/components/SimulationView.css */

.simulation-view {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
}

.simulation-view canvas {
  width: 100% !important;
  height: 100% !important;
}

.sim-overlay {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  pointer-events: none;
}

.sim-badge {
  background: rgba(0, 150, 255, 0.8);
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}
```

**Step 3: Commit**

```bash
git add play_on_web/frontend/src/components/SimulationView.tsx play_on_web/frontend/src/components/SimulationView.css
git commit -m "feat: add SimulationView component for 3D rendering"
```

---

### Task 11: Create SimSetup Page

**Files:**
- Create: `play_on_web/frontend/src/components/SimSetup.tsx`
- Create: `play_on_web/frontend/src/components/SimSetup.css`

**Step 1: Implement SimSetup**

A simple page to select robot and environment before entering teleoperation.

```tsx
// play_on_web/frontend/src/components/SimSetup.tsx

import { useState } from 'react'
import { useRobotStore } from '../stores/robotStore'
import { SimRobotBackend } from '../backend/SimRobotBackend'
import './SimSetup.css'

const ROBOTS = [
  { id: 'xlerobot', name: 'XLeRobot', description: 'Dual-arm mobile robot' },
  { id: 'SO101', name: 'SO101', description: 'Single arm manipulator' },
  { id: 'panda', name: 'Panda', description: 'Franka Emika 7-DOF arm' },
]

const ENVIRONMENTS = [
  { id: 'tabletop', name: 'Tabletop', description: 'Table with 3DGS scene' },
  { id: 'basic', name: 'Basic', description: 'Floor and lighting only' },
]

interface SimSetupProps {
  onComplete: () => void
  onBack: () => void
}

function SimSetup({ onComplete, onBack }: SimSetupProps) {
  const { setSimConfig, setBackend, setIsConnected, setObservation } = useRobotStore()
  const [robot, setRobot] = useState('xlerobot')
  const [environment, setEnvironment] = useState('basic')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    setLoading(true)
    setError(null)

    try {
      const config = { robot, environment }
      setSimConfig(config)

      const backend = new SimRobotBackend((obs) => setObservation(obs))
      // Note: container will be set by SimulationView after mount
      await backend.connect(config)

      setBackend(backend)
      setIsConnected(true)
      onComplete()
    } catch (err: any) {
      setError(err.message || 'Failed to load simulation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="sim-setup">
      <h2>Simulation Setup</h2>

      <div className="sim-setup-section">
        <h3>Select Robot</h3>
        <div className="sim-setup-options">
          {ROBOTS.map((r) => (
            <button
              key={r.id}
              className={`sim-option ${robot === r.id ? 'active' : ''}`}
              onClick={() => setRobot(r.id)}
            >
              <strong>{r.name}</strong>
              <span>{r.description}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="sim-setup-section">
        <h3>Select Environment</h3>
        <div className="sim-setup-options">
          {ENVIRONMENTS.map((e) => (
            <button
              key={e.id}
              className={`sim-option ${environment === e.id ? 'active' : ''}`}
              onClick={() => setEnvironment(e.id)}
            >
              <strong>{e.name}</strong>
              <span>{e.description}</span>
            </button>
          ))}
        </div>
      </div>

      {error && <div className="sim-error">{error}</div>}

      <div className="sim-setup-actions">
        <button onClick={onBack} className="btn btn-secondary">Back</button>
        <button onClick={handleStart} className="btn btn-primary" disabled={loading}>
          {loading ? 'Loading...' : 'Start Simulation'}
        </button>
      </div>
    </div>
  )
}

export default SimSetup
```

**Step 2: Add CSS (basic styling matching existing app style)**

Create `SimSetup.css` with card-based option layout and action buttons.

**Step 3: Commit**

```bash
git add play_on_web/frontend/src/components/SimSetup.tsx play_on_web/frontend/src/components/SimSetup.css
git commit -m "feat: add SimSetup page for robot and environment selection"
```

---

### Task 12: Modify App.tsx — Add Mode Selection

**Files:**
- Modify: `play_on_web/frontend/src/App.tsx`

**Step 1: Add mode selection and sim flow**

Update the `Page` type and routing to support mode selection and sim setup:

```typescript
type Page = 'mode-select' | 'setup' | 'sim-setup' | 'teleop' | 'keymap-settings'
```

Add a `ModeSelect` inline component or a simple mode selection at the start:

- Start at `mode-select` page
- "Real Robot" → sets mode to 'real', navigates to `setup`
- "Simulation" → sets mode to 'sim', navigates to `sim-setup`
- SimSetup `onComplete` → navigates to `teleop`
- DeviceSetup `onComplete` → navigates to `teleop`

**Step 2: Import SimSetup and pass mode to TeleopControl**

```typescript
import SimSetup from './components/SimSetup'
```

Add `sim-setup` case to `renderPage()`:
```typescript
case 'sim-setup':
  return <SimSetup onComplete={() => setCurrentPage('teleop')} onBack={() => setCurrentPage('mode-select')} />
```

Add `mode-select` case with two buttons.

**Step 3: Verify in browser**

Run: `cd play_on_web/frontend && npm run dev`
Navigate to localhost:3000 — should see mode selection screen.

**Step 4: Commit**

```bash
git add play_on_web/frontend/src/App.tsx
git commit -m "feat: add mode selection (real/sim) to App routing"
```

---

### Task 13: Modify TeleopControl — Conditional Rendering

**Files:**
- Modify: `play_on_web/frontend/src/components/TeleopControl.tsx`

**Step 1: Conditionally render CameraView vs SimulationView**

Import SimulationView and useRobotStore's `mode`:

```typescript
import SimulationView from './SimulationView'

// Inside component:
const { mode, backend } = useRobotStore()
```

Replace the camera grid section:
```tsx
<div className="camera-grid">
  {mode === 'sim' ? <SimulationView /> : <CameraView />}
</div>
```

**Step 2: Conditionally create WebSocket only in real mode**

Move the WebSocket creation inside an `if (mode === 'real')` check. In sim mode, the backend is already connected from SimSetup.

**Step 3: Wire disconnect to backend**

```typescript
const handleDisconnect = async () => {
  if (backend) {
    await backend.disconnect()
  }
  setIsConnected(false)
  onBack()
}
```

**Step 4: Verify in browser**

Navigate through: Mode Select → Simulation → SimSetup → TeleopControl. Should see SimulationView instead of CameraView.

**Step 5: Commit**

```bash
git add play_on_web/frontend/src/components/TeleopControl.tsx
git commit -m "feat: conditionally render SimulationView vs CameraView based on mode"
```

---

### Task 14: Modify KeyboardControl — Route Through Backend

**Files:**
- Modify: `play_on_web/frontend/src/components/KeyboardControl.tsx`

**Step 1: Use RobotBackend for key events**

In sim mode, keyboard events should go through `backend.onKeyDown(code)` instead of WebSocket. In real mode, they should also go through `backend.onKeyDown(code)` — the RealRobotBackend handles the translation.

Replace the current `handleKeyDown`/`handleKeyUp` to use backend:

```typescript
const { backend, mode } = useRobotStore()

const handleKeyDown = (e: KeyboardEvent) => {
  if (backend) {
    backend.onKeyDown(e.code)
  }
  // Still track pressed keys for visual display
  setPressedKeys((prev) => new Set(prev).add(e.key.toUpperCase()))
  e.preventDefault()
}

const handleKeyUp = (e: KeyboardEvent) => {
  if (backend) {
    backend.onKeyUp(e.code)
  }
  setPressedKeys((prev) => {
    const newSet = new Set(prev)
    newSet.delete(e.key.toUpperCase())
    return newSet
  })
}
```

Note: In sim mode, the visual keymap display should show MuJoCo-GS-Web's key mappings rather than the backend keymap. For v1, we can show a static keymap reference for the sim controller.

**Step 2: Verify keyboard works in both modes**

Test: Open sim mode, press keys — verify console logs or visual feedback that keys are being received.

**Step 3: Commit**

```bash
git add play_on_web/frontend/src/components/KeyboardControl.tsx
git commit -m "feat: route keyboard events through RobotBackend"
```

---

### Task 15: Modify XboxControl — Route Through Backend

**Files:**
- Modify: `play_on_web/frontend/src/components/XboxControl.tsx`

**Step 1: Use RobotBackend for gamepad input**

Replace direct WebSocket calls with `backend.onGamepadInput()`:

```typescript
const { backend } = useRobotStore()

const handleGamepadInput = (gamepad: Gamepad) => {
  if (!backend) return
  backend.onGamepadInput({
    axes: Array.from(gamepad.axes),
    buttons: gamepad.buttons.map(b => b.pressed),
  })
}
```

**Step 2: Commit**

```bash
git add play_on_web/frontend/src/components/XboxControl.tsx
git commit -m "feat: route gamepad input through RobotBackend"
```

---

### Task 16: End-to-End Integration Test

Manual verification that the full simulation flow works.

**Step 1: Start dev server**

```bash
cd play_on_web/frontend && npm run dev
```

**Step 2: Test simulation flow**

1. Open http://localhost:3000
2. Click "Simulation" on mode selection
3. Select XLeRobot + Basic environment
4. Click "Start Simulation"
5. Verify Three.js canvas appears
6. Press keyboard keys (W, S, A, D, etc.) — verify robot moves
7. RobotStatus panel shows joint angles updating
8. OrbitControls: drag to rotate camera

**Step 3: Test real robot flow still works**

1. Go back to mode selection
2. Click "Real Robot"
3. Verify existing DeviceSetup → TeleopControl flow is unchanged

**Step 4: Fix any issues found during testing**

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete simulation integration v1"
```

---

## Task Dependency Graph

```
Task 1 (deps) ─→ Task 2 (assets) ─→ Task 6 (SimEngine) ─→ Task 8 (SimRobotBackend)
                                                               ↑
Task 3 (types) ─→ Task 4 (RealBackend) ──────────────────────┤
                                                               ↑
Task 5 (controllers) ─────────────────→ Task 7 (SimRenderer) ─┘
                                                               ↓
Task 9 (store) ─→ Task 10 (SimView) ─→ Task 12 (App.tsx) ─→ Task 13 (TeleopControl)
                  Task 11 (SimSetup) ─┘                      Task 14 (KeyboardControl)
                                                              Task 15 (XboxControl)
                                                                    ↓
                                                              Task 16 (E2E test)
```

Tasks 1-5 can be partially parallelized. Tasks 6-8 depend on the foundation. Tasks 9-15 wire everything together. Task 16 validates the integration.
