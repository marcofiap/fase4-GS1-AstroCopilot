import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const RISK = {
  normal: { color: '#22c55e', label: 'NORMAL' },
  fadiga: { color: '#f59e0b', label: 'FADIGA' },
  risco: { color: '#ef4444', label: 'RISCO' },
}

function Metric({ label, value, unit }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value">
        {value ?? '--'}<small>{unit}</small>
      </span>
    </div>
  )
}

export default function TelemetryPanel({ latest, history, connected }) {
  const risk = RISK[latest?.risk_level] || RISK.normal

  return (
    <section className="card">
      <header className="card-head">
        <h2>⌚ Telemetria do Tripulante</h2>
        <span className={`dot ${connected ? 'on' : 'off'}`}>
          {connected ? 'ao vivo' : 'desconectado'}
        </span>
      </header>

      <div className="metrics">
        <Metric label="Batimentos" value={latest?.hr} unit=" bpm" />
        <Metric label="SpO₂" value={latest?.spo2} unit=" %" />
        <Metric label="Temperatura" value={latest?.temp} unit=" °C" />
        <div className="metric">
          <span className="metric-label">Status</span>
          <span className="risk-badge" style={{ background: risk.color }}>
            {risk.label}
          </span>
        </div>
      </div>

      <div className="chart">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a44" />
            <XAxis dataKey="time" tick={{ fill: '#7c8db5', fontSize: 11 }} minTickGap={40} />
            <YAxis tick={{ fill: '#7c8db5', fontSize: 11 }} domain={['auto', 'auto']} />
            <Tooltip contentStyle={{ background: '#0b1226', border: '1px solid #1e2a44' }} />
            <Line type="monotone" dataKey="hr" stroke="#ef4444" dot={false} name="HR" isAnimationActive={false} />
            <Line type="monotone" dataKey="spo2" stroke="#38bdf8" dot={false} name="SpO₂" isAnimationActive={false} />
            <Line type="monotone" dataKey="temp" stroke="#f59e0b" dot={false} name="Temp" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
