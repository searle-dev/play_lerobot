/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * XLeRobot Controller - Dual-arm robot controller with inverse kinematics.
 *
 * Actuator index mapping:
 * 0  forward       | 1  turn
 * 2  Rotation_L    | 3  Pitch_L (IK) | 4  Elbow_L (IK)
 * 5  Wrist_Pitch_L | 6  Wrist_Roll_L  | 7  Jaw_L
 * 8  Rotation_R    | 9  Pitch_R (IK) | 10 Elbow_R (IK)
 * 11 Wrist_Pitch_R | 12 Wrist_Roll_R  | 13 Jaw_R
 * 14 head_pan      | 15 head_tilt
 */

import { BaseController, type KeyStates } from './BaseController'
import { inverseKinematics2Link } from '../utils/inverseKinematics'

interface ControllerState {
  targetJoints: Float64Array
  eePos1: [number, number]
  eePos2: [number, number]
  pitch1: number
  pitch2: number
  gripperCooldown: [number, number]
  gripperOpen: [boolean, boolean]
  prevKeyboardActive: [boolean, boolean]
}

export class XLeRobotController extends BaseController {
  private readonly JOINT_STEP = 0.002
  private readonly EE_STEP = 0.0002
  private readonly PITCH_STEP = 0.0025
  private readonly TIP_LENGTH = 0.108
  private readonly BASE_SPEED = 1
  private readonly GRIPPER_OPEN = 1.5
  private readonly GRIPPER_CLOSED = -0.25
  private readonly GRIPPER_COOLDOWN_FRAMES = 60
  private readonly INITIAL_EE_POS: [number, number] = [0.162, 0.118]

  private state: ControllerState | null = null

  private _initState(): void {
    const [j2, j3] = inverseKinematics2Link(this.INITIAL_EE_POS[0], this.INITIAL_EE_POS[1])

    this.state = {
      targetJoints: new Float64Array(16),
      eePos1: [...this.INITIAL_EE_POS],
      eePos2: [...this.INITIAL_EE_POS],
      pitch1: 0.0,
      pitch2: 0.0,
      gripperCooldown: [0, 0],
      gripperOpen: [false, false],
      prevKeyboardActive: [false, false],
    }

    // Left arm initial positions
    this.state.targetJoints[2] = 1.5708
    this.state.targetJoints[3] = j2
    this.state.targetJoints[4] = j3
    this.state.targetJoints[5] = j2 - j3
    this.state.targetJoints[6] = 1.57

    // Right arm initial positions
    this.state.targetJoints[8] = -1.5708
    this.state.targetJoints[9] = j2
    this.state.targetJoints[10] = j3
    this.state.targetJoints[11] = j2 - j3
    this.state.targetJoints[12] = 1.57

    // Grippers closed
    this.state.targetJoints[7] = this.GRIPPER_CLOSED
    this.state.targetJoints[13] = this.GRIPPER_CLOSED
  }

  async initialize(_model: any, data: any, _mujoco: any): Promise<void> {
    this._initState()
    for (let i = 2; i < 16; i++) {
      data.ctrl[i] = this.state!.targetJoints[i]
    }
    this.initialized = true
  }

  reset(_model: any, data: any): void {
    this._initState()
    data.ctrl[0] = 0
    data.ctrl[1] = 0
    for (let i = 2; i < 16; i++) {
      data.ctrl[i] = this.state!.targetJoints[i]
    }
  }

  private _isKeyControlling(actuatorIdx: number, keyStates: KeyStates): boolean {
    switch (actuatorIdx) {
      case 0: return keyStates['KeyS'] || keyStates['KeyW']
      case 1: return keyStates['KeyA'] || keyStates['KeyD']
      case 2: return keyStates['Digit7'] || keyStates['KeyY']
      case 3: case 4: case 5:
        return keyStates['Digit8'] || keyStates['KeyU'] ||
               keyStates['Digit9'] || keyStates['KeyI'] ||
               keyStates['Digit0'] || keyStates['KeyO']
      case 6: return keyStates['Minus'] || keyStates['KeyP']
      case 7: return keyStates['KeyV']
      case 8: return keyStates['KeyH'] || keyStates['KeyN']
      case 9: case 10: case 11:
        return keyStates['KeyJ'] || keyStates['KeyM'] ||
               keyStates['KeyK'] || keyStates['Comma'] ||
               keyStates['KeyL'] || keyStates['Period']
      case 12: return keyStates['Semicolon'] || keyStates['Slash']
      case 13: return keyStates['KeyB']
      case 14: return keyStates['KeyR'] || keyStates['KeyT']
      case 15: return keyStates['KeyF'] || keyStates['KeyG']
      default: return false
    }
  }

