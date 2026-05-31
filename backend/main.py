"""
AstroCopilot — Backend orquestrador (Frente 5)
================================================
API FastAPI que integra todas as frentes do projeto. Por enquanto responde com
*mocks*, o que permite que Frentes 1–4 e o dashboard trabalhem em paralelo desde
o primeiro dia. Cada ponto de integração está marcado com `TODO [Frente N]`.

Monitora uma TRIPULAÇÃO de 3 astronautas (ver CREW), cada um com telemetria
independente (batimentos, SpO2, temperatura, aceleração, respiração, radiação e
bateria do wearable) e mantém um LOG DE ALERTAS quando há escalada de risco.

Como rodar:
    pip install -r requirements.txt
    uvicorn main:app --reload
    -> http://localhost:8000/docs  (Swagger interativo)
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import db
from schemas import (
    AgentQuery,
    AgentResponse,
    HealthResponse,
    Telemetry,
    TelemetryAck,
    VisionResponse,
    VoiceResponse,
)

# --------------------------------------------------------------------------- #
#  Frente 1: cadeia RAG (agent-rag/agent.py)
#  Import resiliente. Se as dependencias ou a base vetorial nao estiverem
#  disponiveis, o endpoint /api/agent/query opera em modo limitado (ver abaixo).
# --------------------------------------------------------------------------- #
_RAG_DIR = os.getenv("AGENT_RAG_DIR") or str(Path(__file__).resolve().parent.parent / "agent-rag")
if _RAG_DIR not in sys.path:
    sys.path.insert(0, _RAG_DIR)
try:
    from agent import query as rag_query  # noqa: E402
except Exception as exc:  # pragma: no cover - depende do ambiente
    rag_query = None
    print(f"[Frente 1] RAG indisponivel, usando modo limitado: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialização da app: garante que as tabelas do SQLite existam."""
    db.init_db()
    yield


app = FastAPI(
    title="AstroCopilot API",
    description="Orquestrador da POC AstroCopilot — GS 2026.1 FIAP",
    version="0.3.0",
    lifespan=lifespan,
)

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
    "cmdr": {"name": "Cmdr. Ana Lima", "role": "Comandante", "base_hr": 72, "battery": 100},
    "eng": {"name": "Eng. Bruno Sá", "role": "Engenheiro de Voo", "base_hr": 80, "battery": 92},
    "med": {"name": "Dra. Clara Reis", "role": "Oficial Médica", "base_hr": 76, "battery": 87},
}

RANK = {"normal": 0, "fadiga": 1, "risco": 2}


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
        "resp": 14.0,
        "radiation": 0.2,
        "battery": float(info["battery"]),
        "risk_level": "normal",
        "ts": _now(),
    }
    for cid, info in CREW.items()
}


def classify_risk(hr: float, spo2: float, temp: float,
                  radiation: float = 0.0, resp: float = 14.0) -> str:
    """Classificador de risco — PLACEHOLDER baseado em regras.

    TODO [Frente 4]: substituir por modelo scikit-learn treinado
    (iot-esp32/ml-edge/model.pkl) carregado uma vez no startup.
    """
    if spo2 < 90 or hr > 140 or temp > 38.5 or radiation > 5.0 or resp > 28:
        return "risco"
    if spo2 < 94 or hr > 110 or temp > 37.8 or radiation > 1.0 or resp > 24 or resp < 8:
        return "fadiga"
    return "normal"


def _log_alert(state: dict, new_risk: str) -> None:
    alert = {
        "ts": _now(),
        "crew_id": state["id"],
        "name": state["name"],
        "risk_level": new_risk,
        "message": (
            f"{state['name']} entrou em estado {new_risk.upper()} "
            f"(HR {state['hr']} bpm · SpO₂ {state['spo2']}% · "
            f"Temp {state['temp']}°C · Rad {state['radiation']} µSv/h)"
        ),
    }
    db.insert_alert(alert)  # persiste no SQLite (sobrevive a reinícios)


def apply_vitals(cid: str, *, hr, spo2, temp, accel, resp, radiation, battery, ts=None) -> dict:
    """Atualiza o estado de um tripulante, classifica o risco e registra alerta
    quando há ESCALADA de severidade (edge-triggered). Retorna o snapshot."""
    state = _crew_state[cid]
    prev = state["risk_level"]
    risk = classify_risk(hr, spo2, temp, radiation, resp)
    state.update(
        hr=hr, spo2=spo2, temp=temp, accel=accel, resp=resp,
        radiation=radiation, battery=battery, risk_level=risk, ts=ts or _now(),
    )
    if RANK[risk] > RANK[prev]:
        _log_alert(state, risk)
    return state


