# 🎬 Roteiro do Vídeo — AstroCopilot (GS 2026.1)

> **Duração-alvo:** 4:30–4:50 (limite 5:00) · **YouTube:** "Não listado"
> **Apresentador único** (narração em off ou na câmera).
> **Regra do pódio:** dizer **"QUERO CONCORRER"** + nome do grupo nos primeiros segundos.

## Antes de gravar (checklist técnico)
- [ ] **Forma fácil:** duplo-clique em **`iniciar.bat`** (sobe backend + dashboard automaticamente)
- [ ] *(ou manual)* Backend: `cd backend` → `source .venv/Scripts/activate` → `uvicorn main:app --reload`
- [ ] *(ou manual)* Dashboard: `cd dashboard && npm run dev` → http://localhost:5173 (Chrome/Edge)
- [ ] Base RAG e `model.pkl` já gerados (prontos na máquina)
- [ ] Microfone OK para demonstrar a voz "Astro"
- [ ] (Opcional) Wokwi aberto para mostrar o ESP32
- [ ] Gravar em 1080p, tela limpa (fechar abas/notificações)

> 💡 Como é **uma pessoa só**, o ideal é **narração em off** (gravar a tela e falar
> por cima). Não precisa aparecer na câmera. Pode gravar cena por cena e juntar na edição.

---

## Estrutura (cena a cena) — tudo narrado por você

### 🎬 Cena 1 — Abertura (0:00–0:25)
**Mostrar:** README no GitHub (ou o diagrama de arquitetura).
> "Olá! Eu sou o Marco, do **Grupo 42** do 2º ano de Inteligência Artificial da FIAP,
> e em nome do grupo: **QUERO CONCORRER**. Vou apresentar o nosso projeto da Global
> Solution 2026.1, o **AstroCopilot** — um copiloto de bordo com IA para tripulações
> espaciais, que responde à pergunta: como IA, automação e computação podem
> impulsionar a nova economia espacial."

*(Se o grupo decidir NÃO concorrer, remova a frase "QUERO CONCORRER".)*

---

### 🎬 Cena 2 — Arquitetura e integração (0:25–1:05)
**Mostrar:** `docs/diagramas/arquitetura.png`.
> "O AstroCopilot foi construído por cinco integrantes, em cinco frentes que se integram
> por um backend único em FastAPI. Cada frente cobre disciplinas das Fases 3 e 4: RAG e
> IA Generativa; NLP e voz; visão computacional; IoT com ESP32 e Machine Learning; e a
> plataforma web com DevOps e governança. Tudo se encontra neste orquestrador central,
> e o dashboard mostra a operação em tempo real. Vou demonstrar cada parte funcionando."

---

### 🎬 Cena 3 — Dashboard + Telemetria (IoT/ML) (1:05–1:45)
**Mostrar:** dashboard com os 3 tripulantes e os gráficos ao vivo.
> "Esta é a telemetria ao vivo de três tripulantes. Um wearable **ESP32**, simulado no
> Wokwi, envia os sinais vitais por WiFi ao backend. Um modelo de **Machine Learning**,
> um RandomForest treinado na borda, classifica o risco de cada um — normal, fadiga ou
> risco — com 94% de acurácia. Quando alguém escala de risco, o sistema gera um alerta."

**Mostrar (rápido):** Wokwi rodando OU um card mudando para FADIGA, e a página **Log de Alertas**.

---

### 🎬 Cena 4 — Copiloto por voz + RAG (1:45–2:55) · **núcleo da demo**
**Mostrar:** o card Copiloto. Clicar em **"Astro"** (ativa a escuta por voz).
> "O coração do projeto é o copiloto. O astronauta fala usando a wake word 'Astro' —
> pensado também para acessibilidade, já que ele ouve a resposta em voz. O áudio é
> transcrito pelo Whisper e respondido com áudio de volta."

**Falar no microfone:** **"Astro, como agir em caso de despressurização da cabine?"**

**Mostrar:** a resposta aparecendo e sendo lida em voz alta.
> "Reparem na resposta: ela vem com um **procedimento real** — colocar o capacete,
> fechar as válvulas, ativar a repressurização — e com a **fonte citada**, o manual de
> operações da Apollo. Isso é **RAG**: o agente busca em manuais reais da NASA indexados
> num banco vetorial e responde com a fonte, em vez de inventar. Em um ambiente crítico
> como o espaço, isso é essencial para confiança."

**(Destaque) Perguntar:** **"Astro, como proteger a tripulação da radiação?"**
> "E aqui o ponto mais legal da integração: ele combina os manuais da NASA com a
> **telemetria ao vivo** — cita o nível atual de radiação da tripulação junto com os
> documentos. É a frente de RAG conversando com a frente de IoT em tempo real."

---

### 🎬 Cena 5 — Visão Computacional (2:55–3:30)
**Mostrar:** página **Visão (imagem)** → enviar uma foto de painel.
> "Se um instrumento falha, o astronauta mostra o painel pela câmera. A visão
> computacional detecta os componentes com YOLO e faz **OCR** dos números e alertas
> do display, devolvendo a leitura para o copiloto interpretar."

---

### 🎬 Cena 6 — Governança e DevOps (3:30–4:05)
**Mostrar:** página **Auditoria** + terminal com `docker compose up` e os testes passando.
> "Para IA em ambiente crítico, governança é indispensável: **toda** decisão do agente
> fica registrada numa trilha de auditoria — pergunta, resposta, fontes e horário. E do
> lado de engenharia: a plataforma inteira sobe com **um** comando, `docker compose up`,
> tem **integração contínua** no GitHub Actions e **37 testes automatizados**. Tudo
> testado e operacional."

---

### 🎬 Cena 7 — Encerramento (4:05–4:35)
**Mostrar:** diagrama de disciplinas (`disciplinas.png`) ou o repositório no GitHub.
> "Resumindo: o AstroCopilot integra IA Generativa, RAG, visão computacional, NLP e voz,
> IoT, Machine Learning, Edge, dashboards em tempo real e DevOps — numa solução real e
> coesa para a economia espacial. Todo o código está no GitHub, com o passo a passo no
> README. Esse foi o AstroCopilot, do Grupo 42. Muito obrigado!"

---

## Dicas de gravação (apresentador único)
- **Narração em off** é o caminho mais fácil: grave a tela com OBS/Xbox Game Bar e fale por cima.
- **Grave cena por cena** e junte na edição — se errar uma fala, refaz só aquele trecho.
- **Tenha um "plano B":** se a voz "Astro" falhar ao vivo, digite a mesma pergunta no chat — o resultado é idêntico.
- **Corte tempos mortos:** acelere uploads/carregamentos na edição para caber em 5 min.
- **Roteiro na tela:** deixe este texto aberto numa segunda tela/celular para não travar.
- Ao final, suba como **"Não listado"** e **cole o link no PDF** (seção 6); depois rode
  `python docs/gerar_pdf.py` para gravar o link no PDF final.
