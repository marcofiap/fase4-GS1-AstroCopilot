import { useEffect, useRef, useState } from 'react'
import { WS_URL } from '../api'

// Conecta ao WebSocket /ws/telemetry e mantém:
//  - crew:    estado atual de cada tripulante (array)
//  - history: linhas {time, [crew_id]: hr} para o gráfico multi-linha
export function useTelemetry(maxPoints = 30) {
  const [crew, setCrew] = useState([])
  const [history, setHistory] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/telemetry`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    ws.onmessage = (e) => {
      const frame = JSON.parse(e.data) // { ts, crew: [...] }
      setCrew(frame.crew)
      const row = { time: new Date(frame.ts).toLocaleTimeString() }
      frame.crew.forEach((c) => {
        row[c.id] = c.hr          // série de batimentos
        row[`${c.id}_rad`] = c.radiation // série de radiação
      })
      setHistory((prev) => [...prev.slice(-(maxPoints - 1)), row])
    }

    return () => ws.close()
  }, [maxPoints])

  return { crew, history, connected }
}
