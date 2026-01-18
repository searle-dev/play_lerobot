import { useState } from 'react'
import './KeymapProfileSelector.css'
import type { KeymapProfile } from '../types/keymap'

interface KeymapProfileSelectorProps {
  profiles: Record<string, KeymapProfile>
  currentProfile: string
  onSwitch: (profileName: string) => void
  onDelete: (profileName: string) => void
  onCreateNew: () => void
}

// 内置预设列表（不可删除）
const BUILTIN_PROFILES = ['default', 'wasd', 'arrows']

function KeymapProfileSelector({
  profiles,
  currentProfile,
  onSwitch,
  onDelete,
  onCreateNew,
}: KeymapProfileSelectorProps) {
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const handleDelete = (profileName: string) => {
    if (confirmDelete === profileName) {
      onDelete(profileName)
      setConfirmDelete(null)
    } else {
      setConfirmDelete(profileName)
      setTimeout(() => setConfirmDelete(null), 3000)
    }
  }

  const isBuiltin = (profileName: string) => BUILTIN_PROFILES.includes(profileName)

  return (
    <div className="keymap-profile-selector">
      <div className="profile-header">
        <h3>配置预设</h3>
        <button className="create-profile-btn" onClick={onCreateNew}>
          + 新建预设
        </button>
      </div>

      <div className="profile-list">
        {Object.entries(profiles).map(([profileName, profile]) => {
          const isCurrent = profileName === currentProfile
          const canDelete = !isBuiltin(profileName)

          return (
            <div
              key={profileName}
              className={`profile-item ${isCurrent ? 'active' : ''}`}
            >
              <div
                className="profile-info"
                onClick={() => !isCurrent && onSwitch(profileName)}
              >
                <div className="profile-name">
                  {profile.name}
                  {isCurrent && <span className="current-badge">当前</span>}
                  {isBuiltin(profileName) && <span className="builtin-badge">内置</span>}
                </div>
                <div className="profile-description">{profile.description}</div>
              </div>

              {canDelete && (
                <button
                  className={`delete-btn ${confirmDelete === profileName ? 'confirm' : ''}`}
                  onClick={() => handleDelete(profileName)}
                >
                  {confirmDelete === profileName ? '确认删除?' : '删除'}
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default KeymapProfileSelector
