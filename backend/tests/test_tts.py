"""Testes do endpoint POST /api/tts (Frente 2)."""
from pathlib import Path

import main


def test_tts_gera_url_de_audio(client, monkeypatch):
    class _FakePath:
        name = "abc123.mp3"

    class _FakeTts:
        @staticmethod
        def synthesize(_text: str, voice_profile=None):
            return _FakePath()

    monkeypatch.setattr(main, "voice_tts", _FakeTts)

    r = client.post("/api/tts", json={"text": "Procedimento de despressurizacao."})
    assert r.status_code == 200
    assert r.json()["audio_url"] == "/media/voice/abc123.mp3"


def test_tts_texto_vazio(client):
    r = client.post("/api/tts", json={"text": "   "})
    assert r.status_code == 400


def test_tts_indisponivel(client, monkeypatch):
    monkeypatch.setattr(main, "voice_tts", None)
    r = client.post("/api/tts", json={"text": "ola"})
    assert r.status_code == 503