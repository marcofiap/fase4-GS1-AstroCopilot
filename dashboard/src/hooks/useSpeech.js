import { useRef, useState } from 'react'

// Reconhecimento de fala (STT) e síntese de voz (TTS) via Web Speech API do
// navegador. Funciona em Chrome/Edge sobre localhost ou HTTPS, em pt-BR.
// A Frente 2 pode depois trocar por Whisper/servidor via POST /api/voice.
const SpeechRecognition =
  typeof window !== 'undefined' &&
  (window.SpeechRecognition || window.webkitSpeechRecognition)

export function useSpeech({ lang = 'pt-BR' } = {}) {
  const [listening, setListening] = useState(false)
  const recRef = useRef(null)

  const sttSupported = !!SpeechRecognition
  const ttsSupported = typeof window !== 'undefined' && !!window.speechSynthesis

  function listen(onResult) {
    if (!SpeechRecognition) return
    const rec = new SpeechRecognition()
    rec.lang = lang
    rec.interimResults = false
    rec.maxAlternatives = 1
    rec.onresult = (e) => onResult(e.results[0][0].transcript)
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
    recRef.current = rec
    setListening(true)
    rec.start()
  }

  function stopListening() {
    recRef.current?.stop()
    setListening(false)
  }

  function speak(text) {
    if (!ttsSupported) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = lang
    window.speechSynthesis.speak(u)
  }

  function cancelSpeak() {
    if (ttsSupported) window.speechSynthesis.cancel()
  }

  return { listening, sttSupported, ttsSupported, listen, stopListening, speak, cancelSpeak }
}
