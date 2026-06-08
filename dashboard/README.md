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
- `src/api.js` — cliente da API (agent, voz, TTS, visão, alertas, auditoria, gravações)
- **Páginas** (`src/pages/`)
  - `Dashboard.jsx` — painel principal (telemetria + copiloto)
  - `VisionPage.jsx` — página de análise de imagem
  - `AlertsPage.jsx` — página de log de alertas
  - `AuditPage.jsx` — página da trilha de auditoria do agente
- **Hooks** (`src/hooks/`)
  - `useTelemetry.js` — conexão WebSocket `/ws/telemetry`
  - `useSpeech.js` — voz no navegador (wake word "Astro", reprodução do áudio do servidor)
  - `useMicLevel.js` — nível do microfone (feedback visual ao gravar)
- **Componentes** (`src/components/`)
  - `TelemetryPanel.jsx` — cards da tripulação + gráficos (Recharts: linha de FC e área de radiação)
  - `ChatPanel.jsx` — chat com o agente (`/api/agent/query`) + entrada/saída de voz e gravação
  - `ChatDebugPanel.jsx` — painel de depuração/opções avançadas de voz
  - `MicFeedback.jsx` — indicador visual do microfone durante a gravação
  - `VisionPanel.jsx` — upload de imagem (`/api/vision`)
  - `AlertLogPanel.jsx` — lista de alertas (`/api/alerts`)
- **Config** (`src/config/`)
  - `astroVoices.js` — perfis de voz do Astro (vozes neurais PT-BR)

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
