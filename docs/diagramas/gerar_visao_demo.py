"""
Gera docs/diagramas/visao.png — figura da análise de visão (entrada + saída OCR
reais) no tema do dashboard, para o PDF de entrega.
Uso: python docs/diagramas/gerar_visao_demo.py
"""
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent.parent / "vision" / "test_images" / "painel_demo.png"
OUT = HERE / "visao.png"

# Saída REAL do POST /api/vision sobre a painel_demo.png
OCR = "O2:21%  CO2:0.4%  PRESS:101kPa  TEMP:22.5C  UMIDADE:45%  ALERTA: PRESSAO BAIXA"
DESC = ("Análise concluída. Dados coletados via telemetria visual. "
        "ATENÇÃO: indicador de anomalia / mensagem crítica ativa no painel!")

W, H = 1200, 560
BG = (6, 10, 22)
CARD = (11, 18, 38)
BORDER = (30, 42, 68)
CYAN = (56, 189, 248)
WHITE = (230, 237, 255)
MUTED = (150, 168, 200)
AMBER = (255, 180, 60)


def font(sz, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "consola.ttf"):
        try:
            return ImageFont.truetype(n, sz)
        except Exception:
            pass
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rounded_rectangle([16, 16, W - 16, H - 16], radius=16, fill=CARD, outline=BORDER, width=2)
d.text((40, 36), "Visão — Análise de Painel", font=font(26, True), fill=WHITE)
d.line([40, 78, W - 40, 78], fill=BORDER, width=1)

# Imagem de entrada (esquerda)
panel = Image.open(PANEL).convert("RGB")
pw = 520
ph = int(panel.height * pw / panel.width)
panel = panel.resize((pw, ph))
img.paste(panel, (40, 110))
d.text((40, 110 + ph + 8), "Entrada: imagem do painel (câmera)", font=font(15), fill=MUTED)

# Saída (direita)
x = 600
d.text((x, 110), "OCR (texto lido):", font=font(18, True), fill=CYAN)
y = 142
mono = font(16)
for line in wrap(OCR, 42):
    d.text((x, y), line, font=mono, fill=WHITE)
    y += 26

y += 18
d.text((x, y), "Descrição gerada:", font=font(18, True), fill=CYAN)
y += 30
for line in wrap(DESC, 46):
    color = AMBER if "ATEN" in line or "anomalia" in line else WHITE
    d.text((x, y), line, font=font(16), fill=color)
    y += 26

y += 16
d.rounded_rectangle([x, y, x + 540, y + 40], radius=8, fill=(60, 16, 16), outline=(255, 90, 90), width=2)
d.text((x + 14, y + 9), "!  Anomalia detectada automaticamente", font=font(17, True), fill=AMBER)

img.save(OUT)
print(f"gerado: {OUT}")
