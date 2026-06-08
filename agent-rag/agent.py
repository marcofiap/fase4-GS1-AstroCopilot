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
import re
import sys
from functools import lru_cache
from pathlib import Path

# Add current folder to sys.path to resolve imports when executed or analyzed from outside agent-rag
_CURRENT_DIR = str(Path(__file__).resolve().parent)
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

import chromadb
from strands import Agent, tool
from strands.models import BedrockModel

import config
import embeddings

# Garante que o boto3 (interno do Strands) enxergue a API key do Bedrock.
if config.BEDROCK_API_KEY:
    os.environ.setdefault("AWS_BEARER_TOKEN_BEDROCK", config.BEDROCK_API_KEY)

GET_CREW_STATE_CALLBACK = None

def register_crew_callback(callback):
    """Permite ao backend registrar uma função para expor a telemetria em tempo real."""
    global GET_CREW_STATE_CALLBACK
    GET_CREW_STATE_CALLBACK = callback

SYSTEM_PROMPT = (
    "Voce e o Astro (AstroCopilot), copiloto de bordo. Use buscar_documentos ou verificar_dados_tripulacao antes de responder.\n\n"
    "REGRAS OBRIGATORIAS (violacao nao permitida):\n"
    "1) MAXIMO 2 frases de conteudo + 1 frase final em forma de pergunta sobre como prosseguir.\n"
    "2) PROIBIDO: listas com bullet, numeracao, mais de 80 palavras no total, paragrafos longos, "
    "pedir ao usuario para consultar outros manuais ou dar orientacoes genericas longas.\n"
    "3) Se nao houver procedimento nos trechos: diga em UMA frase e pergunte como prosseguir.\n"
    "4) Fontes: uma linha curta no final, ex.: Fontes: NTRS X, NTRS Y.\n"
    "5) Pergunta final: Crie uma pergunta final curta (maximo 12 palavras), adaptada ao contexto da "
    "pergunta do usuario e da resposta dada, ajudando a guiar os proximos passos. Evite repetir sempre a mesma pergunta padrao. "
    "Ela DEVE terminar com '?' e ser a ultima frase da resposta.\n"
    "Portugues do Brasil, tom calmo e direto."
)

VOICE_PROMPT_ADDENDUM = (
    "\n\nCanal VOZ: MAXIMO 50 palavras no total. Sem listas. Duas frases + pergunta final."
)

PROCEED_QUESTION = "Como prefere continuar: detalhar mais, ver passos críticos ou outro tema?"


