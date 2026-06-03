"""
Speech-to-Text com Whisper (faster-whisper) em portugues.
"""
from __future__ import annotations

import re
import uuid
from functools import lru_cache
from pathlib import Path

import voice_config as config

_SUFFIXES = {".wav", ".webm", ".mp3", ".ogg", ".m4a", ".flac"}

# Correcoes leves de erros frequentes do Whisper em termos da missao (PT-BR).
_CORRECOES = (
    (re.compile(r"\bcomo a gira em casa\b", re.I), "como agir em caso"),
    (re.compile(r"\bdespresso\b", re.I), "despressurizacao"),
    (re.compile(r"\brisa[cç][aã]o da cabine\b", re.I), "despressurizacao da cabine"),
    (re.compile(r"\bdespressuriz[aã]o\b", re.I), "despressurizacao"),
)


@lru_cache(maxsize=1)
def _whisper_model():
    from faster_whisper import WhisperModel

    return WhisperModel(
        config.WHISPER_MODEL,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )


def _suffix_from_filename(filename: str | None) -> str:
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in _SUFFIXES:
            return ext
    return ".webm"


def _post_correct(texto: str) -> str:
    """Aplica substituicoes de termos tecnicos frequentemente confundidos pelo STT."""
    saida = texto
    for padrao, repl in _CORRECOES:
        saida = padrao.sub(repl, saida)
    return re.sub(r"\s+", " ", saida).strip()


def transcribe(audio_bytes: bytes, filename: str | None = None) -> str:
    """Transcreve bytes de audio para texto (PT-BR)."""
    if not audio_bytes:
        raise ValueError("Arquivo de audio vazio.")

    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    suffix = _suffix_from_filename(filename)
    temp_path = config.TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"
    temp_path.write_bytes(audio_bytes)

    try:
        model = _whisper_model()
        segments, _info = model.transcribe(
            str(temp_path),
            language=config.WHISPER_LANGUAGE,
            beam_size=config.WHISPER_BEAM_SIZE,
            initial_prompt=config.WHISPER_INITIAL_PROMPT,
            vad_filter=config.WHISPER_VAD_FILTER,
            condition_on_previous_text=False,
            temperature=0.0,
        )
        partes = [seg.text.strip() for seg in segments if seg.text.strip()]
        texto = " ".join(partes).strip()
        if not texto:
            raise RuntimeError("Nao foi possivel transcrever o audio (silencio ou formato invalido).")
        return _post_correct(texto)
    finally:
        temp_path.unlink(missing_ok=True)