import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './KeymapSettings.css'
import KeymapEditor from '../components/KeymapEditor'
import KeymapProfileSelector from '../components/KeymapProfileSelector'
import { keymapApi } from '../api/client'
import { useRobotStore } from '../stores/robotStore'
import type { KeymapConfig, KeyboardKeymap } from '../types/keymap'

function KeymapSettings() {
  const navigate = useNavigate()
  const { setKeymapConfig, setCurrentProfile } = useRobotStore()

  const [config, setConfig] = useState<KeymapConfig | null>(null)
  const [editingKeymap, setEditingKeymap] = useState<KeyboardKeymap | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProfileName, setNewProfileName] = useState('')
  const [newProfileDisplayName, setNewProfileDisplayName] = useState('')
  const [newProfileDescription, setNewProfileDescription] = useState('')

  // 加载配置
  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      setLoading(true)
      const response = await keymapApi.getConfig()
      const configData = response.data.config

      setConfig(configData)
      const currentProfile = configData.profiles[configData.current_profile]
      setEditingKeymap(currentProfile?.keyboard || null)
    } catch (error) {
      console.error('加载配置失败:', error)
      showMessage('error', '加载配置失败')
    } finally {
      setLoading(false)
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  // 切换预设
  const handleSwitchProfile = async (profileName: string) => {
    try {
      const response = await keymapApi.switchProfile(profileName)
      if (response.data.status === 'success') {
        showMessage('success', `已切换到预设: ${config?.profiles[profileName]?.name}`)

        // 重新加载配置
        await loadConfig()

        // 更新全局状态
        setCurrentProfile(profileName)
        if (config) {
          setKeymapConfig({ ...config, current_profile: profileName })
        }
      } else {
        showMessage('error', response.data.message)
      }
    } catch (error) {
      console.error('切换预设失败:', error)
      showMessage('error', '切换预设失败')
    }
  }

  // 保存当前配置
  const handleSave = async () => {
    if (!config || !editingKeymap) return

    try {
      setSaving(true)

      // 验证配置
      const validateResponse = await keymapApi.validate(editingKeymap)
      if (validateResponse.data.status !== 'success') {
        showMessage('error', `配置验证失败: ${validateResponse.data.message}`)
        return
      }

      // 保存配置
      const response = await keymapApi.updateProfile(config.current_profile, editingKeymap)

      if (response.data.status === 'success') {
        showMessage('success', '配置已保存并生效')

        // 重新加载配置
        await loadConfig()

        // 更新全局状态
        const updatedConfig = { ...config }
        updatedConfig.profiles[config.current_profile].keyboard = editingKeymap
        setKeymapConfig(updatedConfig)
      } else {
        showMessage('error', response.data.message)
      }
    } catch (error) {
      console.error('保存配置失败:', error)
      showMessage('error', '保存配置失败')
    } finally {
      setSaving(false)
    }
  }

  // 创建新预设
  const handleCreateProfile = async () => {
    if (!newProfileName || !newProfileDisplayName || !editingKeymap) {
      showMessage('error', '请填写完整信息')
      return
    }

    try {
      const response = await keymapApi.createProfile(
        newProfileName,
        newProfileDisplayName,
        newProfileDescription || '用户自定义配置',
        editingKeymap
      )

      if (response.data.status === 'success') {
        showMessage('success', `预设 "${newProfileDisplayName}" 创建成功`)
        setShowCreateModal(false)
        setNewProfileName('')
        setNewProfileDisplayName('')
        setNewProfileDescription('')

        // 重新加载配置
        await loadConfig()
      } else {
        showMessage('error', response.data.message)
      }
    } catch (error) {
      console.error('创建预设失败:', error)
      showMessage('error', '创建预设失败')
    }
  }

  // 删除预设
  const handleDeleteProfile = async (profileName: string) => {
    try {
      const response = await keymapApi.deleteProfile(profileName)

      if (response.data.status === 'success') {
        showMessage('success', '预设已删除')

        // 重新加载配置
        await loadConfig()
      } else {
        showMessage('error', response.data.message)
      }
    } catch (error) {
      console.error('删除预设失败:', error)
      showMessage('error', '删除预设失败')
    }
  }

  // 取消并返回
  const handleCancel = () => {
    navigate('/')
  }

  if (loading) {
    return (
      <div className="keymap-settings">
        <div className="loading">加载中...</div>
      </div>
    )
  }

  if (!config || !editingKeymap) {
    return (
      <div className="keymap-settings">
        <div className="error">无法加载配置</div>
      </div>
    )
  }

  return (
    <div className="keymap-settings">
      {/* 头部 */}
      <div className="settings-header">
        <h2>键位配置管理</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={handleCancel}>
            取消
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? '保存中...' : '保存配置'}
          </button>
        </div>
      </div>

      {/* 消息提示 */}
      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 配置预设选择器 */}
      <KeymapProfileSelector
        profiles={config.profiles}
        currentProfile={config.current_profile}
        onSwitch={handleSwitchProfile}
        onDelete={handleDeleteProfile}
        onCreateNew={() => setShowCreateModal(true)}
      />

      {/* 键位编辑器 */}
      <KeymapEditor
        keymap={editingKeymap}
        onChange={setEditingKeymap}
      />

      {/* 创建新预设模态框 */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>创建新配置预设</h3>
            <div className="modal-form">
              <div className="form-group">
                <label>预设ID（英文标识）</label>
                <input
                  type="text"
                  value={newProfileName}
                  onChange={(e) => setNewProfileName(e.target.value)}
                  placeholder="例如: my_custom"
                />
              </div>
              <div className="form-group">
                <label>预设名称</label>
                <input
                  type="text"
                  value={newProfileDisplayName}
                  onChange={(e) => setNewProfileDisplayName(e.target.value)}
                  placeholder="例如: 我的自定义配置"
                />
              </div>
              <div className="form-group">
                <label>预设描述</label>
                <textarea
                  value={newProfileDescription}
                  onChange={(e) => setNewProfileDescription(e.target.value)}
                  placeholder="简短描述这个预设的特点..."
                  rows={3}
                />
              </div>
              <div className="modal-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  取消
                </button>
                <button className="btn btn-primary" onClick={handleCreateProfile}>
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default KeymapSettings
