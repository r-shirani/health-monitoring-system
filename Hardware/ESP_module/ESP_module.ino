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

// OLED configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// MAX30102 sensor
MAX30105 particleSensor;

// Endpoint and header
const char* serverUrl = "http://192.168.1.100:8000/vitals/"; 
const char* userToken = "46e3c4ffa08e942f0e6853452aeb5c026ae56397";
const int deviceId = 22;

// Captive portal and WiFi configuration
const byte DNS_PORT = 53;
IPAddress apIP(192, 168, 4, 1);
DNSServer dnsServer;
WebServer server(80);
Preferences preferences;

String saved_ssid = "";
String saved_pass = "";

// Variables for Heart Rate and SpO2
byte rates[4];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute = 0;
int beatAvg = 0;
int spo2Val = 0;

long irValue = 0;
long redValue = 0;

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 2000;

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

void handleRoot() { server.send(200, "text/html", index_html); }

void handleSave() {
  if (server.hasArg("ssid") && server.hasArg("password")) {
    preferences.begin("wifi-config", false);
    preferences.putString("ssid", server.arg("ssid"));
    preferences.putString("password", server.arg("password"));
    preferences.end();

    String lang = server.hasArg("lang") ? server.arg("lang") : "fa";
    String msgTitle = (lang == "en") ? "Settings Saved!" : "اطلاعات ذخیره شد!";
    String msgBody = (lang == "en") ? "Rebooting device, please wait..." : "در حال راه‌اندازی مجدد دستگاه...";

    String html = "<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
                  "<style>body{font-family:Tahoma,sans-serif;text-align:center;background:#f4f4f9;padding:40px;}"
                  ".card{background:white;padding:25px;border-radius:12px;box-shadow:0 4px 10px rgba(0,0,0,0.1);max-width:360px;margin:auto;}</style></head><body>"
                  "<div class='card'><h3 style='color:#28a745;'>" + msgTitle + "</h3><p>" + msgBody + "</p></div></body></html>";

    server.send(200, "text/html", html);
    delay(2000);
    ESP.restart();
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

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

  // sensore configuration to activate thr red LED and IR to calculate SpO2
  particleSensor.setup(0x1F, 4, 2, 200, 411, 4096);

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
  if (WiFi.status() != WL_CONNECTED) {
    dnsServer.processNextRequest();
    server.handleClient();
  }

  // read Red and IR values
  irValue = particleSensor.getIR();
  redValue = particleSensor.getRed();

  // heart rate
  if (checkForBeat(irValue) == true) {
    long delta = millis() - lastBeat;
    lastBeat = millis();
    beatsPerMinute = 60 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= 4;
      beatAvg = 0;
      for (byte x = 0; x < 4; x++) beatAvg += rates[x];
      beatAvg /= 4;
    }
  }

  //calculate the SpO2 from the Red to IR ration
  if (irValue > 50000) {
    float rRatio = ((float)redValue / (float)irValue);
    // calculate SpO2
    int calculatedSpo2 = 110 - (25 * rRatio); 
    if (calculatedSpo2 > 100) calculatedSpo2 = 100;
    if (calculatedSpo2 < 80) calculatedSpo2 = 80;
    spo2Val = calculatedSpo2;
  } else {
    spo2Val = 0;
    beatAvg = 0;
  }

  // sidplay on the OLED
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
    display.setTextSize(1);
    display.println("Place Finger...");
  } else {
    display.setTextSize(1);
    display.print("BPM: ");
    display.println(beatAvg);
    display.setCursor(0, 40);
    display.print("SpO2: ");
    display.print(spo2Val);
    display.println("%");
  }
  display.display();

  // send real data of SpO2 and BPM to server
  if (WiFi.status() == WL_CONNECTED && (millis() - lastSendTime > sendInterval)) {
    lastSendTime = millis();
    if (beatAvg > 0 && spo2Val > 0) {
      sendDataToServer(beatAvg, spo2Val);
    }
  }
}

void sendDataToServer(int bpm, int spo2) {
  HTTPClient http;
  //server URL to send the data
  http.begin(serverUrl);
  //add HTTP requests headers
  http.addHeader("Content-Type", "application/json");
  
  String authHeader = "Token " + String(userToken);
  http.addHeader("Authorization", authHeader.c_str());

  //Json format
  String jsonPayload = "{";
  jsonPayload += "\"device\":" + String(deviceId) + ",";
  jsonPayload += "\"heart_rate\":" + String(bpm) + ",";
  jsonPayload += "\"oxygen_level\":" + String(spo2);
  jsonPayload += "}";

  //POST request to the server with the JSON payload + receive the response code the response from the server status code
  int httpResponseCode = http.POST(jsonPayload);

  //evaluate the response code and print the response or error message for debugging purposes
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
  
  //close the connection to free up the resources
  http.end();
}
