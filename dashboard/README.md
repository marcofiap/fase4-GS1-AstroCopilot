# 📊 dashboard/ — Centro de Controle (Frente 5)

Dashboard web (**React + Vite**) — telemetria ao vivo, chat com o copiloto e alertas.

## Responsável
**Frente 5** — Backend / Dashboard / DevOps.

## Como criar (a fazer)

```bash
cd dashboard
npm create vite@latest . -- --template react
npm install
npm install recharts
npm run dev          # http://localhost:5173
```

Configure a URL da API em `.env` (`VITE_API_URL=http://localhost:8000`).

## Componentes previstos
- **Telemetria ao vivo** (WebSocket `/ws/telemetry` + Recharts).
- **Chat** com o copiloto (`POST /api/agent/query`).
- **Upload de imagem** para análise (`POST /api/vision`).
- **Painel de alertas** (destaque quando `risk_level != normal`).

## MVP vs. Stretch
- **MVP:** telemetria ao vivo + chat integrados ao backend.
- **Stretch:** layout "centro de controle" com tema espacial + animações.

## Disciplinas
F3 C05 (React + Vite) · F4 C07 (IA em produção) · F3 C07 (Governança).
