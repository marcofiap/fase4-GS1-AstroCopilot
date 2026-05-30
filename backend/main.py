"""
AstroCopilot — Backend orquestrador (Frente 5)
================================================
API FastAPI que integra todas as frentes do projeto. Por enquanto responde com
*mocks*, o que permite que Frentes 1–4 e o dashboard trabalhem em paralelo desde
o primeiro dia. Cada ponto de integração está marcado com `TODO [Frente N]`.

Monitora uma TRIPULAÇÃO de 3 astronautas (ver CREW), cada um com telemetria
independente.

Como rodar:
    pip install -r requirements.txt
    uvicorn main:app --reload
    -> http://localhost:8000/docs  (Swagger interativo)
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    AgentQuery,
    AgentResponse,
    HealthResponse,
    Telemetry,
    TelemetryAck,
    VisionResponse,
    VoiceResponse,
)

app = FastAPI(
    title="AstroCopilot API",
    description="Orquestrador da POC AstroCopilot — GS 2026.1 FIAP",
    version="0.2.0",
)

# CORS liberado em desenvolvimento (dashboard React+Vite roda em :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
#  Tripulação monitorada
# --------------------------------------------------------------------------- #
CREW = {
    "cmdr": {"name": "Cmdr. Ana Lima", "role": "Comandante", "base_hr": 72},
    "eng": {"name": "Eng. Bruno Sá", "role": "Engenheiro de Voo", "base_hr": 80},
    "med": {"name": "Dra. Clara Reis", "role": "Oficial Médica", "base_hr": 76},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Estado em memória: última leitura por tripulante (inicia em valores de repouso)
_crew_state: dict[str, dict] = {
    cid: {
        "id": cid,
        "name": info["name"],
        "role": info["role"],
        "hr": float(info["base_hr"]),
        "spo2": 98.0,
        "temp": 36.6,
        "accel": 0.1,
        "risk_level": "normal",
        "ts": _now(),
    }
    for cid, info in CREW.items()
}


def classify_risk(hr: float, spo2: float, temp: float) -> str:
    """Classificador de risco — PLACEHOLDER baseado em regras.

    TODO [Frente 4]: substituir por modelo scikit-learn treinado
    (iot-esp32/ml-edge/model.pkl) carregado uma vez no startup.
    """
    if spo2 < 90 or hr > 140 or temp > 38.5:
        return "risco"
    if spo2 < 94 or hr > 110 or temp > 37.8:
        return "fadiga"
    return "normal"


def _simulate_step(state: dict) -> dict:
    """Gera a próxima leitura simulada de um tripulante (variação suave em torno
    do último valor recebido). Usado enquanto não há ESP32 real enviando dados."""
    hr = round(state["hr"] + random.uniform(-3, 3), 1)
    spo2 = round(min(100.0, state["spo2"] + random.uniform(-1, 1)), 1)
    temp = round(state["temp"] + random.uniform(-0.1, 0.1), 1)
    return {
        "id": state["id"],
        "name": state["name"],
        "role": state["role"],
        "hr": hr,
        "spo2": spo2,
        "temp": temp,
        "risk_level": classify_risk(hr, spo2, temp),
        "ts": _now(),
    }


# --------------------------------------------------------------------------- #
#  Health
# --------------------------------------------------------------------------- #
@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="online", service="AstroCopilot", version="0.2.0")


@app.get("/api/crew")
def list_crew() -> dict:
    """Lista a tripulação monitorada e o estado atual de cada um."""
    return {"crew": list(_crew_state.values())}


# --------------------------------------------------------------------------- #
#  Agente LLM + RAG  (Frente 1)
# --------------------------------------------------------------------------- #
@app.post("/api/agent/query", response_model=AgentResponse)
def agent_query(q: AgentQuery) -> AgentResponse:
    """Consulta o agente conversacional.

    TODO [Frente 1]: chamar a cadeia RAG (agent-rag/agent.py) que recupera
    trechos do ChromaDB e gera a resposta com o LLM + citação de fontes.
    """
    return AgentResponse(
        answer=(
            f"[MOCK] Resposta do copiloto para: '{q.text}'. "
            "Substituir pela cadeia RAG da Frente 1."
        ),
        sources=["NASA-STD-3001 (mock)", "ESA Crew Manual (mock)"],
    )


# --------------------------------------------------------------------------- #
#  Voz: STT + TTS  (Frente 2)
# --------------------------------------------------------------------------- #
@app.post("/api/voice", response_model=VoiceResponse)
async def voice(audio: UploadFile = File(...)) -> VoiceResponse:
    """Recebe áudio do tripulante, transcreve, consulta o agente e devolve fala.

    TODO [Frente 2]: Whisper (STT) -> /api/agent/query -> gTTS/ElevenLabs (TTS).
    """
    _ = await audio.read()  # consome o upload (mock)
    transcript = "[MOCK] transcrição do áudio recebido"
    answer = agent_query(AgentQuery(text=transcript))
    return VoiceResponse(
        transcript=transcript,
        answer_text=answer.answer,
        answer_audio_url=None,  # Frente 2 retorna URL/arquivo do TTS
    )


# --------------------------------------------------------------------------- #
#  Visão computacional  (Frente 3)
# --------------------------------------------------------------------------- #
@app.post("/api/vision", response_model=VisionResponse)
async def vision(image: UploadFile = File(...)) -> VisionResponse:
    """Analisa a imagem que o astronauta mostra (painel/componente).

    TODO [Frente 3]: YOLOv8/CLIP (detecção) + Tesseract (OCR) em vision/.
    """
    _ = await image.read()  # consome o upload (mock)
    return VisionResponse(
        objects=["painel_de_controle", "led_alerta"],
        ocr_text="O2: 21%  PRESS: 101 kPa  ALERTA",
        description="[MOCK] Painel detectado com alerta ativo.",
    )


# --------------------------------------------------------------------------- #
#  Telemetria do ESP32  (Frente 4) — agora por tripulante
# --------------------------------------------------------------------------- #
@app.post("/api/telemetry", response_model=TelemetryAck)
def telemetry(t: Telemetry) -> TelemetryAck:
    """Recebe leitura do wearable ESP32 de um tripulante, classifica e guarda."""
    if t.crew_id not in _crew_state:
        raise HTTPException(status_code=404, detail=f"Tripulante '{t.crew_id}' não existe")
    risk = classify_risk(t.hr, t.spo2, t.temp)
    _crew_state[t.crew_id].update(
        hr=t.hr, spo2=t.spo2, temp=t.temp, accel=t.accel,
        risk_level=risk, ts=t.ts or _now(),
    )
    return TelemetryAck(status="ok", crew_id=t.crew_id, risk_level=risk)


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket) -> None:
    """Stream de telemetria de TODA a tripulação em tempo real (1 Hz).

    Envia um quadro `{ ts, crew: [ {id, name, role, hr, spo2, temp, risk_level}, ... ] }`.
    Simula leituras enquanto não há ESP32 real conectado.
    """
    await ws.accept()
    try:
        while True:
            crew_frame = []
            for cid, state in _crew_state.items():
                step = _simulate_step(state)
                # mantém o estado "andando" para a simulação ser contínua
                _crew_state[cid].update(hr=step["hr"], spo2=step["spo2"], temp=step["temp"])
                crew_frame.append(step)
            await ws.send_json({"ts": _now(), "crew": crew_frame})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
