"""
Configuracao da Frente 2 (NLP & Voz).

Arquivo renomeado de config.py para nao colidir com agent-rag/config.py quando o
backend importa as duas frentes no mesmo processo.
"""
from __future__ import annotations

import os
from pathlib import Path

import project_env  # noqa: F401 — carrega raiz/.env antes de ler variaveis

BASE_DIR = project_env.VOICE_NLP_DIR
CACHE_DIR = Path(os.getenv("VOICE_CACHE_DIR", str(BASE_DIR / "cache")))
TTS_DIR = CACHE_DIR / "tts"
TEMP_DIR = CACHE_DIR / "tmp"

# Whisper (faster-whisper): tiny (rapido, impreciso) | base (padrao) | small ...
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "pt")
WHISPER_BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
WHISPER_INITIAL_PROMPT = os.getenv(
    "WHISPER_INITIAL_PROMPT",
    "Como agir em caso de despressurizacao da cabine. Tripulacao espacial, astronauta, EVA, ECLSS, cabine pressurizada.",
)
WHISPER_VAD_FILTER = os.getenv("WHISPER_VAD_FILTER", "0").lower() in ("1", "true", "yes")

# TTS: edge (Microsoft Neural, padrao) | gtts (fallback)
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge").lower()
TTS_VOICE = os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")
TTS_RATE = os.getenv("TTS_RATE", "+50%")
TTS_LANG = os.getenv("TTS_LANG", "pt-br")
TTS_MAX_CHARS = int(os.getenv("TTS_MAX_CHARS", "900"))