"""Fixtures compartilhadas dos testes (Frente 5)."""
import pytest
from fastapi.testclient import TestClient

import db
import main


def _fake_rag(text: str, channel: str = "text") -> dict:
    """Cadeia RAG falsa para os testes: deterministica, sem rede nem Bedrock."""
    return {
        "answer": f"[teste] resposta para: {text} (canal={channel})",
        "sources": ["Manual de teste (NTRS 0000)"],
    }


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Cliente de teste com um SQLite TEMPORÁRIO por teste.

    Aponta `db.DB_PATH` para um arquivo dentro do tmp_path do pytest, de modo
    que nenhum teste suje o banco real nem dependa de outro. Tambem substitui a
    cadeia RAG (Frente 1) por uma versao falsa, para os testes do agente nao
    dependerem do Bedrock nem da base vetorial.
    """
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(main, "rag_query", _fake_rag)
    db.init_db()
    # O context manager dispara o evento de startup do FastAPI.
    with TestClient(main.app) as c:
        yield c
