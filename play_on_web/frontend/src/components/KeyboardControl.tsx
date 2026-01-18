import { useEffect, useState, useMemo } from 'react'
import './KeyboardControl.css'
import { useRobotStore } from '../stores/robotStore'
import { keymapApi } from '../api/client'
import type { KeyboardKeymap } from '../types/keymap'

function KeyboardControl() {
  const { teleopWs, keymapConfig, currentProfile } = useRobotStore()
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set())
  const [keymap, setKeymap] = useState<KeyboardKeymap | null>(null)

  // 加载键位配置
  useEffect(() => {
    const loadKeymap = async () => {
      try {
        // 如果全局状态中有配置，直接使用
        if (keymapConfig && currentProfile) {
          const profile = keymapConfig.profiles[currentProfile]
          if (profile) {
            setKeymap(profile.keyboard)
            return
          }
        }

        // 否则从API加载
        const response = await keymapApi.getCurrentKeymap()
        if (response.data.status === 'success') {
          setKeymap(response.data.keymap.keyboard)
        }
      } catch (error) {
        console.error('加载键位配置失败:', error)
        // 如果加载失败，使用硬编码的默认配置
        setKeymap({
          left_arm: {
            'shoulder_pan+': 'Q', 'shoulder_pan-': 'E',
            'wrist_roll+': 'R', 'wrist_roll-': 'F',
            'gripper+': 'T', 'gripper-': 'G',
            'x+': 'W', 'x-': 'S', 'y+': 'A', 'y-': 'D',
            'pitch+': 'Z', 'pitch-': 'X',
            'reset': 'C',
          },
          right_arm: {
            'shoulder_pan+': '7', 'shoulder_pan-': '9',
            'wrist_roll+': '/', 'wrist_roll-': '*',
            'gripper+': '+', 'gripper-': '-',
            'x+': '8', 'x-': '2', 'y+': '4', 'y-': '6',
            'pitch+': '1', 'pitch-': '3',
            'reset': '0',
          },
          base: {
            'forward': 'I', 'backward': 'K',
            'left': 'J', 'right': 'L',
            'rotate_left': 'U', 'rotate_right': 'O',
          }
        })
      }
    }

    loadKeymap()
  }, [keymapConfig, currentProfile])

  // 构建反向键位映射（Key → Action）
  const reverseKeymap = useMemo(() => {
    if (!keymap) return null

    const reverse: Record<string, { category: 'left' | 'right' | 'base'; action: string }> = {}

    Object.entries(keymap.left_arm).forEach(([action, key]) => {
      reverse[key.toUpperCase()] = { category: 'left', action }
    })

    Object.entries(keymap.right_arm).forEach(([action, key]) => {
      reverse[key.toUpperCase()] = { category: 'right', action }
    })

    Object.entries(keymap.base).forEach(([action, key]) => {
      reverse[key.toUpperCase()] = { category: 'base', action }
    })

    return reverse
  }, [keymap])

  // 如果还没有加载配置，显示加载状态
  if (!keymap || !reverseKeymap) {
    return (
      <div className="keyboard-control">
        <h3 className="control-title">⌨️ 键盘控制</h3>
        <div className="loading-keymap">加载键位配置中...</div>
      </div>
    )
  }
  
  useEffect(() => {
    if (!reverseKeymap) return

    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toUpperCase()

      // 查找对应的动作
      const mapping = reverseKeymap[key]
      if (mapping) {
        setPressedKeys((prev) => new Set(prev).add(key))

        if (mapping.category === 'base') {
          sendBaseAction(mapping.action)
        } else {
          sendAction(mapping.category, mapping.action)
        }

        e.preventDefault()
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      const key = e.key.toUpperCase()
      setPressedKeys((prev) => {
        const newSet = new Set(prev)
        newSet.delete(key)
        return newSet
      })

      // 如果是底盘控制键，发送停止命令
      const mapping = reverseKeymap[key]
      if (mapping && mapping.category === 'base') {
        sendBaseStop()
        e.preventDefault()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [teleopWs, reverseKeymap])
  
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
            {Object.entries(keymap.left_arm).map(([action, key]) => (
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
            {Object.entries(keymap.right_arm).map(([action, key]) => (
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
            {Object.entries(keymap.base).map(([action, key]) => (
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

