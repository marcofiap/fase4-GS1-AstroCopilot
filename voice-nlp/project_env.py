"""
Carrega variaveis de ambiente para integrar voice-nlp + agent-rag no backend.

- Prioriza `.env` na raiz do repositorio.
- Se a chave Bedrock so existir em `agent-rag/.env` (RAG isolado), faz fallback.
- `sync_agent_rag_config()` atualiza BEDROCK_API_KEY no config.py ja importado
  (ele e definido uma vez na importacao do modulo).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

VOICE_NLP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = VOICE_NLP_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"
LEGACY_ENV_FILE = PROJECT_ROOT / "agent-rag" / ".env"

_BEDROCK_NAMES = ("AWS_BEARER_TOKEN_BEDROCK", "BEDROCK_API_KEY", "API_KEY")


def bedrock_token() -> str:
    for name in _BEDROCK_NAMES:
        valor = os.getenv(name, "").strip()
        if valor:
            return valor
    return ""


def _apply_bedrock_aliases() -> None:
    token = bedrock_token()
    if token:
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token


def load_project_env() -> Path | None:
    """Carrega envs e normaliza a API Bedrock. Retorna o arquivo principal usado."""
    principal: Path | None = None

    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE, override=True)
        principal = ENV_FILE

    if LEGACY_ENV_FILE.is_file():
        # Preenche chaves que faltarem na raiz (sem apagar as ja definidas).
        load_dotenv(LEGACY_ENV_FILE, override=False)
        if not bedrock_token():
            load_dotenv(LEGACY_ENV_FILE, override=True)
        if principal is None:
            principal = LEGACY_ENV_FILE

    _apply_bedrock_aliases()
    return principal


def sync_agent_rag_config() -> bool:
    """Reaplica o token no agent-rag/config.py apos import (necessario no backend)."""
    cfg = sys.modules.get("config")
    if cfg is None:
        return False
    base = getattr(cfg, "BASE_DIR", None)
    if base is None or Path(base).name != "agent-rag":
        return False

    token = bedrock_token()
    if not token:
        return False

    cfg.BEDROCK_API_KEY = token
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
    return True


# Backend importa este modulo antes do agent-rag.
load_project_env()