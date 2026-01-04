import { useEffect } from 'react'
import './RobotStatus.css'
import { useRobotStore } from '../stores/robotStore'

function RobotStatus() {
  const { observation, teleopWs } = useRobotStore()
  
  useEffect(() => {
    // 定期请求观测值
    const interval = setInterval(() => {
      if (teleopWs && teleopWs.readyState === WebSocket.OPEN) {
        teleopWs.send(JSON.stringify({ type: 'get_observation' }))
      }
    }, 100) // 10 Hz
    
    return () => clearInterval(interval)
  }, [teleopWs])
  
  // 提取各部分的状态
  const getArmStatus = (prefix: string) => {
    if (!observation) return null
    
    return {
      shoulder_pan: observation[`${prefix}_arm_shoulder_pan.pos`],
      shoulder_lift: observation[`${prefix}_arm_shoulder_lift.pos`],
      elbow_flex: observation[`${prefix}_arm_elbow_flex.pos`],
      wrist_flex: observation[`${prefix}_arm_wrist_flex.pos`],
      wrist_roll: observation[`${prefix}_arm_wrist_roll.pos`],
      gripper: observation[`${prefix}_arm_gripper.pos`],
    }
  }
  
  const getHeadStatus = () => {
    if (!observation) return null
    
    return {
      motor_1: observation['head_motor_1.pos'],
      motor_2: observation['head_motor_2.pos'],
    }
  }
  
  const leftArm = getArmStatus('left')
  const rightArm = getArmStatus('right')
  const head = getHeadStatus()
  
  const formatValue = (value: number | undefined) => {
    if (value === undefined) return '-'
    return value.toFixed(2)
  }
  
  return (
    <div className="robot-status">
      <h3 className="status-title">🤖 机器人状态</h3>
      
      {!observation ? (
        <div className="status-loading">
          <div className="loading-spinner"></div>
          <p>获取状态中...</p>
        </div>
      ) : (
        <div className="status-sections">
          {/* 左臂状态 */}
          <div className="status-section">
            <h4 className="section-header">左臂</h4>
            <div className="status-items">
              {leftArm && Object.entries(leftArm).map(([joint, value]) => (
                <div key={joint} className="status-item">
                  <span className="status-label">{joint}</span>
                  <span className="status-value">{formatValue(value)}°</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* 右臂状态 */}
          <div className="status-section">
            <h4 className="section-header">右臂</h4>
            <div className="status-items">
              {rightArm && Object.entries(rightArm).map(([joint, value]) => (
                <div key={joint} className="status-item">
                  <span className="status-label">{joint}</span>
                  <span className="status-value">{formatValue(value)}°</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* 头部状态 */}
          <div className="status-section">
            <h4 className="section-header">头部</h4>
            <div className="status-items">
              {head && Object.entries(head).map(([motor, value]) => (
                <div key={motor} className="status-item">
                  <span className="status-label">{motor}</span>
                  <span className="status-value">{formatValue(value)}°</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RobotStatus

