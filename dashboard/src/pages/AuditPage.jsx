import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchAudit } from '../api'

const CHANNEL = {
  text: { label: 'TEXTO', color: '#38bdf8' },
  voice: { label: 'VOZ', color: '#a78bfa' },
  vision: { label: 'VISÃO', color: '#34d399' },
}

export default function AuditPage() {
  const [audit, setAudit] = useState([])
  const [total, setTotal] = useState(0)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const d = await fetchAudit(100)
        if (active) { setAudit(d.audit); setTotal(d.total) }
      } catch {
        /* backend offline — ignora */
      }
    }
    load()
    const id = setInterval(load, 4000)
    return () => { active = false; clearInterval(id) }
  }, [])

  return (
    <div className="app">
      <header className="topbar">
        <h1>AstroCopilot <span>Trilha de Auditoria</span></h1>
        <Link className="btn" to="/">← Voltar ao painel</Link>
      </header>

      <section className="card">
        <header className="card-head">
          <h2>Decisões do Copiloto (governança de IA)</h2>
          <span className="muted">{total} registros</span>
        </header>

        <p className="muted audit-intro">
          Cada consulta ao agente é registrada com pergunta, resposta, fontes citadas,
          canal e horário — rastreabilidade exigida pela governança de IA.
        </p>

        {audit.length === 0 ? (
          <p className="muted">Nenhuma decisão registrada ainda. Use o Copiloto no painel. 🛰️</p>
        ) : (
          <ul className="audit-log">
            {audit.map((a, i) => {
              const ch = CHANNEL[a.channel] || CHANNEL.text
              return (
                <li key={i} className="audit-row">
                  <div className="audit-meta">
                    <span className="audit-channel" style={{ background: ch.color }}>{ch.label}</span>
                    <span className="audit-time">{new Date(a.ts).toLocaleString()}</span>
                  </div>
                  <p className="audit-q"><b>P:</b> {a.question}</p>
                  <p className="audit-a"><b>R:</b> {a.answer}</p>
                  {a.sources?.length > 0 && (
                    <ul className="audit-sources">
                      {a.sources.map((s, j) => <li key={j}>{s}</li>)}
                    </ul>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </section>

      <footer className="foot">Grupo 42 · GS 2026.1 · FIAP — POC AstroCopilot</footer>
    </div>
  )
}
