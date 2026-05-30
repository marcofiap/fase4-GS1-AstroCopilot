"""Testes do classificador de risco (regras placeholder da Frente 4)."""
import pytest

from main import classify_risk


def test_normal_em_repouso():
    assert classify_risk(hr=72, spo2=98, temp=36.6) == "normal"


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
    assert classify_risk(**kwargs) == "fadiga"


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
    assert classify_risk(**kwargs) == "risco"


def test_risco_tem_prioridade_sobre_fadiga():
    # SpO2 crítica deve vencer mesmo com demais sinais só em fadiga.
    assert classify_risk(hr=115, spo2=80, temp=37.9) == "risco"
