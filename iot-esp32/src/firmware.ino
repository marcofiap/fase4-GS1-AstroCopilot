/*
 * AstroCopilot — Frente 4 — Wearable de telemetria do tripulante (ESP32)
 * =====================================================================
 * Lê os sinais vitais e ENVIA a telemetria ao backend por WiFi + HTTP GET
 * (mesmo padrão dos projetos FarmTech de Config_Luiz). NÃO usa mais a ponte
 * serial RFC2217: o ESP32 simulado conecta no WiFi `Wokwi-GUEST` e bate direto
 * no FastAPI:
 *
 *   ESP32 (WiFi Wokwi-GUEST) --HTTP GET--> http://<host>:8000/api/telemetry?...
 *
 * O `risk_level` classificado pelo modelo de ML volta no corpo da resposta e é
 * impresso no Serial. Além disso, cada linha relevante do Serial é ESPELHADA no
 * backend via GET /terminal_log?line=... — assim dá p/ acompanhar o "monitor
 * serial" da simulação fora do Wokwi (em /terminal_stream).
 *
 * Onde reaching o backend: a extensão Wokwi do VS Code dá acesso de rede ao host.
 * Use o IP da SUA máquina na LAN (rode `ipconfig`/`ifconfig`) em SERVIDORES[],
 * ou `host.wokwi.internal` (alias do host na extensão). O firmware tenta cada
 * endereço da lista até um responder HTTP 200.
 *
 * Sensores no circuito (ver diagram.json):
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
 * Otimização de energia: toggle USE_DEEP_SLEEP. Em 0 (padrão) fica
 * SEMPRE LIGADO — envia a cada SAMPLE_INTERVAL_MS com o WiFi conectado (demo
 * Wokwi fluida, mas é o PIOR caso de energia: ~130-140 mA contínuos).
 * Em 1 vira MODO ENERGIA (duty cycle): acorda → lê → envia → esp_deep_sleep_start()
 * por SLEEP_SECONDS. Ao despertar o ESP32 REINICIA em setup() (loop() nunca roda);
 * `battery` e `bootCount` ficam em memória RTC (RTC_DATA_ATTR), que sobrevive ao
 * sono. Antes de dormir apaga o LED e desliga o WiFi. Deep sleep ~0.15-0.3 mA →
 * leva a autonomia de ~5 h (sempre ligado) para ~dias (ver README, seção Energia).
 */
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>                 // sincronização de tempo via NTP (timestamp ISO)
#include "esp_sleep.h"            // deep sleep / duty cycle (otimização de energia)

// --------------------------- Configuração ---------------------------------- #
#define CREW_ID "cmdr"            // tripulante monitorado (cmdr | eng | med)
#define SAMPLE_INTERVAL_MS 2000   // intervalo entre amostras/envios (ms) — modo sempre ligado

// --- Otimização de energia --- #
// 0 = SEMPRE LIGADO: demo Wokwi fluida (terminal_log/dashboard ao vivo); pior
//     caso de energia (~130-140 mA). 1 = MODO ENERGIA: acorda → envia → deep
//     sleep por SLEEP_SECONDS (duty cycle; ~0.15-0.3 mA dormindo).
#define USE_DEEP_SLEEP 0
#define SLEEP_SECONDS  60         // sono entre envios no modo energia (duty cycle)
#define LED_PIN        2          // LED onboard do devkit-v1 — apagado antes de dormir

// --- WiFi (rede aberta do simulador Wokwi) --- #
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

// --- NTP (timestamp real p/ o backend) --- #
const char* NTP_SERVER = "pool.ntp.org";
const long  GMT_OFFSET_SEC = -3 * 3600;   // GMT-3 (Brasília)
const int   DAYLIGHT_OFFSET_SEC = 0;

// --- Backend: candidatos host:porta (porta 8000 = FastAPI/uvicorn) --- #
// EDITE a 1ª linha p/ o IP da SUA máquina na LAN (ipconfig). O firmware tenta
// cada endereço em ordem até um responder HTTP 200.
const char* SERVIDORES[] = {
  "192.168.3.26:8000",        // IP da sua máquina na LAN (Wi-Fi) — adicione se mudar de rede
  "host.wokwi.internal:8000", // alias do host na extensão Wokwi do VS Code
  "127.0.0.1:8000",
  "localhost:8000"
};
const uint8_t NUM_SERVIDORES = sizeof(SERVIDORES) / sizeof(SERVIDORES[0]);

