"""Schemas (contratos) compartilhados da API AstroCopilot.

São a fonte da verdade da integração entre as frentes. Ver docs/arquitetura.md.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class AgentQuery(BaseModel):
    text: str = Field(..., description="Pergunta/comando do tripulante em texto")
    with_audio: bool = Field(
        False,
        description="Gera MP3 da resposta no mesmo request (Edge TTS, perfil abaixo)",
    )
    voice_profile: Optional[str] = Field(
        "leo",
        description="Perfil de voz quando with_audio=true: eve | ara | leo | rex | sal",
    )


class AgentResponse(BaseModel):
    answer: str
    sources: List[str] = []
    answer_audio_url: Optional[str] = Field(
        None, description="MP3 da resposta em /media/voice/ (quando with_audio=true)"
    )


class VoiceResponse(BaseModel):
    transcript: str
    answer_text: str
    intent: Optional[str] = Field(
        None, description="Classificacao MVP: pergunta | status | emergencia"
    )
    sources: List[str] = []
    answer_audio_url: Optional[str] = None


class TtsRequest(BaseModel):
    text: str = Field(..., description="Texto da resposta do agente para sintetizar em PT-BR")
    voice_profile: Optional[str] = Field(
        "leo",
        description="Perfil de voz: eve | ara | leo | rex | sal",
    )


class TtsResponse(BaseModel):
    audio_url: str = Field(..., description="URL do MP3 em /media/voice/")


class UserRecordingMeta(BaseModel):
    id: str
    filename: str
    label: str
    created_at: str
    size_bytes: int
    audio_url: str


class UserRecordingsListResponse(BaseModel):
    recordings: List[UserRecordingMeta] = []
    max: int = 8


class VisionResponse(BaseModel):
    objects: List[str] = []
    ocr_text: str = ""
    description: str = ""


class Telemetry(BaseModel):
    crew_id: str = Field("cmdr", description="Identificador do tripulante (cmdr, eng, med)")
    hr: float = Field(..., description="Frequência cardíaca (bpm)")
    spo2: float = Field(..., description="Saturação de oxigênio (%)")
    temp: float = Field(..., description="Temperatura corporal (°C)")
    accel: float = Field(..., description="Magnitude de aceleração (g)")
    resp: Optional[float] = Field(None, description="Frequência respiratória (rpm)")
    radiation: Optional[float] = Field(None, description="Dose de radiação (µSv/h)")
    battery: Optional[float] = Field(None, description="Bateria do wearable (%)")
    ts: Optional[str] = Field(None, description="Timestamp ISO-8601")


class TelemetryAck(BaseModel):
    status: str
    crew_id: str
    risk_level: str
