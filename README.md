# IoT-Based Remote Health Monitoring System
An IoT-based health monitoring system using ESP32 and Django for real-time tracking of vital signs (Heart Rate, SpO2) with AI analysis.

**Bachelor's Thesis Project**  
**Department of Computer Engineering, University of Isfahan**  
**Researcher:** Reihaneh Shirani Bidabadi  
**Supervisor:** Dr. Ahmadreza Montazerolghaem  
**Date:** September 2026 (Shahrivar 1405)

---

## 📌 Project Overview
The **IoT-Based Remote Health Monitoring System** is an end-to-end medical IoT (IoMT) solution designed to continuously acquire, store, analyze, and report critical patient vital signs. The system seamlessly integrates low-cost, portable hardware nodes with a highly scalable, asynchronous web backend. 

By combining photoplethysmography (PPG) optical sensing, local screen rendering, automated wireless captive network onboarding, relational data persistence, background clinical alerts, automated PDF reporting, and state-of-the-art LLM clinical assistance, this project provides a reliable platform for home healthcare, clinical monitoring, and athletic training.

---

## 🏗️ System Architecture & Data Flow
The platform is designed around a distributed, non-blocking, client-server architecture to ensure high availability and data integrity:

```
  ┌────────────────┐         I2C         ┌────────────────────────┐
  │ MAX30102 Sensor│ ──────────────────> │ ESP32 Microcontroller  │
  └────────────────┘                     └────────────────────────┘
                                            │                │
                                            │ Local OLED     │ Captive Portal
                                            ▼                ▼
                                      ┌───────────┐    ┌───────────┐
                                      │  SSD1306  │    │  NVS/Web  │
                                      └───────────┘    └───────────┘
                                            │
                                            │ HTTP POST (JSON + Token Auth)
                                            ▼
                                ┌──────────────────────┐
                                │ Django REST Platform │
                                └──────────────────────┘
                                    │      │        │
                     PostgreSQL     │      │        │ Redis Broker
           ┌────────────────────────┘      │        └──────────────────────┐
           ▼                               ▼                               ▼
  ┌────────────────┐             ┌──────────────────┐             ┌────────────────┐
  │  Health DB     │             │ Gemini 1.5 Flash │             │ Celery Workers │
  │  (Telemetry)   │             │   (AI Analysis)  │             │ (Async Alerts) │
  └────────────────┘             └──────────────────┘             └────────────────┘
                                                                           │
                                                                           │ SMTP
                                                                           ▼
                                                                  ┌────────────────┐
                                                                  │   Email Host   │
                                                                  │ (Doctor Alert) │
                                                                  └────────────────┘
```

1. **Acquisition & Processing (Hardware Layer):** The MAX30102 sensor measures light absorption in red and infrared wavelengths. The ESP32 processes the raw PPG signals using a bandpass filter, identifies systolic peaks, and calculates Heart Rate (BPM) and Blood Oxygen Saturation ($SpO_2$).
2. **Local Visualization & Fault Tolerance:** Readings are shown live on an OLED display. If connection is lost, the ESP32 switches to an offline Software Access Point and launches a local DNS/web Captive Portal to let the user set local Wi-Fi credentials dynamically, saving them into the Non-Volatile Storage (NVS).
3. **Secure API Ingestion:** Valid vital signs are packaged as a JSON payload and pushed to the Django backend every 2 seconds via `HTTP POST` authenticated with a secure, hardware-specific token (`Token Authentication`).
4. **Asynchronous Monitoring & Alerting:** When the Django REST Framework (DRF) serializes and saves new telemetry data, it evaluates thresholds. If values fall into a critical zone ($HR > 120\text{ BPM}$, $HR < 50\text{ BPM}$, or $SpO_2 < 92\%$), the backend immediately offloads an emergency alert task to Celery via Redis. The web-server responds to the hardware instantly (non-blocking), while background workers execute secure SMTP email delivery to designated contacts.
5. **Interactive UI, PDF Reporting, and AI Insight:** Medical staff monitor live trends on an interactive dashboard styled with Chart.js. They can generate publication-grade PDF medical logs (built dynamically with ReportLab) or invoke the Gemini 1.5 Flash AI clinical assistant to receive structural diagnostic assessments of patient records.

---

## 📁 Repository Structure
```
├── Backend/                                                # Django Web Backend & Core Framework
│   ├── core/                                               # Main Project Configurations
│   │   ├── celery.py                                       # Celery Instance Setup
│   │   └── settings.py                                     # Global Environment & DB Configurations
│   ├── monitoring/                                         # Telemetry Core Application
│   │   ├── admin.py                                        # Custom Django Admin Interfaces
│   │   ├── ai_service.py                                   # Google Gemini AI Integration Core
│   │   ├── email.py                                        # Emergency Email Services
│   │   ├── models.py                                       # PostgreSQL DB Tables (ORM)
│   │   ├── reports.py                                      # ReportLab Dynamic PDF Generation Engine
│   │   ├── serializers.py                                  # DRF Serialization Interfaces
│   │   ├── tasks.py                                        # Celery Asynchronous Shared Tasks
│   │   ├── templates/                                      # Dashboard and Account HTML Templates
│   │   └── views.py                                        # API & Web Interface Controllers
│   ├── Dockerfile                                          # Web Application Dockerization Blueprint
│   ├── requirements.txt                                    # Python Package Dependency Sheet
│   └── simulate_sensor.py                                  # Mock Biomedical Signal Simulator
├── Hardware/
|   ├── Adafruit_BusIO-master.zip                           # ESP32 libraries
│   ├── Adafruit_SSD1306-master.zip                         # ESP32 libraries
|   ├── Adafruit-GFX-Library-master.zip                     # ESP32 libraries
|   ├── SparkFun_MAX3010x_Sensor_Library-master.zip         # ESP32 libraries
│   └── ESP_module.ino                                      # Production C++ Firmware for ESP32
├── docker-compose.yml                                      # Multicontainer Microservices Configuration
└── README.md                                               # Technical Documentation Sheet
```

