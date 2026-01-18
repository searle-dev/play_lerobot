import { create } from 'zustand'
import { KeymapConfig } from '../types/keymap'

export interface Port {
  name: string
  selected: boolean
}

export interface Camera {
  id: string
  name: string
  type: string
  width: number
  height: number
  fps: number
}

export interface RobotConfig {
  port1: string
  port2: string
  cameras: Map<string, Camera>
}

export interface RobotObservation {
  [key: string]: number
}

interface RobotStore {
  // 连接状态
  isConnected: boolean
  setIsConnected: (connected: boolean) => void

  // 设备配置
  availablePorts: string[]
  setAvailablePorts: (ports: string[]) => void

  availableCameras: Camera[]
  setAvailableCameras: (cameras: Camera[]) => void

  robotConfig: RobotConfig
  setRobotConfig: (config: RobotConfig) => void

  // 机器人状态
  observation: RobotObservation | null
  setObservation: (obs: RobotObservation) => void

  // WebSocket
  teleopWs: WebSocket | null
  cameraWs: WebSocket | null
  setTeleopWs: (ws: WebSocket | null) => void
  setCameraWs: (ws: WebSocket | null) => void

  // 控制模式
  controlMode: 'keyboard' | 'xbox'
  setControlMode: (mode: 'keyboard' | 'xbox') => void

  // 键位配置
  keymapConfig: KeymapConfig | null
  setKeymapConfig: (config: KeymapConfig) => void

  currentProfile: string
  setCurrentProfile: (profile: string) => void
}

export const useRobotStore = create<RobotStore>((set) => ({
  // 连接状态
  isConnected: false,
  setIsConnected: (connected) => set({ isConnected: connected }),

  // 设备配置
  availablePorts: [],
  setAvailablePorts: (ports) => set({ availablePorts: ports }),

  availableCameras: [],
  setAvailableCameras: (cameras) => set({ availableCameras: cameras }),

  robotConfig: {
    port1: '',
    port2: '',
    cameras: new Map(),
  },
  setRobotConfig: (config) => set({ robotConfig: config }),

  // 机器人状态
  observation: null,
  setObservation: (obs) => set({ observation: obs }),

  // WebSocket
  teleopWs: null,
  cameraWs: null,
  setTeleopWs: (ws) => set({ teleopWs: ws }),
  setCameraWs: (ws) => set({ cameraWs: ws }),

  // 控制模式
  controlMode: 'keyboard',
  setControlMode: (mode) => set({ controlMode: mode }),

  // 键位配置
  keymapConfig: null,
  setKeymapConfig: (config) => set({ keymapConfig: config }),

  currentProfile: 'default',
  setCurrentProfile: (profile) => set({ currentProfile: profile }),
}))