def _simulate_step(state: dict) -> dict:
    """Gera a próxima leitura simulada de um tripulante (variação suave em torno
    do último valor). Usado enquanto não há ESP32 real enviando dados."""
    return apply_vitals(
        state["id"],
        hr=round(state["hr"] + random.uniform(-3, 3), 1),
        spo2=round(min(100.0, state["spo2"] + random.uniform(-1, 1)), 1),
        temp=round(state["temp"] + random.uniform(-0.1, 0.1), 1),
        accel=round(abs(state["accel"] + random.uniform(-0.05, 0.05)), 2),
        resp=round(state["resp"] + random.uniform(-1, 1), 1),
        radiation=round(max(0.0, state["radiation"] + random.uniform(-0.05, 0.08)), 2),
        battery=round(max(5.0, state["battery"] - random.uniform(0, 0.05)), 1),
    )


# --------------------------------------------------------------------------- #
#  Health / Crew / Alerts
# --------------------------------------------------------------------------- #
@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="online", service="AstroCopilot", version="0.3.0")


@app.get("/api/crew")
def list_crew() -> dict:
    """Lista a tripulação monitorada e o estado atual de cada um."""
    return {"crew": list(_crew_state.values())}


@app.get("/api/alerts")
def list_alerts(limit: int = 20) -> dict:
    """Retorna os alertas mais recentes (escaladas de risco), do mais novo ao mais antigo.
    Persistido em SQLite — sobrevive a reinícios do backend."""
    return {"alerts": db.get_alerts(limit), "total": db.count_alerts()}


# --------------------------------------------------------------------------- #
#  Agente LLM + RAG  (Frente 1)
# --------------------------------------------------------------------------- #
@app.post("/api/agent/query", response_model=AgentResponse)
def agent_query(q: AgentQuery, channel: str = "text") -> AgentResponse:
    """Consulta o agente conversacional (Frente 1: RAG sobre manuais espaciais).

    A resposta vem da cadeia RAG (agent-rag/agent.py): recupera trechos no ChromaDB
    e gera o texto com o LLM no Bedrock, citando as fontes. Toda decisão é registrada
    na trilha de auditoria (governança de IA): pergunta, resposta, fontes e timestamp.

    Se o RAG não estiver disponível (sem API key ou sem base vetorial), responde em
    modo limitado para não derrubar o restante da aplicação.
    """
    if rag_query is not None:
        try:
            resultado = rag_query(q.text)
            response = AgentResponse(
                answer=resultado["answer"],
                sources=resultado.get("sources") or ["(sem fonte citada)"],
            )
        except Exception as exc:
            print(f"[Frente 1] falha na consulta RAG: {exc}")
            response = AgentResponse(
                answer=(
                    "Base de conhecimento indisponível no momento. Verifique a API key "
                    "do Bedrock e a base vetorial (rode o ingest em agent-rag/)."
                ),
                sources=["(RAG não configurado)"],
            )
    else:
        response = AgentResponse(
            answer=f"[MOCK] Resposta do copiloto para: '{q.text}'.",
            sources=["NASA-STD-3001 (mock)"],
        )
    db.insert_audit(q.text, response.answer, response.sources, channel=channel)
    return response


@app.get("/api/audit")
def list_audit(limit: int = 50) -> dict:
    """Trilha de auditoria das decisões do agente (governança), do mais novo ao mais antigo."""
    return {"audit": db.get_audit(limit), "total": db.count_audit()}


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
    answer = agent_query(AgentQuery(text=transcript), channel="voice")
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
#  Telemetria do ESP32  (Frente 4) — por tripulante, com mais sensores
# --------------------------------------------------------------------------- #
@app.post("/api/telemetry", response_model=TelemetryAck)
def telemetry(t: Telemetry) -> TelemetryAck:
    """Recebe leitura do wearable ESP32 de um tripulante, classifica e guarda.

    Campos opcionais (resp, radiation, battery) ausentes mantêm o valor atual.
    """
    if t.crew_id not in _crew_state:
        raise HTTPException(status_code=404, detail=f"Tripulante '{t.crew_id}' não existe")
    cur = _crew_state[t.crew_id]
    state = apply_vitals(
        t.crew_id,
        hr=t.hr, spo2=t.spo2, temp=t.temp, accel=t.accel,
        resp=t.resp if t.resp is not None else cur["resp"],
        radiation=t.radiation if t.radiation is not None else cur["radiation"],
        battery=t.battery if t.battery is not None else cur["battery"],
        ts=t.ts,
    )
    return TelemetryAck(status="ok", crew_id=t.crew_id, risk_level=state["risk_level"])


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket) -> None:
    """Stream de telemetria de TODA a tripulação em tempo real (1 Hz).

    Envia `{ ts, crew: [ {id, name, role, hr, spo2, temp, resp, radiation,
    battery, risk_level}, ... ] }`. Simula leituras enquanto não há ESP32 real.
    """
    await ws.accept()
    try:
        while True:
            crew_frame = [_simulate_step(state) for state in list(_crew_state.values())]
            await ws.send_json({"ts": _now(), "crew": crew_frame})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
