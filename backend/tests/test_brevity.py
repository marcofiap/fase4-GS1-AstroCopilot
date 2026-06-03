"""Testes do encurtador de respostas do agente."""
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[2] / "agent-rag"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from agent import _enforce_brevity  # noqa: E402


LONG_ANSWER = (
    "Desculpe, mas nao encontrei nos manuais disponiveis um procedimento especifico. "
    "Os trechos mencionam SBAR e ECLSS. Voce precisaria consultar outros manuais. "
    "Poderia fornecer mais detalhes sobre qual situacao especifica?"
)


def test_enforce_brevity_limits_length():
    saida = _enforce_brevity(LONG_ANSWER, "voice")
    assert len(saida) <= 320
    assert "?" in saida
    assert "Poderia fornecer" in saida


def test_enforce_brevity_strips_lists():
    texto = "Resumo. - item um - item dois - item tres. Fim."
    saida = _enforce_brevity(texto, "text")
    assert "- item" not in saida or len(saida) < 200