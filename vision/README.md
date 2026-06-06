# vision/ — Visão Computacional (Frente 3)

Módulo responsável por analisar de forma inteligente as imagens que o astronauta envia à cabine. O sistema realiza a detecção de componentes críticos e extrai informações textuais de displays e painéis em tempo real.

## Responsável
* **Frente 3** — Visão Computacional (Inteligência Artificial).

## Tecnologias Utilizadas
* **YOLOv8 (Ultralytics):** Detecção de componentes e displays na cabine.
* **Tesseract OCR (Pytesseract):** Extração de texto analógico/digital de alertas e pressões.
* **Pillow & OpenCV:** Processamento e manipulação de imagens no pipeline.

## Estrutura de Arquivos

```text
vision/
├── models/             # Pesos treinados (.pt) — [Não Versionados]
├── test_images/        # Imagens de teste (ex: teste.jpg)
├── detector.py         # Classe ComponentDetector (YOLOv8 do grupo)
├── ocr.py              # Classe PanelOCR (Tesseract OCR)
├── pipeline.py         # Orquestrador do fluxo (process_image)
└── README.md           # Documentação da Frente 3
