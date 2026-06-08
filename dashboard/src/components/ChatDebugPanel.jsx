import { ASTRO_VOICE_PROFILES } from '../config/astroVoices'
import MicFeedback from './MicFeedback'

export default function ChatDebugPanel({
  debugOpen,
  onToggle,
  voiceProfile,
  onVoiceProfileChange,
  ttsOn,
  onTtsToggle,
  recording,
  onToggleRecord,
  loading,
  astroSpeaking,
  micMode,
  micLevel,
  micLabel,
  sttSupported,
  awake,
}) {
  return (
    <details
      className="debug-drawer"
      open={debugOpen}
      onToggle={(e) => onToggle(e.currentTarget.open)}
    >
      <summary>Debug e opções avançadas</summary>
      <div className="debug-drawer-body">
        <label className="debug-field">
          <span>Tom da voz do Astro</span>
          <select
            value={voiceProfile}
            onChange={(e) => onVoiceProfileChange(e.target.value)}
            disabled={loading || astroSpeaking}
          >
            {ASTRO_VOICE_PROFILES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {p.tagline}
              </option>
            ))}
          </select>
        </label>

        <div className="debug-actions">
          <button
            type="button"
            className={`icon-btn mic ${recording ? 'rec' : ''}`}
            onClick={onToggleRecord}
            disabled={loading || astroSpeaking || awake}
          >
            {recording ? 'Parar gravação' : 'Gravar minha voz (salva no topo)'}
          </button>
          <button
            type="button"
            className={`icon-btn ${ttsOn ? 'on' : ''}`}
            onClick={onTtsToggle}
          >
            {ttsOn ? 'Voz Astro: ligada' : 'Voz Astro: desligada'}
          </button>
        </div>

        <MicFeedback mode={micMode} level={micLevel} label={micLabel} />

        {!sttSupported && (
          <p className="muted mic-note">Wake word requer Chrome ou Edge.</p>
        )}
      </div>
    </details>
  )
}