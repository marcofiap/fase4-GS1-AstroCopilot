from pipeline import process_image

# ✅ CAMINHO CORRETO: test_images/painel_teste.jpg
with open('test_images/painel_teste.jpg', 'rb') as f:
    image_bytes = f.read()

result = process_image(image_bytes)

print("=" * 50)
print("RESULTADO DO PIPELINE DE VISAO")
print("=" * 50)
print(f"Objetos: {result['objects']}")
print(f"OCR: {result['ocr_text']}")
print(f"Descricao: {result['description']}")