  async step(keyStates: KeyStates, model: any, data: any, _mujoco: any): Promise<void> {
    if (!this.initialized || !this.state) {
      await this.initialize(model, data, _mujoco)
    }
    const s = this.state!

    // Sync external control inputs for non-active controls
    for (let i = 2; i < 16; i++) {
      if (!this._isKeyControlling(i, keyStates)) {
        s.targetJoints[i] = data.ctrl[i]
      }
    }

    // Decrement gripper cooldowns
    if (s.gripperCooldown[0] > 0) s.gripperCooldown[0]--
    if (s.gripperCooldown[1] > 0) s.gripperCooldown[1]--

    // === Base Control ===
    if (keyStates['KeyS']) {
      data.ctrl[0] = this.BASE_SPEED
      s.prevKeyboardActive[0] = true
    } else if (keyStates['KeyW']) {
      data.ctrl[0] = -this.BASE_SPEED
      s.prevKeyboardActive[0] = true
    } else {
      if (s.prevKeyboardActive[0]) data.ctrl[0] = 0
      s.prevKeyboardActive[0] = false
    }

    if (keyStates['KeyA']) {
      data.ctrl[1] = this.BASE_SPEED
      s.prevKeyboardActive[1] = true
    } else if (keyStates['KeyD']) {
      data.ctrl[1] = -this.BASE_SPEED
      s.prevKeyboardActive[1] = true
    } else {
      if (s.prevKeyboardActive[1]) data.ctrl[1] = 0
      s.prevKeyboardActive[1] = false
    }

    // === Left Arm Control (indices 2-7) ===
    if (keyStates['Digit7']) s.targetJoints[2] += this.JOINT_STEP
    if (keyStates['KeyY']) s.targetJoints[2] -= this.JOINT_STEP

    if (keyStates['Digit8']) s.eePos1[1] += this.EE_STEP
    if (keyStates['KeyU']) s.eePos1[1] -= this.EE_STEP

    if (keyStates['Digit9']) s.eePos1[0] += this.EE_STEP
    if (keyStates['KeyI']) s.eePos1[0] -= this.EE_STEP

    if (keyStates['Digit0']) s.pitch1 += this.PITCH_STEP
    if (keyStates['KeyO']) s.pitch1 -= this.PITCH_STEP

    if (keyStates['Minus']) s.targetJoints[6] += this.JOINT_STEP * 3
    if (keyStates['KeyP']) s.targetJoints[6] -= this.JOINT_STEP * 3

    // IK for left arm
    const compensatedY1 = s.eePos1[1] + this.TIP_LENGTH * Math.sin(s.pitch1)
    const [j2_1, j3_1] = inverseKinematics2Link(s.eePos1[0], compensatedY1)
    s.targetJoints[3] = j2_1
    s.targetJoints[4] = j3_1
    s.targetJoints[5] = j2_1 - j3_1 + s.pitch1

    // === Right Arm Control (indices 8-13) ===
    if (keyStates['KeyH']) s.targetJoints[8] += this.JOINT_STEP
    if (keyStates['KeyN']) s.targetJoints[8] -= this.JOINT_STEP

    if (keyStates['KeyJ']) s.eePos2[1] += this.EE_STEP
    if (keyStates['KeyM']) s.eePos2[1] -= this.EE_STEP

    if (keyStates['KeyK']) s.eePos2[0] += this.EE_STEP
    if (keyStates['Comma']) s.eePos2[0] -= this.EE_STEP

    if (keyStates['KeyL']) s.pitch2 += this.PITCH_STEP
    if (keyStates['Period']) s.pitch2 -= this.PITCH_STEP

    if (keyStates['Semicolon']) s.targetJoints[12] += this.JOINT_STEP * 3
    if (keyStates['Slash']) s.targetJoints[12] -= this.JOINT_STEP * 3

    // IK for right arm
    const compensatedY2 = s.eePos2[1] + this.TIP_LENGTH * Math.sin(s.pitch2)
    const [j2_2, j3_2] = inverseKinematics2Link(s.eePos2[0], compensatedY2)
    s.targetJoints[9] = j2_2
    s.targetJoints[10] = j3_2
    s.targetJoints[11] = j2_2 - j3_2 + s.pitch2

    // === Gripper Control ===
    if (keyStates['KeyV'] && s.gripperCooldown[0] === 0) {
      s.gripperOpen[0] = !s.gripperOpen[0]
      s.targetJoints[7] = s.gripperOpen[0] ? this.GRIPPER_OPEN : this.GRIPPER_CLOSED
      s.gripperCooldown[0] = this.GRIPPER_COOLDOWN_FRAMES
    }
    if (keyStates['KeyB'] && s.gripperCooldown[1] === 0) {
      s.gripperOpen[1] = !s.gripperOpen[1]
      s.targetJoints[13] = s.gripperOpen[1] ? this.GRIPPER_OPEN : this.GRIPPER_CLOSED
      s.gripperCooldown[1] = this.GRIPPER_COOLDOWN_FRAMES
    }

    // === Head Control (indices 14-15) ===
    if (keyStates['KeyR']) s.targetJoints[14] += this.JOINT_STEP * 2
    if (keyStates['KeyT']) s.targetJoints[14] -= this.JOINT_STEP * 2
    if (keyStates['KeyF']) s.targetJoints[15] += this.JOINT_STEP * 2
    if (keyStates['KeyG']) s.targetJoints[15] -= this.JOINT_STEP * 2

    // === Reset ===
    if (keyStates['KeyX']) {
      this.reset(model, data)
      return
    }

    // Apply target positions to actuators
    for (let i = 2; i < 16; i++) {
      data.ctrl[i] = s.targetJoints[i]
    }
  }

  getControlKeys(): string[] {
    return [
      'KeyW', 'KeyS', 'KeyA', 'KeyD',
      'Digit7', 'KeyY', 'Digit8', 'KeyU', 'Digit9', 'KeyI',
      'Digit0', 'KeyO', 'Minus', 'KeyP',
      'KeyH', 'KeyN', 'KeyJ', 'KeyM', 'KeyK', 'Comma',
      'KeyL', 'Period', 'Semicolon', 'Slash',
      'KeyV', 'KeyB',
      'KeyR', 'KeyT', 'KeyF', 'KeyG',
      'KeyX'
    ]
  }

  getDescription(): string {
    return [
      'Base: W/S Forward | A/D Turn',
      'Arm1: 7/Y Rotate | 8/U Y | 9/I X | 0/O Pitch | -/P Roll',
      'Arm2: H/N Rotate | J/M Y | K/, X | L/. Pitch | ;/? Roll',
      'Gripper: V/B Toggle | Head: R/T Pan, F/G Tilt | X Reset'
    ].join('\n')
  }
}
