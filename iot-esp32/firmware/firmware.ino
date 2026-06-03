/*
 * AstroCopilot — Frente 4 — Wearable de telemetria do tripulante (ESP32)
 * =====================================================================
 * Lê sinais vitais, monta o JSON do contrato `Telemetry` e envia por WiFi
 * (HTTP POST) para o backend em `POST /api/telemetry`. A resposta traz o
 * `risk_level` classificado pelo modelo de ML (Frente 4) no servidor.
 *
 * Sensores no circuito (ver wokwi/diagram.json):
 *   - MPU6050  (I2C)     -> aceleração REAL (movimento do tripulante)
 *   - DS18B20  (OneWire) -> temperatura REAL (default 36.6 C; arraste no Wokwi
 *                           para simular febre e disparar risco ao vivo)
 *   - Potenciômetro (ADC)-> simula o MAX30102 (HR). Girar o botão eleva o HR;
 *                           SpO2 e respiração são derivados dele.
 *
 * Honestidade (para o PDF): o MAX30102 (HR/SpO2) NÃO existe na biblioteca do
 * Wokwi, então o HR é provocado por um potenciômetro e SpO2/respiração são
 * derivados; a radiação é modelada (não há sensor). MPU6050 e DS18B20 são
 * leituras de sensor reais via I2C/OneWire.
 *
 * Conectividade com o backend:
 *   - Wokwi no VS Code: use  http://host.wokwi.internal:8000/...
 *   - Wokwi.com (web):  exponha o backend com um túnel público (ex.: ngrok)
 *                       e cole a URL pública em BACKEND_URL.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "esp_sleep.h"            // deep sleep (otimização de energia — Frente 4)

// --------------------------- Configuração ---------------------------------- #
#define WIFI_SSID "Wokwi-GUEST"   // rede aberta padrão do Wokwi
#define WIFI_PASS ""
// Backend: troque conforme onde você roda o Wokwi (ver cabeçalho).
#define BACKEND_URL "http://host.wokwi.internal:8000/api/telemetry"
#define CREW_ID "cmdr"            // tripulante monitorado (cmdr | eng | med)
#define SAMPLE_INTERVAL_MS 2000   // intervalo no modo loop contínuo (ms)

// Energia: 1 = deep sleep entre amostras (produção, baixíssimo consumo);
//          0 = loop contínuo (demonstração mais fluida no Wokwi/dashboard).
#define USE_DEEP_SLEEP 1
#define SLEEP_SECONDS 10          // tempo dormindo entre envios (deep sleep)

#define PIN_SDA 21
#define PIN_SCL 22
#define PIN_POT 34                // ADC1_CH6 (entrada) — potenciômetro = HR
#define PIN_ONEWIRE 4             // DS18B20 (com pull-up de 4.7k no diagrama)

Adafruit_MPU6050 mpu;
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature ds18b20(&oneWire);

bool mpuOk = false;
// Memória RTC: sobrevive ao deep sleep (o ESP32 reinicia em setup() ao acordar).
RTC_DATA_ATTR float battery = 100.0;   // bateria do wearable (%)
RTC_DATA_ATTR uint32_t bootCount = 0;  // nº de ciclos acordar→enviar→dormir

// ------------------------------ Utilidades --------------------------------- #
static float clampf(float v, float lo, float hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

// Ruído uniforme em [-amp, +amp]
static float noise(float amp) {
  return ((float)random(-1000, 1001) / 1000.0f) * amp;
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("Conectando ao WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  uint8_t tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries++ < 40) {
    delay(250);
    Serial.print('.');
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " OK" : " FALHOU");
}

// Magnitude de aceleração ACIMA da gravidade (g) — ~0 em repouso, sobe ao mover
float readAccelG() {
  if (!mpuOk) return 0.0f;
  sensors_event_t a, g, t;
  mpu.getEvent(&a, &g, &t);
  float mag = sqrtf(a.acceleration.x * a.acceleration.x +
                    a.acceleration.y * a.acceleration.y +
                    a.acceleration.z * a.acceleration.z);
  return fabsf(mag / 9.81f - 1.0f);
}

// Temperatura corporal pelo DS18B20 (real). Fallback se leitura inválida.
float readTempC() {
  ds18b20.requestTemperatures();
  float c = ds18b20.getTempCByIndex(0);
  if (c < 0.0f || c > 60.0f) return 36.6f;  // sensor ausente/!=
  return c;
}

void postTelemetry(float hr, float spo2, float temp, float accel,
                   float resp, float radiation, float batt) {
  connectWiFi();
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");

  char body[256];
  snprintf(body, sizeof(body),
           "{\"crew_id\":\"%s\",\"hr\":%.1f,\"spo2\":%.1f,\"temp\":%.1f,"
           "\"accel\":%.2f,\"resp\":%.1f,\"radiation\":%.2f,\"battery\":%.1f}",
           CREW_ID, hr, spo2, temp, accel, resp, radiation, batt);

  int code = http.POST((uint8_t *)body, strlen(body));
  if (code > 0) {
    Serial.printf("POST %d -> %s\n", code, http.getString().c_str());
  } else {
    Serial.printf("POST falhou: %s\n", http.errorToString(code).c_str());
  }
  http.end();
}

// Lê todos os sinais, monta o pacote e envia ao backend. Uma chamada por ciclo
// (vale para o modo deep sleep e para o loop contínuo).
void sampleAndSend() {
  // HR pelo potenciômetro (simula MAX30102): 55..180 bpm
  int raw = analogRead(PIN_POT);
  float hr = 55.0f + (raw / 4095.0f) * 125.0f;

  // SpO2 cai com o esforço; respiração sobe — derivados do HR + ruído
  float spo2 = clampf(99.0f - (hr - 70.0f) * 0.10f + noise(0.4f), 80.0f, 100.0f);
  float resp = clampf(12.0f + (hr - 70.0f) * 0.12f + noise(0.6f), 6.0f, 36.0f);

  float temp = readTempC();             // DS18B20 (real)
  float accel = readAccelG();           // MPU6050 (real)

  // Radiação: modelada (sem sensor). Base baixa + pico raro (tempestade solar).
  float radiation = clampf(0.2f + noise(0.1f), 0.0f, 25.0f);
  if (random(0, 100) < 5) radiation += (float)random(3, 9);

  battery = clampf(battery - 0.05f, 5.0f, 100.0f);

  Serial.printf("HR=%.0f SpO2=%.1f Temp=%.1f Accel=%.2f Resp=%.0f Rad=%.2f Bat=%.1f\n",
                hr, spo2, temp, accel, resp, radiation, battery);
  postTelemetry(hr, spo2, temp, accel, resp, radiation, battery);
}

// -------------------------------- Setup ------------------------------------ #
void setup() {
  Serial.begin(115200);
  delay(200);

  Wire.begin(PIN_SDA, PIN_SCL);
  mpuOk = mpu.begin();
  if (mpuOk) {
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    Serial.println("MPU6050 OK");
  } else {
    Serial.println("MPU6050 nao encontrado (aceleracao = 0)");
  }

  ds18b20.begin();
  analogReadResolution(12);             // ADC 0..4095
  randomSeed(analogRead(PIN_POT));
  connectWiFi();

  bootCount++;
  sampleAndSend();                      // uma amostra por "acordar"

#if USE_DEEP_SLEEP
  Serial.printf("Deep sleep por %d s (ciclo #%u, bateria %.1f%%)\n",
                SLEEP_SECONDS, bootCount, battery);
  Serial.flush();
  esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_SECONDS * 1000000ULL);
  esp_deep_sleep_start();               // ao acordar, reinicia em setup()
#endif
}

// -------------------------------- Loop ------------------------------------- #
void loop() {
#if !USE_DEEP_SLEEP
  sampleAndSend();
  delay(SAMPLE_INTERVAL_MS);
#endif
  // No modo deep sleep o setup() dorme e a execução nunca chega aqui.
}
