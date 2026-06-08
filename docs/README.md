# 📚 docs/ — Documentação

Centraliza a documentação técnica e os entregáveis da GS.

## Conteúdo

| Arquivo | Descrição |
|---------|-----------|
| `arquitetura.md` | Visão de arquitetura, fluxo de dados e contratos de API |
| `diagramas/` | Diagramas (`arquitetura.png`, `disciplinas.png`) + script gerador |
| `gerar_pdf.py` | Gera o PDF de entrega (código extraído dos arquivos reais via AST) |
| `GS-AstroCopilot.pdf` | **PDF final de entrega** (capa com nomes, Introdução, Desenvolvimento, Resultados Esperados, Conclusões, código em texto, diagramas, links) |

## Como (re)gerar os entregáveis visuais

```bash
pip install -r docs/requirements.txt
python docs/diagramas/gerar_diagramas.py   # arquitetura.png + disciplinas.png
python docs/gerar_pdf.py                    # docs/GS-AstroCopilot.pdf
```

> O `gerar_pdf.py` lê as funções diretamente do código-fonte, então o PDF
> sempre reflete o que está versionado (código em **texto**, nunca print).

## Checklist do PDF (item 2 do edital)

- [x] Nome completo dos 5 integrantes na 1ª página
- [ ] **RMs** dos integrantes (preencher os faltantes em `gerar_pdf.py` e regerar)
- [ ] Frase `QUERO CONCORRER` (descomente em `gerar_pdf.py` se for concorrer ao pódio)
- [x] Estrutura: Introdução · Desenvolvimento · Resultados Esperados · Conclusões
- [x] Arquitetura, códigos principais (em **texto**, nunca print) e decisões do grupo
- [x] Imagens, dashboards, diagramas, fluxogramas
- [x] Parágrafo teórico de Computação Quântica/Neuromórfica
- [ ] Link do **vídeo** (preencher em `gerar_pdf.py`, seção 6, e regerar)
- [x] Link do repositório
