"""
Embeddings via Amazon Titan no Bedrock, usando a API key (chamada HTTP direta).

Mantemos a chamada simples e sem boto3: um POST no endpoint InvokeModel do Bedrock
com o cabecalho Authorization: Bearer <API_KEY>. A mesma funcao e usada na ingestao
(para indexar os trechos) e no agente (para vetorizar a pergunta).
"""
from __future__ import annotations

import requests

import config


def embed(texto: str) -> list[float]:
    """Gera o vetor de embedding de um texto. Levanta excecao em caso de falha."""
    if not config.BEDROCK_API_KEY:
        raise RuntimeError(
            "AWS_BEARER_TOKEN_BEDROCK ausente. Preencha o .env com a API key do Bedrock."
        )

    url = f"{config.BEDROCK_ENDPOINT}/model/{config.EMBED_MODEL_ID}/invoke"
    headers = {
        "Authorization": f"Bearer {config.BEDROCK_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = requests.post(url, headers=headers, json={"inputText": texto}, timeout=30)
    resp.raise_for_status()
    return resp.json()["embedding"]
