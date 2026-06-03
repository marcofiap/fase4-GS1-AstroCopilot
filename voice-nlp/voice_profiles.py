"""
Perfis de voz do Astro (estilo Grok) mapeados para Edge TTS pt-BR.
"""
from __future__ import annotations

from typing import TypedDict

DEFAULT_PROFILE = "leo"

# Edge TTS: +50% ≈ 1,5× a velocidade normal (100% + 50% = 150%).
MALE_DEFAULT_RATE = "+50%"


class VoiceProfile(TypedDict):
    id: str
    name: str
    tagline: str
    voice: str
    rate: str


VOICE_PROFILES: dict[str, VoiceProfile] = {
    "eve": {
        "id": "eve",
        "name": "Eve",
        "tagline": "Feminina energética, animada",
        "voice": "pt-BR-FranciscaNeural",
        "rate": "+24%",
    },
    "ara": {
        "id": "ara",
        "name": "Ara",
        "tagline": "Feminina quente, amigável e conversacional",
        "voice": "pt-BR-ThalitaNeural",
        "rate": "+12%",
    },
    "leo": {
        "id": "leo",
        "name": "Leo",
        "tagline": "Masculino autoritário, 1,5× (voz padrão)",
        "voice": "pt-BR-AntonioNeural",
        "rate": MALE_DEFAULT_RATE,
    },
    "rex": {
        "id": "rex",
        "name": "Rex",
        "tagline": "Masculino confiante, 1,5×",
        "voice": "pt-BR-DonatoNeural",
        "rate": MALE_DEFAULT_RATE,
    },
    "sal": {
        "id": "sal",
        "name": "Sal",
        "tagline": "Neutra suave, equilibrada e versátil",
        "voice": "pt-BR-ThalitaNeural",
        "rate": "+4%",
    },
}


def resolve_profile(profile_id: str | None) -> VoiceProfile:
    key = (profile_id or DEFAULT_PROFILE).lower().strip()
    if key not in VOICE_PROFILES:
        return VOICE_PROFILES[DEFAULT_PROFILE]
    return VOICE_PROFILES[key]


def list_profiles() -> list[dict[str, str]]:
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "tagline": p["tagline"],
            "label": f"{p['name']} — {p['tagline']}",
        }
        for p in VOICE_PROFILES.values()
    ]