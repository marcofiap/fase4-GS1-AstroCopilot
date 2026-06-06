"""
Treino do classificador de risco do tripulante
===================================================================
Gera um dataset SINTÉTICO físico-plausível, rotula segundo a política de risco
da missão (os mesmos limiares de `backend/main.py:classify_risk`) e treina um
RandomForest que substitui as regras no backend.

Por que NÃO vira "if/else disfarçado":
  - As features são amostradas de forma FÍSICO-PLAUSÍVEL e CORRELACIONADA
    (estresse alto → HR/resp sobem, SpO2 cai, temp sobe) via uma variável
    latente; a radiação é ambiental e quase independente.
  - O rótulo é definido sobre o estado VERDADEIRO; o modelo treina sobre uma
    leitura COM RUÍDO DE SENSOR. Assim ele aprende uma fronteira DIFUSA e
    tolera ruído — ganho real sobre o threshold rígido e quebradiço.

Saídas (na mesma pasta deste arquivo):
  - model.pkl      : bundle joblib {model, features, labels, sklearn_version}
  - metrics.txt    : relatório de métricas para citar no PDF
  - confusion_matrix.png (se matplotlib estiver instalado)

Uso:
    pip install -r requirements.txt
    python train_model.py
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# --------------------------------------------------------------------------- #
#  Contrato de features/rótulos — DEVE bater com backend/main.py:classify_risk
#  A ordem das features é a ordem do vetor que o backend monta para predizer.
# --------------------------------------------------------------------------- #
FEATURES = ["hr", "spo2", "temp", "radiation", "resp"]
LABELS = ["normal", "fadiga", "risco"]  # ordem de severidade crescente

SEED = 42
N_PHYSIO = 7000   # amostras correlacionadas (corpo sob estresse)
N_UNIFORM = 3000  # amostras uniformes (cobrem cantos: resp<8, picos isolados)

HERE = Path(__file__).resolve().parent

# Faixas físicas válidas para recorte (clip) — [mín, máx] por feature
RANGE = {
    "hr": (40.0, 200.0),
    "spo2": (70.0, 100.0),
    "temp": (34.0, 42.0),
    "radiation": (0.0, 25.0),
    "resp": (3.0, 45.0),
}
# Desvio-padrão do RUÍDO DE SENSOR adicionado à leitura observada (por feature)
SENSOR_SIGMA = np.array([2.0, 0.6, 0.10, 0.15, 0.8])


def _clip(X: np.ndarray) -> np.ndarray:
    """Recorta cada coluna para sua faixa física válida (in-place-safe)."""
    out = X.copy()
    for i, f in enumerate(FEATURES):
        lo, hi = RANGE[f]
        out[:, i] = np.clip(out[:, i], lo, hi)
    return out


def _physio_samples(rng: np.random.Generator, n: int) -> np.ndarray:
    """Amostras correlacionadas por uma variável latente de 'estresse' [0,1].

    Estresse alto puxa HR, respiração e temperatura para cima e SpO2 para baixo.
    A radiação é ambiental (não ligada ao corpo): base baixa + picos esporádicos.
    """
    stress = rng.uniform(0.0, 1.0, n)  # cobertura ampla do espaço de features
    hr = 70 + 75 * stress + rng.normal(0, 5, n)
    resp = 13 + 17 * stress + rng.normal(0, 1.2, n)
    spo2 = 99 - 12 * stress + rng.normal(0, 0.8, n)
    temp = 36.5 + 2.4 * stress + rng.normal(0, 0.12, n)

    rad = np.abs(rng.normal(0.3, 0.4, n))           # fundo baixo
    spike = rng.random(n) < 0.12                    # ~12% com tempestade solar
    rad[spike] += rng.exponential(3.0, int(spike.sum()))

    return np.column_stack([hr, spo2, temp, rad, resp])


def _uniform_samples(rng: np.random.Generator, n: int) -> np.ndarray:
    """Amostras uniformes em toda a faixa — cobrem cantos que o modelo físico
    raramente gera (ex.: bradipneia resp<8, pico isolado de radiação)."""
    hr = rng.uniform(45, 185, n)
    spo2 = rng.uniform(80, 100, n)
    temp = rng.uniform(35.0, 40.5, n)
    rad = rng.uniform(0, 8, n)
    resp = rng.uniform(4, 33, n)  # inclui o canto resp<8
    return np.column_stack([hr, spo2, temp, rad, resp])


def _label(X: np.ndarray) -> np.ndarray:
    """Rotula pelo estado VERDADEIRO usando os limiares de
    backend/main.py:classify_risk (risco tem prioridade sobre fadiga)."""
    hr, spo2, temp, rad, resp = X.T
    risco = (spo2 < 90) | (hr > 140) | (temp > 38.5) | (rad > 5.0) | (resp > 28)
    fadiga = (
        (spo2 < 94) | (hr > 110) | (temp > 37.8)
        | (rad > 1.0) | (resp > 24) | (resp < 8)
    )
    return np.where(risco, "risco", np.where(fadiga, "fadiga", "normal"))


def build_dataset(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Monta (X_observado, y). y vem do estado verdadeiro; X recebe ruído de
    sensor para o modelo aprender uma fronteira difusa e robusta."""
    X_true = np.vstack([_physio_samples(rng, N_PHYSIO),
                        _uniform_samples(rng, N_UNIFORM)])
    X_true = _clip(X_true)
    y = _label(X_true)

    X_obs = _clip(X_true + rng.normal(0, SENSOR_SIGMA, X_true.shape))
    return X_obs, y


