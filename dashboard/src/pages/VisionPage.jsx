import { Link } from 'react-router-dom'
import VisionPanel from '../components/VisionPanel'

export default function VisionPage() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>AstroCopilot <span>Visão — Análise de Painel</span></h1>
        <Link className="btn" to="/">← Voltar ao painel</Link>
      </header>

      <VisionPanel />

      <footer className="foot">Grupo 42 · GS 2026.1 · FIAP — POC AstroCopilot</footer>
    </div>
  )
}
