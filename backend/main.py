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
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse
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
    """Inicialização da app: tabelas do SQLite + modelo de risco (Frente 4)."""
    db.init_db()
    if load_model():
        print(f"[startup] Modelo de risco (ML) carregado de {_MODEL_PATH}")
    else:
        print(f"[startup] model.pkl ausente em {_MODEL_PATH} — usando regras (fallback)")
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

# Frente 4: a telemetria REAL do ESP32 tem prioridade sobre a simulação.
# Guarda o instante (relógio monotônico) do último POST real por tripulante;
# enquanto for recente, o stream WS reenvia o dado real em vez de simular.
REAL_TELEMETRY_TTL_S = 10.0
_last_real: dict[str, float] = {}

# Frente 4: "monitor serial" da simulação espelhado pelo ESP32 via GET /terminal_log.
# Buffer circular em memória; exposto por /terminal_logs (JSON) e /terminal_stream (SSE).
_terminal_log: deque[str] = deque(maxlen=1000)
_terminal_lock = threading.Lock()


# --------------------------------------------------------------------------- #
#  Classificador de risco (Frente 4) — modelo ML treinado com fallback p/ regras
# --------------------------------------------------------------------------- #
# Por padrão aponta para iot-esp32/ml-edge/model.pkl no repositório. Em Docker
# (onde o pkl pode não estar na imagem) defina a env ASTRO_MODEL_PATH ou deixe
# cair no fallback de regras — a API nunca quebra por falta do modelo.
_MODEL_PATH = Path(
    os.getenv(
        "ASTRO_MODEL_PATH",
        Path(__file__).resolve().parent.parent / "iot-esp32" / "ml-edge" / "model.pkl",
    )
)
# Bundle carregado uma vez no startup: {model, features, labels, sklearn_version}
_model_bundle: dict | None = None


def load_model() -> bool:
    """Carrega o bundle do modelo de risco em memória (uma vez, no startup).

    Retorna True se carregou; False se o arquivo não existe ou é incompatível —
    nesse caso classify_risk() cai nas regras determinísticas, sem derrubar a API.
    """
    global _model_bundle
    try:
        bundle = joblib.load(_MODEL_PATH)
        _ = bundle["model"], bundle["features"]  # valida o formato do bundle
        _model_bundle = bundle
        return True
    except Exception:  # arquivo ausente, versão incompatível, formato inesperado
        _model_bundle = None
        return False


def _classify_risk_rules(hr: float, spo2: float, temp: float,
                         radiation: float = 0.0, resp: float = 14.0) -> str:
    """Regras determinísticas de risco — política da missão e FALLBACK do modelo.
    É a fonte da verdade dos rótulos usados para treinar o modelo (Frente 4)."""
    if spo2 < 90 or hr > 140 or temp > 38.5 or radiation > 5.0 or resp > 28:
        return "risco"
    if spo2 < 94 or hr > 110 or temp > 37.8 or radiation > 1.0 or resp > 24 or resp < 8:
        return "fadiga"
    return "normal"


def classify_risk(hr: float, spo2: float, temp: float,
                  radiation: float = 0.0, resp: float = 14.0) -> str:
    """Classifica o risco do tripulante em normal/fadiga/risco.

    Usa o modelo scikit-learn da Frente 4 (iot-esp32/ml-edge/model.pkl) quando
    carregado; senão usa as regras determinísticas (_classify_risk_rules).
    """
    if _model_bundle is None:
        return _classify_risk_rules(hr, spo2, temp, radiation, resp)
    values = {"hr": hr, "spo2": spo2, "temp": temp, "radiation": radiation, "resp": resp}
    row = [[values[f] for f in _model_bundle["features"]]]  # respeita a ordem do bundle
    try:
        return str(_model_bundle["model"].predict(row)[0])
    except Exception:  # qualquer falha de inferência → regra (nunca derruba a API)
        return _classify_risk_rules(hr, spo2, temp, radiation, resp)


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


def _build_crew_frame() -> list[dict]:
    """Monta o frame da tripulação para o stream WS: o dado REAL do ESP32 tem
    prioridade enquanto houver POST recente (< TTL); caso contrário, simula."""
    now = time.monotonic()
    frame = []
    for state in list(_crew_state.values()):
        fresh = now - _last_real.get(state["id"], -1e9) < REAL_TELEMETRY_TTL_S
        frame.append(state if fresh else _simulate_step(state))
    return frame


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
def _ingest_telemetry(crew_id, hr, spo2, temp, accel,
                      resp=None, radiation=None, battery=None, ts=None) -> dict:
    """Núcleo compartilhado pelo POST (JSON) e pelo GET (query params) de telemetria.

    Atualiza o estado do tripulante, classifica o risco e marca a leitura como
    REAL (prioridade sobre a simulação por TTL). Campos opcionais (resp,
    radiation, battery) ausentes mantêm o valor atual.
    """
    if crew_id not in _crew_state:
        raise HTTPException(status_code=404, detail=f"Tripulante '{crew_id}' não existe")
    cur = _crew_state[crew_id]
    state = apply_vitals(
        crew_id,
        hr=hr, spo2=spo2, temp=temp, accel=accel,
        resp=resp if resp is not None else cur["resp"],
        radiation=radiation if radiation is not None else cur["radiation"],
        battery=battery if battery is not None else cur["battery"],
        ts=ts,
    )
    _last_real[crew_id] = time.monotonic()  # marca como dado real recente (Frente 4)
    return state


