import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
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
      <div className="crew-extra">
        <span>Resp <b>{c.resp}</b> rpm</span>
        <span>Rad <b>{c.radiation}</b> µSv/h</span>
        <span>Bat <b>{c.battery}</b>%</span>
      </div>
    </div>
  )
}

function CrewChart({ crew, history, suffix, caption, variant = 'line' }) {
  const isArea = variant === 'area'
  const Chart = isArea ? AreaChart : LineChart
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={200}>
        <Chart data={history}>
          <defs>
            {isArea && crew.map((c, i) => {
              const color = PALETTE[i % PALETTE.length]
              return (
                <linearGradient key={c.id} id={`grad-${c.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.5} />
                  <stop offset="100%" stopColor={color} stopOpacity={0.04} />
                </linearGradient>
              )
            })}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2a44" />
          <XAxis dataKey="time" tick={{ fill: '#7c8db5', fontSize: 11 }} minTickGap={40} />
          <YAxis tick={{ fill: '#7c8db5', fontSize: 11 }} domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ background: '#0b1226', border: '1px solid #1e2a44' }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {crew.map((c, i) => {
            const color = PALETTE[i % PALETTE.length]
            const key = `${c.id}${suffix}`
            return isArea ? (
              <Area
                key={c.id}
                type="monotone"
                dataKey={key}
                name={c.name}
                stroke={color}
                strokeWidth={2}
                fill={`url(#grad-${c.id})`}
                isAnimationActive={false}
              />
            ) : (
              <Line
                key={c.id}
                type="monotone"
                dataKey={key}
                name={c.name}
                stroke={color}
                dot={false}
                isAnimationActive={false}
              />
            )
          })}
        </Chart>
      </ResponsiveContainer>
      <p className="chart-cap">{caption}</p>
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

      <CrewChart crew={crew} history={history} suffix="" variant="line" caption="Frequência cardíaca (bpm) por tripulante" />
      <CrewChart crew={crew} history={history} suffix="_rad" variant="area" caption="Radiação (µSv/h) por tripulante" />
    </section>
  )
}
