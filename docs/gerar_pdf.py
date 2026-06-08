"""
Gera o PDF de entrega da GS 2026.1 — AstroCopilot (docs/GS-AstroCopilot.pdf).

Os trechos de código são EXTRAÍDOS DOS ARQUIVOS REAIS do repositório (via AST),
garantindo que o que aparece no PDF é exatamente o que está versionado — em
formato texto, conforme exige o enunciado (nada de screenshots de código).

Uso:  python docs/gerar_pdf.py
Requer: reportlab  (pip install reportlab)
"""
from __future__ import annotations

import ast
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable, Image, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DIAG = DOCS / "diagramas"

NAVY = colors.HexColor("#0b1226")
ACCENT = colors.HexColor("#1f6feb")
INK = colors.HexColor("#10223f")
MUTED = colors.HexColor("#5b6b8c")
CODEBG = colors.HexColor("#f4f6fb")
CODEBORDER = colors.HexColor("#d2dbea")


# --------------------------------------------------------------------------- #
#  Extração de código real
# --------------------------------------------------------------------------- #
def extract_function(rel_path: str, func_name: str, max_lines: int | None = None) -> str:
    """Retorna o código-fonte de uma função/método pelo nome, lido do arquivo real."""
    path = ROOT / rel_path
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            start = node.lineno - 1
            end = node.end_lineno
            block = lines[start:end]
            if max_lines and len(block) > max_lines:
                block = block[:max_lines] + ["    # ... (continua no repositório)"]
            return "\n".join(block)
    raise ValueError(f"{func_name} não encontrada em {rel_path}")


def read_lines(rel_path: str, start: int, end: int) -> str:
    lines = (ROOT / rel_path).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1:end])


# --------------------------------------------------------------------------- #
#  Estilos
# --------------------------------------------------------------------------- #
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=17, textColor=NAVY,
                    spaceBefore=14, spaceAfter=8, fontName="Helvetica-Bold")
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, textColor=ACCENT,
                    spaceBefore=10, spaceAfter=5, fontName="Helvetica-Bold")
BODY = ParagraphStyle("Body", parent=ss["BodyText"], fontSize=10, leading=15,
                      alignment=TA_JUSTIFY, textColor=INK, spaceAfter=6)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=2)
CAP = ParagraphStyle("Cap", parent=BODY, fontSize=8.5, textColor=MUTED,
                     alignment=TA_CENTER, spaceBefore=2)
CODE = ParagraphStyle("Code", parent=ss["Code"], fontName="Courier", fontSize=7.1,
                      leading=8.6, textColor=colors.HexColor("#1b2a44"),
                      backColor=CODEBG, borderColor=CODEBORDER, borderWidth=0.5,
                      borderPadding=6, spaceBefore=4, spaceAfter=10)
CODECAP = ParagraphStyle("CodeCap", parent=BODY, fontSize=8, textColor=MUTED, spaceAfter=2)


def code(rel_path: str, snippet: str) -> list:
    return [Paragraph(f"<b>{rel_path}</b>", CODECAP), Preformatted(snippet, CODE)]


story: list = []


def p(text, style=BODY):
    story.append(Paragraph(text, style))


def h1(text):
    story.append(Spacer(1, 4))
    story.append(Paragraph(text, H1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d2dbea"),
                            spaceBefore=2, spaceAfter=8))


def h2(text):
    story.append(Paragraph(text, H2))


# --------------------------------------------------------------------------- #
#  CAPA (primeira página)
# --------------------------------------------------------------------------- #
story.append(Spacer(1, 1.4 * cm))
story.append(Paragraph("AstroCopilot", ParagraphStyle(
    "T", parent=H1, fontSize=30, alignment=TA_CENTER, textColor=NAVY, spaceAfter=4)))
story.append(Paragraph("Copiloto Conversacional para Missões Espaciais", ParagraphStyle(
    "ST", parent=BODY, fontSize=13, alignment=TA_CENTER, textColor=ACCENT, spaceAfter=2)))
