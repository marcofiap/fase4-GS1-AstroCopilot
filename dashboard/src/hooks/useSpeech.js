import { useCallback, useEffect, useRef, useState } from 'react'

const SpeechRecognition =
  typeof window !== 'undefined' &&
  (window.SpeechRecognition || window.webkitSpeechRecognition)

/** Wake word: "Astro" + pergunta (ex.: "Astro, como despressurizar a cabine?"). */
export const WAKE_WORD = 'astro'

function normalize(s) {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
}

/** Velocidade padrão do Astro no fallback do navegador (1,5×). */
const ASTRO_SPEECH_RATE = 1.5

/** Preferência de voz masculina pt-BR no fallback do navegador (quando Edge TTS falha). */
const MALE_PT_HINTS = /antonio|donato|daniel|male|masculin|homem|google português do brasil/i
const FEMALE_PT_HINTS = /francisca|thalita|maria|female|feminina|mulher|luciana/i

function pickPtVoice(voices, preferMale = true) {
  const pt = voices.filter((v) => v.lang?.toLowerCase().startsWith('pt'))
  if (!pt.length) return null
  if (preferMale) {
    const male = pt.find((v) => MALE_PT_HINTS.test(v.name))
    if (male) return male
    const notFemale = pt.find((v) => !FEMALE_PT_HINTS.test(v.name))
    if (notFemale) return notFemale
  }
  return pt[0]
}

export function useSpeech({ lang = 'pt-BR', wakeWord = WAKE_WORD } = {}) {
  const [listening, setListening] = useState(false)
  const [awake, setAwake] = useState(false)
  const [astroSpeaking, setAstroSpeaking] = useState(false)
  const recRef = useRef(null)
  const wakeRecRef = useRef(null)
  const wakeOnRef = useRef(false)
  const onCommandRef = useRef(null)
  const audioRef = useRef(null)
  const speakGenRef = useRef(0)

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

  const startWakeWord = useCallback(
    (onCommand) => {
      if (!SpeechRecognition) return
      onCommandRef.current = onCommand
      wakeOnRef.current = true
      setAwake(true)
    },
    [],
  )

  const stopWakeWord = useCallback(() => {
    wakeOnRef.current = false
    setAwake(false)
  }, [])

  useEffect(() => {
    if (!SpeechRecognition) return

    let rec = null
    let retryTimeout = null
    let active = false

    const startRec = () => {
      if (!rec || active) return
      try {
        rec.start()
        active = true
      } catch (err) {
        console.warn('Astro SpeechRecognition start failed:', err)
      }
    }

    const shouldRun = awake && !astroSpeaking

    if (shouldRun) {
      rec = new SpeechRecognition()
      rec.lang = lang
      rec.continuous = true
      rec.interimResults = false
      rec.maxAlternatives = 1

      rec.onresult = (e) => {
        const last = e.results[e.results.length - 1]
        if (!last.isFinal) return
        const heard = normalize(last[0].transcript)
        const idx = heard.indexOf(wakeWord)
        if (idx === -1) return
        const after = heard.slice(idx + wakeWord.length).replace(/^[\s,.:!?]+/, '')
        if (after) onCommandRef.current?.(after)
      }

      rec.onerror = (ev) => {
        console.warn('Astro SpeechRecognition error:', ev.error)
        if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
          wakeOnRef.current = false
          setAwake(false)
        }
      }

      rec.onend = () => {
        active = false
        if (wakeOnRef.current && !astroSpeaking) {
          retryTimeout = setTimeout(() => {
            startRec()
          }, 1000)
        }
      }

      startRec()
      wakeRecRef.current = rec
    } else {
      wakeRecRef.current = null
    }

    return () => {
      if (retryTimeout) clearTimeout(retryTimeout)
      if (rec) {
        rec.onresult = null
        rec.onerror = null
        rec.onend = null
        try {
          rec.abort()
        } catch (err) {
          // ignore
        }
      }
    }
  }, [awake, astroSpeaking, lang, wakeWord])

  useEffect(() => {
    return () => {
      recRef.current?.stop()
    }
  }, [])

  const endSpeaking = useCallback((gen) => {
    if (gen === speakGenRef.current) setAstroSpeaking(false)
  }, [])

  const stopPlayback = useCallback(() => {
    speakGenRef.current += 1
    const audio = audioRef.current
    if (audio) {
      audio.onended = null
      audio.onerror = null
      audio.pause()
      audio.currentTime = 0
      audioRef.current = null
    }
    if (ttsSupported) window.speechSynthesis.cancel()
  }, [ttsSupported])

  const cancelSpeak = useCallback(() => {
    stopPlayback()
    setAstroSpeaking(false)
  }, [stopPlayback])

  const stopPlaybackRef = useRef(stopPlayback)
  stopPlaybackRef.current = stopPlayback

  useEffect(() => {
    return () => {
      stopPlaybackRef.current()
      setAstroSpeaking(false)
    }
  }, [])

  function speak(text, { preferMale = true } = {}) {
    if (!ttsSupported) return Promise.resolve()
    stopPlayback()
    const gen = speakGenRef.current
    setAstroSpeaking(true)
    return new Promise((resolve) => {
      const u = new SpeechSynthesisUtterance(text)
      u.lang = lang
      u.rate = ASTRO_SPEECH_RATE
      const assignVoice = () => {
        const picked = pickPtVoice(window.speechSynthesis.getVoices(), preferMale)
        if (picked) u.voice = picked
      }
      assignVoice()
      window.speechSynthesis.onvoiceschanged = assignVoice
      u.onend = () => {
        window.speechSynthesis.onvoiceschanged = null
        endSpeaking(gen)
        resolve()
      }
      u.onerror = () => {
        window.speechSynthesis.onvoiceschanged = null
        endSpeaking(gen)
        resolve()
      }
      window.speechSynthesis.speak(u)
    })
  }

  const playAudioUrl = useCallback((url) => {
    if (!url) return Promise.resolve()
    stopPlayback()
    const gen = speakGenRef.current
    setAstroSpeaking(true)
    const audio = new Audio(url)
    audioRef.current = audio
    return new Promise((resolve) => {
      const finish = () => {
        if (gen !== speakGenRef.current) {
          resolve()
          return
        }
        audioRef.current = null
        endSpeaking(gen)
        resolve()
      }
      audio.onended = finish
      audio.onerror = () => {
        endSpeaking(gen)
        resolve()
      }
      audio.play().catch(() => {
        endSpeaking(gen)
        resolve()
      })
    })
  }, [stopPlayback, endSpeaking])

  return {
    listening,
    awake,
    astroSpeaking,
    sttSupported,
    ttsSupported,
    listen,
    stopListening,
    startWakeWord,
    stopWakeWord,
    speak,
    playAudioUrl,
    cancelSpeak,
  }
}