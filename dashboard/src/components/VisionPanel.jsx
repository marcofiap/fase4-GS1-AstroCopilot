import { useState } from 'react'
import { analyzeImage } from '../api'

export default function VisionPanel() {
  const [result, setResult] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function onFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setPreview(URL.createObjectURL(file))
    setResult(null); setError(null); setLoading(true)
    try {
      setResult(await analyzeImage(file))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card">
      <header className="card-head"><h2>📷 Visão — Análise de Painel</h2></header>

      <label className="upload">
        <input type="file" accept="image/*" onChange={onFile} hidden />
        {preview ? <img src={preview} alt="preview" /> : <span>Clique para enviar uma imagem</span>}
      </label>

      {loading && <p className="muted">Analisando imagem…</p>}
      {error && <p className="msg error">{error}</p>}
      {result && (
        <div className="vision-result">
          <p><strong>Descrição:</strong> {result.description}</p>
          <p><strong>OCR:</strong> <code>{result.ocr_text}</code></p>
          <p><strong>Componentes:</strong> {result.objects?.join(', ')}</p>
        </div>
      )}
    </section>
  )
}
