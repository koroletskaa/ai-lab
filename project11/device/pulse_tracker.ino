/*
 * Емоційний трекер - код для ESP32-C3
 * Зчитує пульс через Pulse Sensor, відображає на OLED та передає дані через Wi-Fi
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <ArduinoJson.h>

// ============= КОНФІГУРАЦІЯ =============
const char* ssid = "YOUR_WIFI_SSID";           // Назва Wi-Fi мережі
const char* password = "YOUR_WIFI_PASSWORD";   // Пароль Wi-Fi
const char* serverURL = "http://192.168.1.100:8000/api/pulse"; // URL бекенду

// Піни для Pulse Sensor та OLED
#define PULSE_SENSOR_PIN A0
#define OLED_SDA 21  // Для ESP32-C3 може бути інший
#define OLED_SCL 22  // Для ESP32-C3 може бути інший

// ============= OLED ДИСПЛЕЙ =============
// Для ESP32-C3 з OLED 0.42" (128x64) SSD1306
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// ============= ЗМІННІ ДЛЯ ПУЛЬСУ =============
int pulsePin = PULSE_SENSOR_PIN;
int pulseValue = 0;
int threshold = 512;  // Поріг для виявлення піку
int lastBeatTime = 0;
int beatInterval = 0;
int beatsPerMinute = 0;
int beatCount = 0;

// Масив для зберігання останніх значень для фільтрації
const int sampleSize = 10;
int samples[sampleSize];
int sampleIndex = 0;
long lastSampleTime = 0;

// Калібровка та стабілізація
bool isCalibrated = false;
int restingHeartRate = 0;
int calibrationSamples = 0;
const int calibrationSampleCount = 30; // 30 секунд для калібровки

unsigned long lastDataSend = 0;
const unsigned long dataSendInterval = 5000; // Надсилаємо дані кожні 5 секунд

// ============= НАЛАШТУВАННЯ =============
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Ініціалізація OLED
  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 10, "Initializing...");
  u8g2.sendBuffer();
  
  // Налаштування піна для пульсу
  pinMode(pulsePin, INPUT);
  
  // Підключення до Wi-Fi
  connectToWiFi();
  
  // Ініціалізація масиву зразків
  for (int i = 0; i < sampleSize; i++) {
    samples[i] = 512;
  }
  
  u8g2.clearBuffer();
  u8g2.drawStr(0, 10, "Calibrating...");
  u8g2.drawStr(0, 30, "Stay still 30s");
  u8g2.sendBuffer();
}

// ============= ОСНОВНИЙ ЦИКЛ =============
void loop() {
  // Зчитування аналогового значення з датчика
  pulseValue = analogRead(pulsePin);
  
  // Фільтрація шуму через згладжування
  samples[sampleIndex] = pulseValue;
  sampleIndex = (sampleIndex + 1) % sampleSize;
  
  // Обчислення середнього значення
  int average = 0;
  for (int i = 0; i < sampleSize; i++) {
    average += samples[i];
  }
  average /= sampleSize;
  
  // Виявлення піку (серцевого скорочення)
  int currentTime = millis();
  
  // Якщо значення перевищує поріг і минуло достатньо часу від останнього піку
  if (pulseValue > threshold && (currentTime - lastBeatTime) > 200) {
    beatInterval = currentTime - lastBeatTime;
    lastBeatTime = currentTime;
    beatCount++;
    
    // Обчислення BPM (ударів за хвилину)
    if (beatInterval > 0) {
      beatsPerMinute = 60000 / beatInterval;
      
      // Обмеження реального діапазону пульсу
      if (beatsPerMinute < 40) beatsPerMinute = 0;
      if (beatsPerMinute > 200) beatsPerMinute = 0;
    }
  }
  
  // Автоматична калібровка (визначення пульсу у спокої)
  if (!isCalibrated && calibrationSamples < calibrationSampleCount) {
    if (beatsPerMinute > 0) {
      restingHeartRate += beatsPerMinute;
      calibrationSamples++;
    }
    
    if (calibrationSamples >= calibrationSampleCount) {
      restingHeartRate /= calibrationSampleCount;
      isCalibrated = true;
      threshold = average + (average * 0.1); // Динамічний поріг
    }
  }
  
  // Динамічне оновлення порогу на основі середнього значення
  threshold = average + (average * 0.15);
  
  // Оновлення дисплею
  updateDisplay();
  
  // Відправка даних на сервер
  if (currentTime - lastDataSend > dataSendInterval && WiFi.status() == WL_CONNECTED) {
    sendPulseData(beatsPerMinute);
    lastDataSend = currentTime;
  }
  
  delay(10); // Невелика затримка для стабільності
}

// ============= ПІДКЛЮЧЕННЯ ДО WI-FI =============
void connectToWiFi() {
  u8g2.clearBuffer();
  u8g2.drawStr(0, 10, "Connecting WiFi");
  u8g2.sendBuffer();
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.print("Connected! IP: ");
    Serial.println(WiFi.localIP());
    
    u8g2.clearBuffer();
    u8g2.drawStr(0, 10, "WiFi Connected");
    u8g2.drawStr(0, 30, WiFi.localIP().toString().c_str());
    u8g2.sendBuffer();
    delay(2000);
  } else {
    Serial.println("WiFi connection failed!");
    u8g2.clearBuffer();
    u8g2.drawStr(0, 10, "WiFi Failed");
    u8g2.sendBuffer();
  }
}

// ============= ОНОВЛЕННЯ ДИСПЛЕЮ =============
void updateDisplay() {
  u8g2.clearBuffer();
  
  // Заголовок
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 10, "Heart Rate");
  
  // Пульс
  u8g2.setFont(u8g2_font_ncenB24_tr);
  char bpmStr[10];
  if (beatsPerMinute > 0) {
    sprintf(bpmStr, "%d", beatsPerMinute);
    u8g2.drawStr(20, 45, bpmStr);
  } else {
    u8g2.drawStr(20, 45, "--");
  }
  
  // Підпис
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(80, 45, "BPM");
  
  // Статус Wi-Fi
  if (WiFi.status() == WL_CONNECTED) {
    u8g2.drawStr(0, 60, "WiFi: ON");
  } else {
    u8g2.drawStr(0, 60, "WiFi: OFF");
  }
  
  // Статус калібровки
  if (isCalibrated) {
    u8g2.drawStr(70, 60, "OK");
  } else {
    u8g2.drawStr(70, 60, "CAL");
  }
  
  u8g2.sendBuffer();
}

// ============= ВІДПРАВКА ДАНИХ НА СЕРВЕР =============
void sendPulseData(int bpm) {
  if (bpm <= 0) return; // Не надсилаємо невалідні дані
  
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Створення JSON об'єкта
  StaticJsonDocument<200> doc;
  doc["bpm"] = bpm;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.print("Data sent. Response: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("Error sending data: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