story.append(Paragraph("Global Solution 2026.1 — FIAP · 2º ano de Inteligência Artificial (2TIAO)",
                       ParagraphStyle("ST2", parent=BODY, fontSize=10.5, alignment=TA_CENTER,
                                      textColor=MUTED, spaceAfter=16)))

# >>> Para concorrer ao pódio, descomente a linha abaixo (e diga no vídeo):
# story.append(Paragraph('<b>QUERO CONCORRER</b>', ParagraphStyle(
#     "QC", parent=BODY, fontSize=13, alignment=TA_CENTER, textColor=colors.red, spaceAfter=16)))

integrantes = [
    ["Integrante", "RM", "Frente"],
    ["Felipe Sabino da Silva", "RM563569", "F1 — Agente LLM + RAG + Scraping"],
    ["Juan Felipe Voltolini", "RM562890", "F2 — NLP & Voz"],
    ["Luiz Henrique Ribeiro de Oliveira", "RM563077", "F4 — IoT ESP32 + Edge + ML"],
    ["Marco Aurélio Eberhardt Assumpção", "RM563348", "F5 — Backend / Dashboard / DevOps"],
    ["Paulo Henrique Senise", "RM565781", "F3 — Visão Computacional"],
]
t = Table(integrantes, colWidths=[7.4 * cm, 2.4 * cm, 6.2 * cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2fa")]),
    ("GRID", (0, 0), (-1, -1), 0.5, CODEBORDER),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t)
story.append(Spacer(1, 10))
p('<i>Grupo 42 · Turma 2TIAO — 2º ano de Inteligência Artificial.</i>',
  ParagraphStyle("note", parent=BODY, fontSize=8.5, textColor=MUTED, alignment=TA_CENTER))
story.append(Spacer(1, 8))
if (DIAG / "arquitetura.png").exists():
    img = Image(str(DIAG / "arquitetura.png"))
    img._restrictSize(16 * cm, 9.5 * cm)
    img.hAlign = "CENTER"
    story.append(img)
    story.append(Paragraph("Figura 1 — Arquitetura da solução (5 frentes integradas).", CAP))
story.append(PageBreak())

# --------------------------------------------------------------------------- #
#  1. INTRODUÇÃO
# --------------------------------------------------------------------------- #
h1("1. Introdução")
p('A pergunta-desafio da GS 2026.1 é: <i>"Como tecnologias avançadas de Inteligência '
  'Artificial, automação e computação podem impulsionar soluções inovadoras para a nova '
  'economia espacial?"</i> A nossa resposta é o <b>AstroCopilot</b>: um copiloto de bordo '
  'conversacional para tripulações espaciais, que reúne em uma única plataforma a consulta '
  'a manuais técnicos reais, o monitoramento de sinais vitais em tempo real, a análise de '
  'painéis por imagem e a interação por voz — pensado inclusive em acessibilidade para '
  'tripulantes com limitação visual.')
p('Em missões espaciais a tripulação precisa de respostas rápidas, confiáveis e rastreáveis, '
  'muitas vezes sem poder folhear manuais ou desviar a atenção dos instrumentos. O AstroCopilot '
  'ataca esse problema combinando <b>IA Generativa com RAG</b> (respostas fundamentadas em '
  'documentos reais da NASA, com citação de fonte), <b>visão computacional</b> (leitura de '
  'painéis), <b>IoT com ESP32 e Machine Learning na borda</b> (telemetria vital classificada '
  'por risco) e <b>voz</b> (falar e ouvir), tudo orquestrado por um backend e exibido em um '
  'dashboard de centro de controle.')
p('A solução foi construída como uma POC integrada por <b>cinco frentes de trabalho</b>, uma '
  'por integrante, todas convergindo para um backend orquestrador comum. Esta organização '
  'permitiu trabalho paralelo desde o primeiro dia (contra contratos de API fixos) e evidencia '
  'a <b>integração interdisciplinar</b> exigida pelo desafio.')

# --------------------------------------------------------------------------- #
#  2. DESENVOLVIMENTO
# --------------------------------------------------------------------------- #
h1("2. Desenvolvimento")
h2("2.1 Visão geral da arquitetura")
p('O <b>backend FastAPI</b> (Frente 5) é o orquestrador central: expõe uma API REST + WebSocket '
  'e chama cada módulo das demais frentes. O <b>dashboard React + Vite</b> consome essa API por '
  'REST (chat, visão, alertas, auditoria) e por WebSocket (telemetria ao vivo, 1 Hz). A '
  'persistência fica em SQLite (histórico de alertas e trilha de auditoria do agente).')
if (DIAG / "disciplinas.png").exists():
    img = Image(str(DIAG / "disciplinas.png"))
    img._restrictSize(16 * cm, 8 * cm)
    img.hAlign = "CENTER"
    story.append(img)
    story.append(Paragraph("Figura 2 — Disciplinas das Fases 3 e 4 cobertas por frente.", CAP))

# Tabela de endpoints
h2("2.2 Contratos de API (integração entre as frentes)")
p('Todas as frentes programaram contra estes contratos. O backend respondia com <i>mocks</i> '
  'desde o início, permitindo desenvolvimento paralelo; depois cada mock foi substituído pela '
  'lógica real da frente correspondente.')
endpoints = [
    ["Método", "Rota", "Frente / Função"],
    ["POST", "/api/agent/query", "F1 — RAG sobre manuais NASA (cita fonte)"],
    ["POST", "/api/voice", "F2 — STT → RAG → TTS + intenção"],
    ["POST", "/api/vision", "F3 — detecção de componentes + OCR"],
    ["POST/GET", "/api/telemetry", "F4 — telemetria do ESP32 (JSON e query)"],
    ["WS", "/ws/telemetry", "F4/F5 — stream de telemetria 1 Hz"],
    ["GET", "/api/alerts", "F5 — histórico de risco (SQLite)"],
    ["GET", "/api/audit", "F5 — trilha de auditoria do agente"],
]
te = Table(endpoints, colWidths=[2.2 * cm, 4.2 * cm, 9.6 * cm])
te.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (1, -1), "Courier"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2fa")]),
    ("GRID", (0, 0), (-1, -1), 0.5, CODEBORDER),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(te)
story.append(Spacer(1, 8))

# 2.3 Frente 1
h2("2.3 Frente 1 — Agente LLM + RAG + Scraping")
p('O agente roda sobre <b>Claude Haiku 4.5 no Amazon Bedrock</b> (via framework Strands) e tem '
  'uma ferramenta <font face="Courier">buscar_documentos</font> que recupera trechos dos manuais '
  'indexados no <b>ChromaDB</b>. Os documentos vêm de <i>scraping</i> da API pública do '
  '<b>NASA NTRS</b> (Technical Reports Server); os embeddings usam o <b>Amazon Titan v2</b>. '
  'O <i>system prompt</i> aplica Prompt Engineering para respostas curtas e com fonte citada.')
story.extend(code("agent-rag/agent.py", extract_function("agent-rag/agent.py", "query", max_lines=22)))

# 2.4 Frente 2
h2("2.4 Frente 2 — NLP & Voz")
p('O pipeline de voz transcreve o áudio com <b>Whisper</b> (STT), classifica a <b>intenção</b> '
  '(pergunta/status/emergência), consulta o mesmo agente RAG e sintetiza a resposta em áudio '
  'com <b>Edge-TTS/gTTS</b>. No dashboard, a ativação por voz usa a <i>wake word</i> "Astro".')
story.extend(code("voice-nlp/pipeline.py", extract_function("voice-nlp/pipeline.py", "process_voice")))

# 2.5 Frente 3
h2("2.5 Frente 3 — Visão Computacional")
p('A imagem enviada pela tripulação passa por <b>detecção de objetos (YOLOv8)</b> e por '
  '<b>OCR (Tesseract)</b> para ler números e alertas do painel. O pipeline devolve o contrato '
  '<font face="Courier">{objects, ocr_text, description}</font>, com tratamento de erro robusto.')
story.extend(code("vision/pipeline.py", read_lines("vision/pipeline.py", 21, 49)))

# 2.6 Frente 4
h2("2.6 Frente 4 — IoT ESP32 + Edge + Machine Learning")
p('Um wearable <b>ESP32 (simulado no Wokwi)</b> lê sensores reais (MPU6050, DS18B20) e envia a '
  'telemetria por WiFi/HTTP ao backend. O risco (normal/fadiga/risco) é classificado por um '
  'modelo <b>RandomForest (scikit-learn)</b> treinado na borda, com <i>fallback</i> para regras '
  'determinísticas — a API nunca quebra se o modelo não estiver presente.')
story.extend(code("backend/main.py", extract_function("backend/main.py", "classify_risk")))

# 2.7 Frente 5
h2("2.7 Frente 5 — Backend, Dashboard, DevOps e Governança")
p('Além de orquestrar as frentes, esta frente entrega: <b>governança de IA</b> (toda consulta '
  'ao agente é registrada em uma trilha de auditoria — pergunta, resposta, fontes, canal e '
  'timestamp), <b>DevOps</b> (Docker + docker-compose sobem tudo com um comando; CI no GitHub '
  'Actions roda testes a cada push) e <b>qualidade</b> (37 testes automatizados). A telemetria '
  'real do ESP32 tem prioridade sobre a simulação no stream em tempo real.')
story.extend(code("backend/main.py", extract_function("backend/main.py", "_log_alert")))

# 2.8 Interfaces
h2("2.8 Interfaces desenvolvidas (dashboard)")
p('O centro de controle web reúne, em tema "mission control", a telemetria ao vivo dos três '
  'tripulantes (cards com risco + gráficos de frequência cardíaca e radiação) e o Copiloto, '
  'com entrada por voz (wake word "Astro") e por texto. Páginas dedicadas trazem a análise de '
  'imagem, o log de alertas e a trilha de auditoria.')
for fname, cap in [
    ("dashboard.png", "Figura 3 — Dashboard: telemetria ao vivo de 3 tripulantes + Copiloto (RAG)."),
    ("auditoria.png", "Figura 4 — Trilha de auditoria: cada decisão do agente é registrada (governança)."),
]:
    if (DIAG / fname).exists():
        im = Image(str(DIAG / fname))
        im._restrictSize(16 * cm, 10 * cm)
        im.hAlign = "CENTER"
        story.append(im)
        story.append(Paragraph(cap, CAP))
        story.append(Spacer(1, 6))

# --------------------------------------------------------------------------- #
#  3. RESULTADOS ESPERADOS
# --------------------------------------------------------------------------- #
h1("3. Resultados Esperados")
p('A POC demonstra, ponta a ponta e de forma testada, os seguintes resultados:')
for item in [
    "<b>Respostas fundamentadas:</b> o copiloto responde perguntas técnicas citando manuais reais "
    "da NASA (NTRS), reduzindo alucinação e aumentando a confiabilidade a bordo.",
    "<b>Operação sem as mãos / acessível:</b> a tripulação fala (\"Astro, ...\") e ouve a resposta, "
    "útil em emergências e para tripulantes com limitação visual.",
    "<b>Monitoramento vital em tempo real:</b> sinais de 3 tripulantes em streaming a 1 Hz, com "
    "classificação automática de risco e log de alertas persistente.",
    "<b>Leitura assistida de painéis:</b> a câmera identifica componentes e lê displays via OCR.",
    "<b>Rastreabilidade (governança):</b> toda decisão do agente fica auditável, requisito central "
    "para IA aplicada a ambientes críticos.",
    "<b>Reprodutibilidade:</b> um único <font face=\"Courier\">docker compose up</font> sobe toda a "
    "stack; CI garante que o projeto continua operacional a cada alteração.",
]:
    p("• " + item, BULLET)
p('O <b>smoke test</b> executado sobre a stack integrada validou os 11 fluxos principais '
  '(health, tripulação, telemetria POST/GET, alertas, RAG real, auditoria, visão, voz STT→RAG→TTS, '
  'TTS e entrega do MP3) — todos com sucesso e sem erros em log.')

# --------------------------------------------------------------------------- #
#  4. CONCLUSÕES
# --------------------------------------------------------------------------- #
h1("4. Conclusões")
p('O AstroCopilot responde à pergunta-desafio mostrando, na prática, como IA Generativa, visão '
  'computacional, IoT/Edge, Machine Learning e automação se combinam para apoiar a operação na '
  'nova economia espacial. A maior contribuição do trabalho foi a <b>integração real entre as '
  'disciplinas das Fases 3 e 4</b>: cada frente entregou um módulo funcional que conversa com as '
  'demais através de um orquestrador comum, em vez de protótipos isolados.')
p('Como evolução natural (fora do escopo desta POC), prevemos: agente com mais ferramentas '
  '(acionar visão e telemetria autonomamente), base RAG ampliada com PDFs completos, modelo de '
  'visão fine-tuned para componentes específicos da nave, e um aplicativo mobile (React Native) '
  'para a equipe de solo. A arquitetura modular adotada torna essas extensões diretas.')

# --------------------------------------------------------------------------- #
#  5. Computação Quântica e Neuromórfica (parágrafo teórico)
# --------------------------------------------------------------------------- #
h1("5. Perspectivas: Computação Quântica e Neuromórfica")
p('Olhando para o futuro da economia espacial, duas fronteiras computacionais se conectam '
  'diretamente ao AstroCopilot. A <b>computação quântica</b> promete acelerar problemas hoje '
  'intratáveis em escala clássica: otimização de trajetórias e janelas de lançamento, simulação '
  'de novos materiais e propelentes (química quântica), e criptografia resistente para '
  'comunicações espaço-Terra. Algoritmos como QAOA e Grover poderiam, por exemplo, otimizar o '
  'escalonamento de tarefas e recursos energéticos de uma missão — exatamente o tipo de decisão '
  'que o copiloto hoje apoia com heurísticas e ML.')
p('Já a <b>computação neuromórfica</b> — chips que imitam o funcionamento de neurônios e sinapses, '
  'como Intel Loihi e IBM TrueNorth — é especialmente promissora para o <b>Edge espacial</b>: '
  'oferece inferência de IA com consumo de energia ordens de grandeza menor, processamento '
  'orientado a eventos e tolerância a ruído/radiação. Em um wearable como o da Frente 4, um '
  'processador neuromórfico permitiria rodar a classificação de risco (e até modelos de visão) '
  'localmente, em tempo real e com bateria mínima, sem depender de conectividade — uma evolução '
  'direta do nosso modelo de ML na borda. Ambas as tecnologias reforçam a tese do projeto: '
  'levar inteligência confiável e eficiente para o ambiente extremo do espaço.')

# --------------------------------------------------------------------------- #
#  6. Links e execução
# --------------------------------------------------------------------------- #
h1("6. Repositório, Execução e Vídeo")
p('<b>Repositório:</b> https://github.com/marcofiap/fase4-GS1-AstroCopilot')
p('<b>Vídeo demonstrativo (YouTube — Não listado):</b> _____ (inserir link antes da entrega)')
h2("Como executar")
story.extend([Preformatted(
    "# Opção 1 — Docker (sobe backend + dashboard)\n"
    "docker compose up --build\n"
    "#   Dashboard: http://localhost:5173\n"
    "#   Backend:   http://localhost:8000/docs\n\n"
    "# Opção 2 — desenvolvimento\n"
    "cd backend && python -m venv .venv && source .venv/Scripts/activate\n"
    "pip install -r requirements.txt && uvicorn main:app --reload\n"
    "cd dashboard && npm install && npm run dev", CODE)])
p('Configuração: um único <font face="Courier">.env</font> na raiz com a chave do Bedrock '
  '(<font face="Courier">AWS_BEARER_TOKEN_BEDROCK</font>). O banco SQLite é criado '
  'automaticamente. Detalhes completos no README de cada pasta.')


# --------------------------------------------------------------------------- #
#  Rodapé com numeração
# --------------------------------------------------------------------------- #
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.1 * cm, "AstroCopilot — GS 2026.1 FIAP · Grupo 42")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def build():
    out = DOCS / "GS-AstroCopilot.pdf"
    doc = SimpleDocTemplate(
        str(out), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="GS 2026.1 — AstroCopilot", author="Grupo 42 — 2TIAO FIAP",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"PDF gerado: {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
