"""Testes de gravacoes temporarias do piloto."""
import sys
from pathlib import Path

import pytest

VOICE_DIR = Path(__file__).resolve().parents[2] / "voice-nlp"
if str(VOICE_DIR) not in sys.path:
    sys.path.insert(0, str(VOICE_DIR))

import user_recordings  # noqa: E402


@pytest.fixture
def recordings_tmp(tmp_path, monkeypatch):
    import voice_config as config

    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    return tmp_path


def test_save_and_list_recordings(recordings_tmp):
    meta = user_recordings.save_recording(b"fake-audio", "test.webm")
    assert meta["id"]
    assert meta["audio_url"].startswith("/media/user-recordings/")
    listed = user_recordings.list_recordings()
    assert len(listed) == 1
    assert listed[0]["id"] == meta["id"]


def test_list_user_recordings_api(client, monkeypatch, tmp_path):
    import voice_config as config
    import user_recordings as ur

    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    ur.save_recording(b"abc", "a.webm")
    r = client.get("/api/voice/recordings")
    assert r.status_code == 200
    assert len(r.json()["recordings"]) == 1


def test_post_user_recording_api(client, monkeypatch, tmp_path):
    import voice_config as config

    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    rec_dir = tmp_path / "user-recordings"

    r = client.post(
        "/api/voice/recordings",
        files={"audio": ("gravacao.webm", b"webm-bytes", "audio/webm")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["label"].startswith("Minha voz")
    assert (rec_dir / body["filename"]).read_bytes() == b"webm-bytes"