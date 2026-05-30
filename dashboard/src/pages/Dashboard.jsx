import { Link } from 'react-router-dom'
import { useTelemetry } from '../hooks/useTelemetry'
import TelemetryPanel from '../components/TelemetryPanel'
import ChatPanel from '../components/ChatPanel'

export default function Dashboard() {
  const { crew, history, connected } = useTelemetry()

  return (
    <div className="app">
      <header className="topbar">
        <h1>AstroCopilot <span>Mission Control</span></h1>
        <div className="topbar-actions">
          <Link className="btn" to="/visao">Visão (imagem)</Link>
          <Link className="btn" to="/alertas">Log de Alertas</Link>
          <span className={`dot ${connected ? 'on' : 'off'}`}>
            backend {connected ? 'conectado' : 'offline'}
          </span>
        </div>
      </header>

      <main className="grid">
        <TelemetryPanel crew={crew} history={history} connected={connected} />
        <ChatPanel />
      </main>

      <footer className="foot">Grupo 42 · GS 2026.1 · FIAP — POC AstroCopilot</footer>
    </div>
  )
}
