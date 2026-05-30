import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts'

const PALETTE = ['#38bdf8', '#f59e0b', '#a78bfa', '#34d399', '#f472b6']

const RISK = {
  normal: { color: '#22c55e', label: 'NORMAL' },
  fadiga: { color: '#f59e0b', label: 'FADIGA' },
  risco: { color: '#ef4444', label: 'RISCO' },
}

function CrewCard({ c, color }) {
  const risk = RISK[c.risk_level] || RISK.normal
  return (
    <div className="crew-card" style={{ borderColor: color }}>
      <div className="crew-head">
        <span className="crew-dot" style={{ background: color }} />
        <div className="crew-id">
          <strong>{c.name}</strong>
          <small>{c.role}</small>
        </div>
        <span className="risk-badge" style={{ background: risk.color }}>{risk.label}</span>
      </div>
      <div className="crew-vitals">
        <span>{c.hr}<small> bpm</small></span>
        <span>{c.spo2}<small> %</small></span>
        <span>{c.temp}<small> °C</small></span>
      </div>
    </div>
  )
}

export default function TelemetryPanel({ crew, history, connected }) {
  return (
    <section className="card">
      <header className="card-head">
        <h2>Telemetria da Tripulação</h2>
        <span className={`dot ${connected ? 'on' : 'off'}`}>
          {connected ? 'ao vivo' : 'desconectado'}
        </span>
      </header>

      <div className="crew-grid">
        {crew.map((c, i) => (
          <CrewCard key={c.id} c={c} color={PALETTE[i % PALETTE.length]} />
        ))}
      </div>

      <div className="chart">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a44" />
            <XAxis dataKey="time" tick={{ fill: '#7c8db5', fontSize: 11 }} minTickGap={40} />
            <YAxis tick={{ fill: '#7c8db5', fontSize: 11 }} domain={['auto', 'auto']} />
            <Tooltip contentStyle={{ background: '#0b1226', border: '1px solid #1e2a44' }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {crew.map((c, i) => (
              <Line
                key={c.id}
                type="monotone"
                dataKey={c.id}
                name={c.name}
                stroke={PALETTE[i % PALETTE.length]}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
        <p className="chart-cap">Frequência cardíaca (bpm) por tripulante</p>
      </div>
    </section>
  )
}
