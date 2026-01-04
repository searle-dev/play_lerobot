import { useState } from 'react'
import './App.css'
import DeviceSetup from './components/DeviceSetup'
import TeleopControl from './components/TeleopControl'
import { useRobotStore } from './stores/robotStore'

function App() {
  const [setupComplete, setSetupComplete] = useState(false)
  const { isConnected } = useRobotStore()

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
        {!setupComplete ? (
          <DeviceSetup onComplete={() => setSetupComplete(true)} />
        ) : (
          <TeleopControl onBack={() => setSetupComplete(false)} />
        )}
      </main>

      <footer className="app-footer">
        <p>XLerobot Web 遥操作系统 v1.0.0 | 基于 lerobot 开发</p>
      </footer>
    </div>
  )
}

export default App

