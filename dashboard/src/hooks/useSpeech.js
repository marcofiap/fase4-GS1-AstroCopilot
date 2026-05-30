import { useCallback, useEffect, useRef, useState } from 'react'

// Reconhecimento de fala (STT) e síntese de voz (TTS) via Web Speech API do
// navegador. Funciona em Chrome/Edge sobre localhost ou HTTPS, em pt-BR.
// A Frente 2 pode depois trocar por Whisper/servidor via POST /api/voice.
const SpeechRecognition =
  typeof window !== 'undefined' &&
  (window.SpeechRecognition || window.webkitSpeechRecognition)

// Palavra de ativação ("wake word"), como "Alexa"/"Ok Google".
// O astronauta diz: "Astra, qual o procedimento...?" e o Copiloto responde.
const WAKE_WORD = 'astra'

// Remove acentos e pontuação para casar a wake word de forma tolerante
// ("Ástra," / "astra." / "Astra" → "astra").
function normalize(s) {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
}

export function useSpeech({ lang = 'pt-BR', wakeWord = WAKE_WORD } = {}) {
  const [listening, setListening] = useState(false)
  const [awake, setAwake] = useState(false) // escuta contínua pela wake word
  const recRef = useRef(null)
  const wakeRecRef = useRef(null)
  const wakeOnRef = useRef(false) // intenção do usuário (sobrevive a reinícios)
  const onCommandRef = useRef(null)

  const sttSupported = !!SpeechRecognition
  const ttsSupported = typeof window !== 'undefined' && !!window.speechSynthesis

  // ---- Captura única (botão "Falar") -------------------------------------
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

  // ---- Escuta contínua pela wake word "Astra" ----------------------------
  const startWakeWord = useCallback(
    (onCommand) => {
      if (!SpeechRecognition) return
      onCommandRef.current = onCommand
      wakeOnRef.current = true
      setAwake(true)

      const rec = new SpeechRecognition()
      rec.lang = lang
      rec.continuous = true
      rec.interimResults = false
      rec.maxAlternatives = 1

      rec.onresult = (e) => {
        const last = e.results[e.results.length - 1]
        if (!last.isFinal) return
        const heard = normalize(last[0].transcript)
        const idx = heard.indexOf(wakeWord)
        if (idx === -1) return // não disse "Astra" — ignora
        // Tudo após a wake word vira a pergunta.
        const after = heard.slice(idx + wakeWord.length).replace(/^[\s,.:!?]+/, '')
        if (after) onCommandRef.current?.(after)
      }

      // Mantém vivo: o reconhecimento contínuo encerra sozinho de tempos em
      // tempos; reiniciamos enquanto o usuário não desligar.
      rec.onend = () => {
        if (wakeOnRef.current) {
          try { rec.start() } catch { /* já iniciando */ }
        } else {
          setAwake(false)
        }
      }
      rec.onerror = (ev) => {
        // "not-allowed"/"service-not-allowed" = sem permissão → desliga de vez.
        if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
          wakeOnRef.current = false
          setAwake(false)
        }
      }

      wakeRecRef.current = rec
      try { rec.start() } catch { /* já ativo */ }
    },
    [lang, wakeWord],
  )

  const stopWakeWord = useCallback(() => {
    wakeOnRef.current = false
    wakeRecRef.current?.stop()
    setAwake(false)
  }, [])

  // Limpa ao desmontar.
  useEffect(() => {
    return () => {
      wakeOnRef.current = false
      wakeRecRef.current?.stop()
      recRef.current?.stop()
    }
  }, [])

  // ---- Síntese de voz (TTS) ----------------------------------------------
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

  return {
    listening,
    awake,
    sttSupported,
    ttsSupported,
    listen,
    stopListening,
    startWakeWord,
    stopWakeWord,
    speak,
    cancelSpeak,
  }
}
