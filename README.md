# AstroCopilot — Copiloto Conversacional para Missões Espaciais

> **Global Solution 2026.1 — FIAP | 2º ano de Inteligência Artificial (2TIAO)**
> Prova de Conceito (POC) integrando IA Generativa, RAG, Visão Computacional, NLP/Voz, IoT (ESP32) e Machine Learning.

<!-- Para concorrer ao pódio, descomente a linha abaixo e diga "QUERO CONCORRER" no início do vídeo -->
<!-- **QUERO CONCORRER** -->

---

## Integrantes — Grupo 42

| Integrante | GitHub | Frente (sugerida) |
|------------|--------|-------------------|
| Felipe Sabino da Silva | [@FelipeSabinoTMRS](https://github.com/FelipeSabinoTMRS) | Frente 1 — Agente LLM + RAG + Scraping |
| Juan Felipe Voltolini | [@juanvoltolini-rm562890](https://github.com/juanvoltolini-rm562890) | Frente 2 — NLP & Voz |
| Luiz Henrique Ribeiro de Oliveira | [@Luiz-FIAP](https://github.com/Luiz-FIAP) | Frente 4 — IoT ESP32 + Edge + ML | 
| Marco Aurelio Eberhardt Assumpção | [@marcofiap](https://github.com/marcofiap) | Frente 5 — Backend / Dashboard / DevOps |
| Paulo Henrique Senise | [@PauloSenise](https://github.com/PauloSenise) | Frente 3 — Visão Computacional |

---

## Proposta

**Pergunta do desafio:** _Como tecnologias avançadas de IA, automação e computação podem impulsionar soluções inovadoras para a nova economia espacial?_

O **AstroCopilot** é um copiloto de bordo para tripulações espaciais:

- **Voz** — o astronauta fala; o sistema entende (STT) e responde por voz (TTS).
- **RAG + LLM** — consulta manuais técnicos reais (NASA/ESA) e responde com fonte citada.
- **Visão** — o astronauta mostra um painel/componente pela câmera; o copiloto identifica e lê (OCR).
- **IoT + ML** — wearable ESP32 monitora sinais vitais em tempo real; um modelo de ML classifica risco.
- **Dashboard** — centro de controle web (React + Vite) com telemetria ao vivo de 3 tripulantes, copiloto por voz (wake word **"Astra"**) ou texto, análise de imagem e log de alertas.

## Arquitetura

```
  Voz     Câmera     ESP32(LoRa/BLE/WiFi)
   │         │            │
[STT/TTS] [Visão CV]  [Edge + ML risco]
   └────────┬┴──────────┬─┘
            ▼            ▼
     BACKEND FastAPI (REST + WebSocket)
            │                 │
   [Agente LLM + RAG]   [Dashboard React+Vite]
   [Vector DB / NASA]
```

Detalhes em [`docs/arquitetura.md`](docs/arquitetura.md).

## Estrutura do repositório

| Pasta | Frente | Conteúdo |
|-------|--------|----------|
| [`backend/`](backend/) | 5 | API FastAPI que orquestra todos os módulos (REST + WebSocket) |
| [`dashboard/`](dashboard/) | 5 | Centro de controle web (React + Vite) |
| [`agent-rag/`](agent-rag/) | 1 | Scraping de manuais + base vetorial + agente LLM/RAG |
| [`voice-nlp/`](voice-nlp/) | 2 | Speech-to-Text, Text-to-Speech e detecção de intenção |
| [`vision/`](vision/) | 3 | Detecção de componentes + OCR de painéis |
| [`iot-esp32/`](iot-esp32/) | 4 | Firmware ESP32 (Wokwi) + Edge + modelo ML de risco |
| [`docs/`](docs/) | — | Arquitetura, diagramas e PDF de entrega |

## Tecnologias

`Python` · `FastAPI` · `WebSocket` · `LangChain/LlamaIndex` · `ChromaDB` · `OpenAI/Anthropic API` ·
`Whisper` · `gTTS` · `PyTorch` · `YOLOv8/CLIP` · `Tesseract` · `ESP32` · `Wokwi` · `LoRa/BLE` ·
`scikit-learn` · `React` · `Vite` · `TailwindCSS` · `Recharts` · `GitHub Actions` · `Docker`

## Configuração de ambiente

Um único arquivo **`.env` na raiz do repositório** (não use `.env` dentro de `agent-rag/` ou `voice-nlp/`):

```bash
cp .env.example .env
# Preencha AWS_BEARER_TOKEN_BEDROCK e, se quiser, ajuste Whisper/TTS (ver .env.example)
```

## Como executar (início rápido)

O backend já roda com **respostas mock**, permitindo que todas as frentes trabalhem em paralelo.

### Opção 1 — Docker (recomendado: sobe tudo com um comando)

```bash
docker compose up --build
#   Dashboard: http://localhost:5173
#   Backend:   http://localhost:8000/docs
```

Para parar: `docker compose down`. O SQLite (alertas + auditoria) persiste no volume `backend-data`.

### Opção 2 — Modo desenvolvimento (hot-reload, 2 terminais)

```bash
# Terminal 1 — Backend (Frente 5), destrava todas as demais
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn main:app --reload                                # http://localhost:8000/docs
```

```bash
# Terminal 2 — Dashboard (React + Vite)
cd dashboard
npm install
npm run dev                                              # http://localhost:5173
```

> Use **Chrome ou Edge** para a entrada/saída de voz do Copiloto (Web Speech API).

### Banco de dados

Nenhuma configuração necessária: um **SQLite** é criado automaticamente no primeiro
start em `backend/data/astrocopilot.db`, guardando o histórico de **alertas** e a
**trilha de auditoria** do agente. O arquivo não é versionado (cada um gera o seu);
no Docker, persiste no volume `backend-data`. Para zerar, basta apagá-lo.

Cada frente tem instruções específicas no `README.md` da sua pasta.

## Links de entrega

- PDF da entrega: `docs/GS-AstroCopilot.pdf`
- Vídeo (YouTube — Não listado): _adicionar link_
- Repositório: _adicionar link_

## Licença

Creative Commons Attribution 4.0 International (CC BY 4.0).