---

## 🔌 Hardware Configurations & Pin Mapping
The ESP32 microcontroller interfaces with both the PPG sensor and the local OLED display using the shared **Inter-Integrated Circuit ($I^2C$)** bus:

| Peripheral | Pin Name | Connected ESP32 GPIO | Description |
| :--- | :--- | :--- | :--- |
| **SSD1306 OLED** | GND | GND | Shared System Ground |
| | VCC | 3.3V | Stabilized Power Rail |
| | SDA | GPIO 21 | $I^2C$ Data Line |
| | SCL | GPIO 22 | $I^2C$ Clock Line |
| **MAX30102 PPG** | GND | GND | Shared System Ground |
| | VIN | 3.3V | Stabilized Power Rail |
| | SDA | GPIO 21 | Shared $I^2C$ Data Line |
| | SCL | GPIO 22 | Shared $I^2C$ Clock Line |
| **Pull-Up Resistors** | $2 \times 4.7\text{ k}\Omega$ | SDA/SCL to 3.3V | Pull-up logic level stabilizer |
| **Bypass Capacitor** | $100\text{ nF}$ | VIN to GND | Decouples high-frequency power noise |

---

## 🚀 Local Setup & Dockerization

### 1. Prerequisites
Ensure you have the following installed on your machine:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
* [Arduino IDE](https://www.arduino.cc/en/software) (for hardware uploading)

### 2. Backend Environment Setup
Create a `.env` file in the `Backend/` directory (adjacent to `manage.py` and `core/`):

```env
# Security Settings
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=health_db
DB_USER=health_user
DB_PASSWORD=health_password
DB_HOST=db
DB_PORT=5432

# Redis Broker Configuration
REDIS_URL=redis://redis:6379/0

# Emergency Alert Email (SMTP)
EMAIL_HOST_USER=your_gmail_address@gmail.com
EMAIL_HOST_PASSWORD=your_app_specific_password

# Gemini AI Integration
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Running with Docker Compose
To build and launch all containers (PostgreSQL database, Redis broker, Django web server, and Celery background worker) in one command:

```bash
docker compose up --build
```

Once execution completes:
* Run database migrations inside the web container:
  ```bash
  docker compose exec web python manage.py migrate
  ```
* Create an administrative account:
  ```bash
  docker compose exec web python manage.py createsuperuser
  ```
* Access the main web dashboard at: `http://localhost:8000/dashboard/`
* Access the Django Admin interface at: `http://localhost:8000/admin/`

### 4. Running the Biomedical Sensor Simulator
If you do not have physical hardware, you can test the system's real-time charting, email alerts, and AI processing using the built-in telemetry stream simulator:

```bash
# Run locally (requires pip install requests)
python Backend/simulate_sensor.py
```

### 5. Hardware Firmware Deployment
1. Open `Hardware/ESP_module.ino` in the **Arduino IDE**.
2. Install necessary libraries via the Library Manager:
   * `Adafruit SSD1306` & `Adafruit GFX` (OLED rendering)
   * `MAX30105` by SparkFun (Sensor communication)
3. Set your server target endpoint (e.g., `http://<your-server-ip>:8000/vitals/`) and paste the secure authentication token generated inside Django Admin for the respective hardware client.
4. Connect your ESP32 to your PC, choose your board port, and click **Upload**.

---

## ⚙️ RESTful API Specifications
The platform exposes several standard REST endpoints protected with token-based headers for hardware devices:

| Endpoint | HTTP Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `/admin/` | GET | Session (Staff) | Django Admin portal |
| `/vitals/` | GET / POST | Token / Session | Retrieve or upload vital sign measurements |
| `/devices/` | GET / POST | Token / Session | Retrieve or provision physical devices |
| `/dashboard/` | GET | Session | Live patient charts & interactive dashboard |
| `/dashboard/report/` | GET | Session | Dynamically exports PDF medical logs |
| `/api/analyze-ai-range/` | GET | Session | Triggers Gemini AI range diagnostic review |
| `/api/analyze-ai-session/` | GET | Session | Triggers Gemini AI last session analysis |

---

## 🔒 Safety, Security & Optimization
* **Emergency Rate Limiting:** Emergency alerts include an integrated cooldown threshold. A maximum of one email is dispatched every 5 minutes per device to prevent SMTP server flooding, ensuring vital diagnostic delivery without triggering spam filters.
* **Token Tokenization:** ESP32 devices utilize a static cryptographic Token (`Authorization: Token <key>`) sent inside the HTTP header. This secures the transmission channel and prevents unauthorized spoofing of biometric records.
* **Token Sampling Optimization:** To avoid hitting Google Gemini API token length limits, the backend automatically performs mathematical sampling of telemetry points if the record length exceeds 200 data points, preserving trend fidelity while operating within API efficiency rules.
