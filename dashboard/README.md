# 📊 dashboard/ — Centro de Controle (Frente 5)

Dashboard web (**React + Vite**) — telemetria ao vivo, copiloto por voz/texto, análise de imagem e log de alertas.

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

## Páginas (react-router-dom)
- `/` — **Painel principal**: telemetria ao vivo + Copiloto (RAG).
- `/visao` — **Visão**: upload de imagem para análise (`/api/vision`).
- `/alertas` — **Log de Alertas**: histórico completo de escalonamentos de risco.
- `/auditoria` — **Trilha de Auditoria**: decisões do Copiloto (governança de IA — `/api/audit`).

## Arquivos
- `src/App.jsx` — rotas da aplicação
- `src/pages/Dashboard.jsx` — painel principal (telemetria + copiloto)
- `src/pages/VisionPage.jsx` — página de análise de imagem
- `src/pages/AlertsPage.jsx` — página de log de alertas
- `src/pages/AuditPage.jsx` — página da trilha de auditoria do agente
- `src/hooks/useTelemetry.js` — conexão WebSocket `/ws/telemetry`
- `src/hooks/useSpeech.js` — voz no navegador (STT/TTS + wake word "Astro")
- `src/components/TelemetryPanel.jsx` — cards da tripulação + gráficos (Recharts: linha de FC e área de radiação)
- `src/components/ChatPanel.jsx` — chat com o agente (`/api/agent/query`) + entrada/saída de voz
- `src/components/VisionPanel.jsx` — upload de imagem (`/api/vision`)
- `src/components/AlertLogPanel.jsx` — lista de alertas (`/api/alerts`)
- `src/api.js` — cliente da API

## Funcionalidades
- **Telemetria ao vivo** de 3 tripulantes (WebSocket `/ws/telemetry` + Recharts: FC, SpO₂, temperatura, respiração, radiação, bateria).
- **Copiloto (RAG)** por texto **ou voz**: ative **Astro On** e diga **"Astro" + pergunta** (escuta contínua); resposta em áudio via servidor (Edge TTS).
- **Análise de imagem** de painéis/instrumentos (`POST /api/vision`).
- **Log de alertas** com registro a cada escalonamento de risco.

## MVP vs. Stretch
- **MVP:** telemetria ao vivo + chat integrados ao backend.
- **Stretch:** layout "centro de controle" com tema espacial + animações.

## Disciplinas
F3 C05 (React + Vite) · F4 C07 (IA em produção) · F3 C07 (Governança).
