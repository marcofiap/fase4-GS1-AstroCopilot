"""
Configuracao da Frente 1 (Agente LLM + RAG).

Le as variaveis de ambiente uma unica vez e expoe constantes simples usadas pelo
ingest e pelo agente. As credenciais ficam em um arquivo .env (nao versionado);
em desenvolvimento ele e procurado subindo a partir do diretorio atual.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Carrega o .env mais proximo (procura a partir do diretorio atual para cima).
load_dotenv(find_dotenv(usecwd=True))

# --- Bedrock / credenciais ------------------------------------------------- #
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
# A API key do Bedrock (bearer token). O Strands a le via esta mesma variavel.
BEDROCK_API_KEY = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
# Modelo de geracao (inference profile regional por padrao).
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
# Modelo de embeddings (Amazon Titan Text Embeddings v2).
EMBED_MODEL_ID = os.getenv("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
BEDROCK_ENDPOINT = f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com"

# --- Caminhos e base vetorial ---------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent
VECTORSTORE_DIR = Path(os.getenv("VECTORSTORE_DIR", str(BASE_DIR / "vectorstore")))
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
COLLECTION = "manuais"

# --- Parametros de RAG ------------------------------------------------------ #
TOP_K = int(os.getenv("RAG_TOP_K", "4"))
CHUNK_CHARS = int(os.getenv("RAG_CHUNK_CHARS", "1000"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))


def configurado() -> bool:
    """Indica se o RAG esta pronto: precisa da API key e da base vetorial populada.

    A base so e considerada pronta quando o arquivo chroma.sqlite3 existe, ou seja,
    apos rodar o ingest (a pasta vectorstore/ sozinha tem apenas o .gitkeep).
    """
    return bool(BEDROCK_API_KEY) and (VECTORSTORE_DIR / "chroma.sqlite3").exists()