@app.post("/api/telemetry", response_model=TelemetryAck)
def telemetry(t: Telemetry) -> TelemetryAck:
    """Recebe leitura do wearable ESP32 (JSON), classifica e guarda."""
    state = _ingest_telemetry(
        t.crew_id, t.hr, t.spo2, t.temp, t.accel,
        resp=t.resp, radiation=t.radiation, battery=t.battery, ts=t.ts,
    )
    return TelemetryAck(status="ok", crew_id=t.crew_id, risk_level=state["risk_level"])


@app.get("/api/telemetry", response_model=TelemetryAck)
def telemetry_get(
    crew_id: str = "cmdr",
    hr: float = Query(..., description="Frequência cardíaca (bpm)"),
    spo2: float = Query(..., description="Saturação de oxigênio (%)"),
    temp: float = Query(..., description="Temperatura corporal (°C)"),
    accel: float = Query(0.0, description="Magnitude de aceleração (g)"),
    resp: Optional[float] = Query(None, description="Frequência respiratória (rpm)"),
    radiation: Optional[float] = Query(None, description="Dose de radiação (µSv/h)"),
    battery: Optional[float] = Query(None, description="Bateria do wearable (%)"),
    ts: Optional[str] = Query(None, description="Timestamp ISO-8601"),
) -> TelemetryAck:
    """Variante GET para a simulação Wokwi.

    O ESP32 envia a telemetria via WiFi + HTTP GET (mesmo padrão dos projetos
    FarmTech): `/api/telemetry?crew_id=cmdr&hr=..&spo2=..&temp=..&accel=..&ts=..`.
    Mesma lógica do POST — existe porque o HTTPClient do firmware manda os dados
    como query params, e não como corpo JSON.
    """
    state = _ingest_telemetry(
        crew_id, hr, spo2, temp, accel,
        resp=resp, radiation=radiation, battery=battery, ts=ts,
    )
    return TelemetryAck(status="ok", crew_id=crew_id, risk_level=state["risk_level"])


# --------------------------------------------------------------------------- #
#  "Monitor serial" da simulação espelhado por HTTP (Frente 4)
#  O firmware faz GET /terminal_log?line=<linha> a cada evento do Serial. Daí dá
#  para acompanhar o monitor serial do Wokwi fora do simulador: /terminal_logs
#  (JSON) para um snapshot e /terminal_stream (SSE) para o stream ao vivo.
# --------------------------------------------------------------------------- #
@app.get("/terminal_log")
def terminal_log(line: str = "") -> PlainTextResponse:
    """Recebe uma linha do monitor serial espelhada pelo ESP32 (query `line`)."""
    if not line:
        return PlainTextResponse("MISSING_LINE", status_code=400)
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {line}"
    with _terminal_lock:
        _terminal_log.append(entry)
    return PlainTextResponse("OK")


@app.get("/terminal_logs")
def terminal_logs(limit: int = 500) -> dict:
    """Últimas linhas espelhadas do monitor serial da simulação (snapshot JSON)."""
    with _terminal_lock:
        lines = list(_terminal_log)[-limit:]
    return {"lines": lines, "count": len(lines)}


@app.get("/terminal_stream")
async def terminal_stream() -> StreamingResponse:
    """Stream SSE do monitor serial espelhado — abra no navegador p/ ver ao vivo."""

    async def gen():
        last = 0
        while True:
            with _terminal_lock:
                lines = list(_terminal_log)
            if len(lines) > last:
                for ln in lines[last:]:
                    yield f"data: {ln}\n\n"
                last = len(lines)
            await asyncio.sleep(0.5)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket) -> None:
    """Stream de telemetria de TODA a tripulação em tempo real (1 Hz).

    Envia `{ ts, crew: [ {id, name, role, hr, spo2, temp, resp, radiation,
    battery, risk_level}, ... ] }`. Para cada tripulante, reenvia a telemetria
    REAL do ESP32 se houver POST recente (< TTL); caso contrário, simula.
    """
    await ws.accept()
    try:
        while True:
            await ws.send_json({"ts": _now(), "crew": _build_crew_frame()})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
