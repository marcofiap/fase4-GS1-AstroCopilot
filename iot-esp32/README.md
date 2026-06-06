# iot-esp32/ - IoT ESP32 + Edge + ML (Frente 4)

Wearable simulado que mede sinais vitais, processa na borda e classifica risco.

## Responsável
**Frente 4** - IoT ESP32 + Edge + Machine Learning.

## Estrutura
| Caminho | Descrição |
|---------|-----------|
| `platformio.ini` | Projeto PlatformIO: board `esp32doit-devkit-v1`, framework Arduino, `lib_deps` |
| `src/firmware.ino` | Código do ESP32: lê sensores, conecta no **WiFi `Wokwi-GUEST`** e envia a telemetria por **HTTP GET** ao backend |
| `wokwi.toml` + `diagram.json` | Simulação Wokwi (extensão VS Code); o ESP32 tem acesso de rede ao host |
| `ml-edge/` | Modelo de risco scikit-learn (`model.pkl`) + treino + métricas |

> O "servidor" da simulação é o próprio **backend FastAPI** (`../backend`, porta 8000),
> estendido com uma rota **GET** `/api/telemetry` (o ESP32 manda os dados como query
> params) e com o "monitor serial" espelhado em `/terminal_log` → `/terminal_stream`.

## Pipeline
1. ESP32 (Wokwi) lê **potenciômetro** (HR, simula MAX30102) + **MPU6050** (movimento) + **DS18B20** (temperatura).
2. Conecta no **WiFi `Wokwi-GUEST`**, sincroniza o relógio via **NTP** e **envia a telemetria por HTTP GET**:
   `GET http://<host>:8000/api/telemetry?crew_id=cmdr&hr=..&spo2=..&temp=..&accel=..&ts=..`.
