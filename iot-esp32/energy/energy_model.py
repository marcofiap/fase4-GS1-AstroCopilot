"""
Modelo de energia do wearable — Frente 4 (AstroCopilot)
=======================================================
O Wokwi NÃO mede consumo, então a autonomia é estimada a partir de números de
datasheet (ESP32 da Espressif; SX1276/LoRa da Semtech) e de um modelo simples de
duty cycle (acordar → enviar → dormir). Gera dois gráficos PNG para o PDF e
imprime as tabelas usadas no relatório.

Uso:
    pip install matplotlib
    python energy_model.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
#  Premissas (datasheet / ordem de grandeza)
# --------------------------------------------------------------------------- #
I_ACTIVE_MA = 120.0   # ESP32 + WiFi, corrente média enquanto acordado
I_DEEP_MA = 0.010     # deep sleep com RTC timer (~10 µA)
T_ACTIVE_S = 3.0      # acordar + associar WiFi + POST
BATT_MAH = 500.0      # bateria LiPo pequena de wearable
I_ALWAYS_ON_MA = 100.0  # WiFi sempre ligado (loop contínuo, sem dormir)


def duty_cycle_autonomy(sleep_s: float) -> tuple[float, float]:
    """Retorna (corrente_média_mA, autonomia_horas) para um intervalo de sono."""
    period = T_ACTIVE_S + sleep_s
    i_avg = (I_ACTIVE_MA * T_ACTIVE_S + I_DEEP_MA * sleep_s) / period
    return i_avg, BATT_MAH / i_avg


def fmt_hours(h: float) -> str:
    if h < 48:
        return f"{h:.1f} h"
    return f"{h / 24:.1f} dias"


# --------------------------------------------------------------------------- #
#  Tabela 1 — autonomia: sempre-ligado vs deep sleep com vários intervalos
# --------------------------------------------------------------------------- #
sleeps = [10, 30, 60, 300, 900]
print("Autonomia do wearable (bateria %.0f mAh, ativo %.0f mA por %.0fs/envio)" %
      (BATT_MAH, I_ACTIVE_MA, T_ACTIVE_S))
print("-" * 64)
i_avg0 = I_ALWAYS_ON_MA
print(f"{'modo':<22}{'I_média (mA)':>16}{'autonomia':>16}")
print(f"{'sempre ligado (WiFi)':<22}{i_avg0:>16.2f}{fmt_hours(BATT_MAH / i_avg0):>16}")
rows = []
for s in sleeps:
    i_avg, h = duty_cycle_autonomy(s)
    rows.append((s, i_avg, h))
    print(f"{'deep sleep ' + str(s) + 's':<22}{i_avg:>16.2f}{fmt_hours(h):>16}")

# --------------------------------------------------------------------------- #
#  Tabela 2 — energia por pacote: WiFi vs BLE vs LoRa (estimativa datasheet)
# --------------------------------------------------------------------------- #
# (corrente de TX média, tempo para enviar 1 pacote) -> energia = I*t
radios = {
    "WiFi":  (120.0, 2.0),    # associação + TX, segundos
    "BLE":   (130.0, 0.030),  # advertise/connection event curto, ~30 ms
    "LoRa":  (40.0, 0.300),   # airtime SF7-ish, ~300 ms
}
print("\nEnergia por pacote (TX) — estimativa de datasheet")
print("-" * 64)
print(f"{'tecnologia':<10}{'I_TX (mA)':>12}{'t (s)':>10}{'mAh/pacote':>16}")
energy_per_pkt = {}
for name, (i_tx, t) in radios.items():
    mah = i_tx * t / 3600.0
    energy_per_pkt[name] = mah
    print(f"{name:<10}{i_tx:>12.0f}{t:>10.3f}{mah:>16.5f}")

# --------------------------------------------------------------------------- #
#  Gráfico 1 — autonomia vs intervalo de deep sleep
# --------------------------------------------------------------------------- #
fig, ax = plt.subplots(figsize=(5.5, 3.6))
xs = [s for s, _, _ in rows]
ys = [h for _, _, h in rows]
ax.plot(xs, ys, "o-", color="#2563eb", label="deep sleep")
ax.axhline(BATT_MAH / I_ALWAYS_ON_MA, color="#dc2626", ls="--",
           label=f"sempre ligado ({BATT_MAH / I_ALWAYS_ON_MA:.1f} h)")
ax.set_xlabel("Intervalo de deep sleep (s)")
ax.set_ylabel("Autonomia (horas)")
ax.set_title("Autonomia do wearable vs deep sleep (bateria 500 mAh)")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(HERE / "autonomy.png", dpi=130)

# --------------------------------------------------------------------------- #
#  Gráfico 2 — energia por pacote (escala log) WiFi vs BLE vs LoRa
# --------------------------------------------------------------------------- #
fig2, ax2 = plt.subplots(figsize=(5.0, 3.6))
names = list(energy_per_pkt.keys())
vals = [energy_per_pkt[n] for n in names]
bars = ax2.bar(names, vals, color=["#dc2626", "#16a34a", "#2563eb"])
ax2.set_yscale("log")
ax2.set_ylabel("mAh por pacote (log)")
ax2.set_title("Custo de energia por pacote enviado")
for b, v in zip(bars, vals):
    ax2.text(b.get_x() + b.get_width() / 2, v, f"{v:.5f}",
             ha="center", va="bottom", fontsize=8)
fig2.tight_layout()
fig2.savefig(HERE / "energy_per_packet.png", dpi=130)

print(f"\nGráficos salvos em {HERE}\\autonomy.png e energy_per_packet.png")
