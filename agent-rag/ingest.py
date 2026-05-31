"""
Ingestao da base de conhecimento (Frente 1).

Busca manuais espaciais publicos na API do NASA NTRS, baixa os PDFs, extrai o texto,
divide em trechos (chunks), gera os embeddings com o Titan e grava tudo no ChromaDB.

Uso:
    python ingest.py

Pre-requisitos: .env com AWS_BEARER_TOKEN_BEDROCK preenchido (ver .env.example).
"""
from __future__ import annotations

import os
import time

import chromadb
import requests
from pypdf import PdfReader

import config
import embeddings

NTRS = "https://ntrs.nasa.gov"

# Termos de busca. Cada termo rende varios documentos; o total alvo fica entre 20 e 50.
TERMOS = [
    "spacecraft cabin pressurization",
    "extravehicular activity procedures",
    "life support systems ECLSS",
    "astronaut health monitoring",
    "spacecraft emergency procedures",
    "space radiation crew protection",
]
DOCS_POR_TERMO = 6
MAX_DOCS = 40  # teto de seguranca para nao baixar demais


def buscar(termo: str, n: int) -> list[dict]:
    """Busca citacoes no NTRS. Retorna [{id, titulo, abstract, pdf_url}].

    Indexamos sempre o resumo (abstract), que ja vem na resposta da busca, e
    usamos o PDF completo como complemento quando o download esta disponivel.
    """
    resp = requests.get(
        f"{NTRS}/api/citations/search",
        params={"q": termo, "page.size": n},
        timeout=30,
    )
    resp.raise_for_status()
    achados = []
    for item in resp.json().get("results", []):
        abstract = (item.get("abstract") or "").strip()
        if not abstract:
            continue  # sem texto util para indexar
        achados.append({
            "id": item["id"],
            "titulo": item.get("title", "Documento"),
            "abstract": abstract,
            "pdf_url": _link_pdf(item),  # pode ser None
        })
    return achados


def _link_pdf(item: dict) -> str | None:
    """Extrai a URL absoluta do primeiro PDF (nao rascunho) de uma citacao."""
    for dl in item.get("downloads", []):
        if dl.get("mimetype") == "application/pdf" and not dl.get("draft"):
            caminho = dl.get("links", {}).get("pdf") or dl.get("links", {}).get("original")
            if caminho:
                return NTRS + caminho if caminho.startswith("/") else caminho
    return None


def baixar(doc: dict):
    """Baixa o PDF para data/ (best-effort). Retorna o caminho ou None.

    Alguns ambientes nao conseguem baixar do NTRS (o endpoint de download pode
    bloquear robos); nesse caso seguimos so com o resumo. Reutiliza se ja existe.
    """
    # INGEST_SKIP_PDF=1 indexa so os resumos (util onde o NTRS bloqueia o download).
    if not doc.get("pdf_url") or os.getenv("INGEST_SKIP_PDF"):
        return None
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    destino = config.DATA_DIR / f"{doc['id']}.pdf"
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    try:
        resp = requests.get(
            doc["pdf_url"], timeout=(10, 20),
            headers={"User-Agent": "AstroCopilot-FIAP/1.0"},
        )
        resp.raise_for_status()
        destino.write_bytes(resp.content)
        return destino
    except Exception:
        print(f"  {doc['id']}: PDF indisponivel, usando so o resumo")
        return None


def extrair_texto(caminho) -> str:
    """Extrai o texto de todas as paginas de um PDF."""
    try:
        leitor = PdfReader(str(caminho))
        return "\n".join((pagina.extract_text() or "") for pagina in leitor.pages)
    except Exception as exc:
        print(f"  falha ao ler PDF {caminho.name}: {exc}")
        return ""


def chunk(texto: str) -> list[str]:
    """Divide o texto em janelas de CHUNK_CHARS com sobreposicao CHUNK_OVERLAP."""
    texto = " ".join(texto.split())  # normaliza espacos e quebras de linha
    passo = config.CHUNK_CHARS - config.CHUNK_OVERLAP
    pedacos = [texto[i:i + config.CHUNK_CHARS] for i in range(0, len(texto), passo)]
    # Descarta pedacos muito curtos (ruido do final do documento).
    return [p for p in pedacos if len(p) > 100]


def main() -> None:
    if not config.BEDROCK_API_KEY:
        raise SystemExit(
            "AWS_BEARER_TOKEN_BEDROCK ausente. Preencha o .env (ver .env.example) e tente de novo."
        )

    print(f"Coletando documentos do NASA NTRS (alvo: ate {MAX_DOCS})...")
    selecionados: dict[int, dict] = {}
    for termo in TERMOS:
        if len(selecionados) >= MAX_DOCS:
            break
        try:
            for doc in buscar(termo, DOCS_POR_TERMO):
                if doc["id"] not in selecionados and len(selecionados) < MAX_DOCS:
                    selecionados[doc["id"]] = doc
        except Exception as exc:
            print(f"  busca falhou para '{termo}': {exc}")
        time.sleep(0.5)  # respeita o rate limit do NTRS

    print(f"{len(selecionados)} documentos selecionados. Baixando e indexando...")

    client = chromadb.PersistentClient(path=str(config.VECTORSTORE_DIR))
    colecao = client.get_or_create_collection(config.COLLECTION)

    total_docs = 0
    total_chunks = 0
    for doc in selecionados.values():
        partes = [doc["abstract"]]
        caminho = baixar(doc)
        if caminho:
            texto_pdf = extrair_texto(caminho)
            if texto_pdf.strip():
                partes.append(texto_pdf)
        trechos = chunk("\n\n".join(partes))
        if not trechos:
            print(f"  {doc['id']}: sem texto util, ignorado")
            continue

        ids, vetores, documentos, metadados = [], [], [], []
        for i, trecho in enumerate(trechos):
            try:
                vetores.append(embeddings.embed(trecho))
            except Exception as exc:
                print(f"  {doc['id']} chunk {i}: embedding falhou ({exc}), pulando")
                continue
            ids.append(f"{doc['id']}-{i}")
            documentos.append(trecho)
            metadados.append({
                "titulo": doc["titulo"],
                "ntrs_id": str(doc["id"]),
                "url": f"{NTRS}/citations/{doc['id']}",
                "chunk": i,
            })

        if ids:
            colecao.upsert(ids=ids, embeddings=vetores, documents=documentos, metadatas=metadados)
            total_docs += 1
            total_chunks += len(ids)
            print(f"  {doc['id']}: {len(ids)} trechos indexados")

    print("\nIngestao concluida.")
    print(f"  Documentos indexados: {total_docs}")
    print(f"  Trechos (chunks):     {total_chunks}")
    print(f"  Base vetorial:        {config.VECTORSTORE_DIR}")


if __name__ == "__main__":
    main()
