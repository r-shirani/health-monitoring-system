#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <DNSServer.h>
#include <WebServer.h>
#include <Preferences.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "MAX30105.h"
#include "heartRate.h"

// OLED Display Configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// MAX30102 Sensor Object
MAX30105 particleSensor;

// Local Network Server Endpoint Settings (Configured for mobile hotspot IP)
const char* serverUrl = "http://192.168.1.104:8000/vitals/";
const char* userToken = "46e3c4ffa08e942f0e6853452aeb5c026ae56397";
const int deviceId = 22;

// Captive Portal and WiFi Settings
const byte DNS_PORT = 53;
IPAddress apIP(192, 168, 4, 1);
DNSServer dnsServer;
WebServer server(80);
Preferences preferences;

String saved_ssid = "";
String saved_pass = "";

// Variables for Bio-Telemetry Processing (Corrected Array Size)
byte rates[4];              // Circular buffer to store the last 4 valid heart rate readings
byte rateSpot = 0;          // Index pointer for the circular rates array
byte rateCount = 0;         // Tracks actual filled samples to prevent low average starts
long lastBeat = 0;          // Timestamp (in ms) of the last detected heart beat
float beatsPerMinute = 0;   // Calculated raw BPM
int beatAvg = 0;            // Stable rolling average of the heart rate
int spo2Val = 0;            // Extracted blood oxygen saturation level (SpO2)

long irValue = 0;
long redValue = 0;

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 2000; // API telemetry send interval (2 seconds)
unsigned long lastDisplayTime = 0;

// Embedded HTML page for Captive Portal configuration
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta charset="UTF-8">
  <title>WiFi Setup</title>
  <style>
    body { font-family: Tahoma, sans-serif; text-align: center; background: #f4f4f9; padding: 20px; }
    .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 360px; margin: auto; position: relative; }
    .lang-btn { position: absolute; top: 15px; left: 15px; background: #007bff; color: white; border: none; padding: 5px 12px; border-radius: 20px; cursor: pointer; font-size: 12px; font-weight: bold; }
    input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
    button[type="submit"] { width: 90%; padding: 11px; background: #28a745; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 15px; }
  </style>
</head>
<body>
  <div class="card">
    <button class="lang-btn" onclick="toggleLanguage()" id="langBtn">EN</button>
    <h2 id="title">تنظیمات وای‌فای</h2>
    <p id="desc">لطفاً اطلاعات وای‌فای خود را وارد کنید:</p>
    <form action="/save" method="POST">
      <input type="hidden" name="lang" id="langInput" value="fa">
      <input type="text" name="ssid" id="ssidInput" placeholder="نام وای‌فای (SSID)" required><br>
      <input type="password" name="password" id="passInput" placeholder="رمز عبور" required><br>
      <button type="submit" id="submitBtn">ذخیره و اتصال</button>
    </form>
  </div>
  <script>
    const translations = {
      fa: { title: "تنظیمات وای‌فای", desc: "لطفاً اطلاعات وای‌فای خود را وارد کنید:", ssid: "نام وای‌فای (SSID)", pass: "رمز عبور", submit: "ذخیره و اتصال", btn: "EN", dir: "rtl" },
      en: { title: "Wi-Fi Configuration", desc: "Please enter your Wi-Fi credentials:", ssid: "Wi-Fi Name (SSID)", pass: "Password", submit: "Save & Connect", btn: "فارسی", dir: "ltr" }
    };
    let currentLang = localStorage.getItem("app_lang") || "fa";
    function updateLanguage() {
      const t = translations[currentLang];
      document.documentElement.dir = t.dir;
      document.getElementById("title").innerText = t.title;
      document.getElementById("desc").innerText = t.desc;
      document.getElementById("ssidInput").placeholder = t.ssid;
      document.getElementById("passInput").placeholder = t.pass;
      document.getElementById("submitBtn").innerText = t.submit;
      document.getElementById("langBtn").innerText = t.btn;
      document.getElementById("langInput").value = currentLang;
      localStorage.setItem("app_lang", currentLang);
    }
    function toggleLanguage() { currentLang = currentLang === "fa" ? "en" : "fa"; updateLanguage(); }
    updateLanguage();
  </script>
</body>
</html>
)rawliteral";

void handleRoot() { 
  server.send(200, "text/html", index_html); 
}

void handleSave() { 
  if (server.hasArg("ssid") && server.hasArg("password")) { 
    preferences.begin("wifi-config", false); 
    preferences.putString("ssid", server.arg("ssid")); 
    preferences.putString("password", server.arg("password")); 
    preferences.end();
    server.send(200, "text/html", "Configuration saved! Device is restarting...");
    delay(2000);
    ESP.restart();
  } 
}

// Sends telemetry payload to Django web backend using HTTP POST
void sendDataToServer(int bpm, int spo2) { 
  HTTPClient http; 
  http.begin(serverUrl); 
  http.addHeader("Content-Type", "application/json");
  
  String authHeader = "Token " + String(userToken); 
  http.addHeader("Authorization", authHeader.c_str());
  
  // Format clinical metrics as a structured JSON object
  String jsonPayload = "{"; 
  jsonPayload += "\"device\":" + String(deviceId) + ","; 
  jsonPayload += "\"heart_rate\":" + String(bpm) + ","; 
  jsonPayload += "\"oxygen_level\":" + String(spo2); 
  jsonPayload += "}";
  
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) { 
    Serial.print("HTTP Status: "); 
    Serial.print(httpResponseCode); 
    String response = http.getString(); 
    Serial.print(" | Response: "); 
    Serial.println(response); 
  } else { 
    Serial.print("HTTP Error: "); 
    Serial.println(http.errorToString(httpResponseCode).c_str()); 
  }
  http.end(); 
}

