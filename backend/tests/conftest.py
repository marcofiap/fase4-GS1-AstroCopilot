"""Fixtures compartilhadas dos testes (Frente 5)."""
import pytest
from fastapi.testclient import TestClient

import db
import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Cliente de teste com um SQLite TEMPORÁRIO por teste.

    Aponta `db.DB_PATH` para um arquivo dentro do tmp_path do pytest, de modo
    que nenhum teste suje o banco real nem dependa de outro.
    """
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    # O context manager dispara o evento de startup do FastAPI.
    with TestClient(main.app) as c:
        yield c
