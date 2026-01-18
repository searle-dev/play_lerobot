import { useState, useEffect } from 'react'
import './KeymapEditor.css'
import type { KeyboardKeymap } from '../types/keymap'

interface KeymapEditorProps {
  keymap: KeyboardKeymap
  onChange: (keymap: KeyboardKeymap) => void
}

interface EditingState {
  category: 'left_arm' | 'right_arm' | 'base'
  action: string
}

// 动作名称本地化
const ACTION_NAMES: Record<string, string> = {
  'shoulder_pan+': '肩部旋转+',
  'shoulder_pan-': '肩部旋转-',
  'wrist_roll+': '腕部旋转+',
  'wrist_roll-': '腕部旋转-',
  'gripper+': '夹爪张开',
  'gripper-': '夹爪闭合',
  'x+': 'X轴+',
  'x-': 'X轴-',
  'y+': 'Y轴+',
  'y-': 'Y轴-',
  'pitch+': '俯仰+',
  'pitch-': '俯仰-',
  'reset': '归零',
  'forward': '前进',
  'backward': '后退',
  'left': '左移',
  'right': '右移',
  'rotate_left': '左转',
  'rotate_right': '右转',
}

// 类别名称本地化
const CATEGORY_NAMES: Record<string, string> = {
  'left_arm': '左臂控制',
  'right_arm': '右臂控制',
  'base': '底盘控制',
}

function KeymapEditor({ keymap, onChange }: KeymapEditorProps) {
  const [editingState, setEditingState] = useState<EditingState | null>(null)
  const [conflictError, setConflictError] = useState<string>('')

  // 检测按键冲突
  const detectConflict = (
    newKey: string,
    targetCategory: string,
    targetAction: string
  ): string | null => {
    const allMappings: Array<[string, string, string]> = []

    // 收集所有映射
    Object.entries(keymap.left_arm).forEach(([action, key]) => {
      allMappings.push(['left_arm', action, key])
    })
    Object.entries(keymap.right_arm).forEach(([action, key]) => {
      allMappings.push(['right_arm', action, key])
    })
    Object.entries(keymap.base).forEach(([action, key]) => {
      allMappings.push(['base', action, key])
    })

    // 检查冲突（排除自己）
    for (const [category, action, key] of allMappings) {
      if (
        key.toUpperCase() === newKey.toUpperCase() &&
        !(category === targetCategory && action === targetAction)
      ) {
        const categoryName = CATEGORY_NAMES[category] || category
        const actionName = ACTION_NAMES[action] || action
        return `按键 "${newKey}" 已被 ${categoryName} 的 "${actionName}" 使用`
      }
    }

    return null
  }

  // 处理按键捕获
  useEffect(() => {
    if (!editingState) return

    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault()

      // 忽略单独的修饰键
      if (['Shift', 'Control', 'Alt', 'Meta'].includes(e.key)) {
        return
      }

      const key = e.key

      // 检测冲突
      const conflict = detectConflict(key, editingState.category, editingState.action)
      if (conflict) {
        setConflictError(conflict)
        setTimeout(() => setConflictError(''), 3000)
        return
      }

      // 更新键位映射
      const newKeymap = { ...keymap }
      newKeymap[editingState.category] = {
        ...newKeymap[editingState.category],
        [editingState.action]: key,
      }

      onChange(newKeymap)
      setEditingState(null)
      setConflictError('')
    }

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setEditingState(null)
        setConflictError('')
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keydown', handleEscape)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keydown', handleEscape)
    }
  }, [editingState, keymap, onChange])

  // 开始编辑按键
  const startEditing = (category: 'left_arm' | 'right_arm' | 'base', action: string) => {
    setEditingState({ category, action })
    setConflictError('')
  }

  // 渲染键位映射项
  const renderKeymapItem = (
    category: 'left_arm' | 'right_arm' | 'base',
    action: string,
    key: string
  ) => {
    const isEditing =
      editingState?.category === category && editingState?.action === action

    return (
      <div
        key={action}
        className={`keymap-item ${isEditing ? 'editing' : ''}`}
        onClick={() => startEditing(category, action)}
      >
        <span className="action-label">{ACTION_NAMES[action] || action}</span>
        <span className="key-display">{key}</span>
      </div>
    )
  }

  return (
    <div className="keymap-editor">
      {/* 监听模式覆盖层 */}
      {editingState && (
        <div className="listening-overlay">
          <div className="listening-modal">
            <h3>等待按键输入...</h3>
            <p>
              正在为 <strong>{CATEGORY_NAMES[editingState.category]}</strong> 的{' '}
              <strong>{ACTION_NAMES[editingState.action]}</strong> 设置按键
            </p>
            <p className="hint">请按下要映射的按键</p>
            <p className="hint-small">按 ESC 取消</p>
            {conflictError && <p className="error-message">{conflictError}</p>}
          </div>
        </div>
      )}

      {/* 键位映射编辑区域 */}
      <div className="keymap-sections">
        {/* 左臂控制 */}
        <div className="keymap-section">
          <h4 className="section-title">{CATEGORY_NAMES.left_arm}</h4>
          <div className="keymap-grid">
            {Object.entries(keymap.left_arm).map(([action, key]) =>
              renderKeymapItem('left_arm', action, key)
            )}
          </div>
        </div>

        {/* 右臂控制 */}
        <div className="keymap-section">
          <h4 className="section-title">{CATEGORY_NAMES.right_arm}</h4>
          <div className="keymap-grid">
            {Object.entries(keymap.right_arm).map(([action, key]) =>
              renderKeymapItem('right_arm', action, key)
            )}
          </div>
        </div>

        {/* 底盘控制 */}
        <div className="keymap-section">
          <h4 className="section-title">{CATEGORY_NAMES.base}</h4>
          <div className="keymap-grid">
            {Object.entries(keymap.base).map(([action, key]) =>
              renderKeymapItem('base', action, key)
            )}
          </div>
        </div>
      </div>

      {/* 使用说明 */}
      <div className="editor-instructions">
        <p>点击任意动作来修改其对应的按键</p>
      </div>
    </div>
  )
}

export default KeymapEditor