3. **Edge:** o backend classifica `normal / fadiga / risco` com o modelo de ML e devolve o `risk_level` na resposta.
4. **Monitor serial:** o firmware também espelha cada linha do Serial em `GET /terminal_log?line=...` - dá p/ acompanhar a simulação ao vivo em `/terminal_stream` (SSE).
5. **Dashboard:** o tripulante **cmdr** passa a mostrar o dado **REAL** (prioridade sobre a simulação por 10 s a cada envio).
6. **Energia:** duty cycle + deep sleep no firmware (toggle `USE_DEEP_SLEEP`) - ver [Otimização de energia](#otimização-de-energia).

## Sensores no circuito (honestidade para o PDF)
| Sinal | Origem | Real? |
|-------|--------|-------|
| Aceleração | MPU6050 (I²C) | sensor real |
| Temperatura | DS18B20 (OneWire) | sensor real (arraste no Wokwi p/ simular febre) |
| HR | Potenciômetro (ADC) | simula o MAX30102 |
| SpO₂, Respiração | derivados do HR | modelados |
| Radiação | modelada | sem sensor |

O **MAX30102 não está na biblioteca do Wokwi**; usamos um potenciômetro como
"botão de esforço" - girá-lo eleva o HR e derruba a SpO₂, permitindo disparar
`fadiga`/`risco` ao vivo na demonstração. MPU6050 e DS18B20 são leituras reais.

## Conexão WiFi
O ESP32 simulado conecta no WiFi **`Wokwi-GUEST`** e bate **direto** no backend: `HTTP GET` com os dados em query
params. A **extensão Wokwi do VS Code dá acesso de rede ao host**, então a simulação
alcança um servidor rodando na sua máquina - basta apontar para o **IP da sua LAN**
(ou `host.wokwi.internal`).

```
ESP32 (WiFi Wokwi-GUEST) --HTTP GET--> http://<host>:8000/api/telemetry?...
```

> **Importante:** edite a 1ª entrada de `SERVIDORES[]` em [`src/firmware.ino`](src/firmware.ino)
> com o **IP da sua máquina na LAN** (rode `ipconfig` no Windows / `ifconfig` no Linux/Mac).
> O firmware tenta cada endereço da lista até um responder HTTP 200, então
> `host.wokwi.internal`, `127.0.0.1` e `localhost` ficam como fallback.

## Otimização de energia

> O Wokwi **não mede potência** - os valores abaixo vêm de referências reais e de um modelo de duty cycle (datasheet ESP32).

O firmware aplica **duty cycle + deep sleep** por um toggle
`USE_DEEP_SLEEP` em [`src/firmware.ino`](src/firmware.ino):

- **`0` (padrão)** - *sempre ligado*: envia a cada 2 s com o WiFi conectado. Demo
  Wokwi fluida (`terminal_log`/dashboard ao vivo). É o **pior caso**.
- **`1`** - *modo energia*: acorda → lê → envia → `esp_deep_sleep_start()` por
  `SLEEP_SECONDS`. O ESP32 reinicia em `setup()` ao despertar; `battery` e
  `bootCount` ficam em **memória RTC** (`RTC_DATA_ATTR`, sobrevive ao sono). Antes
  de dormir apaga o LED (GPIO2) e desliga o WiFi (`WiFi.disconnect`):
  desligar periféricos e rádio antes do sono.

### Consumo por modo do ESP32
| Modo | I_média | Observação |
|------|--------:|------------|
| Ativo + WiFi + loop | ~130–140 mA | estado atual com `USE_DEEP_SLEEP=0` |
| Light sleep | ~10–20 mA | mantém RAM; desperta rápido |
| **Deep sleep (timer)** | **~0.15–0.3 mA** | só o RTC ligado; ideal p/ wearable a bateria |

### Autonomia estimada (bateria 500 mAh; ~120 mA por ~3 s acordado/envio)
`I_média = (I_ativo·t_ativo + I_sleep·t_sleep) / período` · `autonomia = 500 mAh / I_média`

| Modo | I_média | Autonomia | vs. sempre ligado |
|------|--------:|----------:|------------------:|
| Sempre ligado (WiFi) | 100 mA | ~5 h | 1× |
| Deep sleep 60 s | 5.7 mA | **~3.6 dias** | 17× |
| Deep sleep 300 s | 1.2 mA | ~17 dias | 83× |

### Rádios sem fio
| Rádio | I_média | Pico | Alcance | Melhor para |
|-------|--------:|-----:|---------|-------------|
| **WiFi** (HTTP/MQTT) | ~84 mA | 387 mA | 30–50 m | infra local + backend (**POC atual**) |
| BLE (UART) | ~76 mA | 243 mA | 15–30 m | wearable → gateway na cabine |
| LoRa (p2p) | ~98 mA | >200 mA | **> 2 km** | EVA / telemetria remota esparsa |

> O WiFi é versátil mas **inviável a bateria sem deep sleep**. A POC usa
> WiFi+HTTP (já integrado ao backend); o deep sleep entre envios é o maior fator
> isolado de autonomia. Os sensores do circuito são de baixo consumo:
> MPU6050 ~3.9 mA / ~3 µA em standby; DS18B20 ~1.5 mA na medição.

## Como rodar (VS Code + PlatformIO + Wokwi)

**Pré-requisitos:** [PlatformIO IDE](https://platformio.org/install/ide?install=vscode) +
extensão **Wokwi Simulator** ([docs](https://docs.wokwi.com/vscode/getting-started);
na 1ª vez, `F1` → *Wokwi: Request a new License*).

Precisa de **2 coisas rodando ao mesmo tempo**: o backend e a simulação Wokwi.

1. **Backend** (terminal 1):
   ```powershell
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   > Use `--host 0.0.0.0` para o backend aceitar conexões da simulação (não só de `localhost`).
2. **Aponte o firmware para o seu host:** em [`src/firmware.ino`](src/firmware.ino),
   troque a 1ª entrada de `SERVIDORES[]` pelo **IP da sua máquina** (ex.: `192.168.0.42:8000`).
3. **Compile e simule** (VS Code):
   ```powershell
   cd iot-esp32
   pio run        # gera .pio/build/esp32doit-devkit-v1/firmware.{bin,elf}
   ```
   `Ctrl+Shift+P` → **Wokwi: Start Simulator** (com `wokwi.toml` ou `diagram.json` aberto).
   **Mantenha a aba do simulador visível** - o Wokwi **pausa** quando a aba perde o foco.

### Verifique (monitor serial da simulação)
- **Monitor serial espelhado no backend:** abra `http://localhost:8000/terminal_stream`
  no navegador (stream SSE) ou `http://localhost:8000/terminal_logs` (snapshot JSON) -
  são as mesmas linhas do Serial, repassadas pelo ESP32 via `/terminal_log`. A cada ~2 s, linhas
  `cmdr HR=... SpO2=... Temp=...`, depois `GET [1/4] ...` e `HTTP OK [...] -> risk=normal`.
- **Dashboard (frontend):** o tripulante **Cmdr. Ana Lima** passa a mostrar o dado **REAL**.
- **Gire o potenciômetro** (ou arraste a temperatura do DS18B20) → HR sobe → o dashboard
  escala para `fadiga`/`risco` e registra alerta.

> O contrato bate com `Telemetry` ([`backend/schemas.py`](../backend/schemas.py)):
> `crew_id, hr, spo2, temp, accel, resp, radiation, battery, ts`. A rota **GET**
> `/api/telemetry` (query params) e a **POST** (JSON) compartilham a mesma lógica.

### Troubleshooting
| Sintoma | Causa provável | Correção |
|---------|----------------|----------|
| Serial do Wokwi mostra `HTTP erro [...]` em todos | backend fora do ar, ou IP errado em `SERVIDORES[]` | suba o `uvicorn --host 0.0.0.0`; ponha o IP da sua LAN; teste `curl http://<host>:8000/` |
| `HTTP 404 ... Tripulante 'x' não existe` | `CREW_ID` inválido no firmware | use `cmdr`, `eng` ou `med` |
| Painel Serial do Wokwi **vazio** | aba do sim sem foco (Wokwi pausa) | foque a aba do simulador; a sim não tem porta COM (veja a serial no painel da simulação) |
| `WiFi conectado` mas todo envio falha | firewall do host bloqueia a porta 8000 | libere a porta 8000 no firewall, ou use `host.wokwi.internal:8000` |
| Dashboard volta a "simular" | passaram >10 s sem envio (TTL do dado real) | mantenha o sim rodando (aba visível) |
| `/terminal_stream` vazio | o ESP32 ainda não conectou no WiFi, ou backend reiniciou | aguarde o `WiFi conectado`; o buffer é em memória (zera ao reiniciar o backend) |

## MVP vs. Stretch
- **MVP:** telemetria chegando ao backend (via WiFi+HTTP) + modelo ML classificando risco.
- **Stretch:** deep sleep + duty cycle e comparação de rádios WiFi/BLE/LoRa - ver [Otimização de energia](#otimização-de-energia).

