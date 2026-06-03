# voice-nlp/ — NLP & Voz (Frente 2)

Transforma fala em texto, consulta o agente RAG e devolve resposta falada em PT-BR.

## Pipeline

1. **STT** — Whisper (`faster-whisper`) converte o audio em texto.
2. **Agente** — o backend chama a mesma cadeia RAG da Frente 1 (`agent-rag/agent.py`).
3. **TTS** — **Edge Neural** (`pt-BR-AntonioNeural`, +18% velocidade) gera MP3; fallback `gTTS`.
4. **Intencao** — classificador MVP (`intent.py`): `pergunta` | `status` | `emergencia`.
5. **API** — `POST /api/voice` (ciclo completo) e `POST /api/tts` (so a resposta falada).

## Estrutura

| Arquivo | Descricao |
|---------|-----------|
| `project_env.py` | Carrega `.env` da raiz (antes do agent-rag no backend) |
| `run_rag.py` | Atalho CLI para agent/ingest com `.env` da raiz |
| `voice_config.py` | Modelo Whisper, idioma, pastas de cache |
| `stt.py` | Transcricao de audio |
| `tts.py` | Sintese de voz (Edge neural ou gTTS) |
| `intent.py` | Classificador de intencao (regras) |
| `pipeline.py` | Orquestra STT → agente → TTS |
| `samples/` | Audios de teste versionados (ex.: `audio_piloto.ogg`) |
| `user_recordings.py` | Gravacoes temporarias do usuario (piloto) |
| `cache/` | TTS, tmp STT e `user-recordings/` (nao versionado) |

## Pre-requisitos

- Python 3.11+ (mesmo do backend).
- **ffmpeg** no PATH (necessario para webm/mp3/ogg no STT).
- Frente 1 configurada: **apenas** `.env` na raiz (`AWS_BEARER_TOKEN_BEDROCK` + ingest).

### Por que o RAG “para” com um `.env` só na raiz?

O `agent-rag/config.py` (inalterado) usa `find_dotenv(usecwd=True)`. Se existir **`agent-rag/.env`**, ele é carregado **em vez** do `.env` da raiz.

| Como você roda | Solução (sem editar agent-rag) |
|----------------|--------------------------------|
| `uvicorn` + `/api/voice` | `project_env.py` no backend (já ativo) |
| `python agent.py` dentro de `agent-rag/` | Apague `agent-rag/.env` ou use `run_rag.py` |

```bash
python voice-nlp/run_rag.py ingest
python voice-nlp/run_rag.py agent "Como agir em caso de despressurizacao da cabine?"
```

## Instalacao

```bash
# Na raiz do projeto, com o venv ativo:
pip install -r voice-nlp/requirements.txt
pip install -r backend/requirements.txt   # se ainda nao instalou o backend
```

Na primeira execucao o Whisper baixa o modelo (`base` por padrao — melhor que `tiny` para termos tecnicos).

Se a transcricao ainda falhar, use `WHISPER_MODEL=small` no `.env` (mais lento, mais preciso).

## Teste local (sem backend)

Amostra padrao do repositorio:

```bash
cd voice-nlp
python pipeline.py samples/audio_piloto.ogg
```

Usa um agente mock. Para testar com RAG real, use a API abaixo.

## Como rodar backend + dashboard (proximo dev)

A Frente 2 roda **dentro do backend** (`backend/main.py` importa `voice-nlp/pipeline.py`). O dashboard (Frente 5) consome a API. Use **dois terminais**.

### Terminal 1 — API (obrigatorio)

Na **raiz** do repositorio, com o venv ativo:

```powershell
cd C:\caminho\para\fase4-GS1-AstroCopilot
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt -r voice-nlp\requirements.txt
cd backend
uvicorn main:app --reload
```

- Swagger: http://127.0.0.1:8000/docs
- **Nao** rode `uvicorn` dentro de `voice-nlp/` — nao existe `main.py` ali (`Could not import module "main"`).

Ao subir, o log deve mostrar RAG e voz carregados (sem `[Frente 2] Voz indisponivel`).

### Terminal 2 — Dashboard (UI)

```powershell
cd dashboard
npm install
npm run dev
```

- Painel: http://localhost:5173
- API padrao: `http://localhost:8000` (ver `dashboard/.env.example` → copie para `.env` se precisar mudar a URL)
- Navegador: **Chrome ou Edge** (wake word e gravacao de voz)

