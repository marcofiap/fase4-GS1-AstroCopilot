# Arquitetura — AstroCopilot

## Visão geral

O backend (FastAPI) é o **orquestrador central**. Cada módulo das demais frentes expõe sua
função e é chamado pelo backend via funções/HTTP. O dashboard consome o backend por REST e
WebSocket (tempo real).

```
        ┌─────────────────────── TRIPULANTE ───────────────────────┐
        │   🎙️ voz          📷 câmera          ⌚ wearable ESP32    │
        └─────┬──────────────────┬────────────────────┬────────────┘
              │                  │                     │ LoRa/BLE/WiFi
        ┌─────▼─────┐      ┌──────▼──────┐       ┌──────▼───────┐
        │ Voz STT/  │      │  Visão CV   │       │ Nó de Borda   │
        │ TTS (F2)  │      │ OCR+detect  │       │ Edge + ML(F4) │
        └─────┬─────┘      └──────┬──────┘       └──────┬────────┘
              └──────────┬────────┴─────────┬───────────┘
                         ▼                  ▼
              ┌──────────────────────────────────────┐
              │   BACKEND FastAPI (orquestrador)      │
              │   REST + WebSocket (tempo real)       │
              └───────┬───────────────────────┬───────┘
                      ▼                       ▼
        ┌─────────────────────────┐   ┌───────────────────────┐
        │  AGENTE LLM + RAG (F1)   │   │  DASHBOARD React+Vite  │
        │  ChromaDB · docs NASA    │   │  (F5)                  │
        └─────────────────────────┘   └───────────────────────┘
```

## Contratos de API (fonte da verdade da integração)

Todas as frentes programam contra estes contratos desde a Semana 1 (o backend já responde com mocks).

| Método | Rota | Entrada | Saída |
|--------|------|---------|-------|
| GET | `/` | — | `{ status, service, version }` |
| POST | `/api/agent/query` | `{ text }` | `{ answer, sources[] }` |
| POST | `/api/voice` | `multipart: audio` | `{ transcript, answer_text, answer_audio_url }` |
| POST | `/api/vision` | `multipart: image` | `{ objects[], ocr_text, description }` |
| POST | `/api/telemetry` | `{ hr, spo2, temp, accel, ts? }` | `{ status, risk_level }` |
| WS | `/ws/telemetry` | — | stream `{ hr, spo2, temp, risk_level, ts }` a cada 1s |

- Timestamps em **ISO-8601**.
- Erros no formato `{ "detail": "<mensagem>" }`.
- CORS liberado para o dashboard em desenvolvimento.

## Onde cada disciplina aparece

| Disciplina (Fase) | Frente |
|---|---|
| IA Generativa (F3) / LLM-RAG (F4) | 1 |
| Scraping/RPA/APIs (F3+F4) | 1 / 5 |
| NLP (F3) | 2 |
| Visão Computacional (F3+F4) | 3 |
| ESP32/Energia, LoRa/BLE (F4) | 4 |
| Cloud+IoT, Edge/Fog (F3) | 4 / 5 |
| Machine Learning | 4 |
| React+Vite (F3) | 5 |
| Governança/Ética/CI-CD (F3+F4) | 5 |
| Quântica/Neuromórfica (F3+F4) | Parágrafo teórico no PDF |
