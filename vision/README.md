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

## O Pipeline de Execução
O processamento ocorre de forma sequencial através de um pipeline unificado:
[Imagem Bruta] ➔ [YOLOv8: Detecção do Componente] ➔ [Recorte de ROI] ➔ [Tesseract: OCR do Display] ➔ [Lógica de Descrição] ➔ [JSON de Saída]

1. Detecção: O ComponentDetector recebe a imagem e localiza os componentes mapeados pelo modelo YOLOv8.

2. OCR: O PanelOCR isola as coordenadas delimitadoras (Bounding Boxes) dos displays detectados e extrai strings de texto (como dados de pressão ou alertas).

3. Engenharia de Prompt/Regras: O pipeline consolida as classes e os textos em uma descrição dinâmica e contextualizada.

4. Integração: O fluxo é exposto ao ecossistema através do endpoint POST /api/vision no backend (FastAPI).

## Escopo de Entrega (MVP vs. Stretch)
MVP: Detecção estável de classes de componentes cruciais + Extração funcional do texto de pelo menos um display principal.

Stretch: Classificação dinâmica de anomalias visuais (ex: identificação de LEDs de alerta ativos e geração de alarmes prioritários na descrição de cabine).

## Como Testar o Módulo Localmente
1. Pré-requisitos do Sistema
Certifique-se de ter o executável do Tesseract OCR instalado no seu sistema operacional e configurado nas variáveis de ambiente, além das dependências especificadas no requirements.txt do backend (ultralytics, pillow, pytesseract).

## Executando o disparo de teste via API
Com o servidor backend rodando na raiz do projeto (uvicorn backend.main:app --reload), você pode validar o pipeline enviando uma imagem real através do terminal:

curl -X POST [http://127.0.0.1:8000/api/vision](http://127.0.0.1:8000/api/vision) -F "image=@test_images/teste.jpg"

Exemplo de Retorno (JSON Real)
{
  "objects": ["objeto_74"],
  "ocr_text": "PRESS: 101 kPa",
  "description": "Análise concluída. Componentes identificados na cabine: objeto_74. Leituras adicionais: PRESS: 101 kPa."
}

## Disciplinas Correlacionadas
F4 C01 + C11: Visão Computacional, Fine-Tuning e Treinamento de Modelos de Detecção.
F3 C11: Segmentação de Imagens, Extração de Features e Pipelines de Pré-processamento.
