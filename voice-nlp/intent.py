"""
Classificador de intencao (MVP) — regras em portugues.

Stretch: modelo supervisionado ou analise de emocao na voz.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Literal

Intent = Literal["pergunta", "status", "emergencia"]

_EMERGENCIA = (
    "emergencia", "urgente", "socorro", "ajuda imediata", "evacuacao",
    "despressurizacao critica", "incendio", "vazamento", "panico",
)
_STATUS = (
    "status", "como esta", "telemetria", "sinais vitais", "bateria",
    "nivel de oxigenio", "spo2", "frequencia cardiaca", "tripulacao",
)


def _normalize(text: str) -> str:
    t = text.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"\s+", " ", t)
    return t


def classify(text: str) -> Intent:
    """Classifica a fala transcrita em pergunta, status ou emergencia."""
    norm = _normalize(text)
    if not norm:
        return "pergunta"

    for frase in _EMERGENCIA:
        if frase in norm:
            return "emergencia"

    for frase in _STATUS:
        if frase in norm:
            return "status"

    if norm.endswith("?"):
        return "pergunta"

    if any(norm.startswith(p) for p in ("como ", "qual ", "quais ", "onde ", "quando ", "por que ")):
        return "pergunta"

    return "pergunta"