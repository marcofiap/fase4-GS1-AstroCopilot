import { useEffect, useState } from 'react'
import { fetchAlerts } from '../api'

const LEVEL_COLOR = { fadiga: '#f59e0b', risco: '#ef4444', normal: '#22c55e' }

export default function AlertLogPanel({ limit = 20, fullPage = false }) {
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const d = await fetchAlerts(limit)
        if (active) setAlerts(d.alerts)
      } catch {
        /* backend offline — ignora */
      }
    }
    load()
    const id = setInterval(load, 3000)
    return () => { active = false; clearInterval(id) }
  }, [limit])

  return (
    <section className="card">
      <header className="card-head">
        <h2>Log de Alertas</h2>
        <span className="muted">{alerts.length} {fullPage ? 'registros' : 'recentes'}</span>
      </header>

      {alerts.length === 0 ? (
        <p className="muted">Nenhum alerta registrado. Tripulação estável. ✅</p>
      ) : (
        <ul className={`alert-log ${fullPage ? 'full' : ''}`}>
          {alerts.map((a, i) => (
            <li key={i} className="alert-row">
              <span className="alert-level" style={{ background: LEVEL_COLOR[a.risk_level] }}>
                {a.risk_level.toUpperCase()}
              </span>
              <span className="alert-msg">{a.message}</span>
              <span className="alert-time">{new Date(a.ts).toLocaleTimeString()}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
