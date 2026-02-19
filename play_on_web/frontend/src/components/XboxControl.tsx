import { useEffect, useState } from 'react'
import './XboxControl.css'
import { useRobotStore } from '../stores/robotStore'

function XboxControl() {
  const { teleopWs, mode, backend } = useRobotStore()
  const isSimMode = mode === 'sim'
  const [gamepadConnected, setGamepadConnected] = useState(false)
  const [gamepadIndex, setGamepadIndex] = useState<number | null>(null)
  const [buttonStates, setButtonStates] = useState<boolean[]>([])
  const [axisValues, setAxisValues] = useState<number[]>([])
  
  useEffect(() => {
    // 检测手柄连接
    const handleGamepadConnected = (e: GamepadEvent) => {
      console.log('Gamepad connected:', e.gamepad)
      setGamepadConnected(true)
      setGamepadIndex(e.gamepad.index)
    }
    
    const handleGamepadDisconnected = (e: GamepadEvent) => {
      console.log('Gamepad disconnected:', e.gamepad)
      setGamepadConnected(false)
      setGamepadIndex(null)
    }
    
    window.addEventListener('gamepadconnected', handleGamepadConnected)
    window.addEventListener('gamepaddisconnected', handleGamepadDisconnected)
    
    // 定期轮询手柄状态
    const pollGamepad = () => {
      if (gamepadIndex !== null) {
        const gamepads = navigator.getGamepads()
        const gamepad = gamepads[gamepadIndex]
        
        if (gamepad) {
          // 更新按钮状态
          const buttons = gamepad.buttons.map((btn) => btn.pressed)
          setButtonStates(buttons)
          
          // 更新摇杆值
          const axes = Array.from(gamepad.axes)
          setAxisValues(axes)
          
          // 处理手柄输入并发送到后端
          handleGamepadInput(gamepad)
        }
      }
    }
    
    const intervalId = setInterval(pollGamepad, 50) // 20 Hz
    
    return () => {
      window.removeEventListener('gamepadconnected', handleGamepadConnected)
      window.removeEventListener('gamepaddisconnected', handleGamepadDisconnected)
      clearInterval(intervalId)
    }
  }, [gamepadIndex, teleopWs, isSimMode, backend])

  const handleGamepadInput = (gamepad: Gamepad) => {
    const axes = Array.from(gamepad.axes)
    const buttons = gamepad.buttons.map((btn) => btn.pressed)

    // Route through backend if available
    if (isSimMode && backend) {
      backend.onGamepadInput({ axes, buttons })
      return
    }

    if (!teleopWs || teleopWs.readyState !== WebSocket.OPEN) return

    // Left stick controls left arm XY
    if (Math.abs(axes[0]) > 0.5) {
      sendArmAction('left', axes[0] > 0 ? 'y+' : 'y-')
    }
    if (Math.abs(axes[1]) > 0.5) {
      sendArmAction('left', axes[1] > 0 ? 'x-' : 'x+')
    }

    // Right stick controls right arm XY
    if (Math.abs(axes[2]) > 0.5) {
      sendArmAction('right', axes[2] > 0 ? 'y+' : 'y-')
    }
    if (Math.abs(axes[3]) > 0.5) {
      sendArmAction('right', axes[3] > 0 ? 'x-' : 'x+')
    }
  }

  const sendArmAction = (arm: string, action: string) => {
    if (teleopWs && teleopWs.readyState === WebSocket.OPEN) {
      teleopWs.send(JSON.stringify({
        type: 'keyboard_action',
        data: { arm, action }
      }))
    }
  }
  
  return (
    <div className="xbox-control">
      <h3 className="control-title">🎮 Xbox 手柄控制</h3>
      
      {!gamepadConnected ? (
        <div className="gamepad-prompt">
          <div className="prompt-icon">🎮</div>
          <h4>未检测到手柄</h4>
          <p>请连接 Xbox 手柄并按任意按钮激活</p>
        </div>
      ) : (
        <div className="gamepad-info">
          <div className="connection-status connected">
            <span className="status-dot"></span>
            <span>手柄已连接</span>
          </div>
          
          <div className="gamepad-layout">
            {/* 手柄布局可视化 */}
            <svg viewBox="0 0 400 300" className="gamepad-svg">
              {/* 左摇杆 */}
              <circle cx="100" cy="150" r="40" fill="var(--gray-200)" stroke="var(--gray-400)" strokeWidth="2"/>
              <circle 
                cx={100 + (axisValues[0] || 0) * 30} 
                cy={150 + (axisValues[1] || 0) * 30} 
                r="15" 
                fill={Math.abs(axisValues[0] || 0) > 0.5 || Math.abs(axisValues[1] || 0) > 0.5 ? 'var(--primary)' : 'var(--gray-400)'}
              />
              
              {/* 右摇杆 */}
              <circle cx="300" cy="150" r="40" fill="var(--gray-200)" stroke="var(--gray-400)" strokeWidth="2"/>
              <circle 
                cx={300 + (axisValues[2] || 0) * 30} 
                cy={150 + (axisValues[3] || 0) * 30} 
                r="15" 
                fill={Math.abs(axisValues[2] || 0) > 0.5 || Math.abs(axisValues[3] || 0) > 0.5 ? 'var(--primary)' : 'var(--gray-400)'}
              />
              
              {/* 按钮 A B X Y */}
              <circle cx="300" cy="80" r="12" fill={buttonStates[0] ? 'var(--success)' : 'var(--gray-200)'} stroke="var(--gray-400)" strokeWidth="2"/>
              <text x="300" y="85" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">A</text>
              
              <circle cx="330" cy="50" r="12" fill={buttonStates[1] ? 'var(--danger)' : 'var(--gray-200)'} stroke="var(--gray-400)" strokeWidth="2"/>
              <text x="330" y="55" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">B</text>
              
              <circle cx="270" cy="50" r="12" fill={buttonStates[2] ? 'var(--primary)' : 'var(--gray-200)'} stroke="var(--gray-400)" strokeWidth="2"/>
              <text x="270" y="55" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">X</text>
              
              <circle cx="300" cy="20" r="12" fill={buttonStates[3] ? 'var(--warning)' : 'var(--gray-200)'} stroke="var(--gray-400)" strokeWidth="2"/>
              <text x="300" y="25" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">Y</text>
            </svg>
          </div>
          
          <div className="control-mapping">
            <h4>控制映射</h4>
            <div className="mapping-list">
              <div className="mapping-item">
                <span className="mapping-input">左摇杆</span>
                <span className="mapping-arrow">→</span>
                <span className="mapping-output">左臂 XY</span>
              </div>
              <div className="mapping-item">
                <span className="mapping-input">右摇杆</span>
                <span className="mapping-arrow">→</span>
                <span className="mapping-output">右臂 XY</span>
              </div>
              <div className="mapping-item">
                <span className="mapping-input">左/右扳机</span>
                <span className="mapping-arrow">→</span>
                <span className="mapping-output">左/右夹爪</span>
              </div>
              <div className="mapping-item">
                <span className="mapping-input">D-Pad</span>
                <span className="mapping-arrow">→</span>
                <span className="mapping-output">底盘移动</span>
              </div>
              <div className="mapping-item">
                <span className="mapping-input">LB/RB</span>
                <span className="mapping-arrow">→</span>
                <span className="mapping-output">俯仰/旋转</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default XboxControl