// --- Pinos (casam com o diagram.json) --- #
#define PIN_SDA 21
#define PIN_SCL 22
#define PIN_POT 34                // ADC1_CH6 — potenciômetro = HR (simula MAX30102)
#define PIN_ONEWIRE 4             // DS18B20 (pull-up de 4.7k no diagrama)

Adafruit_MPU6050 mpu;
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature ds18b20(&oneWire);

bool mpuOk = false;
bool ntpSincronizado = false;
// RTC_DATA_ATTR: sobrevivem ao deep sleep (a RAM comum é apagada ao dormir).
// Sem deep sleep funcionam como variáveis globais normais.
RTC_DATA_ATTR float battery = 100.0;     // bateria do wearable (%)
RTC_DATA_ATTR uint32_t bootCount = 0;    // nº de ciclos acordar→enviar→(dormir)

// Reutiliza o cliente HTTP entre envios (economiza heap/handshake)
static WiFiClient wifiClient;
static HTTPClient http;
static bool httpInicializado = false;

// ------------------------------ Utilidades --------------------------------- #
static float clampf(float v, float lo, float hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

// Ruído uniforme em [-amp, +amp]
static float noise(float amp) {
  return ((float)random(-1000, 1001) / 1000.0f) * amp;
}

// Percent-encode p/ usar em query string (timestamp e linhas de log)
String urlEncode(const String& s) {
  String out;
  const char* hex = "0123456789ABCDEF";
  for (size_t i = 0; i < s.length(); i++) {
    unsigned char c = (unsigned char)s[i];
    if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
        (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == '~') {
      out += (char)c;
    } else {
      out += '%';
      out += hex[(c >> 4) & 0xF];
      out += hex[c & 0xF];
    }
  }
  return out;
}

// Timestamp ISO YYYY-MM-DDTHH:MM:SS (NTP; cai p/ millis() se NTP indisponível)
String obterTimestamp() {
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    char buf[20];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &timeinfo);
    return String(buf);
  }
  uint32_t s = millis() / 1000, m = s / 60, h = m / 60;
  char buf[20];
  snprintf(buf, sizeof(buf), "2024-01-01T%02d:%02d:%02d",
           (int)(h % 24), (int)(m % 60), (int)(s % 60));
  return String(buf);
}

// Espelha uma linha do Serial no backend: GET /terminal_log?line=<urlencoded>
// (best-effort; não trava o loop se o backend estiver fora).
void enviarLogServidor(const String& msg) {
  if (WiFi.status() != WL_CONNECTED) return;
  if (!httpInicializado) { http.setTimeout(3000); httpInicializado = true; }
  String enc = urlEncode(msg);
  for (uint8_t i = 0; i < NUM_SERVIDORES; i++) {
    char url[320];
    snprintf(url, sizeof(url), "http://%s/terminal_log?line=%s", SERVIDORES[i], enc.c_str());
    http.begin(wifiClient, url);
    int code = http.GET();
    http.end();
    if (code == 200) break;   // entregou em um servidor; basta
  }
}

// Extrai o valor de "risk_level":"..." do corpo JSON da resposta do backend
String extrairRisco(const String& body) {
  int k = body.indexOf("risk_level");
  if (k < 0) return "?";
  int c = body.indexOf(':', k);
  int q1 = body.indexOf('"', c + 1);
  int q2 = body.indexOf('"', q1 + 1);
  if (q1 < 0 || q2 < 0) return "?";
  return body.substring(q1 + 1, q2);
}

// --------------------------- Leitura de sensores --------------------------- #
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

// ----------------------- Envio da telemetria ao backend -------------------- #
// Monta a query e faz GET /api/telemetry?... em cada servidor até um responder
// 200. Imprime o risco classificado e espelha um resumo no /terminal_log.
void enviarTelemetria(float hr, float spo2, float temp, float accel,
                      float resp, float radiation, float batt) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado — pulando envio HTTP");
    return;
  }
  if (!httpInicializado) { http.setTimeout(3000); httpInicializado = true; }

  String ts = obterTimestamp();
  bool ok = false;

  for (uint8_t i = 0; i < NUM_SERVIDORES && !ok; i++) {
    char url[420];
    snprintf(url, sizeof(url),
             "http://%s/api/telemetry?crew_id=%s&hr=%.1f&spo2=%.1f&temp=%.1f"
             "&accel=%.2f&resp=%.1f&radiation=%.2f&battery=%.1f&ts=%s",
             SERVIDORES[i], CREW_ID, hr, spo2, temp, accel, resp, radiation,
             batt, urlEncode(ts).c_str());

    Serial.printf("GET [%d/%d] %s\n", i + 1, NUM_SERVIDORES, SERVIDORES[i]);
    http.begin(wifiClient, url);
    int code = http.GET();

    if (code == 200) {
      String risco = extrairRisco(http.getString());
      Serial.printf("HTTP OK [%s] -> risk=%s\n", SERVIDORES[i], risco.c_str());
      enviarLogServidor(String("OK ") + SERVIDORES[i] + " risk=" + risco);
      ok = true;
    } else if (code > 0) {
      Serial.printf("HTTP %d [%s]\n", code, SERVIDORES[i]);
    } else {
      Serial.printf("HTTP erro [%s]: %s\n", SERVIDORES[i],
                    http.errorToString(code).c_str());
    }
    http.end();
    if (!ok && i < NUM_SERVIDORES - 1) delay(300);  // tenta o próximo
  }

  if (!ok) {
    Serial.println("Falha ao enviar p/ todos os servidores");
    enviarLogServidor("Falha ao enviar telemetria p/ todos os servidores");
  }
}

