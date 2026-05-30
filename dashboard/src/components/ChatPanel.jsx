import { useState } from 'react'
import { askAgent } from '../api'

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    { role: 'system', text: 'Copiloto online. Faça uma pergunta sobre o manual da missão.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function send(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      const res = await askAgent(text)
      setMessages((m) => [...m, { role: 'bot', text: res.answer, sources: res.sources }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: err.message }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card chat">
      <header className="card-head"><h2>🧠 Copiloto (RAG)</h2></header>

      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <p>{m.text}</p>
            {m.sources?.length > 0 && (
              <ul className="sources">
                {m.sources.map((s, j) => <li key={j}>📄 {s}</li>)}
              </ul>
            )}
          </div>
        ))}
        {loading && <div className="msg bot"><p>…consultando manuais</p></div>}
      </div>

      <form className="chat-input" onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ex: procedimento em caso de despressurização?"
        />
        <button type="submit" disabled={loading}>Enviar</button>
      </form>
    </section>
  )
}
