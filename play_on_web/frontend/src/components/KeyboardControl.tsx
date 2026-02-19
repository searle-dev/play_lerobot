import { useEffect, useState, useMemo } from 'react'
import './KeyboardControl.css'
import { useRobotStore } from '../stores/robotStore'
import { keymapApi } from '../api/client'
import type { KeyboardKeymap } from '../types/keymap'

// Simulation mode keymap: shows the hardcoded XLeRobot controller keys
const SIM_KEYMAP: KeyboardKeymap = {
  left_arm: {
    'rotate+': '7', 'rotate-': 'Y',
    'y+': '8', 'y-': 'U',
    'x+': '9', 'x-': 'I',
    'pitch+': '0', 'pitch-': 'O',
    'roll+': '-', 'roll-': 'P',
    'gripper': 'V',
  },
  right_arm: {
    'rotate+': 'H', 'rotate-': 'N',
    'y+': 'J', 'y-': 'M',
    'x+': 'K', 'x-': ',',
    'pitch+': 'L', 'pitch-': '.',
    'roll+': ';', 'roll-': '/',
    'gripper': 'B',
  },
  base: {
    'forward': 'W', 'backward': 'S',
    'left': 'A', 'right': 'D',
    'head_pan_l': 'R', 'head_pan_r': 'T',
    'head_tilt_u': 'F', 'head_tilt_d': 'G',
    'reset': 'X',
  },
}

function KeyboardControl() {
  const { teleopWs, keymapConfig, currentProfile, mode, backend } = useRobotStore()
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set())
  const [keymap, setKeymap] = useState<KeyboardKeymap | null>(null)

  const isSimMode = mode === 'sim'

  // Load keymap
  useEffect(() => {
    if (isSimMode) {
      setKeymap(SIM_KEYMAP)
      return
    }

    const loadKeymap = async () => {
      try {
        if (keymapConfig && currentProfile) {
          const profile = keymapConfig.profiles[currentProfile]
          if (profile) {
            setKeymap(profile.keyboard)
            return
          }
        }
        const response = await keymapApi.getCurrentKeymap()
        if (response.data.status === 'success') {
          setKeymap(response.data.keymap.keyboard)
        }
      } catch {
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
  }, [keymapConfig, currentProfile, isSimMode])

  // Build reverse keymap for visual highlight
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

  useEffect(() => {
    if (!reverseKeymap) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // In sim mode, route through backend using event.code
      if (isSimMode && backend) {
        backend.onKeyDown(e.code)
        // Visual highlight: translate code to display key
        const displayKey = codeToDisplayKey(e.code)
        if (displayKey && reverseKeymap[displayKey]) {
          setPressedKeys((prev) => new Set(prev).add(displayKey))
          e.preventDefault()
        }
        return
      }

      // Real mode: existing behavior
      const key = e.key.toUpperCase()
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
      // In sim mode, route through backend
      if (isSimMode && backend) {
        backend.onKeyUp(e.code)
        const displayKey = codeToDisplayKey(e.code)
        if (displayKey) {
          setPressedKeys((prev) => {
            const newSet = new Set(prev)
            newSet.delete(displayKey)
            return newSet
          })
        }
        return
      }

      // Real mode
      const key = e.key.toUpperCase()
      setPressedKeys((prev) => {
        const newSet = new Set(prev)
        newSet.delete(key)
        return newSet
      })
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
  }, [teleopWs, reverseKeymap, isSimMode, backend])

  const isKeyPressed = (key: string) => pressedKeys.has(key)

  if (!keymap || !reverseKeymap) {
    return (
      <div className="keyboard-control">
        <h3 className="control-title">Keyboard Control</h3>
        <div className="loading-keymap">Loading keymap...</div>
      </div>
    )
  }

  return (
    <div className="keyboard-control">
      <h3 className="control-title">Keyboard Control</h3>

      <div className="keyboard-sections">
        <div className="keyboard-section">
          <h4 className="section-title">Left Arm</h4>
          <div className="keymap-grid">
            {Object.entries(keymap.left_arm).map(([action, key]) => (
              <div key={action} className={`key-item ${isKeyPressed(key) ? 'active' : ''}`}>
                <span className="key-visual">{key}</span>
                <span className="key-label">{action}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="keyboard-section">
          <h4 className="section-title">Right Arm</h4>
          <div className="keymap-grid">
            {Object.entries(keymap.right_arm).map(([action, key]) => (
              <div key={action} className={`key-item ${isKeyPressed(key) ? 'active' : ''}`}>
                <span className="key-visual">{key}</span>
                <span className="key-label">{action}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="keyboard-section">
          <h4 className="section-title">Base / Head</h4>
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
        <p>Hold keys to control the robot</p>
      </div>
    </div>
  )
}

/** Convert KeyboardEvent.code to the display character used in keymap */
function codeToDisplayKey(code: string): string | null {
  if (code.startsWith('Key')) return code.slice(3)
  if (code.startsWith('Digit')) return code.slice(5)
  const map: Record<string, string> = {
    'Minus': '-', 'Equal': '+', 'Comma': ',', 'Period': '.',
    'Semicolon': ';', 'Slash': '/', 'Quote': "'", 'Backquote': '`',
    'BracketLeft': '[', 'BracketRight': ']',
  }
  return map[code] ?? null
}

export default KeyboardControl
