import { useState } from 'react'
import { useRobotStore } from '../stores/robotStore'
import { SimRobotBackend } from '../backend/SimRobotBackend'
import './SimSetup.css'

const ROBOTS = [
  { id: 'xlerobot', name: 'XLeRobot', description: 'Dual-arm mobile robot' },
]

const ENVIRONMENTS = [
  { id: 'basic', name: 'Basic', description: 'Floor and lighting only' },
  { id: 'tabletop', name: 'Tabletop', description: 'Table with objects' },
]

interface SimSetupProps {
  onComplete: () => void
  onBack: () => void
}

function SimSetup({ onComplete, onBack }: SimSetupProps) {
  const { setSimConfig, setBackend, setIsConnected, setObservation } = useRobotStore()
  const [robot, setRobot] = useState('xlerobot')
  const [environment, setEnvironment] = useState('basic')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    setLoading(true)
    setError(null)

    try {
      const config = { robot, environment }
      setSimConfig(config)

      const backend = new SimRobotBackend((obs) => setObservation(obs))
      // Note: container will be set by SimulationView after mount
      await backend.connect(config)

      setBackend(backend)
      setIsConnected(true)
      onComplete()
    } catch (err: any) {
      setError(err.message || 'Failed to load simulation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="sim-setup">
      <div className="setup-card">
        <div className="setup-header">
          <h2 className="setup-title">Simulation Setup</h2>
          <p className="setup-subtitle">Select a robot and environment to simulate</p>
        </div>

        <div className="setup-content">
          <div className="sim-setup-section">
            <h3>Select Robot</h3>
            <div className="sim-setup-options">
              {ROBOTS.map((r) => (
                <button
                  key={r.id}
                  className={`sim-option ${robot === r.id ? 'active' : ''}`}
                  onClick={() => setRobot(r.id)}
                >
                  <strong>{r.name}</strong>
                  <span>{r.description}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="sim-setup-section">
            <h3>Select Environment</h3>
            <div className="sim-setup-options">
              {ENVIRONMENTS.map((e) => (
                <button
                  key={e.id}
                  className={`sim-option ${environment === e.id ? 'active' : ''}`}
                  onClick={() => setEnvironment(e.id)}
                >
                  <strong>{e.name}</strong>
                  <span>{e.description}</span>
                </button>
              ))}
            </div>
          </div>

          {error && <div className="sim-error">{error}</div>}

          <div className="setup-actions">
            <button onClick={onBack} className="btn btn-secondary">Back</button>
            <button onClick={handleStart} className="btn btn-primary btn-large" disabled={loading}>
              {loading ? 'Loading WASM...' : 'Start Simulation'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SimSetup
