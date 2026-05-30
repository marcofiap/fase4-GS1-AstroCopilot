# 🎙️ voice-nlp/ — NLP & Voz (Frente 2)

Transforma fala em texto, devolve resposta falada e detecta intenção/comandos.

## Responsável
**Frente 2** — NLP & Voz.

## Pipeline
1. **STT** com Whisper (áudio → texto, PT-BR).
2. Envia texto ao agente (`POST /api/agent/query`).
3. **TTS** (gTTS/ElevenLabs) → áudio de resposta.
4. Classificador de **intenção** (status / pergunta / emergência).
5. Integra no backend em `POST /api/voice`.

## MVP vs. Stretch
- **MVP:** ciclo voz → texto → resposta → voz em PT-BR.
- **Stretch:** detecção de estresse/emoção na voz (conecta com F2 C11 — emoções em texto).

## Disciplinas
F3 C10 (NLP profundo) · F2 C10/C11 (NLP) · parte de F4 C06 (prompting).
