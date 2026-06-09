"""
Gera uma imagem de display de cabine LIMPA para a demo de visão/OCR.
Texto grande e contrastado (estilo LCD) -> o Tesseract lê com precisão.
Uso: python vision/test_images/gerar_painel_demo.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "painel_demo.png"
W, H = 1000, 640
BG = (8, 14, 28)          # navy escuro
PANEL = (12, 20, 40)
BORDER = (40, 70, 120)
CYAN = (120, 220, 255)
WHITE = (235, 240, 255)
AMBER = (255, 180, 60)
RED = (255, 90, 90)


def _font(size, bold=True):
    for name in (("consolab.ttf" if bold else "consola.ttf"), "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# Moldura do painel
d.rounded_rectangle([20, 20, W - 20, H - 20], radius=18, fill=PANEL, outline=BORDER, width=3)

title = _font(40)
big = _font(54)
small = _font(30)

d.text((50, 45), "PAINEL ECLSS  STATUS", font=title, fill=CYAN)
d.line([50, 110, W - 50, 110], fill=BORDER, width=2)

# Leituras (texto dentro do whitelist do OCR: A-Z a-z 0-9 . : % e espaco)
linhas = [
    ("O2: 21%", WHITE),
    ("CO2: 0.4%", WHITE),
    ("PRESS: 101 kPa", WHITE),
    ("TEMP: 22.5 C", WHITE),
    ("UMIDADE: 45%", WHITE),
]
y = 140
for txt, cor in linhas:
    d.text((60, y), txt, font=big, fill=cor)
    y += 72

# Linha de alerta (dispara a deteccao de anomalia no pipeline)
d.rounded_rectangle([50, H - 90, W - 50, H - 35], radius=10, fill=(60, 16, 16), outline=RED, width=2)
d.text((70, H - 84), "ALERTA: PRESSAO BAIXA", font=_font(38), fill=AMBER)

img.save(OUT)
print(f"gerado: {OUT}")
