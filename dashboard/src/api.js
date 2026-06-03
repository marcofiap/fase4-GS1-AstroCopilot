// Cliente da API AstroCopilot (Frente 5).
// As URLs vêm do .env (VITE_API_URL / VITE_WS_URL) com fallback para localhost.

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

/** Monta URL absoluta para MP3/OGG servidos pelo backend (/media/voice, /media/samples). */
export function mediaUrl(path) {
  if (!path) return null
  if (path.startsWith('http')) return path
  return `${API}${path.startsWith('/') ? path : `/${path}`}`
}

// POST /api/agent/query  -> { answer, sources[], answer_audio_url? }
export async function askAgent(text, { withAudio = false, voiceProfile = 'leo' } = {}) {
  const r = await fetch(`${API}/api/agent/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      with_audio: withAudio,
      voice_profile: voiceProfile,
    }),
  })
  if (!r.ok) throw new Error('Falha ao consultar o agente')
  return r.json()
}

// GET /api/tts/ack -> { audio_url }  (MP3 fixo "Verificando")
export async function fetchAckAudio(voiceProfile = 'leo') {
  const r = await fetch(`${API}/api/tts/ack?voice_profile=${encodeURIComponent(voiceProfile)}`)
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || 'Falha ao carregar áudio de confirmação')
  }
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

// GET /api/alerts -> { alerts[], total }
export async function fetchAlerts(limit = 20) {
  const r = await fetch(`${API}/api/alerts?limit=${limit}`)
  if (!r.ok) throw new Error('Falha ao buscar alertas')
  return r.json()
}

// GET /api/audit -> { audit[], total }  (trilha de decisões do agente)
export async function fetchAudit(limit = 50) {
  const r = await fetch(`${API}/api/audit?limit=${limit}`)
  if (!r.ok) throw new Error('Falha ao buscar a trilha de auditoria')
  return r.json()
}

// POST /api/voice (multipart: audio) -> { transcript, answer_text, answer_audio_url, ... }
export async function askVoice(audioBlob, filename = 'piloto.ogg', voiceProfile = 'leo') {
  const fd = new FormData()
  fd.append('audio', audioBlob, filename)
  fd.append('voice_profile', voiceProfile)
  const r = await fetch(`${API}/api/voice`, { method: 'POST', body: fd })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || 'Falha no processamento de voz')
  }
  return r.json()
}

// POST /api/tts -> { audio_url }  (gTTS PT-BR da resposta do agente)
export async function synthesizeSpeech(text, voiceProfile = 'leo') {
  const r = await fetch(`${API}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice_profile: voiceProfile }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || 'Falha na síntese de voz')
  }
  return r.json()
}

/** Busca amostra do piloto versionada no backend e envia ao pipeline de voz. */
export async function fetchPilotSampleBlob(sampleFile) {
  const url = mediaUrl(`/media/samples/${sampleFile}`)
  const r = await fetch(url)
  if (!r.ok) throw new Error(`Amostra não encontrada: ${sampleFile}`)
  return r.blob()
}

export async function askPilotSample(sampleFile, voiceProfile = 'leo') {
  const blob = await fetchPilotSampleBlob(sampleFile)
  return askVoice(blob, sampleFile, voiceProfile)
}

// GET /api/voice/recordings -> { recordings[], max }
export async function fetchUserRecordings() {
  const r = await fetch(`${API}/api/voice/recordings`)
  if (!r.ok) throw new Error('Falha ao listar gravações')
  return r.json()
}

// POST /api/voice/recordings (multipart) -> metadados + audio_url
export async function saveUserRecording(audioBlob, filename = 'piloto.webm') {
  const fd = new FormData()
  fd.append('audio', audioBlob, filename)
  const r = await fetch(`${API}/api/voice/recordings`, { method: 'POST', body: fd })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || 'Falha ao salvar gravação')
  }
  return r.json()
}

export async function fetchUserRecordingBlob(recordingId) {
  const { recordings } = await fetchUserRecordings()
  const item = recordings.find((x) => x.id === recordingId)
  if (!item) throw new Error('Gravação não encontrada')
  const r = await fetch(mediaUrl(item.audio_url))
  if (!r.ok) throw new Error('Falha ao carregar gravação')
  return { meta: item, blob: await r.blob() }
}
