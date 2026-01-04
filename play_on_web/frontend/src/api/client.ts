import axios from 'axios'

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 设备扫描 API
export const deviceApi = {
  getPorts: () => apiClient.get('/devices/ports'),
  startPortDetection: () => apiClient.get('/devices/ports/detect/start'),
  completePortDetection: (portsBefore: string[]) => 
    apiClient.post('/devices/ports/detect/complete', { ports_before: portsBefore }),
  getCameras: () => apiClient.get('/devices/cameras'),
}

// 机器人控制 API
export const robotApi = {
  connect: (port1: string, port2: string) =>
    apiClient.post('/robot/connect', { port1, port2 }),
  disconnect: () => apiClient.post('/robot/disconnect'),
  moveToZero: (arm: string = 'both') =>
    apiClient.post('/robot/zero', { arm }),
  recordResetPosition: (arm: string = 'both') =>
    apiClient.post('/robot/record_reset_position', { arm }),
  moveToResetPosition: (arm: string = 'both') =>
    apiClient.post('/robot/move_to_reset', { arm }),
  getResetPositions: () => apiClient.get('/robot/reset_positions'),
  setStepLevel: (arm: string = 'both', level: string = 'normal') =>
    apiClient.post('/robot/set_step_level', { arm, level }),
  stopBase: () => apiClient.post('/robot/stop_base'),
  getObservation: () => apiClient.get('/robot/observation'),
}

// 相机管理 API
export const cameraApi = {
  addCamera: (data: {
    name: string
    camera_id: string
    camera_type: string
    width?: number
    height?: number
    fps?: number
  }) => apiClient.post('/cameras/add', data),
  removeCamera: (name: string) =>
    apiClient.delete(`/cameras/${name}`),
  getFrame: (name: string) =>
    apiClient.get(`/cameras/${name}/frame`, { responseType: 'blob' }),
}

// WebSocket 连接
export const createTeleopWebSocket = (
  onMessage: (data: any) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): WebSocket => {
  const wsUrl = `ws://${window.location.hostname}:8000/ws/teleop`
  const ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('Teleop WebSocket connected')
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }
  
  ws.onerror = (error) => {
    console.error('Teleop WebSocket error:', error)
    onError?.(error)
  }
  
  ws.onclose = () => {
    console.log('Teleop WebSocket closed')
    onClose?.()
  }
  
  return ws
}

export const createCameraWebSocket = (
  cameraNames: string[],
  onMessage: (data: any) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): WebSocket => {
  const wsUrl = `ws://${window.location.hostname}:8000/ws/camera`
  const ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('Camera WebSocket connected')
    // 发送相机列表
    ws.send(JSON.stringify({ cameras: cameraNames }))
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }
  
  ws.onerror = (error) => {
    console.error('Camera WebSocket error:', error)
    onError?.(error)
  }
  
  ws.onclose = () => {
    console.log('Camera WebSocket closed')
    onClose?.()
  }
  
  return ws
}

