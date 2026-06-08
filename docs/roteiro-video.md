# 🎬 Roteiro do Vídeo — AstroCopilot (GS 2026.1)

> **Duração-alvo:** 4:30–4:50 (limite 5:00) · **YouTube:** "Não listado"
> **Regra do pódio:** dizer **"QUERO CONCORRER"** + nome do grupo nos primeiros segundos.

## Antes de gravar (checklist técnico)
- [ ] Backend no ar: `cd backend && uvicorn main:app --reload` (com `ffmpeg` no PATH e `.env` preenchido)
- [ ] Dashboard no ar: `cd dashboard && npm run dev` → http://localhost:5173 (Chrome/Edge)
- [ ] Base RAG e `model.pkl` gerados (já estão prontos na máquina do Marco)
- [ ] Áudio do mic OK para demonstrar a voz "Astro"
- [ ] (Opcional) Wokwi aberto para mostrar o ESP32
- [ ] Gravar em 1080p, tela limpa (fechar abas/notificações)

---

## Estrutura (cena a cena)

### 🎬 Cena 1 — Abertura (0:00–0:25) · **Marco**
**Mostrar:** rosto/câmera ou o README no GitHub.
> "Olá! Somos o **Grupo 42** do 2º ano de IA da FIAP, e **QUERO CONCORRER**.
> Nosso projeto para a Global Solution 2026.1 é o **AstroCopilot** — um copiloto de
> bordo com IA para tripulações espaciais. Ele responde à pergunta do desafio:
> como IA, automação e computação podem impulsionar a nova economia espacial."

*(Se o grupo decidir NÃO concorrer, basta remover a frase "QUERO CONCORRER".)*

---

### 🎬 Cena 2 — Arquitetura e integração (0:25–1:05) · **Marco**
**Mostrar:** `docs/diagramas/arquitetura.png`.
> "O AstroCopilot integra **cinco frentes** que conversam por um backend único em
> FastAPI. Cada integrante tocou uma disciplina das Fases 3 e 4: RAG e IA Generativa,
> NLP e voz, visão computacional, IoT com ESP32 e Machine Learning, e a plataforma
> web com DevOps e governança. Tudo se encontra neste orquestrador central, e o
> dashboard mostra tudo em tempo real."

---

### 🎬 Cena 3 — Dashboard + Telemetria (IoT/ML) (1:05–1:45) · **Luiz (F4)**
**Mostrar:** dashboard com os 3 tripulantes e os gráficos ao vivo.
> "Esta é a telemetria ao vivo de três tripulantes. Um **wearable ESP32**, simulado
> no Wokwi, envia sinais vitais por WiFi ao backend. Um modelo de **Machine Learning**
> (RandomForest) treinado na borda classifica o risco — normal, fadiga ou risco —
> com 94% de acurácia. Quando alguém escala de risco, gera um alerta persistido."

**Mostrar (rápido):** Wokwi rodando OU o card mudando de NORMAL→FADIGA, e a página **Log de Alertas**.

---

### 🎬 Cena 4 — Copiloto por voz + RAG (1:45–2:55) · **Felipe (F1) + Juan (F2)**
**Mostrar:** o card Copiloto. Clicar em **"Astro"** (ativa a escuta).

**Juan (voz):**
> "O astronauta fala com o copiloto pela wake word 'Astro' — pensado também para
> acessibilidade. O áudio é transcrito por Whisper e a resposta sai em voz."

**Felipe:** *(falar no mic)* — **"Astro, como agir em caso de despressurização da cabine?"**

**Mostrar:** a resposta aparecendo + sendo lida em voz alta.
> *(Resposta esperada, vinda dos manuais reais da NASA:)*
> "Coloque o capacete e luvas imediatamente, feche as válvulas e ative a
> repressurização da cabine..." — **com a fonte citada** (Apollo Operations Handbook).

**Felipe:**
> "A resposta não é inventada: é **RAG** sobre manuais reais da NASA, indexados num
> banco vetorial, com a **fonte citada**. Isso reduz alucinação — crítico no espaço."

**(Destaque forte) Felipe pergunta:** **"Astro, como proteger a tripulação da radiação?"**
> "Reparem: ele combina os **manuais** com a **telemetria ao vivo** — cita o nível
> atual de radiação da tripulação junto com os papers da NASA. É a F1 conversando
> com a F4 em tempo real."

---

### 🎬 Cena 5 — Visão Computacional (2:55–3:30) · **Paulo (F3)**
**Mostrar:** página **Visão (imagem)** → enviar uma foto de painel.
> "Se um instrumento falha, o astronauta mostra o painel pela câmera. A visão
> computacional **detecta os componentes** (YOLO) e faz **OCR** dos números e
> alertas do display, devolvendo a leitura para o copiloto interpretar."

---

### 🎬 Cena 6 — Governança e DevOps (3:30–4:05) · **Marco (F5)**
**Mostrar:** página **Auditoria** + terminal com `docker compose up` e os testes.
> "Para IA em ambiente crítico, governança é essencial: **toda** decisão do agente
> fica registrada numa trilha de auditoria — pergunta, resposta, fontes e horário.
> A plataforma sobe inteira com **um** `docker compose up`, tem **CI no GitHub
> Actions** e **37 testes automatizados**. Tudo testado e operacional."

---

### 🎬 Cena 7 — Encerramento (4:05–4:35) · **Todos / Marco**
**Mostrar:** diagrama de disciplinas (`disciplinas.png`) ou o repositório.
> "Em resumo: o AstroCopilot integra IA Generativa, RAG, visão, NLP/voz, IoT, Machine
> Learning, Edge, dashboards em tempo real e DevOps — numa solução real e coesa para
> a economia espacial. O código está no GitHub e o passo a passo no README.
> Obrigado!"

---

## Dicas de gravação
- **Divida a tela:** quem narra cada cena pode gravar sua parte e depois juntar — fica mais leve.
- **Tenha um "plano B":** se a voz falhar ao vivo, mostre digitando a mesma pergunta no chat (o resultado é o mesmo).
- **Corte tempos mortos:** acelere uploads/carregamentos na edição para caber em 5 min.
- **Legenda opcional:** ajuda se o áudio do ambiente não estiver perfeito.
- Ao final, suba como **"Não listado"** e **cole o link no PDF** (seção 6) — depois rode
  `python docs/gerar_pdf.py` para gravar o link no PDF final.
