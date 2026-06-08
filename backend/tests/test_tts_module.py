"""Testes do modulo voice-nlp/tts.py."""
import sys
from pathlib import Path

import pytest

VOICE_DIR = Path(__file__).resolve().parents[2] / "voice-nlp"
if str(VOICE_DIR) not in sys.path:
    sys.path.insert(0, str(VOICE_DIR))

import tts  # noqa: E402


def test_limpar_remove_markdown_e_fontes():
    texto = "**Alerta**\nLinha\n[fonte: NASA]\nMais texto."
    limpo = tts._limpar_para_fala(texto)
    assert "Alerta" in limpo
    assert "NASA" not in limpo
    assert "**" not in limpo


@pytest.mark.skipif(not pytest.importorskip("edge_tts"), reason="edge-tts nao instalado")
def test_synthesize_edge_cria_arquivo(tmp_path, monkeypatch):
    import voice_config as config

    monkeypatch.setattr(config, "TTS_DIR", tmp_path)
    monkeypatch.setattr(config, "TTS_PROVIDER", "edge")
    monkeypatch.setattr(config, "TTS_MAX_CHARS", 500)
    path = tts.synthesize("Copiloto Astro online.")
    assert path.exists()
    assert path.stat().st_size > 500