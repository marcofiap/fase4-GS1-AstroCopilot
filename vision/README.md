# 📷 vision/ — Visão Computacional (Frente 3)

Analisa a imagem que o astronauta mostra: identifica componentes e lê displays/painéis.

## Responsável
**Frente 3** — Visão Computacional.

## Estrutura
| Pasta | Descrição |
|-------|-----------|
| `models/` | Pesos treinados — **não versionados** (ver .gitignore) |

## Pipeline
1. **Detecção** com YOLOv8 (ou CLIP zero-shot) de componentes.
2. **OCR** com Tesseract para ler números/alertas do painel.
3. Integra no backend em `POST /api/vision`.

## MVP vs. Stretch
- **MVP:** detecta 2–3 classes de componente + lê o texto de um painel.
- **Stretch:** classificação de anomalia visual (LED vermelho aceso = alerta).

## Disciplinas
F4 C01 + C11 (visão/fine-tuning) · F3 C11 (segmentação/features).
