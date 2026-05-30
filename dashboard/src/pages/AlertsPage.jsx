import { Link } from 'react-router-dom'
import AlertLogPanel from '../components/AlertLogPanel'

export default function AlertsPage() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>AstroCopilot <span>Log de Alertas</span></h1>
        <Link className="btn" to="/">← Voltar ao painel</Link>
      </header>

      <AlertLogPanel limit={100} fullPage />

      <footer className="foot">Grupo 42 · GS 2026.1 · FIAP — POC AstroCopilot</footer>
    </div>
  )
}
