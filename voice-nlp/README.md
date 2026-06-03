# voice-nlp/ — NLP & Voz (Frente 2)

Transforma fala em texto, consulta o agente RAG e devolve resposta falada em PT-BR.

## Pipeline

1. **STT** — Whisper (`faster-whisper`) converte o audio em texto.
2. **Agente** — o backend chama a mesma cadeia RAG da Frente 1 (`agent-rag/agent.py`).
3. **TTS** — `gTTS` gera MP3 da resposta.
4. **Intencao** — classificador MVP (`intent.py`): `pergunta` | `status` | `emergencia`.
5. **API** — exposto em `POST /api/voice` pelo backend.

## Estrutura

| Arquivo | Descricao |
|---------|-----------|
| `project_env.py` | Carrega `.env` da raiz (antes do agent-rag no backend) |
| `run_rag.py` | Atalho CLI para agent/ingest com `.env` da raiz |
| `voice_config.py` | Modelo Whisper, idioma, pastas de cache |
| `stt.py` | Transcricao de audio |
| `tts.py` | Sintese de voz (MP3) |
| `intent.py` | Classificador de intencao (regras) |
| `pipeline.py` | Orquestra STT → agente → TTS |
| `samples/` | Audios de teste versionados (ex.: `audio_piloto.ogg`) |
| `cache/` | Audios TTS gerados (nao versionado) |

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

## Teste via API (integracao completa)

```bash
cd backend
uvicorn main:app --reload
```

No Swagger (`http://localhost:8000/docs`), em **POST /api/voice**, envie `voice-nlp/samples/audio_piloto.ogg`.

Ou pela linha de comando (na raiz do projeto, com o backend rodando):

```powershell
# Na raiz do projeto:
curl.exe -X POST "http://localhost:8000/api/voice" -F "audio=@voice-nlp/samples/audio_piloto.ogg;type=audio/ogg"

# Se o terminal estiver em voice-nlp/:
curl.exe -X POST "http://localhost:8000/api/voice" -F "audio=@samples/audio_piloto.ogg;type=audio/ogg"
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

Reproduza o audio: `http://localhost:8000` + `answer_audio_url`.

## Variaveis de ambiente (opcionais)

Ver `voice-nlp/.env.example`. Podem ficar no `.env` da raiz do projeto.

## MVP vs. Stretch

- **MVP:** ciclo voz → texto → resposta RAG → voz em PT-BR + intencao por regras.
- **Stretch:** emocao/estresse na voz; ElevenLabs; modelo de intencao treinado.