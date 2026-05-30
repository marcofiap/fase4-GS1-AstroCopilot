"""
Persistência (Frente 5 / Governança)
=====================================
SQLite simples para dar durabilidade a dois registros que não podem se perder
ao reiniciar o backend:

  • alerts — histórico de escaladas de risco da tripulação
  • audit  — trilha de auditoria das decisões do agente (pergunta -> resposta ->
             fontes -> timestamp), exigida pela governança de IA.

Abre uma conexão por operação (SQLite lida bem com isso e evita problemas de
thread, já que as rotas síncronas do FastAPI rodam em um threadpool).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "astrocopilot.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria as tabelas se ainda não existirem (idempotente)."""
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ts         TEXT NOT NULL,
                crew_id    TEXT NOT NULL,
                name       TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                message    TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ts       TEXT NOT NULL,
                question TEXT NOT NULL,
                answer   TEXT NOT NULL,
                sources  TEXT NOT NULL,
                channel  TEXT NOT NULL
            )
            """
        )


# --------------------------------------------------------------------------- #
#  Alertas
# --------------------------------------------------------------------------- #
def insert_alert(alert: dict) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO alerts (ts, crew_id, name, risk_level, message) VALUES (?, ?, ?, ?, ?)",
            (alert["ts"], alert["crew_id"], alert["name"], alert["risk_level"], alert["message"]),
        )


def get_alerts(limit: int = 20) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT ts, crew_id, name, risk_level, message FROM alerts ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def count_alerts() -> int:
    with _conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]


# --------------------------------------------------------------------------- #
#  Trilha de auditoria do agente
# --------------------------------------------------------------------------- #
def insert_audit(question: str, answer: str, sources: list[str], channel: str = "text") -> None:
    """Registra uma decisão do agente. `channel` = 'text' | 'voice' | 'vision'."""
    with _conn() as conn:
        conn.execute(
            "INSERT INTO audit (ts, question, answer, sources, channel) VALUES (?, ?, ?, ?, ?)",
            (_now(), question, answer, json.dumps(sources, ensure_ascii=False), channel),
        )


def get_audit(limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT ts, question, answer, sources, channel FROM audit ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["sources"] = json.loads(d["sources"])
        out.append(d)
    return out


def count_audit() -> int:
    with _conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
