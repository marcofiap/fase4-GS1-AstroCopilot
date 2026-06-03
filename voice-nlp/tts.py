"""
Text-to-Speech com gTTS (portugues do Brasil).
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from gtts import gTTS

import voice_config as config


def _limpar_para_fala(texto: str) -> str:
    """Remove blocos de citacao longos e limita tamanho para o TTS."""
    linhas = []
    for linha in texto.splitlines():
        if re.match(r"^\s*(\[fonte:|fontes?:|sources?:)", linha, re.I):
            continue
        linhas.append(linha)
    limpo = "\n".join(linhas).strip() or texto.strip()
    if len(limpo) > config.TTS_MAX_CHARS:
        limpo = limpo[: config.TTS_MAX_CHARS].rsplit(" ", 1)[0] + "…"
    return limpo


def synthesize(text: str) -> Path:
    """Gera MP3 da resposta. Retorna o caminho do arquivo em cache/tts/."""
    fala = _limpar_para_fala(text)
    if not fala:
        raise ValueError("Texto vazio para sintese de voz.")

    config.TTS_DIR.mkdir(parents=True, exist_ok=True)
    destino = config.TTS_DIR / f"{uuid.uuid4().hex}.mp3"
    gTTS(text=fala, lang=config.TTS_LANG).save(str(destino))
    return destino