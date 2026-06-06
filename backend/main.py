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
from fastapi.staticfiles import StaticFiles

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

# Garante que o Python encontre a pasta 'vision' na raiz do projeto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_VISION_DIR = str(_PROJECT_ROOT / "vision")
if _VISION_DIR not in sys.path:
    sys.path.insert(0, _VISION_DIR)

# Importa a função de processamento real que você desenvolveu e validou
from pipeline import process_image as vision_process

# --------------------------------------------------------------------------- #
#  Frente 2 (bootstrap): carrega raiz/.env antes do agent-rag/config.py
# --------------------------------------------------------------------------- #
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_VOICE_DIR = os.getenv("VOICE_NLP_DIR") or str(_PROJECT_ROOT / "voice-nlp")
if _VOICE_DIR not in sys.path:
    sys.path.insert(0, _VOICE_DIR)
import project_env  # noqa: E402

# --------------------------------------------------------------------------- #
#  Frente 1: cadeia RAG (agent-rag/agent.py)
#  Import resiliente. Se as dependencias ou a base vetorial nao estiverem
#  disponiveis, o endpoint /api/agent/query opera em modo limitado (ver abaixo).
# --------------------------------------------------------------------------- #
_RAG_DIR = os.getenv("AGENT_RAG_DIR") or str(_PROJECT_ROOT / "agent-rag")
if _RAG_DIR not in sys.path:
    sys.path.insert(0, _RAG_DIR)
try:
    from agent import query as rag_query  # noqa: E402
    project_env.sync_agent_rag_config()  # config.py le BEDROCK_API_KEY so na importacao
except Exception as exc:  # pragma: no cover - depende do ambiente
    rag_query = None
    print(f"[Frente 1] RAG indisponivel, usando modo limitado: {exc}")

# --------------------------------------------------------------------------- #
#  Frente 2: pipeline de voz (voice-nlp/pipeline.py)
# --------------------------------------------------------------------------- #
try:
    import voice_config  # noqa: E402  # nao usar "config" (colide com agent-rag)
    from pipeline import process_voice as voice_process  # noqa: E402

    voice_config.TTS_DIR.mkdir(parents=True, exist_ok=True)
except Exception as exc:  # pragma: no cover - depende do ambiente
    voice_process = None
    voice_config = None
    print(f"[Frente 2] Voz indisponivel: {exc}")


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

if voice_config is not None:
    app.mount(
        "/media/voice",
        StaticFiles(directory=str(voice_config.TTS_DIR)),
        name="voice_media",
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
def _ask_agent_for_voice(text: str) -> dict:
    """Callback do pipeline de voz: mesma resposta do agente + auditoria channel=voice."""
    resposta = agent_query(AgentQuery(text=text), channel="voice")
    return {"answer": resposta.answer, "sources": resposta.sources}


@app.post("/api/voice", response_model=VoiceResponse)
async def voice(audio: UploadFile = File(...)) -> VoiceResponse:
    """Recebe audio, transcreve (Whisper), consulta o agente RAG e sintetiza a resposta (gTTS)."""
    dados = await audio.read()
    if not dados:
        raise HTTPException(status_code=400, detail="Arquivo de audio vazio.")

    if voice_process is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Pipeline de voz indisponivel. Instale: pip install -r voice-nlp/requirements.txt "
                "e tenha ffmpeg no PATH."
            ),
        )

    try:
        resultado = await asyncio.to_thread(
            voice_process,
            dados,
            audio.filename,
            _ask_agent_for_voice,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"[Frente 2] falha no pipeline de voz: {exc}")
        raise HTTPException(status_code=500, detail=f"Falha no processamento de voz: {exc}") from exc

    audio_url = None
    arquivo = resultado.get("answer_audio_file")
    if arquivo is not None:
        audio_url = f"/media/voice/{arquivo.name}"

    return VoiceResponse(
        transcript=resultado["transcript"],
        answer_text=resultado["answer_text"],
        intent=resultado.get("intent"),
        sources=resultado.get("sources") or [],
        answer_audio_url=audio_url,
    )


# --------------------------------------------------------------------------- #
#  Visão computacional  (Frente 3)
# --------------------------------------------------------------------------- #
@app.post("/api/vision", response_model=VisionResponse)
async def vision(image: UploadFile = File(...)) -> VisionResponse:
    """
    Analisa a imagem real que o astronauta mostra (painel/componente).
    Roda a detecção YOLOv8 + Extração Tesseract OCR de forma dinâmica.
    """
    image_bytes = await image.read()
    
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Arquivo de imagem vazio ou corrompido.")
    
    try:
        # Executa o seu pipeline real da Frente 3 com os bytes da foto
        resultado = vision_process(image_bytes)
        
        # Devolve a resposta estruturada para o cliente (Frontend/API)
        return VisionResponse(
            objects=resultado.get("objects", []),
            ocr_text=resultado.get("ocr_text", ""),
            description=resultado.get("description", "")
        )
    except Exception as exc:
        print(f"[Erro Crítico Frente 3]: {exc}")
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento de visão: {exc}")

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