### Testar voz no dashboard

Na pagina inicial, card **Copiloto (RAG)**:

| Acao | Botao / campo |
|------|----------------|
| Mesmo teste das amostras OGG | **Piloto 1**, **Piloto 2**, **Piloto 3** |
| Gravar pergunta ao vivo | **Gravar voz** (parar gravacao envia ao Whisper) |
| Pergunta por texto | campo de texto + **Enviar** |
| Wake word | **Astro On** → diga *"Astro, ..."* + pergunta |
| Ouvir resposta em PT-BR (Edge neural) | **Voz: ON** |

Fluxo: audio ou texto → `POST /api/voice` ou `/api/agent/query` + `/api/tts` → resposta no chat → MP3 reproduzido pelo navegador.

### Onde ficam os MP3 gerados

| Uso | Caminho |
|-----|---------|
| Disco | `voice-nlp/cache/tts/<uuid>.mp3` (nao versionado, `.gitignore`) |
| URL | `http://127.0.0.1:8000/media/voice/<uuid>.mp3` (campo `answer_audio_url` no JSON) |
| Audio temporario do STT | `voice-nlp/cache/tmp/` (apagado apos transcrever) |
| Gravacoes do usuario | `voice-nlp/cache/user-recordings/` (ate 8; chips **Minha voz** no dashboard) |

## Teste via API (curl / Swagger)

Com o backend rodando (terminal 1 acima).

Swagger: **POST /api/voice** → envie `voice-nlp/samples/audio_piloto.ogg`.

```powershell
# Na raiz do projeto:
curl.exe -X POST "http://127.0.0.1:8000/api/voice" -F "audio=@voice-nlp/samples/audio_piloto.ogg;type=audio/ogg"

# Se o terminal estiver em voice-nlp/:
curl.exe -X POST "http://127.0.0.1:8000/api/voice" -F "audio=@samples/audio_piloto.ogg;type=audio/ogg"
```

Resposta esperada:

```json
{
  "transcript": "...",
  "intent": "pergunta",
  "answer_text": "...",
  "sources": ["..."],
  "answer_audio_url": "/media/voice/<id>.mp3"
}
```

Reproduza o audio: `http://127.0.0.1:8000` + `answer_audio_url`.

## Variaveis de ambiente (opcionais)

No `.env` da raiz:

| Variavel | Padrao | Descricao |
|----------|--------|-----------|
| `TTS_PROVIDER` | `edge` | `edge` (neural) ou `gtts` |
| `TTS_VOICE` | `pt-BR-AntonioNeural` | Voz do Astro (ex.: `pt-BR-FranciscaNeural`) |
| `TTS_RATE` | `+18%` | Velocidade da fala (`+10%` … `+30%`) |
| `TTS_MAX_CHARS` | `2200` | Limite de texto sintetizado (mais rapido) |

## MVP vs. Stretch

- **MVP:** ciclo voz → texto → resposta RAG → voz em PT-BR + intencao por regras.
- **Stretch:** emocao/estresse na voz; ElevenLabs; modelo de intencao treinado.

## Como Funciona a Infraestrutura (Local vs. Nuvem)

Aqui está um resumo de quais serviços rodam localmente e quais dependem da internet:

1. **Processamento do LLM (Texto ➔ Texto)**:
   * **Serviço**: Claude 3.5 Haiku via AWS Bedrock.
   * **Execução**: **Online** (consome tokens e requer a chave Bedrock).

2. **Transcrição de Áudio (STT - Áudio ➔ Texto)**:
   * **Serviço**: Whisper (`faster-whisper`).
   * **Execução**: **100% Local** (roda na CPU/GPU do próprio computador do usuário, sem custos e sem enviar dados de voz à internet).

3. **Resposta por Voz (TTS - Texto ➔ Áudio)**:
   * **Provedor Padrão**: Microsoft Edge Neural TTS.
     * **Execução**: **Online** (faz requisições às APIs públicas de voz do Microsoft Edge; é 100% gratuito e não consome chave).
   * **Provedor Fallback**: Google TTS (`gtts`).
     * **Execução**: **Online** (faz requisições web ao serviço do Google Tradutor; é gratuito, mas produz uma voz mais robótica/metalizada).