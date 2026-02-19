import type { RobotObservation } from '../stores/robotStore'

export interface GamepadInput {
  axes: number[]
  buttons: boolean[]
}

export interface RobotBackend {
  connect(config: Record<string, unknown>): Promise<void>
  disconnect(): Promise<void>
  onKeyDown(code: string): void
  onKeyUp(code: string): void
  onGamepadInput(input: GamepadInput): void
  getObservation(): RobotObservation
  reset(): void
  readonly isConnected: boolean
}

export type RobotMode = 'real' | 'sim'

export interface SimConfig {
  robot: string
  environment: string
}
