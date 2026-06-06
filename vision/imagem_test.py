from PIL import Image, ImageDraw, ImageFont

# Cria imagem escura (simulando painel de controle espacial)
img = Image.new('RGB', (640, 480), color=(20, 20, 30))
draw = ImageDraw.Draw(img)

# Desenha um retangulo (simulando display LCD)
draw.rectangle([100, 100, 540, 380], fill=(0, 0, 0), outline=(0, 255, 0), width=3)

# Adiciona texto
try:
    font = ImageFont.truetype("arial.ttf", 32)
except:
    font = ImageFont.load_default()

draw.text((120, 150), "O2: 21%", fill=(0, 255, 0), font=font)
draw.text((120, 210), "PRESS: 101 kPa", fill=(0, 255, 0), font=font)
draw.text((120, 270), "ALERTA", fill=(255, 0, 0), font=font)

# ✅ SALVA NA SUBPASTA test_images/
img.save('test_images/painel_teste.jpg')
print("Imagem criada: test_images/painel_teste.jpg")