def main() -> None:
    rng = np.random.default_rng(SEED)
    X, y = build_dataset(rng)

    # Distribuição de classes (importante: deve haver as 3 classes representadas)
    classes, counts = np.unique(y, return_counts=True)
    dist = dict(zip(classes.tolist(), counts.tolist()))

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=SEED
    )

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=16,          # limita o tamanho do modelo (pkl menor p/ git)
        min_samples_leaf=5,    # regulariza ruído de rótulo + reduz nº de nós
        class_weight="balanced",
        random_state=SEED,
        n_jobs=-1,
    )
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    report = classification_report(y_te, y_pred, labels=LABELS, digits=3)
    cm = confusion_matrix(y_te, y_pred, labels=LABELS)
    importances = dict(zip(FEATURES, model.feature_importances_.round(4).tolist()))

    # ---- Relatório (stdout + metrics.txt) ---- #
    lines = [
        "AstroCopilot — Frente 4 — Modelo de risco (RandomForest)",
        "=" * 56,
        f"scikit-learn  : {sklearn.__version__}",
        f"Seed          : {SEED}",
        f"Amostras      : {len(y)} (treino {len(y_tr)} / teste {len(y_te)})",
        f"Distribuição  : {dist}",
        "",
        f"Acurácia (teste): {acc:.3%}",
        "",
        "Relatório de classificação:",
        report,
        "Matriz de confusão (linhas=verdadeiro, colunas=previsto):",
        f"  ordem: {LABELS}",
        np.array2string(cm),
        "",
        "Importância das features:",
        json.dumps(importances, ensure_ascii=False, indent=2),
    ]
    out = "\n".join(lines)
    print(out)
    (HERE / "metrics.txt").write_text(out + "\n", encoding="utf-8")

    # ---- Bundle do modelo (auto-descritivo p/ o backend) ---- #
    bundle = {
        "model": model,
        "features": FEATURES,      # ordem do vetor de entrada
        "labels": LABELS,
        "sklearn_version": sklearn.__version__,
    }
    joblib.dump(bundle, HERE / "model.pkl", compress=3)  # comprime p/ caber no git
    size_kb = (HERE / "model.pkl").stat().st_size / 1024
    print(f"\nmodel.pkl salvo em {HERE / 'model.pkl'} ({size_kb:.0f} KB)")

    # ---- Matriz de confusão em PNG (opcional, bom para o PDF) ---- #
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(4.5, 4))
        im = ax.imshow(cm, cmap="Blues")
        ax.set_xticks(range(len(LABELS)), LABELS)
        ax.set_yticks(range(len(LABELS)), LABELS)
        ax.set_xlabel("Previsto")
        ax.set_ylabel("Verdadeiro")
        ax.set_title(f"Matriz de confusão (acc {acc:.1%})")
        for i in range(len(LABELS)):
            for j in range(len(LABELS)):
                ax.text(j, i, cm[i, j], ha="center", va="center",
                        color="white" if cm[i, j] > cm.max() / 2 else "black")
        fig.colorbar(im, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(HERE / "confusion_matrix.png", dpi=130)
        print(f"confusion_matrix.png salvo em {HERE / 'confusion_matrix.png'}")
    except ImportError:
        print("(matplotlib ausente — pulei o PNG; instale para gerar a figura)")


if __name__ == "__main__":
    main()
