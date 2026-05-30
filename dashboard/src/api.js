// Cliente da API AstroCopilot (Frente 5).
// As URLs vêm do .env (VITE_API_URL / VITE_WS_URL) com fallback para localhost.

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

// POST /api/agent/query  -> { answer, sources[] }
export async function askAgent(text) {
  const r = await fetch(`${API}/api/agent/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!r.ok) throw new Error('Falha ao consultar o agente')
  return r.json()
}

// POST /api/vision (multipart: image) -> { objects[], ocr_text, description }
export async function analyzeImage(file) {
  const fd = new FormData()
  fd.append('image', file)
  const r = await fetch(`${API}/api/vision`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error('Falha na análise de imagem')
  return r.json()
}
