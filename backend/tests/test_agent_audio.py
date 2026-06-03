"""Testes de TTS integrado em POST /api/agent/query."""
import main


def test_agent_query_com_audio(client, monkeypatch):
    class _FakePath:
        def relative_to(self, _base):
            return self

        def as_posix(self):
            return "abc123.mp3"

        name = "abc123.mp3"

    class _FakeTts:
        @staticmethod
        def synthesize(_text: str, voice_profile=None):
            return _FakePath()

    monkeypatch.setattr(main, "voice_tts", _FakeTts)

    r = client.post(
        "/api/agent/query",
        json={"text": "como despressurizar?", "with_audio": True, "voice_profile": "leo"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["answer_audio_url"] == "/media/voice/abc123.mp3"


def test_tts_ack_endpoint(client, monkeypatch):
    class _AckPath:
        def relative_to(self, _base):
            return self

        def as_posix(self):
            return "ack/leo.mp3"

    class _FakeTts:
        @staticmethod
        def synthesize_ack(profile=None):
            return _AckPath()

    monkeypatch.setattr(main, "voice_tts", _FakeTts)

    r = client.get("/api/tts/ack?voice_profile=leo")
    assert r.status_code == 200
    assert r.json()["audio_url"] == "/media/voice/ack/leo.mp3"