def _enforce_brevity(answer: str, channel: str) -> str:
    """Garante resposta curta mesmo se o LLM extrapolar."""
    texto = re.sub(r"\*\*|__|\*|_", "", answer)
    texto = re.sub(r"\n+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    max_chars = 280 if (channel or "text").lower() == "voice" else 420
    partes = re.split(r"(?<=[.!?])\s+", texto)
    
    content_sentences: list[str] = []
    question_sentences: list[str] = []

    for parte in partes:
        p = parte.strip()
        if not p:
            continue
        if re.match(r"^[-•*]\s", p) or p.count(":") > 1:
            continue
        if p.endswith("?"):
            question_sentences.append(p)
        else:
            content_sentences.append(p)

    selected_content = content_sentences[:2]

    if question_sentences:
        question = question_sentences[0]
    else:
        question = PROCEED_QUESTION

    saida = selected_content + [question]
    resultado = " ".join(saida).strip()

    if len(resultado) > max_chars:
        if len(selected_content) > 1:
            selected_content = selected_content[:1]
            saida = selected_content + [question]
            resultado = " ".join(saida).strip()
        
        if len(resultado) > max_chars:
            max_content_len = max_chars - len(question) - 8
            if max_content_len > 0:
                content_text = " ".join(selected_content)
                if len(content_text) > max_content_len:
                    words = content_text[:max_content_len].rsplit(" ", 1)
                    truncated_content = words[0] if len(words) > 1 else content_text[:max_content_len]
                else:
                    truncated_content = content_text
                resultado = truncated_content.rstrip(".!? ") + ". " + question
            else:
                resultado = question

    return resultado


@lru_cache(maxsize=1)
def _modelo() -> BedrockModel:
    """Cria o modelo Bedrock uma unica vez (reaproveitado entre chamadas)."""
    return BedrockModel(
        model_id=config.MODEL_ID,
        region_name=config.AWS_REGION,
        temperature=0.2,
        max_tokens=280,
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


def query(text: str, channel: str = "text") -> dict:
    """Responde uma pergunta usando RAG. Retorna {'answer': str, 'sources': list[str]}.

    channel: 'text' | 'voice' — em voz as respostas ficam ainda mais curtas.
    """
    if not config.configurado():
        raise RuntimeError("RAG nao configurado (API key ou base vetorial ausente).")

    prompt = SYSTEM_PROMPT
    if (channel or "text").lower() == "voice":
        prompt += VOICE_PROMPT_ADDENDUM

    fontes: list[str] = []

    @tool
    def buscar_documentos(consulta: str) -> str:
        """Busca trechos dos manuais espaciais relevantes para a consulta."""
        resultado = _colecao().query(
            query_embeddings=[embeddings.embed(consulta)],
            n_results=config.TOP_K,
        )
        documentos = resultado.get("documents")
        metadados = resultado.get("metadatas")
        docs_list = documentos[0] if documentos is not None else []
        metas_list = metadados[0] if metadados is not None else []
        if not docs_list:
            return "Nenhum trecho encontrado nos manuais."

        blocos = []
        for texto, meta in zip(docs_list, metas_list):
            meta_dict = meta or {}
            etiqueta = f"{meta_dict.get('titulo', 'Documento')} (NTRS {meta_dict.get('ntrs_id', '?')})"
            if etiqueta not in fontes:
                fontes.append(etiqueta)
            blocos.append(f"[Fonte: {etiqueta}]\n{texto}")
        return "\n\n".join(blocos)

    @tool
    def verificar_dados_tripulacao() -> str:
        """Verifica a telemetria e os dados de saúde mais recentes de toda a tripulação (batimentos, SpO2, temperatura, respiração, radiação, status de risco e bateria)."""
        if "Telemetria em Tempo Real" not in fontes:
            fontes.append("Telemetria em Tempo Real")

        crew_list = None
        if GET_CREW_STATE_CALLBACK is not None:
            try:
                crew_list = GET_CREW_STATE_CALLBACK()
            except Exception:
                pass

        if not crew_list:
            try:
                import requests
                r = requests.get("http://127.0.0.1:8000/api/crew", timeout=1.0)
                if r.status_code == 200:
                    crew_list = r.json().get("crew")
            except Exception:
                pass

        if not crew_list:
            return "Não foi possível obter os dados da tripulação no momento."

        lines = []
        for c in crew_list:
            lines.append(
                f"- {c['name']} ({c['role']}): "
                f"Batimentos: {c['hr']} bpm, "
                f"SpO2: {c['spo2']}%, "
                f"Temp: {c['temp']}°C, "
                f"Resp: {c['resp']} rpm, "
                f"Radiação: {c['radiation']} µSv/h, "
                f"Bateria: {c['battery']}%, "
                f"Status: {c['risk_level']}"
            )
        return "\n".join(lines)

    agente = Agent(model=_modelo(), system_prompt=prompt, tools=[buscar_documentos, verificar_dados_tripulacao])
    entrada = text
    if (channel or "text").lower() == "voice":
        entrada = f"[Limite: 50 palavras, sem listas]\n{text}"
    resposta = _enforce_brevity(str(agente(entrada)).strip(), channel)
    return {"answer": resposta, "sources": fontes}

if __name__ == "__main__":
    # Teste rapido pela linha de comando: python agent.py "sua pergunta"
    import sys

    pergunta = sys.argv[1] if len(sys.argv) > 1 else "Como agir em caso de despressurizacao da cabine?"
    resultado = query(pergunta)
    print("PERGUNTA:", pergunta)
    print("\nRESPOSTA:\n", resultado["answer"])
    print("\nFONTES:", resultado["sources"])
