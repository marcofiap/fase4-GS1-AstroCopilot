# ⌚ iot-esp32/ — IoT ESP32 + Edge + ML (Frente 4)

Wearable simulado que mede sinais vitais, processa na borda e classifica risco.

## Responsável
**Frente 4** — IoT ESP32 + Edge + Machine Learning.

## Estrutura
| Pasta | Descrição |
|-------|-----------|
| `firmware/` | Código do ESP32 (`.ino`): leitura de sensores + envio |
| `ml-edge/` | Modelo de risco em scikit-learn (`model.pkl`) + script de treino |
| `wokwi/` | Projeto Wokwi (`diagram.json`) — simulação sem hardware físico |

## Pipeline
1. ESP32 (Wokwi) lê **MAX30102** (HR/SpO₂) + **MPU6050** (movimento) + temperatura.
2. Envia por WiFi/LoRa/BLE para o backend (`POST /api/telemetry`).
3. **Edge:** modelo de ML classifica `normal / fadiga / risco`.
4. Otimização de energia (deep sleep).

## MVP vs. Stretch
- **MVP:** telemetria chegando ao backend + modelo classificando risco.
- **Stretch:** comparar consumo WiFi vs. BLE vs. LoRa (gráfico para o PDF).

## Disciplinas
F4 C08 (energia ESP32) · F4 C09 (LoRa/BLE/WiFi) · F3 C08 (Cloud+IoT) · F3 C09 (Edge/Fog) · ML.
