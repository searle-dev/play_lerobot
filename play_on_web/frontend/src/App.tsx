import { useState } from 'react'
import './App.css'
import DeviceSetup from './components/DeviceSetup'
import TeleopControl from './components/TeleopControl'
import SimSetup from './components/SimSetup'
import KeymapSettings from './pages/KeymapSettings'
import { useRobotStore } from './stores/robotStore'

type Page = 'mode-select' | 'setup' | 'sim-setup' | 'teleop' | 'keymap-settings'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('mode-select')
  const { isConnected, setMode } = useRobotStore()

  const handleModeSelect = (mode: 'real' | 'sim') => {
    setMode(mode)
    if (mode === 'real') {
      setCurrentPage('setup')
    } else {
      setCurrentPage('sim-setup')
    }
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'mode-select':
        return (
          <div className="mode-select">
            <div className="setup-card">
              <div className="setup-header">
                <h2 className="setup-title">Select Mode</h2>
              </div>
              <div className="setup-content">
                <div className="mode-options">
                  <button
                    className="mode-card"
                    onClick={() => handleModeSelect('real')}
                  >
                    <div className="mode-icon">🤖</div>
                    <strong>Real Robot</strong>
                    <span>Connect to physical hardware via serial ports</span>
                  </button>
                  <button
                    className="mode-card"
                    onClick={() => handleModeSelect('sim')}
                  >
                    <div className="mode-icon">🎮</div>
                    <strong>Simulation</strong>
                    <span>Run MuJoCo physics simulation in browser</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
      case 'setup':
        return <DeviceSetup onComplete={() => setCurrentPage('teleop')} />
      case 'sim-setup':
        return (
          <SimSetup
            onComplete={() => setCurrentPage('teleop')}
            onBack={() => setCurrentPage('mode-select')}
          />
        )
      case 'teleop':
        return (
          <TeleopControl
            onBack={() => setCurrentPage('mode-select')}
            onOpenSettings={() => setCurrentPage('keymap-settings')}
          />
        )
      case 'keymap-settings':
        return <KeymapSettings />
      default:
        return null
    }
  }

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
