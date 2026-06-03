"""
Atalhos para rodar a Frente 1 com o .env da RAIZ, sem alterar agent-rag/config.py.

O config.py original usa find_dotenv(usecwd=True): se existir agent-rag/.env,
ele ignora o .env da raiz. Este script carrega a raiz antes e evita esse conflito.

Uso (na raiz ou em voice-nlp/):
    python voice-nlp/run_rag.py agent "Como agir em caso de despressurizacao?"
    python voice-nlp/run_rag.py ingest
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

import project_env

AGENT_RAG_DIR = project_env.PROJECT_ROOT / "agent-rag"


def _run_agent(argv: list[str]) -> None:
    sys.argv = ["agent.py", *argv]
    runpy.run_path(str(AGENT_RAG_DIR / "agent.py"), run_name="__main__")


def _run_ingest() -> None:
    sys.argv = ["ingest.py"]
    runpy.run_path(str(AGENT_RAG_DIR / "ingest.py"), run_name="__main__")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)

    if project_env.load_project_env() is None:
        print("Nenhum .env encontrado. Copie .env.example para a raiz do projeto.")
        raise SystemExit(1)

    cmd = sys.argv[1].lower()
    rest = sys.argv[2:]

    if cmd == "agent":
        _run_agent(rest)
    elif cmd == "ingest":
        _run_ingest()
    else:
        print(f"Comando desconhecido: {cmd}. Use: agent | ingest")
        raise SystemExit(1)


if __name__ == "__main__":
    main()