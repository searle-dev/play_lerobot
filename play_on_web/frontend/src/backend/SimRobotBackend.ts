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

  /** Attach a DOM container for rendering. Can be called before or after connect(). */
  setContainer(container: HTMLElement): void {
    this.container = container

    // If engine already loaded but renderer not yet created, create it now
    if (this.engine.initialized && !this.renderer) {
      this.renderer = new SimRenderer(container)
      this.renderer.buildScene(
        this.engine.getModel(),
        this.engine.getData(),
        this.engine.getMuJoCo()
      )
    }
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

  /** Get the SimRenderer instance (for external resize handling) */
  getRenderer(): SimRenderer | null {
    return this.renderer
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
