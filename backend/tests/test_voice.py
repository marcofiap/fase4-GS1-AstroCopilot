"""Testes do endpoint POST /api/voice (Frente 2)."""
from pathlib import Path

import main


def _fake_voice_pipeline(audio_bytes: bytes, filename: str | None, ask_agent):
    assert audio_bytes
    resultado = ask_agent("como despressurizar a cabine")
    return {
        "transcript": "como despressurizar a cabine",
        "intent": "pergunta",
        "answer_text": resultado["answer"],
        "sources": resultado["sources"],
        "answer_audio_file": None,
    }


def test_voice_pipeline_integrado(client, monkeypatch):
    monkeypatch.setattr(main, "voice_process", _fake_voice_pipeline)
    r = client.post(
        "/api/voice",
        files={"audio": ("pergunta.wav", b"fake-audio-bytes", "audio/wav")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["transcript"] == "como despressurizar a cabine"
    assert body["intent"] == "pergunta"
    assert "answer" in body["answer_text"].lower() or "teste" in body["answer_text"].lower()
    assert body["sources"]

    audit = client.get("/api/audit").json()
    assert audit["audit"][0]["channel"] == "voice"
    assert audit["audit"][0]["question"] == "como despressurizar a cabine"


def test_voice_audio_vazio(client, monkeypatch):
    monkeypatch.setattr(main, "voice_process", _fake_voice_pipeline)
    r = client.post("/api/voice", files={"audio": ("vazio.wav", b"", "audio/wav")})
    assert r.status_code == 400


def test_intent_emergencia():
    from pathlib import Path
    import sys

    voice_dir = Path(__file__).resolve().parents[2] / "voice-nlp"
    sys.path.insert(0, str(voice_dir))
    import intent  # noqa: E402

    assert intent.classify("Emergencia! vazamento na cabine") == "emergencia"
    assert intent.classify("Qual o status da telemetria do comandante") == "status"