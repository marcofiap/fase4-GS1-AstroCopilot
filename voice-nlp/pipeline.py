"""
Pipeline da Frente 2: STT -> agente (RAG) -> TTS + classificacao de intencao.

A funcao `process_voice` e chamada pelo backend em POST /api/voice. O callback
`ask_agent` deve encapsular a mesma logica de POST /api/agent/query (incluindo
auditoria), tipicamente via agent-rag/agent.query no orquestrador.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import project_env  # noqa: F401 — garante raiz/.env em execucao direta do pipeline

import intent
import stt
import tts

AskAgent = Callable[[str], dict[str, Any]]


def process_voice(
    audio_bytes: bytes,
    filename: str | None,
    ask_agent: AskAgent,
) -> dict[str, Any]:
    """
    Executa o ciclo completo de voz.

    Retorna:
        transcript, intent, answer_text, sources, answer_audio_file (Path | None)
    """
    transcript = stt.transcribe(audio_bytes, filename=filename)
    classificacao = intent.classify(transcript)

    resultado = ask_agent(transcript)
    answer_text = (resultado.get("answer") or "").strip()
    sources = resultado.get("sources") or []

    audio_path = None
    if answer_text:
        try:
            audio_path = tts.synthesize(answer_text)
        except Exception as exc:
            print(f"[Frente 2] TTS falhou (resposta so em texto): {exc}")

    return {
        "transcript": transcript,
        "intent": classificacao,
        "answer_text": answer_text,
        "sources": sources,
        "answer_audio_file": audio_path,
    }


if __name__ == "__main__":
    # Teste local: python pipeline.py caminho/para/audio.wav
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Uso: python pipeline.py <arquivo.wav|webm|mp3>")
        raise SystemExit(1)

    caminho = Path(sys.argv[1])
    dados = caminho.read_bytes()

    def _mock_agent(texto: str) -> dict:
        return {
            "answer": f"[teste local] Voce perguntou: {texto}",
            "sources": ["Manual de teste"],
        }

    saida = process_voice(dados, caminho.name, _mock_agent)
    print("TRANSCRICAO:", saida["transcript"])
    print("INTENCAO:", saida["intent"])
    print("RESPOSTA:", saida["answer_text"])
    print("AUDIO:", saida["answer_audio_file"])