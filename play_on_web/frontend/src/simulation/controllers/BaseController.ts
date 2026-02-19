export interface KeyStates {
  [code: string]: boolean
}

/* eslint-disable @typescript-eslint/no-explicit-any */
export abstract class BaseController {
  initialized = false

  abstract initialize(model: any, data: any, mujoco: any): Promise<void>
  abstract reset(model: any, data: any): void
  abstract step(keyStates: KeyStates, model: any, data: any, mujoco: any): Promise<void>
  abstract getControlKeys(): string[]
  abstract getDescription(): string
}
