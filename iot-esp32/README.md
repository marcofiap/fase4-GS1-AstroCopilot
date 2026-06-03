# iot-esp32/ — IoT ESP32 + Edge + ML (Frente 4)

Wearable simulado que mede sinais vitais, processa na borda e classifica risco.

## Responsável
**Frente 4** — IoT ESP32 + Edge + Machine Learning.

## Estrutura
| Pasta | Descrição |
|-------|-----------|
| `firmware/` | Código do ESP32 (`.ino`): leitura de sensores + envio + deep sleep |
| `ml-edge/` | Modelo de risco scikit-learn (`model.pkl`) + treino + métricas |
| `wokwi/` | Simulação Wokwi: `wokwi.toml` (extensão VS Code) + `diagram.json` + `libraries.txt` + `build.ps1` |
| `energy/` | Modelo de autonomia + comparação de rádios ([energia.md](energy/energia.md)) |

## Pipeline
1. ESP32 (Wokwi) lê **MAX30102** (HR/SpO₂) + **MPU6050** (movimento) + temperatura.
2. Envia por WiFi/LoRa/BLE para o backend (`POST /api/telemetry`).
3. **Edge:** modelo de ML classifica `normal / fadiga / risco`.
4. **Energia:** deep sleep entre envios — ver [energy/energia.md](energy/energia.md).

## Sensores no circuito (honestidade para o PDF)
| Sinal | Origem | Real? |
|-------|--------|-------|
| Aceleração | MPU6050 (I²C) | sensor real |
| Temperatura | DS18B20 (OneWire) | sensor real (arraste no Wokwi p/ simular febre) |
| HR | Potenciômetro (ADC) | simula o MAX30102 |
| SpO₂, Respiração | derivados do HR | modelados |
| Radiação | modelada | sem sensor |

O **MAX30102 não está na biblioteca do Wokwi**; usamos um potenciômetro como
"botão de esforço" — girá-lo eleva o HR e derruba a SpO₂, permitindo disparar
`fadiga`/`risco` ao vivo na demonstração. MPU6050 e DS18B20 são leituras reais.

## Como rodar no Wokwi

### A) VS Code + extensão Wokwi (recomendado)
Arquivos da extensão já versionados em [`wokwi/`](wokwi/): [`wokwi.toml`](wokwi/wokwi.toml) + [`diagram.json`](wokwi/diagram.json).
Instale a extensão **Wokwi Simulator** ([docs](https://docs.wokwi.com/vscode/getting-started)) e o `arduino-cli`.

1. Suba o backend (`backend/`): `uvicorn main:app --port 8000`. O `BACKEND_URL` já aponta
   para `http://host.wokwi.internal:8000` — a extensão expõe seu host à simulação (sem túnel).
2. Compile o firmware para `wokwi/build/` (a extensão lê o `.bin`/`.elf` de lá). A partir de `iot-esp32/`:
   ```powershell
   arduino-cli core install esp32:esp32
   arduino-cli lib install "Adafruit MPU6050" "Adafruit Unified Sensor" "Adafruit BusIO" OneWire DallasTemperature
   arduino-cli compile --fqbn esp32:esp32:esp32doit-devkit-v1 --output-dir wokwi/build firmware/firmware.ino
   ```
   Atalho: `pwsh wokwi/build.ps1`.
3. `Ctrl+Shift+P` → **Wokwi: Start Simulator** (com um arquivo da pasta `wokwi/` aberto).
4. O Serial Monitor mostra cada envio e o `risk_level` retornado. Gire o potenciômetro
   (ou arraste a temperatura do DS18B20) para disparar `fadiga`/`risco` no dashboard.

### B) Wokwi.com (web)
1. Suba o backend e exponha com túnel público (`ngrok http 8000`); cole a URL em
   `BACKEND_URL` no [`firmware/firmware.ino`](firmware/firmware.ino).
2. Abra um projeto ESP32 no Wokwi, cole o `firmware.ino`, substitua o `diagram.json`
   pelo [`wokwi/diagram.json`](wokwi/diagram.json) e garanta as bibliotecas de
   [`wokwi/libraries.txt`](wokwi/libraries.txt). Rode.

> O JSON enviado bate com o contrato `Telemetry` ([`backend/schemas.py`](../backend/schemas.py))
> e foi validado end-to-end contra o backend real (resposta `risk_level` + alerta).

## MVP vs. Stretch
- **MVP:** telemetria chegando ao backend + modelo ML classificando risco.
- **Stretch:** deep sleep + comparação de consumo WiFi vs. BLE vs. LoRa ([energia.md](energy/energia.md)).

## Disciplinas
F4 C08 (energia ESP32) · F4 C09 (LoRa/BLE/WiFi) · F3 C08 (Cloud+IoT) · F3 C09 (Edge/Fog) · ML.
