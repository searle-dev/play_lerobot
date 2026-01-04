import { useEffect, useState } from 'react'
import './CameraView.css'
import { useRobotStore } from '../stores/robotStore'
import { createCameraWebSocket } from '../api/client'

interface CameraFrame {
  [cameraName: string]: string // base64 编码的图像
}

function CameraView() {
  const { robotConfig, setCameraWs } = useRobotStore()
  const [frames, setFrames] = useState<CameraFrame>({})
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null)
  
  const cameraNames = Array.from(robotConfig.cameras.keys())
  
  useEffect(() => {
    if (cameraNames.length === 0) return
    
    // 创建相机 WebSocket
    const ws = createCameraWebSocket(
      cameraNames,
      (data) => {
        if (data.type === 'camera_frames') {
          setFrames(data.data)
        }
      },
      (error) => {
        console.error('Camera WebSocket error:', error)
      },
      () => {
        setCameraWs(null)
      }
    )
    
    setCameraWs(ws)
    
    // 默认选择第一个相机
    if (cameraNames.length > 0 && !selectedCamera) {
      setSelectedCamera(cameraNames[0])
    }
    
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [cameraNames.length])
  
  if (cameraNames.length === 0) {
    return (
      <div className="camera-view empty">
        <div className="empty-state">
          <span className="empty-icon">📹</span>
          <h3>未配置相机</h3>
          <p>请在设备配置中添加相机</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="camera-view">
      {/* 相机标签 */}
      {cameraNames.length > 1 && (
        <div className="camera-tabs">
          {cameraNames.map((name) => (
            <button
              key={name}
              className={`camera-tab ${selectedCamera === name ? 'active' : ''}`}
              onClick={() => setSelectedCamera(name)}
            >
              📹 {name}
            </button>
          ))}
          <button
            className={`camera-tab ${selectedCamera === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCamera('all')}
          >
            📊 全部
          </button>
        </div>
      )}
      
      {/* 相机画面 */}
      <div className={`camera-container ${selectedCamera === 'all' ? 'grid-view' : 'single-view'}`}>
        {selectedCamera === 'all' ? (
          // 网格视图
          cameraNames.map((name) => (
            <div key={name} className="camera-frame">
              <div className="frame-header">
                <span className="frame-title">{name}</span>
                <span className="frame-status">
                  <span className={`status-dot ${frames[name] ? 'active' : ''}`} />
                  {frames[name] ? '在线' : '离线'}
                </span>
              </div>
              <div className="frame-content">
                {frames[name] ? (
                  <img
                    src={`data:image/jpeg;base64,${frames[name]}`}
                    alt={name}
                    className="camera-image"
                  />
                ) : (
                  <div className="frame-placeholder">
                    <span className="placeholder-icon">📹</span>
                    <span>等待视频流...</span>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          // 单个视图
          selectedCamera && (
            <div className="camera-frame single">
              <div className="frame-header">
                <span className="frame-title">{selectedCamera}</span>
                <span className="frame-status">
                  <span className={`status-dot ${frames[selectedCamera] ? 'active' : ''}`} />
                  {frames[selectedCamera] ? '在线' : '离线'}
                </span>
              </div>
              <div className="frame-content">
                {frames[selectedCamera] ? (
                  <img
                    src={`data:image/jpeg;base64,${frames[selectedCamera]}`}
                    alt={selectedCamera}
                    className="camera-image"
                  />
                ) : (
                  <div className="frame-placeholder">
                    <span className="placeholder-icon">📹</span>
                    <span>等待视频流...</span>
                  </div>
                )}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  )
}

export default CameraView

