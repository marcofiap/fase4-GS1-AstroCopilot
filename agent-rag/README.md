# 🧠 agent-rag/ — Agente LLM + RAG + Scraping (Frente 1)

Coleta manuais espaciais públicos, monta a base vetorial e o agente que responde
perguntas com **citação de fonte**.

## Responsável
**Frente 1** — Agente LLM + RAG + Scraping.

## Estrutura
| Pasta/arquivo | Descrição |
|---------------|-----------|
| `ingest/` | Scripts de scraping/download + chunking + geração de embeddings |
| `vectorstore/` | Base vetorial (ChromaDB) — **não versionada** (ver .gitignore) |
| `agent.py` | Cadeia RAG: retrieval + prompt + LLM (a criar) |

## Pipeline
1. **Scraping** de manuais (NASA Technical Reports Server, ESA, docs SpaceX).
2. **Chunking** + **embeddings** → ChromaDB.
3. **Cadeia RAG** com prompt engineering.
4. Expor função consumida pelo backend em `POST /api/agent/query`.

## MVP vs. Stretch
- **MVP:** RAG sobre ~20–50 documentos, resposta com fonte citada.
- **Stretch:** agente com *tools* (aciona visão e telemetria sozinho).

## Disciplinas
F4 C06/C10 (LLM/RAG/Prompting) · F3 C06 (IA Generativa) · F4 C02 + F3 C02 (Scraping/APIs/RPA).
