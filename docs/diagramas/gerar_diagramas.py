"""
Gera os diagramas do projeto AstroCopilot (Frente 5 / docs).
Saída: arquitetura.png e disciplinas.png em docs/diagramas/.
Uso: python docs/diagramas/gerar_diagramas.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent

BG = "#060a16"
PANEL = "#0b1226"
BORDER = "#1e2a44"
TEXT = "#e6edff"
ACCENT = "#38bdf8"
COLORS = {
    "f1": "#a78bfa",  # RAG
    "f2": "#34d399",  # Voz
    "f3": "#f59e0b",  # Visão
    "f4": "#f472b6",  # IoT
    "f5": "#38bdf8",  # Backend/Dash
}


def _box(ax, x, y, w, h, title, subtitle, color):
    box = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=2, edgecolor=color, facecolor=PANEL, mutation_aspect=1,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center",
            color=TEXT, fontsize=11, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center",
            color="#9fb0d8", fontsize=8.5)


def _arrow(ax, p1, p2, color=ACCENT):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=14,
        linewidth=1.6, color=color, shrinkA=2, shrinkB=2,
    ))


def arquitetura():
    fig, ax = plt.subplots(figsize=(11, 7.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")

    ax.text(6, 7.6, "AstroCopilot — Arquitetura da POC", ha="center",
            color=TEXT, fontsize=16, fontweight="bold")
    ax.text(6, 7.2, "Copiloto conversacional para tripulações espaciais · GS 2026.1 FIAP",
            ha="center", color="#9fb0d8", fontsize=9.5)

    # Camada de entrada (tripulante)
    _box(ax, 0.4, 5.6, 2.5, 1.0, "Voz (F2)", "STT Whisper + TTS", COLORS["f2"])
    _box(ax, 3.2, 5.6, 2.5, 1.0, "Câmera (F3)", "Visão CV + OCR", COLORS["f3"])
    _box(ax, 6.0, 5.6, 2.5, 1.0, "Wearable ESP32 (F4)", "Sinais vitais", COLORS["f4"])
    _box(ax, 8.9, 5.6, 2.7, 1.0, "Texto/Wake word", '"Astro" (navegador)', COLORS["f5"])

    # Backend orquestrador
    _box(ax, 2.6, 3.5, 6.8, 1.1, "BACKEND FastAPI (F5)",
         "REST + WebSocket · orquestra todas as frentes", COLORS["f5"])

    # Camada inferior
    _box(ax, 0.4, 1.4, 2.7, 1.1, "Agente RAG (F1)",
         "Bedrock + ChromaDB\nmanuais NASA NTRS", COLORS["f1"])
    _box(ax, 3.5, 1.4, 2.7, 1.1, "Modelo ML (F4)",
         "RandomForest\nclassifica risco", COLORS["f4"])
    _box(ax, 6.6, 1.4, 2.7, 1.1, "SQLite (F5)",
         "alertas + auditoria\n(governança)", COLORS["f5"])
    _box(ax, 9.0, 1.4, 2.6, 1.1, "Dashboard (F5)",
         "React + Vite\ntempo real", COLORS["f5"])

    # Setas entrada -> backend
    for cx in (1.65, 4.45, 7.25, 10.25):
        _arrow(ax, (cx, 5.6), (min(max(cx, 3.0), 9.0), 4.6), color=BORDER)
    # Backend -> inferior
    for cx in (1.75, 4.85, 7.95, 10.3):
        _arrow(ax, (6.0, 3.5), (cx, 2.5), color=BORDER)

    # Legenda
    handles = [
        mpatches.Patch(color=COLORS["f1"], label="F1 · RAG/LLM"),
        mpatches.Patch(color=COLORS["f2"], label="F2 · NLP/Voz"),
        mpatches.Patch(color=COLORS["f3"], label="F3 · Visão"),
        mpatches.Patch(color=COLORS["f4"], label="F4 · IoT/ML"),
        mpatches.Patch(color=COLORS["f5"], label="F5 · Backend/Dash/DevOps"),
    ]
    leg = ax.legend(handles=handles, loc="lower center", ncol=5,
                    bbox_to_anchor=(0.5, -0.02), frameon=False, fontsize=8.5)
    for txt in leg.get_texts():
        txt.set_color(TEXT)

    fig.tight_layout()
    fig.savefig(OUT / "arquitetura.png", dpi=160, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print("gerado: arquitetura.png")


def disciplinas():
    """Mapa de disciplinas das Fases 3/4 cobertas por frente."""
    fig, ax = plt.subplots(figsize=(11, 6.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.text(0.5, 0.96, "Cobertura de Disciplinas (Fases 3 e 4)", transform=ax.transAxes,
            ha="center", color=TEXT, fontsize=16, fontweight="bold")

    linhas = [
        ("F1 · RAG/LLM", "IA Generativa · RAG · Prompt Engineering · Scraping/APIs (NTRS)", COLORS["f1"]),
        ("F2 · NLP/Voz", "NLP profundo · Speech-to-Text (Whisper) · Text-to-Speech", COLORS["f2"]),
        ("F3 · Visão", "Visão Computacional · Detecção de objetos · OCR de painéis", COLORS["f3"]),
        ("F4 · IoT/ML", "ESP32 · Edge/Fog · Machine Learning · LoRa/BLE/WiFi · Energia", COLORS["f4"]),
        ("F5 · Plataforma", "React+Vite · Tempo real · CI/CD · Docker · Governança/Ética", COLORS["f5"]),
    ]
    y = 0.80
    for nome, desc, cor in linhas:
        chip = FancyBboxPatch((0.04, y - 0.05), 0.24, 0.1,
                              boxstyle="round,pad=0.01,rounding_size=0.02",
                              transform=ax.transAxes, linewidth=2,
                              edgecolor=cor, facecolor=PANEL)
        ax.add_patch(chip)
        ax.text(0.16, y, nome, transform=ax.transAxes, ha="center", va="center",
                color=TEXT, fontsize=10.5, fontweight="bold")
        ax.text(0.31, y, desc, transform=ax.transAxes, ha="left", va="center",
                color="#cdd8f3", fontsize=10)
        y -= 0.15

    fig.savefig(OUT / "disciplinas.png", dpi=160, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print("gerado: disciplinas.png")


if __name__ == "__main__":
    arquitetura()
    disciplinas()
