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


class AgentResponse(BaseModel):
    answer: str
    sources: List[str] = []


class VoiceResponse(BaseModel):
    transcript: str
    answer_text: str
    answer_audio_url: Optional[str] = None


class VisionResponse(BaseModel):
    objects: List[str] = []
    ocr_text: str = ""
    description: str = ""


class Telemetry(BaseModel):
    hr: float = Field(..., description="Frequência cardíaca (bpm)")
    spo2: float = Field(..., description="Saturação de oxigênio (%)")
    temp: float = Field(..., description="Temperatura corporal (°C)")
    accel: float = Field(..., description="Magnitude de aceleração (g)")
    ts: Optional[str] = Field(None, description="Timestamp ISO-8601")


class TelemetryAck(BaseModel):
    status: str
    risk_level: str
