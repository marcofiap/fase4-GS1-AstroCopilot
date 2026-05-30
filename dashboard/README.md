# 📊 dashboard/ — Centro de Controle (Frente 5)

Dashboard web (**React + Vite**) — telemetria ao vivo, chat com o copiloto e alertas.

## Responsável
**Frente 5** — Backend / Dashboard / DevOps.

## Como rodar (já scaffoldado)

O app React+Vite já está montado e cabeado no backend. Basta:

```bash
cd dashboard
cp .env.example .env        # opcional (já tem fallback para localhost)
npm install
npm run dev                 # http://localhost:5173
```

> Pré-requisito: o **backend** precisa estar rodando (`uvicorn main:app --reload`).
> A telemetria aparece ao vivo via WebSocket; o chat e a análise de imagem usam REST.

## Arquivos
- `src/App.jsx` — layout do centro de controle + banner de alerta de risco
- `src/hooks/useTelemetry.js` — conexão WebSocket `/ws/telemetry`
- `src/components/TelemetryPanel.jsx` — métricas + gráfico (Recharts)
- `src/components/ChatPanel.jsx` — chat com o agente (`/api/agent/query`)
- `src/components/VisionPanel.jsx` — upload de imagem (`/api/vision`)
- `src/api.js` — cliente da API

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
