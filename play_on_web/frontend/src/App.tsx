import { useState } from 'react'
import './App.css'
import DeviceSetup from './components/DeviceSetup'
import TeleopControl from './components/TeleopControl'
import KeymapSettings from './pages/KeymapSettings'
import { useRobotStore } from './stores/robotStore'

type Page = 'setup' | 'teleop' | 'keymap-settings'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('setup')
  const { isConnected } = useRobotStore()

  const renderPage = () => {
    switch (currentPage) {
      case 'setup':
        return <DeviceSetup onComplete={() => setCurrentPage('teleop')} />
      case 'teleop':
        return (
          <TeleopControl
            onBack={() => setCurrentPage('setup')}
            onOpenSettings={() => setCurrentPage('keymap-settings')}
          />
        )
      case 'keymap-settings':
        return <KeymapSettings />
      default:
        return null
    }
  }

  // 设置页面有自己的导航，不需要显示header和footer
  if (currentPage === 'keymap-settings') {
    return (
      <div className="app">
        <main className="app-main">
          {renderPage()}
        </main>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">🤖 XLerobot Web Teleop</h1>
          <div className="connection-status">
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
            <span className="status-text">
              {isConnected ? '已连接' : '未连接'}
            </span>
          </div>
        </div>
      </header>

      <main className="app-main">
        {renderPage()}
      </main>

      <footer className="app-footer">
        <p>XLerobot Web 遥操作系统 v1.0.0 | 基于 lerobot 开发</p>
      </footer>
    </div>
  )
}

export default App

