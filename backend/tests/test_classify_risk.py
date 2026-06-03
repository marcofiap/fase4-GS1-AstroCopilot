"""Testes do classificador de risco (Frente 4): regras (política), fallback e ML."""
import pytest

import main
from main import _classify_risk_rules, classify_risk, load_model


# --------------------------------------------------------------------------- #
#  Política de risco — testa as REGRAS diretamente (determinístico, fonte da
#  verdade), independente de o modelo ML estar carregado ou não.
# --------------------------------------------------------------------------- #
def test_normal_em_repouso():
    assert _classify_risk_rules(hr=72, spo2=98, temp=36.6) == "normal"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"hr": 120, "spo2": 98, "temp": 36.6},   # taquicardia leve
        {"hr": 72, "spo2": 92, "temp": 36.6},    # SpO2 baixa
        {"hr": 72, "spo2": 98, "temp": 38.0},    # febre
        {"hr": 72, "spo2": 98, "temp": 36.6, "radiation": 2.0},  # radiação
        {"hr": 72, "spo2": 98, "temp": 36.6, "resp": 26},        # respiração alta
    ],
)
def test_fadiga(kwargs):
    assert _classify_risk_rules(**kwargs) == "fadiga"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"hr": 160, "spo2": 98, "temp": 36.6},   # taquicardia severa
        {"hr": 72, "spo2": 85, "temp": 36.6},    # hipóxia
        {"hr": 72, "spo2": 98, "temp": 39.0},    # febre alta
        {"hr": 72, "spo2": 98, "temp": 36.6, "radiation": 6.0},  # radiação crítica
        {"hr": 72, "spo2": 98, "temp": 36.6, "resp": 30},        # taquipneia
    ],
)
def test_risco(kwargs):
    assert _classify_risk_rules(**kwargs) == "risco"


def test_risco_tem_prioridade_sobre_fadiga():
    # SpO2 crítica deve vencer mesmo com demais sinais só em fadiga.
    assert _classify_risk_rules(hr=115, spo2=80, temp=37.9) == "risco"


# --------------------------------------------------------------------------- #
#  Fallback — sem modelo carregado, classify_risk() usa as regras (não quebra).
# --------------------------------------------------------------------------- #
def test_classify_risk_cai_no_fallback_sem_modelo(monkeypatch):
    monkeypatch.setattr(main, "_model_bundle", None)
    assert classify_risk(hr=72, spo2=98, temp=36.6) == "normal"
    assert classify_risk(hr=160, spo2=85, temp=39.0) == "risco"


# --------------------------------------------------------------------------- #
#  Caminho ML — com o modelo treinado carregado, classifica casos claros certo.
#  Pula se model.pkl ainda não foi gerado (iot-esp32/ml-edge/train_model.py).
# --------------------------------------------------------------------------- #
@pytest.fixture()
def _modelo_ml():
    if not load_model():
        pytest.skip("model.pkl ausente — gere via iot-esp32/ml-edge/train_model.py")
    yield
    main._model_bundle = None  # reseta o estado global após o teste


def test_modelo_ml_carrega_com_contrato_correto(_modelo_ml):
    assert main._model_bundle["features"] == ["hr", "spo2", "temp", "radiation", "resp"]
    assert main._model_bundle["labels"] == ["normal", "fadiga", "risco"]


@pytest.mark.parametrize(
    "args, esperado",
    [
        ((72, 98, 36.6, 0.2, 14), "normal"),
        ((72, 85, 36.6, 0.2, 14), "risco"),    # hipóxia
        ((72, 98, 39.0, 0.2, 14), "risco"),    # febre alta
        ((120, 98, 36.6, 0.2, 14), "fadiga"),  # taquicardia leve
    ],
)
def test_modelo_ml_classifica_casos_claros(_modelo_ml, args, esperado):
    assert classify_risk(*args) == esperado
