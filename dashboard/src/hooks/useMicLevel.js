import { useEffect, useState } from 'react'

/**
 * Nivel de volume do microfone (0–1) a partir de um MediaStream.
 * Usado para feedback visual durante gravacao.
 */
export function useMicLevel(stream) {
  const [level, setLevel] = useState(0)
  const [active, setActive] = useState(false)

  useEffect(() => {
    if (!stream) {
      setLevel(0)
      setActive(false)
      return undefined
    }

    let ctx
    let raf
    try {
      ctx = new AudioContext()
      const src = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 512
      analyser.smoothingTimeConstant = 0.75
      src.connect(analyser)
      const buf = new Uint8Array(analyser.frequencyBinCount)

      const tick = () => {
        analyser.getByteFrequencyData(buf)
        let sum = 0
        for (let i = 0; i < buf.length; i += 1) sum += buf[i]
        const avg = sum / buf.length / 255
        setLevel(avg)
        setActive(avg > 0.04)
        raf = requestAnimationFrame(tick)
      }
      tick()
    } catch {
      setLevel(0)
      setActive(false)
    }

    return () => {
      if (raf) cancelAnimationFrame(raf)
      ctx?.close?.()
    }
  }, [stream])

  return { level, active }
}