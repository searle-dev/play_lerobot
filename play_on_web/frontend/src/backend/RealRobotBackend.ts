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

  async connect(_config: Record<string, unknown>): Promise<void> {
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
      (_error: Event) => console.error('Teleop WebSocket error'),
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
