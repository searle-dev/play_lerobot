import { useEffect, useState } from 'react'
import './KeyboardControl.css'
import { useRobotStore } from '../stores/robotStore'

// 键位映射 - 参考 4_xlerobot_teleop_keyboard.py
const LEFT_KEYMAP = {
  'shoulder_pan+': 'Q', 'shoulder_pan-': 'E',
  'wrist_roll+': 'R', 'wrist_roll-': 'F',
  'gripper+': 'T', 'gripper-': 'G',
  'x+': 'W', 'x-': 'S', 'y+': 'A', 'y-': 'D',
  'pitch+': 'Z', 'pitch-': 'X',
  'reset': 'C',
}

const RIGHT_KEYMAP = {
  'shoulder_pan+': '7', 'shoulder_pan-': '9',
  'wrist_roll+': '/', 'wrist_roll-': '*',
  'gripper+': '+', 'gripper-': '-',
  'x+': '8', 'x-': '2', 'y+': '4', 'y-': '6',
  'pitch+': '1', 'pitch-': '3',
  'reset': '0',
}

const BASE_KEYMAP = {
  'forward': 'I', 'backward': 'K',
  'left': 'J', 'right': 'L',
  'rotate_left': 'U', 'rotate_right': 'O',
}

function KeyboardControl() {
  const { teleopWs } = useRobotStore()
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set())
  
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toUpperCase()
      
      // 检查是否是左臂控制键
      for (const [action, mappedKey] of Object.entries(LEFT_KEYMAP)) {
        if (key === mappedKey) {
          setPressedKeys((prev) => new Set(prev).add(key))
          sendAction('left', action)
          e.preventDefault()
          return
        }
      }
      
      // 检查是否是右臂控制键
      for (const [action, mappedKey] of Object.entries(RIGHT_KEYMAP)) {
        if (key === mappedKey) {
          setPressedKeys((prev) => new Set(prev).add(key))
          sendAction('right', action)
          e.preventDefault()
          return
        }
      }
      
      // 检查是否是底盘控制键
      for (const [action, mappedKey] of Object.entries(BASE_KEYMAP)) {
        if (key === mappedKey) {
          setPressedKeys((prev) => new Set(prev).add(key))
          sendBaseAction(action)
          e.preventDefault()
          return
        }
      }
    }
    
    const handleKeyUp = (e: KeyboardEvent) => {
      const key = e.key.toUpperCase()
      setPressedKeys((prev) => {
        const newSet = new Set(prev)
        newSet.delete(key)
        return newSet
      })
      
      // 检查是否是底盘控制键，如果是则发送停止命令
      for (const [, mappedKey] of Object.entries(BASE_KEYMAP)) {
        if (key === mappedKey) {
          sendBaseStop()
          e.preventDefault()
          return
        }
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [teleopWs])
  
  const sendAction = (arm: string, action: string) => {
    if (teleopWs && teleopWs.readyState === WebSocket.OPEN) {
      teleopWs.send(JSON.stringify({
        type: 'keyboard_action',
        data: { arm, action }
      }))
    }
  }
  
  const sendBaseAction = (direction: string) => {
    if (teleopWs && teleopWs.readyState === WebSocket.OPEN) {
      teleopWs.send(JSON.stringify({
        type: 'base_action',
        data: { direction }
      }))
    }
  }
  
  const sendBaseStop = () => {
    if (teleopWs && teleopWs.readyState === WebSocket.OPEN) {
      teleopWs.send(JSON.stringify({
        type: 'base_stop'
      }))
    }
  }
  
  const isKeyPressed = (key: string) => pressedKeys.has(key)
  
  return (
    <div className="keyboard-control">
      <h3 className="control-title">⌨️ 键盘控制</h3>
      
      <div className="keyboard-sections">
        {/* 左臂控制 */}
        <div className="keyboard-section">
          <h4 className="section-title">左臂控制</h4>
          <div className="keymap-grid">
            {Object.entries(LEFT_KEYMAP).map(([action, key]) => (
              <div key={action} className={`key-item ${isKeyPressed(key) ? 'active' : ''}`}>
                <span className="key-visual">{key}</span>
                <span className="key-label">{action}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* 右臂控制 */}
        <div className="keyboard-section">
          <h4 className="section-title">右臂控制</h4>
          <div className="keymap-grid">
            {Object.entries(RIGHT_KEYMAP).map(([action, key]) => (
              <div key={action} className={`key-item ${isKeyPressed(key) ? 'active' : ''}`}>
                <span className="key-visual">{key}</span>
                <span className="key-label">{action}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* 底盘控制 */}
        <div className="keyboard-section">
          <h4 className="section-title">底盘控制</h4>
          <div className="keymap-grid">
            {Object.entries(BASE_KEYMAP).map(([action, key]) => (
              <div key={action} className={`key-item ${isKeyPressed(key) ? 'active' : ''}`}>
                <span className="key-visual">{key}</span>
                <span className="key-label">{action}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="keyboard-hint">
        <p>💡 提示：按住对应按键进行控制</p>
      </div>
    </div>
  )
}

export default KeyboardControl

