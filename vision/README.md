# Frente 3 — Visão Computacional (`vision/`)

Módulo responsável por analisar de forma inteligente as imagens enviadas pelo astronauta à cabine. O sistema realiza a detecção de componentes críticos e extrai informações textuais de displays e painéis em tempo real.

---

## Responsabilidade

**Frente 3 — Visão Computacional (Inteligência Artificial)**

Esta frente é responsável por:

* Detectar componentes da cabine utilizando IA.
* Identificar displays e painéis relevantes.
* Extrair textos e leituras presentes nos equipamentos.
* Gerar descrições estruturadas para consumo pelo backend.

---

## Tecnologias Utilizadas

| Tecnologia                  | Finalidade                             |
| --------------------------- | -------------------------------------- |
| YOLOv8 (Ultralytics)        | Detecção de componentes e displays     |
| Tesseract OCR (Pytesseract) | Extração de texto de painéis e alertas |
| OpenCV                      | Pré-processamento de imagens           |
| Pillow (PIL)                | Manipulação de imagens                 |
| Python                      | Orquestração do pipeline               |

---

## Estrutura de Arquivos

```text
vision/
├── models/             # Pesos treinados (.pt) - Não versionados
├── test_images/        # Imagens de teste
├── detector.py         # Classe ComponentDetector (YOLOv8)
├── ocr.py              # Classe PanelOCR (Tesseract)
├── pipeline.py         # Orquestrador principal
└── README.md           # Documentação da Frente 3
```

---

## Pipeline de Execução

O processamento ocorre através de um pipeline unificado:

```text
[Imagem Bruta]
       ↓
[YOLOv8 - Detecção de Componentes]
       ↓
[Recorte da ROI]
       ↓
[Tesseract OCR]
       ↓
[Lógica de Descrição]
       ↓
[JSON de Saída]
```

### Detecção de Componentes

O `ComponentDetector` recebe a imagem e utiliza o modelo YOLOv8 treinado pelo grupo para localizar os componentes presentes na cabine.

### OCR dos Displays

O módulo `PanelOCR` utiliza as coordenadas detectadas para isolar regiões de interesse (*Regions of Interest - ROI*) e extrair textos relevantes, como:

* Pressões
* Temperaturas
* Alertas
* Indicadores de status

### Consolidação e Descrição

O pipeline combina:

* Classes detectadas
* Textos extraídos
* Regras de negócio

para produzir uma descrição contextualizada da situação observada.

### Integração com Backend

O módulo é disponibilizado através do endpoint:

```http
POST /api/vision
```

implementado no backend FastAPI.

---

### Teste de Resiliência: Input Vazio ou Apagado (Edge Case)

Para garantir que o ecossistema do **AstroCopilot** permaneça estável mesmo diante de falhas físicas de captura (ex: câmera obstruída, ausência de luz na cabine ou envio de arquivos corrompidos), o pipeline foi submetido a testes de estresse com imagens zeradas (pixels pretos/brancos criados via MS Paint) e payloads de 0 bytes.

**Comportamento Isolado dos Componentes:**

* **YOLOv8 (Detector):** Realiza a varredura matricial com sucesso e retorna uma lista vazia de detecções (`[]`), sem estourar índices.
* **Tesseract (PanelOCR):** O pipeline de binarização adaptativa do OpenCV trata a imagem escura e o motor de OCR retorna uma string vazia (`""`), filtrando ruídos.

#### Exemplo de Resposta Estruturada (Log Real)
Mesmo sem nenhum estímulo visual válido, o sistema intercepta o estado nulo graciosamente e responde com o contrato JSON perfeitamente íntegro, evitando quedas no backend:

```json
{
  "objects": [],
  "ocr_text": "",
  "description": "Nenhum componente ou dado legível identificado na captura da câmera."
}
```

## Escopo de Entrega

### MVP

* Detecção estável dos componentes principais da cabine.
* Extração funcional de texto de pelo menos um display.
* Retorno estruturado em JSON.

### Stretch Goals

* Detecção automática de anomalias visuais.
* Identificação de LEDs de alerta ativos.
* Priorização automática de alarmes.
* Geração de descrições avançadas da cabine.

---

## Como Executar Localmente

### Pré-requisitos

Instale o Tesseract OCR no sistema operacional e configure-o nas variáveis de ambiente.

Além disso, instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

Principais bibliotecas utilizadas:

* ultralytics
* pytesseract
* pillow
* opencv-python

---

## Iniciando o Backend

Na raiz do projeto:

```bash
uvicorn backend.main:app --reload
```

Servidor disponível em:

```text
http://127.0.0.1:8000
```

---

## Testando o Endpoint

Envie uma imagem para validação do pipeline:

```bash
curl -X POST http://127.0.0.1:8000/api/vision \
-F "image=@test_images/teste.jpg"
```

---

## Exemplo de Resposta

```json
{
  "objects": ["objeto_74"],
  "ocr_text": "PRESS: 101 kPa",
  "description": "Análise concluída. Componentes identificados na cabine: objeto_74. Leituras adicionais: PRESS: 101 kPa."
}
```

---

## Disciplinas Correlacionadas

### F4 C01 + F4 C11

* Visão Computacional
* Fine-Tuning
* Treinamento de Modelos de Detecção

### F3 C11

* Segmentação de Imagens
* Extração de Features
* Pipelines de Pré-processamento

---

Responsável pela análise automática das imagens da cabine, integração com modelos de IA e geração de informações estruturadas para o sistema de suporte ao astronauta.
