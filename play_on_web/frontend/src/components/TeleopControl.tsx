import { useState, useEffect } from 'react'
import './TeleopControl.css'
import KeyboardControl from './KeyboardControl'
import XboxControl from './XboxControl'
import CameraView from './CameraView'
import RobotStatus from './RobotStatus'
import { useRobotStore } from '../stores/robotStore'
import { createTeleopWebSocket, robotApi } from '../api/client'

interface TeleopControlProps {
  onBack: () => void
}

function TeleopControl({ onBack }: TeleopControlProps) {
  const { controlMode, setControlMode, teleopWs, setTeleopWs, setObservation, setIsConnected } = useRobotStore()
  const [showStatus, setShowStatus] = useState(true)
  const [stepLevel, setStepLevel] = useState('normal')
  
  useEffect(() => {
    // 创建 WebSocket 连接
    const ws = createTeleopWebSocket(
      (data) => {
        if (data.type === 'observation') {
          setObservation(data.data.observation)
        } else if (data.type === 'action_result') {
          if (data.data.observation) {
            setObservation(data.data.observation)
          }
        }
      },
      (error) => {
        console.error('Teleop WebSocket error:', error)
      },
      () => {
        setTeleopWs(null)
      }
    )
    
    setTeleopWs(ws)
    
    // 定期心跳
    const heartbeatInterval = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 5000)
    
    return () => {
      clearInterval(heartbeatInterval)
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [])
  
  const handleDisconnect = async () => {
    try {
      await robotApi.disconnect()
      setIsConnected(false)
      if (teleopWs) {
        teleopWs.close()
      }
      onBack()
    } catch (err: any) {
      console.error('Disconnect error:', err)
    }
  }
  
  const handleZeroPosition = async (arm: string) => {
    try {
      await robotApi.moveToZero(arm)
    } catch (err: any) {
      console.error('Zero position error:', err)
    }
  }
  
  const handleResetPosition = async (arm: string) => {
    try {
      const response = await robotApi.moveToResetPosition(arm)
      if (response.data.status === 'error') {
        alert('⚠️ ' + response.data.message)
      }
    } catch (err: any) {
      console.error('Reset position error:', err)
      alert('移动到复位位置失败: ' + err.message)
    }
  }
  
  const handleStepLevelChange = async (level: string) => {
    try {
      setStepLevel(level)
      const response = await robotApi.setStepLevel('both', level)
      if (response.data.status === 'error') {
        alert('⚠️ ' + response.data.message)
      }
    } catch (err: any) {
      console.error('Step level change error:', err)
      alert('设置步长失败: ' + err.message)
    }
  }
  
  return (
    <div className="teleop-control">
      <div className="control-header">
        <div className="control-header-left">
          <button onClick={handleDisconnect} className="btn btn-secondary">
            ← 返回设置
          </button>
          <button onClick={() => setShowStatus(!showStatus)} className="btn btn-text">
            {showStatus ? '隐藏状态' : '显示状态'}
          </button>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="control-mode-toggle">
            <button
              className={`mode-btn ${controlMode === 'keyboard' ? 'active' : ''}`}
              onClick={() => setControlMode('keyboard')}
            >
              ⌨️ 键盘
            </button>
            <button
              className={`mode-btn ${controlMode === 'xbox' ? 'active' : ''}`}
              onClick={() => setControlMode('xbox')}
            >
              🎮 Xbox
            </button>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--gray-600)' }}>步长:</span>
            <select 
              value={stepLevel}
              onChange={(e) => handleStepLevelChange(e.target.value)}
              style={{
                padding: '0.375rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid var(--gray-300)',
                fontSize: '0.8125rem',
                background: 'white',
                cursor: 'pointer'
              }}
              title="调整运动步长大小"
            >
              <option value="slow">慢速 (精细)</option>
              <option value="normal">正常</option>
              <option value="fast">快速</option>
            </select>
          </div>
        </div>
        
        <div className="control-header-right">
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '0.25rem' }}>
              <button 
                onClick={() => handleZeroPosition('left')} 
                className="btn btn-secondary"
                style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
                title="左臂归零"
              >
                左臂归零
              </button>
              <button 
                onClick={() => handleZeroPosition('right')} 
                className="btn btn-secondary"
                style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
                title="右臂归零"
              >
                右臂归零
              </button>
              <button 
                onClick={() => handleZeroPosition('both')} 
                className="btn btn-primary"
                style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
                title="全部归零"
              >
                全部归零
              </button>
            </div>
            <div style={{ width: '1px', height: '24px', background: 'var(--gray-300, #dee2e6)' }} />
            <button 
              onClick={() => handleResetPosition('both')} 
              className="btn"
              style={{ 
                fontSize: '0.8125rem', 
                padding: '0.375rem 0.75rem',
                background: 'var(--success, #28a745)',
                color: 'white',
                fontWeight: 600
              }}
              title="移动到安全复位位置（断电前建议使用）"
            >
              🏠 安全复位
            </button>
          </div>
        </div>
      </div>
      
      <div className="control-layout">
        <div className="control-main">
          <div className="camera-grid">
            <CameraView />
          </div>
          
          <div className="control-panel">
            {controlMode === 'keyboard' ? (
              <KeyboardControl />
            ) : (
              <XboxControl />
            )}
          </div>
        </div>
        
        {showStatus && (
          <div className="control-sidebar">
            <RobotStatus />
          </div>
        )}
      </div>
    </div>
  )
}

export default TeleopControl

