import { useState, useEffect } from 'react'
import './TeleopControl.css'
import KeyboardControl from './KeyboardControl'
import XboxControl from './XboxControl'
import CameraView from './CameraView'
import SimulationView from './SimulationView'
import RobotStatus from './RobotStatus'
import { useRobotStore } from '../stores/robotStore'
import { createTeleopWebSocket, robotApi } from '../api/client'

interface TeleopControlProps {
  onBack: () => void
  onOpenSettings?: () => void
}

function TeleopControl({ onBack, onOpenSettings }: TeleopControlProps) {
  const {
    controlMode, setControlMode,
    teleopWs, setTeleopWs,
    setObservation, setIsConnected,
    mode, backend,
  } = useRobotStore()
  const [showStatus, setShowStatus] = useState(true)
  const [stepLevel, setStepLevel] = useState('normal')

  const isRealMode = mode === 'real'

  useEffect(() => {
    // Only create WebSocket in real mode
    if (!isRealMode) return

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
  }, [isRealMode])

  const handleDisconnect = async () => {
    try {
      if (backend) {
        await backend.disconnect()
      }
      if (isRealMode) {
        await robotApi.disconnect()
        if (teleopWs) {
          teleopWs.close()
        }
      }
      setIsConnected(false)
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
        alert(response.data.message)
      }
    } catch (err: any) {
      console.error('Reset position error:', err)
    }
  }

  const handleStepLevelChange = async (level: string) => {
    try {
      setStepLevel(level)
      const response = await robotApi.setStepLevel('both', level)
      if (response.data.status === 'error') {
        alert(response.data.message)
      }
    } catch (err: any) {
      console.error('Step level change error:', err)
    }
  }

  const handleSimReset = () => {
    if (backend) {
      backend.reset()
    }
  }

  return (
    <div className="teleop-control">
      <div className="control-header">
        <div className="control-header-left">
          <button onClick={handleDisconnect} className="btn btn-secondary">
            ← Back
          </button>
          <button onClick={() => setShowStatus(!showStatus)} className="btn btn-text">
            {showStatus ? 'Hide Status' : 'Show Status'}
          </button>
          {isRealMode && onOpenSettings && (
            <button onClick={onOpenSettings} className="btn btn-settings">
              Keymap Settings
            </button>
          )}
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="control-mode-toggle">
            <button
              className={`mode-btn ${controlMode === 'keyboard' ? 'active' : ''}`}
              onClick={() => setControlMode('keyboard')}
            >
              Keyboard
            </button>
            <button
              className={`mode-btn ${controlMode === 'xbox' ? 'active' : ''}`}
              onClick={() => setControlMode('xbox')}
            >
              Xbox
            </button>
          </div>

          {isRealMode && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8125rem', color: 'var(--gray-600)' }}>Step:</span>
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
              >
                <option value="slow">Slow</option>
                <option value="normal">Normal</option>
                <option value="fast">Fast</option>
              </select>
            </div>
          )}
        </div>

        <div className="control-header-right">
          {isRealMode ? (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                <button
                  onClick={() => handleZeroPosition('left')}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
                >
                  Zero Left
                </button>
                <button
                  onClick={() => handleZeroPosition('right')}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
                >
                  Zero Right
                </button>
                <button
                  onClick={() => handleZeroPosition('both')}
                  className="btn btn-primary"
                  style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
                >
                  Zero All
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
              >
                Safe Reset
              </button>
            </div>
          ) : (
            <button
              onClick={handleSimReset}
              className="btn btn-primary"
              style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
            >
              Reset Sim
            </button>
          )}
        </div>
      </div>

      <div className="control-layout">
        <div className="control-main">
          <div className="camera-grid">
            {mode === 'sim' ? <SimulationView /> : <CameraView />}
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
