# 🛰️ backend/ — Orquestrador (Frente 5)

API **FastAPI** que integra todas as frentes (REST + WebSocket). Já roda com **mocks**,
permitindo que as demais frentes e o dashboard trabalhem em paralelo desde o início.

## Responsável
**Frente 5** — Backend / Dashboard / DevOps / Governança.

## Como rodar

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash) | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- Swagger interativo: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/**

## Endpoints (contratos)

| Método | Rota | Frente que pluga a lógica real |
|--------|------|-------------------------------|
| GET | `/` | — (health) |
| POST | `/api/agent/query` | 1 (RAG) |
| POST | `/api/voice` | 2 (STT/TTS) |
| POST | `/api/vision` | 3 (CV/OCR) |
| POST | `/api/telemetry` | 4 (ESP32) |
| WS | `/ws/telemetry` | 4 (stream tempo real) |

Os contratos detalhados estão em [`../docs/arquitetura.md`](../docs/arquitetura.md).
Cada integração está marcada no código com `TODO [Frente N]`.

## Teste rápido (com o servidor no ar)

```bash
curl http://localhost:8000/
curl -X POST http://localhost:8000/api/agent/query -H "Content-Type: application/json" -d '{"text":"procedimento de despressurização?"}'
curl -X POST http://localhost:8000/api/telemetry -H "Content-Type: application/json" -d '{"hr":150,"spo2":88,"temp":37.0,"accel":0.2}'
```

## MVP vs. Stretch

- **MVP:** endpoints respondendo + WebSocket de telemetria + dashboard consumindo.
- **Stretch:** `docker compose` subindo tudo; trilha de auditoria das decisões do agente; CI no GitHub Actions.