void setup() { 
  Serial.begin(115200); 
  Wire.begin(21, 22); // Initialize I2C Communication pins (SDA=21, SCL=22)
  
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("OLED failed")); 
  } 
  display.clearDisplay(); 
  display.setTextColor(SSD1306_WHITE); 
  display.setTextSize(1); 
  display.setCursor(0, 0); 
  display.println("Initializing..."); 
  display.display();
  
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) { 
    display.clearDisplay(); 
    display.setCursor(0, 0); 
    display.println("MAX30102 Not Found!"); 
    display.display(); 
    while (1); 
  }
  
  // Sensor configuration: Active Red LED + IR LED to compute SpO2 and Heart Rate
  particleSensor.setup(0x1F, 4, 2, 200, 411, 4096);
  
  // Load saved Wi-Fi credentials from Non-Volatile Storage (NVS)
  preferences.begin("wifi-config", true); 
  saved_ssid = preferences.getString("ssid", ""); 
  saved_pass = preferences.getString("password", ""); 
  preferences.end();
  
  if (saved_ssid != "") { 
    WiFi.mode(WIFI_STA); 
    WiFi.begin(saved_ssid.c_str(), saved_pass.c_str()); 
    int attempts = 0; 
    while (WiFi.status() != WL_CONNECTED && attempts < 10) { 
      delay(500); 
      attempts++; 
    } 
  }
  
  // Print ESP32 local IP to Serial Monitor for testing and ping diagnostics
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.print("Connected successfully! ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
  }
  
  // Fallback to Captive Portal mode if connection to router fails
  if (WiFi.status() != WL_CONNECTED) { 
    WiFi.mode(WIFI_AP); 
    WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0)); 
    WiFi.softAP("Health monitoring system"); 
    dnsServer.start(DNS_PORT, "*", apIP); 
    server.on("/", handleRoot); 
    server.on("/save", handleSave); 
    server.onNotFound(handleRoot); 
    server.begin(); 
  } 
}

void loop() { 
  // Process captive portal web requests if Wi-Fi is not connected to router
  if (WiFi.status() != WL_CONNECTED) { 
    dnsServer.processNextRequest(); 
    server.handleClient(); 
  }
  
  // Read raw optical signals from MAX30102 sensor
  irValue = particleSensor.getIR(); 
  redValue = particleSensor.getRed();
  
  // Check if a finger is securely placed on the sensor
  if (irValue < 50000) { 
    // Finger removed: reset calculations and clear buffer to prevent noisy telemetry
    spo2Val = 0; 
    beatAvg = 0; 
    rateSpot = 0; 
    rateCount = 0; 
    for (byte i = 0; i < 4; i++) rates[i] = 0; 
  } else { 
    // Finger is present: track cardiac contractions and calculate pulse wave
    if (checkForBeat(irValue) == true) { 
      long delta = millis() - lastBeat; 
      lastBeat = millis(); 
      
      // Prevent wild calculations on the very first cold-start beat
      if (delta > 250 && delta < 3000) {
        beatsPerMinute = 60 / (delta / 1000.0);
        
        // Accept only realistic physiological human heart rates (40 to 220 BPM)
        if (beatsPerMinute < 220 && beatsPerMinute > 40) { 
          rates[rateSpot++] = (byte)beatsPerMinute; 
          rateSpot %= 4; // Keep index pointer within 0-3 range
          
          // Increment actual populated sample size count up to array limit (4)
          if (rateCount < 4) rateCount++;
          
          // Compute the rolling average of the verified heart rate readings
          int sum = 0;
          for (byte x = 0; x < rateCount; x++) {
            sum += rates[x];
          }
          beatAvg = sum / rateCount;
        } 
      }
    }
    
    // Calculate blood oxygen levels using the Red/IR light absorption ratio
    float rRatio = ((float)redValue / (float)irValue); 
    int calculatedSpo2 = 110 - (25 * rRatio); 
    
    // Constrain SpO2 readings to medically realistic ranges (80% - 100%)
    if (calculatedSpo2 > 100) calculatedSpo2 = 100; 
    if (calculatedSpo2 < 80) calculatedSpo2 = 80; 
    spo2Val = calculatedSpo2; 
  }
  
  // Refresh the local OLED display every 200ms to avoid system lagging
  if (millis() - lastDisplayTime > 200) { 
    lastDisplayTime = millis();
    display.clearDisplay(); 
    display.setCursor(0, 0); 
    display.setTextSize(1); 
    
    if (WiFi.status() == WL_CONNECTED) { 
      display.print("WiFi: Connected"); 
    } else { 
      display.print("WiFi: Setup Mode"); 
    }
    
    display.setCursor(0, 20); 
    if (irValue < 50000) { 
      display.println("Place Finger..."); 
    } else { 
      display.print("BPM: "); 
      display.println(beatAvg); 
      display.setCursor(0, 40); 
      display.print("SpO2: "); 
      display.print(spo2Val); 
      display.println("%"); 
    } 
    display.display(); 
  }
  
  // Telemetry Transmission: Send data to local Django webserver via HTTP POST
  if (WiFi.status() == WL_CONNECTED && (millis() - lastSendTime > sendInterval)) { 
    lastSendTime = millis(); 
    // Transmit data only when valid physiological metrics are stabilized
    if (beatAvg > 40 && spo2Val > 80) { 
      sendDataToServer(beatAvg, spo2Val); 
    } 
  } 
}
