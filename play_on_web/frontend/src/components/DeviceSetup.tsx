import { useState, useEffect } from 'react'
import './DeviceSetup.css'
import { deviceApi, robotApi, cameraApi } from '../api/client'
import { useRobotStore, Camera } from '../stores/robotStore'

interface DeviceSetupProps {
  onComplete: () => void
}

type SetupStep = 'port' | 'camera' | 'calibration'

function DeviceSetup({ onComplete }: DeviceSetupProps) {
  const [currentStep, setCurrentStep] = useState<SetupStep>('port')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Port 相关状态
  const [selectedPort1, setSelectedPort1] = useState('')
  const [selectedPort2, setSelectedPort2] = useState('')
  const [detectingPort, setDetectingPort] = useState<'port1' | 'port2' | null>(null)
  const [portsBefore, setPortsBefore] = useState<string[]>([])
  
  // Camera 相关状态
  const [selectedCameras, setSelectedCameras] = useState<Map<string, Camera>>(new Map())
  
  const {
    availablePorts,
    setAvailablePorts,
    availableCameras,
    setAvailableCameras,
    setRobotConfig,
    setIsConnected,
  } = useRobotStore()
  
  // 加载可用串口
  const loadPorts = async () => {
    try {
      setError(null) // 清除之前的错误
      const response = await deviceApi.getPorts()
      setAvailablePorts(response.data.ports)
      console.log(`✅ 已加载 ${response.data.ports.length} 个串口`)
    } catch (err: any) {
      setError('加载串口失败: ' + err.message)
    }
  }
  
  // 加载可用相机
  const loadCameras = async () => {
    try {
      const response = await deviceApi.getCameras()
      setAvailableCameras(response.data.cameras)
    } catch (err: any) {
      setError('加载相机失败: ' + err.message)
    }
  }
  
  useEffect(() => {
    loadPorts()
    loadCameras()
  }, [])
  
  // 开始端口检测
  const startPortDetection = async (portNum: 'port1' | 'port2') => {
    try {
      setDetectingPort(portNum)
      const response = await deviceApi.startPortDetection()
      setPortsBefore(response.data.ports_before)
    } catch (err: any) {
      setError('开始端口检测失败: ' + err.message)
      setDetectingPort(null)
    }
  }
  
  // 完成端口检测
  const completePortDetection = async () => {
    try {
      const response = await deviceApi.completePortDetection(portsBefore)
      if (response.data.status === 'success') {
        const detectedPort = response.data.port
        if (detectingPort === 'port1') {
          setSelectedPort1(detectedPort)
        } else if (detectingPort === 'port2') {
          setSelectedPort2(detectedPort)
        }
        
        // 将检测到的端口添加到可用端口列表中（如果不存在）
        // 因为此时 USB 可能还没重新插回，所以手动添加
        if (!availablePorts.includes(detectedPort)) {
          setAvailablePorts([...availablePorts, detectedPort].sort())
        }
        
        setDetectingPort(null)
        setError(null) // 清除错误信息
        
        // 显示成功提示
        console.log(`✅ 成功识别端口: ${detectedPort}`)
      } else {
        setError(response.data.message)
        setDetectingPort(null)
      }
    } catch (err: any) {
      setError('完成端口检测失败: ' + err.message)
      setDetectingPort(null)
    }
  }
  
  // 连接机器人
  const connectRobot = async () => {
    if (!selectedPort1 || !selectedPort2) {
      setError('请选择两个串口')
      return
    }
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await robotApi.connect(selectedPort1, selectedPort2)
      if (response.data.status === 'success') {
        setIsConnected(true)
        setRobotConfig({
          port1: selectedPort1,
          port2: selectedPort2,
          cameras: selectedCameras,
        })
        setCurrentStep('camera')
      } else {
        setError(response.data.message)
      }
    } catch (err: any) {
      setError('连接机器人失败: ' + err.message)
    } finally {
      setLoading(false)
    }
  }
  
  // 切换相机选择
  const toggleCamera = (camera: Camera, position: string) => {
    setSelectedCameras((prev) => {
      const newMap = new Map(prev)
      if (newMap.has(position)) {
        newMap.delete(position)
      } else {
        newMap.set(position, camera)
      }
      return newMap
    })
  }
  
  // 添加相机
  const addCameras = async () => {
    setLoading(true)
    setError(null)
    
    try {
      for (const [name, camera] of selectedCameras.entries()) {
        await cameraApi.addCamera({
          name,
          camera_id: camera.id,
          camera_type: camera.type,
          width: camera.width,
          height: camera.height,
          fps: camera.fps,
        })
      }
      setCurrentStep('calibration')
    } catch (err: any) {
      setError('添加相机失败: ' + err.message)
    } finally {
      setLoading(false)
    }
  }
  
  
  return (
    <div className="device-setup">
      <div className="setup-card">
        <div className="setup-header">
          <h2 className="setup-title">设备配置</h2>
          <div className="setup-steps">
            <div className={`step ${currentStep === 'port' ? 'active' : currentStep > 'port' ? 'completed' : ''}`}>
              <span className="step-number">1</span>
              <span className="step-label">串口配置</span>
            </div>
            <div className="step-divider" />
            <div className={`step ${currentStep === 'camera' ? 'active' : currentStep > 'camera' ? 'completed' : ''}`}>
              <span className="step-number">2</span>
              <span className="step-label">相机配置</span>
            </div>
            <div className="step-divider" />
            <div className={`step ${currentStep === 'calibration' ? 'active' : ''}`}>
              <span className="step-number">3</span>
              <span className="step-label">校准</span>
            </div>
          </div>
        </div>
        
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="error-close">×</button>
          </div>
        )}
        
        <div className="setup-content">
          {currentStep === 'port' && (
            <div className="port-setup">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0 }}>选择串口 {availablePorts.length > 0 && <span style={{ fontSize: '0.875rem', color: 'var(--gray-600)', fontWeight: 'normal' }}>({availablePorts.length} 个可用)</span>}</h3>
                <button 
                  onClick={loadPorts} 
                  className="btn btn-text"
                  style={{ fontSize: '0.875rem' }}
                  disabled={detectingPort !== null}
                  title="重新扫描串口设备"
                >
                  🔄 刷新列表
                </button>
              </div>
              <p className="setup-description">
                请选择两个串口分别连接 SO101 机械臂和头部相机。您可以手动选择，也可以使用自动检测功能。
              </p>
              
              <div className="port-section">
                <h4>串口 1 (SO101 + 头部相机)</h4>
                {selectedPort1 && (
                  <div style={{ fontSize: '0.875rem', color: 'var(--success)', marginTop: '0.25rem' }}>
                    ✓ 已选择: {selectedPort1}
                  </div>
                )}
                <div className="port-controls">
                  <select
                    value={selectedPort1}
                    onChange={(e) => {
                      const newValue = e.target.value
                      console.log('串口 1 选择变化:', newValue)
                      setSelectedPort1(newValue)
                    }}
                    className="port-select"
                    disabled={detectingPort !== null}
                  >
                    <option value="">请选择串口</option>
                    {availablePorts.map((port) => (
                      <option key={port} value={port}>{port}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => startPortDetection('port1')}
                    className="btn btn-secondary"
                    disabled={detectingPort !== null}
                  >
                    {detectingPort === 'port1' ? '检测中...' : '自动检测'}
                  </button>
                </div>
              </div>
              
              <div className="port-section">
                <h4>串口 2 (与 Lekiwi 相同配置)</h4>
                {selectedPort2 && (
                  <div style={{ fontSize: '0.875rem', color: 'var(--success)', marginTop: '0.25rem' }}>
                    ✓ 已选择: {selectedPort2}
                  </div>
                )}
                <div className="port-controls">
                  <select
                    value={selectedPort2}
                    onChange={(e) => {
                      const newValue = e.target.value
                      console.log('串口 2 选择变化:', newValue)
                      setSelectedPort2(newValue)
                    }}
                    className="port-select"
                    disabled={detectingPort !== null}
                  >
                    <option value="">请选择串口</option>
                    {availablePorts.map((port) => (
                      <option key={port} value={port}>{port}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => startPortDetection('port2')}
                    className="btn btn-secondary"
                    disabled={detectingPort !== null}
                  >
                    {detectingPort === 'port2' ? '检测中...' : '自动检测'}
                  </button>
                </div>
              </div>
              
              {detectingPort && (
                <div className="detection-prompt">
                  <p>👉 请拔出 USB 线缆，然后点击"完成检测"</p>
                  <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: 'var(--gray-600)' }}>
                    💡 提示：检测完成后可以重新插入 USB，或稍后手动选择
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                    <button onClick={completePortDetection} className="btn btn-primary">
                      完成检测
                    </button>
                    <button onClick={() => setDetectingPort(null)} className="btn btn-text">
                      取消
                    </button>
                  </div>
                </div>
              )}
              
              <div className="setup-actions">
                <button
                  onClick={connectRobot}
                  className="btn btn-primary btn-large"
                  disabled={!selectedPort1 || !selectedPort2 || loading}
                >
                  {loading ? '连接中...' : '连接机器人'}
                </button>
              </div>
            </div>
          )}
          
          {currentStep === 'camera' && (
            <div className="camera-setup">
              <h3>选择相机</h3>
              <p className="setup-description">
                选择要使用的相机并分配位置。支持多机位同时查看。
              </p>
              
              <div className="camera-positions">
                {['left_wrist', 'right_wrist', 'head'].map((position) => (
                  <div key={position} className="camera-position">
                    <h4>{position === 'left_wrist' ? '左手腕' : position === 'right_wrist' ? '右手腕' : '头部'}</h4>
                    <select
                      value={selectedCameras.get(position)?.id || ''}
                      onChange={(e) => {
                        const camera = availableCameras.find((c) => c.id === e.target.value)
                        if (camera) {
                          toggleCamera(camera, position)
                        } else {
                          setSelectedCameras((prev) => {
                            const newMap = new Map(prev)
                            newMap.delete(position)
                            return newMap
                          })
                        }
                      }}
                      className="camera-select"
                    >
                      <option value="">不使用</option>
                      {availableCameras.map((camera) => (
                        <option key={camera.id} value={camera.id}>
                          {camera.name} ({camera.type})
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
              
              <div className="setup-actions">
                <button onClick={() => setCurrentStep('port')} className="btn btn-text">
                  上一步
                </button>
                <button
                  onClick={() => {
                    // 如果没有选择相机，直接跳到下一步
                    if (selectedCameras.size === 0) {
                      setCurrentStep('calibration')
                    } else {
                      addCameras()
                    }
                  }}
                  className="btn btn-primary btn-large"
                  disabled={loading}
                >
                  {loading ? '添加中...' : selectedCameras.size === 0 ? '跳过（不使用相机）' : '继续'}
                </button>
              </div>
            </div>
          )}
          
          {currentStep === 'calibration' && (
            <div className="calibration-setup">
              <h3>校准与初始化</h3>
              <p className="setup-description">
                设置机械臂的复位位置。这是一个安全位置，用于开机复位或断电前的归位，可以防止机械臂断电时前臂掉落。
              </p>
              
              <div style={{ 
                background: 'var(--warning-bg, #fff3cd)', 
                border: '1px solid var(--warning, #ffc107)',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '1.5rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'start', gap: '0.75rem' }}>
                  <span style={{ fontSize: '1.25rem' }}>💡</span>
                  <div style={{ flex: 1 }}>
                    <strong style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--warning-dark, #856404)' }}>
                      安全提示
                    </strong>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--warning-dark, #856404)', lineHeight: '1.5' }}>
                      建议将机械臂移动到一个稳定的姿态（例如：肩关节和肘关节略微向上弯曲），这样即使断电，前臂也不会因重力而快速掉落。
                      记录当前位置后，系统将在每次启动时自动使用该位置作为复位位置。
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="calibration-info">
                <h4 style={{ marginBottom: '1rem', fontSize: '0.9375rem', fontWeight: 600 }}>复位位置设置</h4>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                  <button
                    onClick={async () => {
                      try {
                        setLoading(true)
                        setError(null)
                        const response = await robotApi.moveToZero('both')
                        if (response.data.status === 'error') {
                          setError(response.data.message)
                        }
                      } catch (err: any) {
                        setError('移动到零位失败: ' + err.message)
                      } finally {
                        setLoading(false)
                      }
                    }}
                    className="btn btn-secondary"
                    disabled={loading}
                    title="先移动到零位，然后手动调整到安全位置"
                  >
                    📍 移动到零位
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        setLoading(true)
                        setError(null)
                        const response = await robotApi.recordResetPosition('both')
                        if (response.data.status === 'success') {
                          alert('✅ ' + response.data.message)
                        } else {
                          setError(response.data.message)
                        }
                      } catch (err: any) {
                        setError('记录复位位置失败: ' + err.message)
                      } finally {
                        setLoading(false)
                      }
                    }}
                    className="btn btn-primary"
                    disabled={loading}
                    title="记录当前机械臂位置作为复位位置"
                  >
                    💾 记录当前位置为复位位置
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        setLoading(true)
                        setError(null)
                        const response = await robotApi.moveToResetPosition('both')
                        if (response.data.status === 'error') {
                          setError(response.data.message)
                        }
                      } catch (err: any) {
                        setError('移动到复位位置失败: ' + err.message)
                      } finally {
                        setLoading(false)
                      }
                    }}
                    className="btn btn-secondary"
                    disabled={loading}
                    title="测试复位位置"
                  >
                    🔄 测试复位位置
                  </button>
                </div>
                <div style={{ 
                  fontSize: '0.8125rem', 
                  color: 'var(--gray-600)', 
                  padding: '0.75rem', 
                  background: 'var(--gray-50, #f8f9fa)',
                  borderRadius: '6px',
                  marginBottom: '1rem'
                }}>
                  <strong>操作步骤：</strong>
                  <ol style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem' }}>
                    <li>点击"移动到零位"让机械臂归零</li>
                    <li>使用键盘或手柄手动调整机械臂到一个安全的姿态</li>
                    <li>点击"记录当前位置为复位位置"保存该位置</li>
                    <li>点击"测试复位位置"验证是否正确</li>
                  </ol>
                </div>
              </div>
              
              <div className="setup-actions">
                <button onClick={() => setCurrentStep('camera')} className="btn btn-text">
                  上一步
                </button>
                <button
                  onClick={onComplete}
                  className="btn btn-primary btn-large"
                  disabled={loading}
                >
                  {loading ? '处理中...' : '完成设置，开始遥操作'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DeviceSetup

