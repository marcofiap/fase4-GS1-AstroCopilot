# agent-rag/ - Agente LLM + RAG + Scraping (Frente 1)

Coleta manuais espaciais publicos (NASA NTRS), monta a base vetorial (ChromaDB) e um
agente que responde perguntas da tripulacao com citacao de fonte. O backend consome
este agente no endpoint `POST /api/agent/query`.

## Responsavel
Frente 1 - Agente LLM + RAG + Scraping.

## Como funciona

- LLM de geracao: Claude Haiku 4.5 no Amazon Bedrock, via agente Strands.
- Embeddings: Amazon Titan Text Embeddings v2 no Bedrock (chamada HTTP com a API key).
- Documentos: resumos (abstracts) dos manuais obtidos pela API do NTRS, mais o texto
  completo do PDF quando o download esta disponivel.
- Base vetorial: ChromaDB persistente em `vectorstore/` (nao versionada).
- Autenticacao: somente a API key do Bedrock (variavel `AWS_BEARER_TOKEN_BEDROCK`),
  sem credenciais AWS tradicionais.

## Estrutura

| Arquivo | Descricao |
|---------|-----------|
| `config.py` | Le as variaveis de ambiente e define caminhos e parametros |
| `embeddings.py` | Funcao de embeddings Titan via HTTP + API key |
| `ingest.py` | Scraping no NTRS, download de PDFs, chunking e indexacao no ChromaDB |
| `agent.py` | Cadeia RAG com Strands e a funcao `query(text)` usada pelo backend |
| `data/` | PDFs baixados (nao versionado) |
| `vectorstore/` | Base vetorial ChromaDB (nao versionada) |

## Passo a passo

1. Crie o arquivo `.env` na RAIZ do projeto a partir do exemplo e preencha a API key:

   ```bash
   cp agent-rag/.env.example .env
   # edite .env e preencha AWS_BEARER_TOKEN_BEDROCK
   ```

   Garanta que os modelos Claude Haiku 4.5 e Titan Embeddings v2 estao habilitados na
   sua conta do Bedrock, na regiao escolhida.

2. Instale as dependencias (use Python 3.12 ou 3.13):

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r agent-rag/requirements.txt
   ```

3. Rode a ingestao (coleta os manuais e popula a base vetorial):

   ```bash
   cd agent-rag && python ingest.py
   ```

   Se a sua rede bloquear o download de PDFs do NTRS, indexe apenas os resumos:

   ```bash
   INGEST_SKIP_PDF=1 python ingest.py
   ```

4. Teste o agente isolado:

   ```bash
   python agent.py "Como agir em caso de despressurizacao da cabine?"
   ```

## Integracao com o backend

O backend adiciona esta pasta ao `sys.path` e importa `agent.query`. Se a API key ou a
base vetorial nao estiverem presentes, o endpoint responde em modo limitado, sem quebrar.
As dependencias de runtime ja estao em `backend/requirements.txt`; para o Docker, a pasta
e montada como volume (ver `docker-compose.yml`).

## Escopo (MVP)
RAG sobre 20 a 50 documentos com resposta e fonte citada. O stretch (agente acionando
visao e telemetria como ferramentas) fica fora desta entrega.
