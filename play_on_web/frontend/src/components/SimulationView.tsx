import { useEffect, useRef } from 'react'
import { useRobotStore } from '../stores/robotStore'
import { SimRobotBackend } from '../backend/SimRobotBackend'
import './SimulationView.css'

function SimulationView() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { backend } = useRobotStore()

  useEffect(() => {
    if (!containerRef.current || !backend) return
    if (!(backend instanceof SimRobotBackend)) return

    // Attach renderer to container
    backend.setContainer(containerRef.current)

    // Handle resize
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        const renderer = backend.getRenderer()
        if (renderer && width > 0 && height > 0) {
          renderer.resize(width, height)
        }
      }
    })
    observer.observe(containerRef.current)

    return () => {
      observer.disconnect()
    }
  }, [backend])

  return (
    <div className="simulation-view" ref={containerRef}>
      <div className="sim-overlay">
        <span className="sim-badge">Simulation Mode</span>
      </div>
    </div>
  )
}

export default SimulationView