// Lê todos os sinais, imprime no Serial e envia ao backend. Uma chamada por ciclo.
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
  bootCount++;

  // Linha legível p/ o Serial Monitor do Wokwi (e espelhada no backend)
  char resumo[160];
  snprintf(resumo, sizeof(resumo),
           "%s HR=%.0f SpO2=%.1f Temp=%.1f Accel=%.2f Resp=%.0f Rad=%.2f Bat=%.1f",
           CREW_ID, hr, spo2, temp, accel, resp, radiation, battery);
  Serial.println(resumo);
  enviarLogServidor(resumo);

  enviarTelemetria(hr, spo2, temp, accel, resp, radiation, battery);
}

// ----------------------- Deep sleep -------------------------------- #
#if USE_DEEP_SLEEP
// Apaga periféricos, desliga o WiFi e entra em deep sleep por SLEEP_SECONDS. Ao
// despertar (timer do RTC) o ESP32 reinicia do zero em setup() — loop() nunca roda.
void enterDeepSleep() {
  Serial.printf("Deep sleep %d s (duty cycle, ciclo %u)\n", SLEEP_SECONDS, bootCount);
  enviarLogServidor(String("Deep sleep ") + SLEEP_SECONDS + "s (ciclo " + bootCount + ")");
  Serial.flush();
  digitalWrite(LED_PIN, LOW);             // desligar periféricos antes de dormir
  WiFi.disconnect(true);                  // desligar o rádio WiFi (maior consumo)
  WiFi.mode(WIFI_OFF);
  esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_SECONDS * 1000000ULL);
  esp_deep_sleep_start();                 // ~0.15-0.3 mA até o próximo despertar
}
#endif

// -------------------------------- Setup ------------------------------------ #
void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);             // LED apagado por padrão (economia)

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

  // Conecta ao WiFi do Wokwi
  Serial.printf("Conectando ao WiFi '%s'", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
  uint8_t tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 40) {  // ~20 s máx
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\nWiFi conectado! IP: ");
    Serial.println(WiFi.localIP());
    enviarLogServidor(String("WiFi conectado IP=") + WiFi.localIP().toString());

    // Sincroniza o relógio via NTP (timestamp ISO p/ o backend)
    configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
    struct tm timeinfo;
    uint8_t ntp = 0;
    while (!getLocalTime(&timeinfo) && ntp < 20) { delay(500); Serial.print("."); ntp++; }
    ntpSincronizado = getLocalTime(&timeinfo);
    Serial.println(ntpSincronizado ? "\nNTP sincronizado!" : "\nNTP falhou — usando millis()");
    enviarLogServidor(ntpSincronizado ? "NTP sincronizado" : "NTP falhou (millis)");
  } else {
    Serial.println("\nFalha na conexao WiFi — sem envio HTTP");
  }

#if USE_DEEP_SLEEP
  // Modo energia: setup() é o "loop". Faz UM ciclo (lê + envia) e dorme.
  sampleAndSend();
  enterDeepSleep();   // não retorna — reinicia em setup() ao despertar pelo timer
#endif
}

// -------------------------------- Loop ------------------------------------- #
void loop() {
  // No modo energia (USE_DEEP_SLEEP=1) o ESP32 dorme em setup() e nunca chega
  // aqui. Sem deep sleep (=0), amostra periodicamente, sempre ligado.
#if !USE_DEEP_SLEEP
  sampleAndSend();
  delay(SAMPLE_INTERVAL_MS);
#endif
}
