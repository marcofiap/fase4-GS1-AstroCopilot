"""
Gravacoes temporarias do piloto (usuario) — reutilizaveis entre interacoes.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import voice_config as config

_INDEX_FILE = "index.json"
_MAX_RECORDINGS = 8
_ALLOWED_SUFFIXES = {".webm", ".ogg", ".wav", ".mp3", ".m4a"}


def _recordings_dir() -> Path:
    path = config.CACHE_DIR / "user-recordings"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path() -> Path:
    return _recordings_dir() / _INDEX_FILE


def _load_index() -> list[dict]:
    path = _index_path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_index(entries: list[dict]) -> None:
    _index_path().write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _suffix_from_filename(filename: str | None) -> str:
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in _ALLOWED_SUFFIXES:
            return ext
    return ".webm"


def _label_for_entry(created_at: str) -> str:
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return f"Minha voz {dt.astimezone().strftime('%H:%M')}"
    except ValueError:
        return "Minha voz"


def save_recording(audio_bytes: bytes, filename: str | None = None) -> dict:
    """Persiste audio do usuario e retorna metadados."""
    if not audio_bytes:
        raise ValueError("Arquivo de audio vazio.")

    rec_id = uuid.uuid4().hex
    suffix = _suffix_from_filename(filename)
    stored_name = f"{rec_id}{suffix}"
    dest = _recordings_dir() / stored_name
    dest.write_bytes(audio_bytes)

    entries = _load_index()
    created_at = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": rec_id,
        "filename": stored_name,
        "label": _label_for_entry(created_at),
        "created_at": created_at,
        "size_bytes": len(audio_bytes),
    }
    entries.append(entry)

    while len(entries) > _MAX_RECORDINGS:
        removed = entries.pop(0)
        old_file = _recordings_dir() / removed.get("filename", "")
        old_file.unlink(missing_ok=True)

    _save_index(entries)
    return _entry_with_urls(entry)


def _entry_with_urls(entry: dict) -> dict:
    name = entry.get("filename") or ""
    return {
        **entry,
        "audio_url": f"/media/user-recordings/{name}",
    }


def list_recordings() -> list[dict]:
    """Lista gravacoes do usuario, da mais recente para a mais antiga."""
    entries = _load_index()
    out = [_entry_with_urls(e) for e in entries]
    out.reverse()
    return out


def get_recording(recording_id: str) -> tuple[dict, Path] | None:
    if not re.fullmatch(r"[a-f0-9]{32}", recording_id or ""):
        return None
    for entry in _load_index():
        if entry.get("id") == recording_id:
            path = _recordings_dir() / entry.get("filename", "")
            if path.is_file():
                return _entry_with_urls(entry), path
    return None


def read_recording_bytes(recording_id: str) -> tuple[dict, bytes] | None:
    found = get_recording(recording_id)
    if found is None:
        return None
    meta, path = found
    return meta, path.read_bytes()