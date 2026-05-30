import { useState } from 'react'
import { askAgent } from '../api'
import { useSpeech } from '../hooks/useSpeech'

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    { role: 'system', text: 'Copiloto online. Diga "Astra" para ativar por voz, ou pergunte por texto.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ttsOn, setTtsOn] = useState(true)

  const {
    listening, awake, sttSupported, ttsSupported,
    listen, stopListening, startWakeWord, stopWakeWord, speak, cancelSpeak,
  } = useSpeech()

  async function send(raw) {
    const text = (raw ?? '').trim()
    if (!text || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      const res = await askAgent(text)
      setMessages((m) => [...m, { role: 'bot', text: res.answer, sources: res.sources }])
      if (ttsOn) speak(res.answer) // lê a resposta em voz alta
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: err.message }])
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    send(input)
  }

  function onMic() {
    if (listening) { stopListening(); return }
    listen((text) => { setInput(text); send(text) }) // transcreve e já envia
  }

  function toggleWake() {
    if (awake) { stopWakeWord(); return }
    // Escuta contínua: ao ouvir "Astra ...", envia o que vier depois.
    startWakeWord((command) => { setInput(command); send(command) })
  }

  function toggleTts() {
    setTtsOn((v) => {
      if (v) cancelSpeak() // desligando: interrompe fala atual
      return !v
    })
  }

  return (
    <section className="card chat">
      <header className="card-head">
        <h2>Copiloto (RAG)</h2>
        <div className="head-actions">
          {sttSupported && (
            <button
              type="button"
              className={`icon-btn wake ${awake ? 'on' : ''}`}
              onClick={toggleWake}
              title='Ativação por voz: diga "Astra" para perguntar'
            >
              {awake ? 'Astra: ouvindo' : 'Astra: OFF'}
            </button>
          )}
          {ttsSupported && (
            <button
              type="button"
              className={`icon-btn ${ttsOn ? 'on' : ''}`}
              onClick={toggleTts}
              title="Ler respostas em voz alta"
            >
              {ttsOn ? 'Voz: ON' : 'Voz: OFF'}
            </button>
          )}
        </div>
      </header>

      {awake && (
        <p className="wake-note">
          🎙️ Diga <b>"Astra"</b> seguido da sua pergunta. Ex: <i>"Astra, procedimento em caso de despressurização?"</i>
        </p>
      )}

      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <p>{m.text}</p>
            {m.sources?.length > 0 && (
              <ul className="sources">
                {m.sources.map((s, j) => <li key={j}>{s}</li>)}
              </ul>
            )}
          </div>
        ))}
        {loading && <div className="msg bot"><p>…consultando manuais</p></div>}
      </div>

      <form className="chat-input" onSubmit={onSubmit}>
        {sttSupported && (
          <button
            type="button"
            className={`icon-btn mic ${listening ? 'rec' : ''}`}
            onClick={onMic}
            title="Falar uma pergunta"
          >
            {listening ? '● Ouvindo' : 'Falar'}
          </button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={listening ? 'Ouvindo…' : 'Ex: procedimento em caso de despressurização?'}
        />
        <button type="submit" disabled={loading}>Enviar</button>
      </form>

      {!sttSupported && (
        <p className="muted mic-note">
          Entrada por voz não suportada neste navegador (use Chrome ou Edge).
        </p>
      )}
    </section>
  )
}
