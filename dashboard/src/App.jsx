import { useTelemetry } from './hooks/useTelemetry'
import TelemetryPanel from './components/TelemetryPanel'
import ChatPanel from './components/ChatPanel'
import VisionPanel from './components/VisionPanel'

export default function App() {
  const { latest, history, connected } = useTelemetry()
  const risk = latest?.risk_level
  const alert = risk && risk !== 'normal'

  return (
    <div className="app">
      <header className="topbar">
        <h1>🚀 AstroCopilot <span>Mission Control</span></h1>
        <span className={`dot ${connected ? 'on' : 'off'}`}>
          backend {connected ? 'conectado' : 'offline'}
        </span>
      </header>

      {alert && (
        <div className={`alert ${risk}`}>
          ⚠️ ALERTA: sinais vitais do tripulante em estado <strong>{risk.toUpperCase()}</strong>
        </div>
      )}

      <main className="grid">
        <TelemetryPanel latest={latest} history={history} connected={connected} />
        <ChatPanel />
        <VisionPanel />
      </main>

      <footer className="foot">Grupo 42 · GS 2026.1 · FIAP — POC AstroCopilot</footer>
    </div>
  )
}
