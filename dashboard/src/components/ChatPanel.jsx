import { useCallback, useEffect, useRef, useState } from 'react'
import {
  askAgent,
  askVoice,
  fetchPilotSampleBlob,
  fetchUserRecordingBlob,
  fetchAckAudio,
  fetchUserRecordings,
  mediaUrl,
  saveUserRecording,
  synthesizeSpeech,
} from '../api'
import { DEFAULT_ASTRO_VOICE } from '../config/astroVoices'
import { useMicLevel } from '../hooks/useMicLevel'
import { useSpeech } from '../hooks/useSpeech'
import ChatDebugPanel from './ChatDebugPanel'

const PILOT_SAMPLES = [
  { file: 'audio_piloto.ogg', label: 'Piloto 1' },
  { file: 'audio_piloto_2.ogg', label: 'Piloto 2' },
  { file: 'audio_piloto_3.ogg', label: 'Piloto 3' },
]

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ttsOn, setTtsOn] = useState(true)
  const [recording, setRecording] = useState(false)
  const [micStream, setMicStream] = useState(null)
  const [voiceProfile, setVoiceProfile] = useState(DEFAULT_ASTRO_VOICE)
  const [debugOpen, setDebugOpen] = useState(false)
  const [activeSample, setActiveSample] = useState(null)
  const [myRecordings, setMyRecordings] = useState([])

  const mediaRecRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)
  const pilotAudioRef = useRef(null)
  const ackAudioUrlRef = useRef(null)
  const chatLogRef = useRef(null)

  const { level: micLevel } = useMicLevel(micStream)

  const {
    awake, sttSupported, astroSpeaking,
    startWakeWord, stopWakeWord, playAudioUrl, cancelSpeak,
  } = useSpeech()

  function stopPilotPreview() {
    const a = pilotAudioRef.current
    if (a) {
      a.pause()
      a.currentTime = 0
      pilotAudioRef.current = null
    }
  }

  const refreshMyRecordings = useCallback(async () => {
    try {
      const data = await fetchUserRecordings()
      setMyRecordings(data.recordings || [])
    } catch {
      setMyRecordings([])
    }
  }, [])

  useEffect(() => {
    refreshMyRecordings()
  }, [refreshMyRecordings])

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight
    }
  }, [messages, loading])

  useEffect(() => {
    if (!ttsOn) {
      ackAudioUrlRef.current = null
      return
    }
    let cancelled = false
    fetchAckAudio(voiceProfile)
      .then((data) => {
        if (!cancelled) ackAudioUrlRef.current = mediaUrl(data?.audio_url)
      })
      .catch(() => {
        if (!cancelled) ackAudioUrlRef.current = null
      })
    return () => { cancelled = true }
  }, [voiceProfile, ttsOn])

  function playPreviewUrl(url) {
    stopPilotPreview()
    if (!url) return
    const audio = new Audio(url)
    pilotAudioRef.current = audio
    audio.play().catch(() => {})
  }

  function playPilotPreview(sampleFile) {
    playPreviewUrl(mediaUrl(`/media/samples/${sampleFile}`))
  }

  function stopMicStream() {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    setMicStream(null)
  }

  async function speakPhrase(text, audioPath) {
    if (!ttsOn || !text) return
    stopPilotPreview()
    const url = audioPath ? mediaUrl(audioPath) : null
    if (!url) {
      setMessages((m) => [
        ...m,
        {
          role: 'system',
          text: 'Áudio do Astro indisponível (Edge TTS). Reinicie o backend com edge-tts instalado.',
        },
      ])
      return
    }
    try {
      await playAudioUrl(url)
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'system', text: 'Não foi possível reproduzir o áudio do Astro.' },
      ])
    }
  }

  async function playAcknowledgment() {
    if (!ttsOn) return
    let url = ackAudioUrlRef.current
    if (!url) {
      try {
        const data = await fetchAckAudio(voiceProfile)
        url = mediaUrl(data?.audio_url)
        ackAudioUrlRef.current = url
      } catch { /* sem ack */ }
    }
    if (url) await playAudioUrl(url).catch(() => {})
  }

  async function speakAnswer(text, audioPath) {
    await speakPhrase(text, audioPath)
  }

  function stopAstro() {
    cancelSpeak()
    stopPilotPreview()
  }

  async function send(raw) {
    const text = (raw ?? '').trim()
    if (!text || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text }])
    setLoading(true)
    const ack = playAcknowledgment()
    try {
      const res = await askAgent(text, { withAudio: ttsOn, voiceProfile })
      await ack
      setMessages((m) => [...m, { role: 'bot', text: res.answer, sources: res.sources }])
      setLoading(false)
      let audioUrl = res.answer_audio_url
      if (ttsOn && !audioUrl) {
        const tts = await synthesizeSpeech(res.answer, voiceProfile).catch(() => null)
        audioUrl = tts?.audio_url
      }
      await speakAnswer(res.answer, audioUrl)
    } catch (err) {
      await ack.catch(() => {})
      setMessages((m) => [...m, { role: 'error', text: err.message }])
      setLoading(false)
    }
  }

  async function sendVoiceBlob(blob, filename, userLabel) {
    if (!blob?.size || loading) return
    setMessages((m) => [...m, { role: 'user', text: userLabel || 'Pergunta por voz' }])
    setLoading(true)
    const ack = playAcknowledgment()
    try {
      const res = await askVoice(blob, filename, voiceProfile)
      await ack
      const userLine = res.transcript
        ? `${res.transcript}${res.intent ? ` (${res.intent})` : ''}`
        : userLabel || 'Pergunta por voz'
      setMessages((m) => {
        const next = [...m]
        next[next.length - 1] = { role: 'user', text: userLine }
        next.push({ role: 'bot', text: res.answer_text, sources: res.sources })
        return next
      })
      setLoading(false)
      await speakAnswer(res.answer_text, res.answer_audio_url)
    } catch (err) {
      await ack.catch(() => {})
      setMessages((m) => [...m, { role: 'error', text: err.message }])
      setLoading(false)
    } finally {
      setActiveSample(null)
    }
  }

  async function runPilotSample(sampleFile, label) {
    if (loading) return
    setActiveSample(sampleFile)
    setMessages((m) => [...m, { role: 'user', text: `[${label}] reproduzindo áudio do piloto…` }])
    setLoading(true)
    playPilotPreview(sampleFile)
    const ack = playAcknowledgment()

    try {
      const blob = await fetchPilotSampleBlob(sampleFile)
      const res = await askVoice(blob, sampleFile, voiceProfile)
      await ack
      const userLine = res.transcript
        ? `[${label}] ${res.transcript}${res.intent ? ` (${res.intent})` : ''}`
        : `[${label}]`
      setMessages((m) => {
        const next = [...m]
        next[next.length - 1] = { role: 'user', text: userLine }
        next.push({ role: 'bot', text: res.answer_text, sources: res.sources })
        return next
      })
      setLoading(false)
      await speakAnswer(res.answer_text, res.answer_audio_url)
    } catch (err) {
      await ack.catch(() => {})
      setMessages((m) => [...m, { role: 'error', text: err.message }])
      setLoading(false)
      stopPilotPreview()
    } finally {
      setActiveSample(null)
    }
  }

  async function runUserRecording(rec) {
    if (loading) return
    const key = `user:${rec.id}`
    setActiveSample(key)
    setMessages((m) => [...m, { role: 'user', text: `[${rec.label}] reproduzindo sua gravação…` }])
    setLoading(true)
    playPreviewUrl(mediaUrl(rec.audio_url))
    const ack = playAcknowledgment()

    try {
      const { meta, blob } = await fetchUserRecordingBlob(rec.id)
      const res = await askVoice(blob, meta.filename, voiceProfile)
      await ack
      const userLine = res.transcript
        ? `[${rec.label}] ${res.transcript}${res.intent ? ` (${res.intent})` : ''}`
        : `[${rec.label}]`
      setMessages((m) => {
        const next = [...m]
        next[next.length - 1] = { role: 'user', text: userLine }
        next.push({ role: 'bot', text: res.answer_text, sources: res.sources })
        return next
      })
      setLoading(false)
      await speakAnswer(res.answer_text, res.answer_audio_url)
    } catch (err) {
      await ack.catch(() => {})
      setMessages((m) => [...m, { role: 'error', text: err.message }])
      setLoading(false)
      stopPilotPreview()
    } finally {
      setActiveSample(null)
    }
  }

  function toggleAstro() {
    if (awake) {
      stopWakeWord()
      return
    }
    startWakeWord((command) => send(command))
  }

  function onSubmit(e) {
    e.preventDefault()
    if (astroSpeaking) {
      stopAstro()
      return
    }
    send(input)
  }

  async function toggleRecord() {
    if (recording) {
      mediaRecRef.current?.stop()
      return
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setMessages((m) => [...m, { role: 'error', text: 'Gravação não suportada neste navegador.' }])
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      setMicStream(stream)
      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      const rec = new MediaRecorder(stream, { mimeType: mime })
      chunksRef.current = []
      rec.ondataavailable = (e) => { if (e.data.size) chunksRef.current.push(e.data) }
      rec.onstop = async () => {
        stopMicStream()
        setRecording(false)
        const blob = new Blob(chunksRef.current, { type: mime })
        if (!blob.size) return
        try {
          const saved = await saveUserRecording(blob, 'piloto.webm')
          await refreshMyRecordings()
          playPreviewUrl(mediaUrl(saved.audio_url))
          setMessages((m) => [
            ...m,
            {
              role: 'system',
              text: `Gravação salva como "${saved.label}". Clique no chip para ouvir e enviar ao Astro; botão direito: só ouvir.`,
            },
          ])
        } catch (err) {
          setMessages((m) => [...m, { role: 'error', text: err.message }])
        }
      }
      mediaRecRef.current = rec
      setRecording(true)
      rec.start()
    } catch {
      stopMicStream()
      setMessages((m) => [...m, { role: 'error', text: 'Permissão de microfone negada.' }])
    }
  }

  const micMode = recording ? 'recording' : awake ? 'wake' : 'idle'
  const micLabel = recording
    ? 'Gravando — fale agora'
    : awake
      ? 'Astro ouvindo — diga Astro + pergunta'
      : ''

  return (
    <section className="card chat">
      <header className="astro-bar">
        <button
          type="button"
          className={`astro-on-btn ${awake ? 'on' : ''}`}
          onClick={toggleAstro}
          disabled={!sttSupported || recording || loading}
          title={sttSupported ? 'Diga "Astro" seguido da sua pergunta' : 'Requer Chrome ou Edge'}
        >
          {awake ? 'Astro On' : 'Astro Off'}
        </button>
        <div className="pilot-chips" role="group" aria-label="Amostras de voz">
          {PILOT_SAMPLES.map((s) => (
            <button
              key={s.file}
              type="button"
              className={`pilot-chip ${activeSample === s.file ? 'active' : ''}`}
              disabled={loading}
              title="Ouvir piloto e enviar ao Astro"
              onClick={() => runPilotSample(s.file, s.label)}
              onContextMenu={(e) => {
                e.preventDefault()
                playPilotPreview(s.file)
              }}
            >
              {s.label}
            </button>
          ))}
          {myRecordings.map((rec) => (
            <button
              key={rec.id}
              type="button"
              className={`pilot-chip user-chip ${activeSample === `user:${rec.id}` ? 'active' : ''}`}
              disabled={loading}
              title="Ouvir sua gravação e enviar ao Astro (botão direito: só ouvir)"
              onClick={() => runUserRecording(rec)}
              onContextMenu={(e) => {
                e.preventDefault()
                playPreviewUrl(mediaUrl(rec.audio_url))
              }}
            >
              {rec.label}
            </button>
          ))}
        </div>
      </header>

      {awake && !recording && (
        <p className="wake-note">
          Diga <b>Astro</b> + sua pergunta. Ex.: <i>Astro, procedimento em caso de despressurização?</i>
        </p>
      )}

      {astroSpeaking && (
        <p className="astro-speaking" role="status">
          Astro falando… use <b>Parar</b> para interromper.
        </p>
      )}

      <div className="chat-log" ref={chatLogRef}>
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
        {loading && <div className="msg bot"><p>…Astro consultando manuais</p></div>}
      </div>

      <form className="chat-input" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pergunta por texto (opcional)"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading && !astroSpeaking}
          className={astroSpeaking ? 'btn-parar' : ''}
        >
          {astroSpeaking ? 'Parar' : 'Enviar'}
        </button>
      </form>

      <ChatDebugPanel
        debugOpen={debugOpen}
        onToggle={setDebugOpen}
        voiceProfile={voiceProfile}
        onVoiceProfileChange={setVoiceProfile}
        ttsOn={ttsOn}
        onTtsToggle={() => setTtsOn((v) => { if (v) cancelSpeak(); return !v })}
        recording={recording}
        onToggleRecord={toggleRecord}
        loading={loading}
        astroSpeaking={astroSpeaking}
        micMode={micMode}
        micLevel={micLevel}
        micLabel={micLabel}
        sttSupported={sttSupported}
        awake={awake}
      />
    </section>
  )
}