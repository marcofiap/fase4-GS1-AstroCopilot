import { useTelemetry } from './hooks/useTelemetry'
import TelemetryPanel from './components/TelemetryPanel'
import ChatPanel from './components/ChatPanel'
import VisionPanel from './components/VisionPanel'

const RANK = { normal: 0, fadiga: 1, risco: 2 }

export default function App() {
  const { crew, history, connected } = useTelemetry()

  const inAlert = crew.filter((c) => c.risk_level && c.risk_level !== 'normal')
  const worst = inAlert.reduce(
    (acc, c) => (RANK[c.risk_level] > RANK[acc] ? c.risk_level : acc),
    'normal',
  )

  return (
    <div className="app">
      <header className="topbar">
        <h1>AstroCopilot <span>Mission Control</span></h1>
        <span className={`dot ${connected ? 'on' : 'off'}`}>
          backend {connected ? 'conectado' : 'offline'}
        </span>
      </header>

      {inAlert.length > 0 && (
        <div className={`alert ${worst}`}>
          ⚠️ ALERTA: {inAlert.map((c) => c.name).join(', ')}
          {inAlert.length > 1 ? ' em estado crítico' : ` em estado ${worst.toUpperCase()}`}
        </div>
      )}

      <main className="grid">
        <TelemetryPanel crew={crew} history={history} connected={connected} />
        <ChatPanel />
        <VisionPanel />
      </main>

      <footer className="foot">Grupo 42 · GS 2026.1 · FIAP — POC AstroCopilot</footer>
    </div>
  )
}
