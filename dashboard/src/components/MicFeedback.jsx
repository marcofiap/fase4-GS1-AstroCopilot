const BAR_COUNT = 12

export default function MicFeedback({ mode = 'idle', level = 0, label }) {
  const isRecording = mode === 'recording'
  const isWake = mode === 'wake'
  const visible = isRecording || isWake

  if (!visible) return null

  const bars = Array.from({ length: BAR_COUNT }, (_, i) => {
    const threshold = (i + 1) / BAR_COUNT
    const lit = isRecording ? level >= threshold * 0.35 : isWake
    return lit
  })

  return (
    <div
      className={`mic-feedback ${mode}`}
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <span className={`mic-feedback-dot ${isRecording && level > 0.05 ? 'hot' : ''}`} />
      <div className="mic-feedback-bars" aria-hidden="true">
        {bars.map((lit, i) => (
          <span
            key={i}
            className={`mic-bar ${lit ? 'on' : ''}`}
            style={isRecording ? { '--h': `${20 + level * 80 * (1 - i / BAR_COUNT)}%` } : undefined}
          />
        ))}
      </div>
      <span className="mic-feedback-label">{label}</span>
    </div>
  )
}