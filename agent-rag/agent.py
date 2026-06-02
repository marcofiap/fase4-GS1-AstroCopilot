"""
Cadeia RAG da Frente 1 com Strands Agents.

O agente roda sobre o Claude Haiku 4.5 no Bedrock e tem uma ferramenta de busca
(`buscar_documentos`) que recupera trechos dos manuais no ChromaDB. A funcao
publica `query(text)` e o que o backend chama no endpoint POST /api/agent/query.

Autenticacao: o BedrockModel do Strands usa boto3 internamente, e o boto3 le a
API key da variavel de ambiente AWS_BEARER_TOKEN_BEDROCK. Nao usamos credenciais
AWS tradicionais. Os embeddings (Titan) sao chamados via HTTP em embeddings.py.
"""
from __future__ import annotations

import os
from functools import lru_cache

import chromadb
from strands import Agent, tool
from strands.models import BedrockModel

import config
import embeddings

# Garante que o boto3 (interno do Strands) enxergue a API key do Bedrock.
if config.BEDROCK_API_KEY:
    os.environ.setdefault("AWS_BEARER_TOKEN_BEDROCK", config.BEDROCK_API_KEY)

SYSTEM_PROMPT = (
    "Voce e o AstroCopilot, copiloto de bordo de uma tripulacao espacial. "
    "Para qualquer pergunta tecnica ou operacional, use sempre a ferramenta "
    "buscar_documentos para recuperar trechos dos manuais antes de responder. "
    "Responda em portugues do Brasil, de forma objetiva e direta, apenas com base "
    "nos trechos recuperados, e cite as fontes utilizadas no final. Se os trechos "
    "nao cobrirem a pergunta, diga com clareza que nao encontrou a informacao nos "
    "manuais disponiveis, sem inventar."
)


@lru_cache(maxsize=1)
def _modelo() -> BedrockModel:
    """Cria o modelo Bedrock uma unica vez (reaproveitado entre chamadas)."""
    return BedrockModel(
        model_id=config.MODEL_ID,
        region_name=config.AWS_REGION,
        temperature=0.2,
        max_tokens=1024,
        streaming=False,
    )


@lru_cache(maxsize=1)
def _colecao():
    """Abre a colecao do ChromaDB (base vetorial criada pelo ingest)."""
    client = chromadb.PersistentClient(path=str(config.VECTORSTORE_DIR))
    try:
        return client.get_collection(config.COLLECTION)
    except Exception as exc:  # colecao ainda nao criada
        raise RuntimeError(
            "Base vetorial nao encontrada. Rode 'python ingest.py' antes de consultar."
        ) from exc


def query(text: str) -> dict:
    """Responde uma pergunta usando RAG. Retorna {'answer': str, 'sources': list[str]}."""
    if not config.configurado():
        raise RuntimeError("RAG nao configurado (API key ou base vetorial ausente).")

    fontes: list[str] = []

    @tool
    def buscar_documentos(consulta: str) -> str:
        """Busca trechos dos manuais espaciais relevantes para a consulta."""
        resultado = _colecao().query(
            query_embeddings=[embeddings.embed(consulta)],
            n_results=config.TOP_K,
        )
        documentos = resultado["documents"][0]
        metadados = resultado["metadatas"][0]
        if not documentos:
            return "Nenhum trecho encontrado nos manuais."

        blocos = []
        for texto, meta in zip(documentos, metadados):
            etiqueta = f"{meta.get('titulo', 'Documento')} (NTRS {meta.get('ntrs_id', '?')})"
            if etiqueta not in fontes:
                fontes.append(etiqueta)
            blocos.append(f"[Fonte: {etiqueta}]\n{texto}")
        return "\n\n".join(blocos)

    agente = Agent(model=_modelo(), system_prompt=SYSTEM_PROMPT, tools=[buscar_documentos])
    resposta = str(agente(text)).strip()
    return {"answer": resposta, "sources": fontes}


if __name__ == "__main__":
    # Teste rapido pela linha de comando: python agent.py "sua pergunta"
    import sys

    pergunta = sys.argv[1] if len(sys.argv) > 1 else "Como agir em caso de despressurizacao da cabine?"
    resultado = query(pergunta)
    print("PERGUNTA:", pergunta)
    print("\nRESPOSTA:\n", resultado["answer"])
    print("\nFONTES:", resultado["sources"])
