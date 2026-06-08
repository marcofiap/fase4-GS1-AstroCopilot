"""
Text-to-Speech em PT-BR: Edge Neural (padrao, mais natural e rapido) ou gTTS (fallback).
"""
from __future__ import annotations

import asyncio
import re
import threading
import uuid
from pathlib import Path

import voice_config as config

_MARKDOWN_RE = re.compile(r"\*\*|__|\*|_|`+|#{1,6}\s?")

_ACK_PHRASE = "Verificando"
_thread_local = threading.local()


def _limpar_para_fala(texto: str) -> str:
    """Remove citacoes, markdown e limita tamanho para sintese mais rapida."""
    linhas = []
    for linha in texto.splitlines():
        if re.match(r"^\s*(\[fonte:|fontes?:|sources?:)", linha, re.I):
            continue
        linhas.append(linha)
    limpo = "\n".join(linhas).strip() or texto.strip()
    limpo = _MARKDOWN_RE.sub("", limpo)
    limpo = re.sub(r"\s+", " ", limpo).strip()
    if len(limpo) > config.TTS_MAX_CHARS:
        corte = limpo[: config.TTS_MAX_CHARS]
        limpo = corte.rsplit(" ", 1)[0] + "…"
    return limpo


def _get_loop() -> asyncio.AbstractEventLoop:
    loop = getattr(_thread_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _thread_local.loop = loop
    return loop


def _run_async(coro) -> None:
    _get_loop().run_until_complete(coro)


async def _synthesize_edge(fala: str, destino: Path, voice: str, rate: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(fala, voice, rate=rate)
    await communicate.save(str(destino))


def _synthesize_gtts(fala: str, destino: Path) -> None:
    from gtts import gTTS

    gTTS(text=fala, lang=config.TTS_LANG).save(str(destino))


def _synthesize_edge_file(fala: str, destino: Path, voice: str, rate: str) -> None:
    if config.TTS_PROVIDER == "edge":
        try:
            _run_async(_synthesize_edge(fala, destino, voice, rate))
            return
        except Exception as exc:
            print(
                f"[Frente 2] Edge TTS falhou ({voice}/{rate}): {exc}"
            )
        raise RuntimeError(
            "Edge TTS indisponivel. Instale edge-tts e reinicie o backend "
            "(pip install edge-tts) para voz masculina pt-BR-AntonioNeural."
        )
    _synthesize_gtts(fala, destino)


def synthesize(text: str, voice_profile: str | None = None) -> Path:
    """Gera MP3 da resposta. Retorna o caminho do arquivo em cache/tts/."""
    from voice_profiles import resolve_profile

    perfil = resolve_profile(voice_profile)
    fala = _limpar_para_fala(text)
    if not fala:
        raise ValueError("Texto vazio para sintese de voz.")

    config.TTS_DIR.mkdir(parents=True, exist_ok=True)
    destino = config.TTS_DIR / f"{uuid.uuid4().hex}.mp3"
    _synthesize_edge_file(fala, destino, perfil["voice"], perfil["rate"])
    return destino


def synthesize_ack(voice_profile: str | None = None) -> Path:
    """MP3 fixo de confirmacao (Verificando) em cache/tts/ack/<perfil>.mp3."""
    from voice_profiles import resolve_profile

    perfil = resolve_profile(voice_profile)
    ack_dir = config.TTS_DIR / "ack"
    ack_dir.mkdir(parents=True, exist_ok=True)
    destino = ack_dir / f"{perfil['id']}.mp3"
    if destino.exists() and destino.stat().st_size > 400:
        return destino

    fala = _limpar_para_fala(_ACK_PHRASE)
    _synthesize_edge_file(fala, destino, perfil["voice"], perfil["rate"])
    return destino


def warmup(voice_profile: str | None = None) -> None:
    """Pre-aquece Edge TTS (ack + conexao) para reduzir latencia da primeira fala."""
    try:
        synthesize_ack(voice_profile)
    except Exception as exc:
        print(f"[Frente 2] warmup TTS falhou: {exc}")