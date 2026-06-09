# 🛰️ backend/ — Orquestrador (Frente 5)

API **FastAPI** que integra todas as frentes (REST + WebSocket). Já roda com **mocks**,
permitindo que as demais frentes e o dashboard trabalhem em paralelo desde o início.

## Responsável
**Frente 5** — Backend / Dashboard / DevOps / Governança.

## Como rodar

> 💡 Atalho (sobe backend + dashboard juntos, da raiz do projeto): `./iniciar.sh`
> (Mac/Linux) ou duplo-clique em `iniciar.bat` (Windows).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Mac/Linux
# source .venv/Scripts/activate    # Windows (Git Bash)
pip install -r requirements.txt
uvicorn main:app --reload
```

- Swagger interativo: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/**

## Endpoints (contratos)

| Método | Rota | Frente que pluga a lógica real |
|--------|------|-------------------------------|
| GET | `/` | — (health) |
| GET | `/api/crew` | 4 (estado atual da tripulação) |
| GET | `/api/alerts` | 5 (histórico de risco — SQLite) |
| GET | `/api/audit` | 5 (trilha de auditoria do agente — SQLite) |
| POST | `/api/agent/query` | 1 (RAG) |
| POST | `/api/voice` | 2 (STT/TTS) |
| POST | `/api/vision` | 3 (CV/OCR) |
| POST | `/api/telemetry` | 4 (ESP32 — corpo JSON) |
| GET | `/api/telemetry` | 4 (ESP32 — query params, WiFi+HTTP do Wokwi) |
| GET | `/terminal_log` | 4 (espelha 1 linha do monitor serial: `?line=...`) |
| GET | `/terminal_logs` | 4 (snapshot JSON do monitor serial) |
| GET | `/terminal_stream` | 4 (stream SSE do monitor serial ao vivo) |
| WS | `/ws/telemetry` | 4 (stream tempo real) |

### Classificador de risco (Frente 4 — Edge ML)

O risco (`normal`/`fadiga`/`risco`) de cada leitura de telemetria é classificado
por um modelo **RandomForest** (scikit-learn) treinado em
[`../iot-esp32/ml-edge/`](../iot-esp32/ml-edge). O bundle `model.pkl` é carregado
**uma vez no startup** (`load_model()` no `lifespan`).

- **Fallback:** se o `model.pkl` não existir ou a inferência falhar, cai nas
  regras determinísticas (`_classify_risk_rules`) — a API nunca quebra por isso.
- **Caminho do modelo:** resolvido a partir do repositório; sobrescreva com a env
  `ASTRO_MODEL_PATH` (útil no Docker, onde o pkl pode não estar na imagem).
- **Versão:** `scikit-learn` deve ser a **mesma** do treino (pinada em ambos os
  `requirements.txt`), senão o `joblib.load` pode falhar.
- **Geração:** o `model.pkl` é gitignored; gere com
  `python ../iot-esp32/ml-edge/train_model.py`. Sem ele a API usa as regras.

### Telemetria em tempo real (Frente 4)

O stream `/ws/telemetry` dá **prioridade à telemetria real** do ESP32: quando um
tripulante recebe telemetria (`POST` JSON **ou** `GET` query params em
`/api/telemetry`), o WebSocket reenvia o dado real dele por `REAL_TELEMETRY_TTL_S`
(10 s) — então o card desse tripulante muda ao vivo no dashboard. Os demais
continuam simulados; sem leitura recente, todos voltam a simular.

A simulação Wokwi usa a variante **GET** (o `HTTPClient` do ESP32 manda os dados
como query params via WiFi — ver [`../iot-esp32/`](../iot-esp32)). O firmware também
espelha o monitor serial em `GET /terminal_log?line=...`; acompanhe ao vivo em
`/terminal_stream` (SSE) ou `/terminal_logs` (JSON).

### Persistência & Governança (`db.py`)

Um SQLite (`backend/data/astrocopilot.db`, fora do versionamento) guarda:
- **`alerts`** — cada escalada de risco da tripulação (sobrevive a reinícios).
- **`audit`** — trilha de auditoria das decisões do agente: pergunta, resposta,
  fontes citadas, canal (`text`/`voice`) e timestamp. Requisito de governança de IA.

No Docker, um volume `backend-data` mantém o banco entre recriações do container.

Os contratos detalhados estão em [`../docs/arquitetura.md`](../docs/arquitetura.md).
Cada integração está marcada no código com `TODO [Frente N]`.

## Teste rápido (com o servidor no ar)

```bash
curl http://localhost:8000/
curl -X POST http://localhost:8000/api/agent/query -H "Content-Type: application/json" -d '{"text":"procedimento de despressurização?"}'
curl -X POST http://localhost:8000/api/telemetry -H "Content-Type: application/json" -d '{"hr":150,"spo2":88,"temp":37.0,"accel":0.2}'
curl "http://localhost:8000/api/telemetry?crew_id=cmdr&hr=150&spo2=88&temp=37.0&accel=0.2"   # variante GET (igual à do ESP32)
curl "http://localhost:8000/terminal_logs"                                                   # monitor serial espelhado
```

## Rodar com Docker (stack completa)

Da **raiz** do repositório, um único comando sobe backend + dashboard:

```bash
docker compose up --build
#   Dashboard: http://localhost:5173
#   Backend:   http://localhost:8000/docs
```

Para parar: `docker compose down`.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Cobrem o classificador de risco — regras (política), **fallback** sem modelo e
**caminho ML** com o `model.pkl` carregado — e os endpoints REST (health, crew,
agente + auditoria, telemetria com/sem escalada de alerta, 404 e visão).
Cada teste roda contra um SQLite temporário isolado (fixture `client`).

## CI (GitHub Actions)

O workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) roda a cada push/PR na `main`:
compila o backend + **pytest**, e faz o build de produção do dashboard.

## MVP vs. Stretch

- **MVP:** endpoints respondendo + WebSocket de telemetria + dashboard consumindo. ✅
- **DevOps:** `docker compose` subindo tudo ✅ · CI no GitHub Actions ✅
- **Governança:** persistência dos alertas (SQLite) ✅ · trilha de auditoria das decisões do agente ✅
- **Qualidade:** testes pytest (26) rodando no CI ✅
- **Frente 4 integrada:** telemetria classificada por modelo ML real (não-mock) com fallback ✅
- **Stretch:** troca dos mocks restantes pela lógica real das Frentes 1–3.
