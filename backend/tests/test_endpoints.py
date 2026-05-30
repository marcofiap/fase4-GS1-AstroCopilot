"""Testes dos endpoints da API (REST)."""


def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "online"
    assert body["service"] == "AstroCopilot"


def test_crew_tem_tres_tripulantes(client):
    r = client.get("/api/crew")
    assert r.status_code == 200
    crew = r.json()["crew"]
    assert len(crew) == 3
    assert {c["id"] for c in crew} == {"cmdr", "eng", "med"}


def test_agent_query_responde_e_audita(client):
    r = client.post("/api/agent/query", json={"text": "como despressurizar?"})
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body and body["sources"]

    # A consulta deve ter sido registrada na trilha de auditoria.
    audit = client.get("/api/audit").json()
    assert audit["total"] == 1
    assert audit["audit"][0]["question"] == "como despressurizar?"
    assert audit["audit"][0]["channel"] == "text"


def test_agent_query_canal_voice(client):
    client.post("/api/agent/query?channel=voice", json={"text": "teste voz"})
    audit = client.get("/api/audit").json()
    assert audit["audit"][0]["channel"] == "voice"


def test_telemetry_normal_nao_gera_alerta(client):
    r = client.post(
        "/api/telemetry",
        json={"crew_id": "cmdr", "hr": 72, "spo2": 98, "temp": 36.6, "accel": 0.1},
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "normal"
    assert client.get("/api/alerts").json()["total"] == 0


def test_telemetry_escalada_gera_alerta(client):
    r = client.post(
        "/api/telemetry",
        json={"crew_id": "eng", "hr": 160, "spo2": 85, "temp": 39.0, "accel": 0.2},
    )
    assert r.status_code == 200
    assert r.json()["risk_level"] == "risco"

    alerts = client.get("/api/alerts").json()
    assert alerts["total"] == 1
    assert alerts["alerts"][0]["crew_id"] == "eng"
    assert alerts["alerts"][0]["risk_level"] == "risco"


def test_telemetry_crew_inexistente_404(client):
    r = client.post(
        "/api/telemetry",
        json={"crew_id": "ninguem", "hr": 72, "spo2": 98, "temp": 36.6, "accel": 0.1},
    )
    assert r.status_code == 404


def test_vision_mock(client):
    r = client.post("/api/vision", files={"image": ("p.png", b"fakebytes", "image/png")})
    assert r.status_code == 200
    assert "objects" in r.json()
