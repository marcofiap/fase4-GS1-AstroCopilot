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
| GET | `/api/crew` | — | `{ crew[] }` (estado atual dos 3 tripulantes) |
| GET | `/api/alerts` | `?limit=20` | `{ alerts[], total }` (escaladas de risco — SQLite) |
| GET | `/api/audit` | `?limit=50` | `{ audit[], total }` (trilha de decisões do agente — SQLite) |
| POST | `/api/agent/query` | `{ text }` `?channel=text\|voice` | `{ answer, sources[] }` (registra auditoria) |
| POST | `/api/voice` | `multipart: audio` | `{ transcript, answer_text, answer_audio_url }` |
| POST | `/api/vision` | `multipart: image` | `{ objects[], ocr_text, description }` |
| POST | `/api/telemetry` | `{ crew_id, hr, spo2, temp, accel, resp?, radiation?, battery?, ts? }` | `{ status, crew_id, risk_level }` |
| WS | `/ws/telemetry` | — | stream `{ ts, crew:[{id,name,role,hr,spo2,temp,resp,radiation,battery,risk_level}] }` a cada 1s |

**Sensores por tripulante:** batimentos (bpm), SpO₂ (%), temperatura (°C), aceleração (g),
respiração (rpm), radiação (µSv/h) e bateria do wearable (%).
**Log de alertas:** registrado quando um tripulante *escala* de risco (normal→fadiga→risco).
**Persistência (SQLite):** `alerts` e `audit` ficam em `backend/data/astrocopilot.db`
(volume Docker `backend-data`), sobrevivendo a reinícios — base da governança de IA.

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
