# IoT Monitoring System 🌡️📊

A real-time IoT sensor monitoring and analytics dashboard built with Django. This system collects, stores, and visualizes environmental sensor data from LoRaWAN devices connected via The Things Network (TTN).

## 🎯 Project Overview

The IoT Monitoring System provides a comprehensive web-based platform for monitoring environmental sensors in real-time. It ingests data from LoRa-enabled sensors (temperature, humidity, motion, battery) via MQTT and presents the information through an intuitive dashboard with historical analytics and data export capabilities.

### Key Capabilities:
- **Real-time Data Collection**: Automatic sensor data ingestion via MQTT from TTN
- **Live Dashboard**: Monitor current sensor readings and device status
- **Analytics & Insights**: Historical data analysis with interactive charts
- **Device Management**: Track multiple IoT devices and their health status
- **Data Export**: Export sensor readings in CSV and JSON formats
- **RESTful API**: Programmatic access to sensor data

## ✨ Features

### 📊 Real-time Dashboard
- Live sensor metrics (Temperature, Humidity, Battery, Motion)
- Device status overview (online/offline tracking)
- 24-hour trend charts
- Recent readings table with auto-refresh

### 📈 Analytics & Insights
- Temperature and humidity statistics (avg, min, max)
- Daily reading counts and trends
- Temperature distribution analysis
- Battery level monitoring
- Motion detection analytics
- Hourly data aggregation

### 🔧 Device Management
- Multi-device support
- Device health monitoring (last seen, online status)
- Per-device statistics and readings
- Device detail views with historical data

### 💾 Data Export & History
- Filter readings by device and date range
- Export to CSV or JSON formats
- Paginated historical data view
- Statistical summaries

### 🔌 Data Ingestion
- **MQTT Listener**: Real-time data collection from TTN
- **REST API**: Manual data ingestion endpoint
- **TTN Poller**: Fallback polling service
- Automatic data deduplication

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 5.2.6 (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **MQTT Client**: Paho MQTT
- **Frontend**: Bootstrap 5, Chart.js, Font Awesome
- **Deployment**: Railway, Render (WSGI: Gunicorn)
- **IoT Platform**: The Things Network (TTN)

### System Components

```
┌─────────────────┐
│  LoRa Sensors   │ (Temperature, Humidity, Motion)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  The Things     │ (LoRaWAN Network Server)
│  Network (TTN)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MQTT Broker    │ (eu1.cloud.thethings.network)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      IoT Monitoring System          │
│  ┌──────────────┐  ┌──────────────┐ │
│  │ MQTT Worker  │  │  Web Service │ │
│  │ (Listener)   │  │  (Dashboard) │ │
│  └──────┬───────┘  └───────▲──────┘ │
│         │                  │        │
│         ▼                  │        │
│  ┌─────────────────────────┴─────┐  │
│  │    PostgreSQL Database        │  │
│  │  (SensorReading Model)        │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Web Browser   │ (Dashboard UI)
└─────────────────┘
```

### Data Flow
1. **Sensors** → Transmit data via LoRa
2. **TTN** → Receives and decodes LoRa packets
3. **MQTT Broker** → Publishes sensor data to topic
4. **MQTT Worker** → Subscribes to topic and receives messages
5. **Ingest API** → Processes and stores data in database
6. **Web Dashboard** → Queries database and displays visualizations

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip
- Git

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/Arokrokie/Iot_Monitoring_System.git
cd Iot_Monitoring_System
```

2. **Create virtual environment and install dependencies**
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate
.\.venv\Scripts\pip install -r requirements.txt

# Linux/Mac
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Apply database migrations**
```bash
python manage.py migrate
```

4. **Create admin user**
```bash
python manage.py createsuperuser --username admin --email admin@example.com
```

5. **Run the development server**
```bash
python manage.py runserver 0.0.0.0:8000
```

6. **Access the application**
- Dashboard: `http://127.0.0.1:8000/`
- Admin Panel: `http://127.0.0.1:8000/admin/`

### Running the MQTT Listener

In a separate terminal (keep Django server running):

```bash
# Set environment variables
export IOT_INGEST_URL=http://localhost:8000/api/ingest/
export TTN_USERNAME=your-ttn-username@ttn
export TTN_PASSWORD=your-ttn-api-key
export TTN_DEVICE_ID=your-device-id
export TTN_PORT=1883

# Run MQTT worker
python manage.py run_mqtt
```

### Verify Data Collection

```bash
python check_data.py
```

## 🌐 Deployment (Railway)

### Step 1: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Connect your repository

### Step 2: Configure Web Service

Set these environment variables in Railway:

| Variable | Value |
|----------|-------|
| `DJANGO_SECRET_KEY` | Your Django secret key |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `*.up.railway.app,localhost,127.0.0.1` |
| `DATABASE_URL` | Auto-provided by Railway |

### Step 3: Create Worker Service

1. Click "New Service" → "Empty Service"
2. Connect to same GitHub repository
3. Settings → Service Type → Select "Worker"
4. Add environment variables:

| Variable | Value |
|----------|-------|
| `IOT_INGEST_URL` | `https://your-app.up.railway.app/api/ingest/` |
| `TTN_BROKER` | `eu1.cloud.thethings.network` |
| `TTN_PORT` | `1883` |
| `TTN_USERNAME` | Your TTN app username |
| `TTN_PASSWORD` | Your TTN API key |
| `TTN_DEVICE_ID` | Your device ID |

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed deployment instructions.

## 📡 API Documentation

### Data Ingestion Endpoint

**POST** `/api/ingest/`

Accepts sensor readings in JSON format.

**Request Body:**
```json
{
  "device_id": "lht65n-01-temp-humidity-sensor",
  "received_at": "2026-01-19T10:30:00Z",
  "battery_voltage": 3.6,
  "humidity": 65.5,
  "motion_counts": 5,
  "temperature_c": 22.3
}
```

**Response:**
```json
{
  "status": "success",
  "id": 123
}
```

### Get Reading Details

**GET** `/api/reading/<id>/`

Returns detailed information about a specific sensor reading.

### Fetch TTN Data

**POST** `/api/fetch-data/`

Manually trigger data fetch from TTN API.

## 📊 Data Model

### SensorReading Model

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | CharField(128) | Unique device identifier |
| `battery_voltage` | FloatField | Battery voltage (V) |
| `humidity` | FloatField | Relative humidity (%) |
| `motion_counts` | IntegerField | Motion detection count |
| `temperature_c` | FloatField | Temperature (°C) |
| `received_at` | DateTimeField | Timestamp from sensor |
| `created_at` | DateTimeField | Database insertion time |

### TTN Field Mapping

| TTN Field | Database Field | Description |
|-----------|----------------|-------------|
| `field1` | `battery_voltage` | Battery voltage |
| `field3` | `humidity` | Humidity percentage |
| `field4` | `motion_counts` | Motion detection count |
| `field5` | `temperature_c` | Temperature in Celsius |

## 🛠️ Management Commands

### Run MQTT Listener
```bash
python manage.py run_mqtt
```

### Fetch Sensor Data from TTN
```bash
python manage.py fetch_sensor_data
```

### Check Database Data
```bash
python check_data.py
```

## 📁 Project Structure

```
Iot_Monitoring_System/
├── iot_dashboard/          # Django project settings
│   ├── settings.py         # Configuration
│   ├── urls.py             # URL routing
│   ├── wsgi.py             # WSGI entry point
│   ├── apps.py             # App configuration
│   └── mqtt_service.py     # MQTT client implementation
├── sensors/                # Main application
│   ├── models.py           # SensorReading model
│   ├── views.py            # Dashboard views
│   ├── urls.py             # URL patterns
│   ├── admin.py            # Django admin config
│   ├── ttn_poller.py       # TTN API poller
│   ├── templates/          # HTML templates
│   │   └── sensors/
│   │       ├── dashboard.html
│   │       ├── analytics.html
│   │       ├── devices.html
│   │       ├── history.html
│   │       └── base.html
│   └── management/
│       └── commands/
│           └── run_mqtt.py # MQTT worker command
├── data_collector_service.py  # Standalone data collector
├── check_data.py           # Database verification script
├── Procfile                # Railway/Heroku deployment config
├── requirements.txt        # Python dependencies
├── RAILWAY_DEPLOYMENT.md   # Deployment guide
└── README.md               # This file
```

## 🔧 Troubleshooting

### MQTT Worker Not Connecting
- Verify TTN credentials are correct
- Check `TTN_USERNAME` format: `app-name@ttn`
- Ensure `TTN_PASSWORD` is a valid API key
- Check Railway worker logs for errors

### No Data in Dashboard
- Verify `IOT_INGEST_URL` points to correct web service
- Test API endpoint: `curl https://your-app.up.railway.app/api/ingest/`
- Run `python check_data.py` to verify database
- Check MQTT worker is running and connected

### Database Issues
- Ensure migrations are applied: `python manage.py migrate`
- Check database permissions in Railway
- Verify `DATABASE_URL` environment variable

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available for educational and commercial use.

## 👤 Author

**Arokrokie**
- GitHub: [@Arokrokie](https://github.com/Arokrokie)

## 🙏 Acknowledgments

- The Things Network for LoRaWAN infrastructure
- Django community for the excellent web framework
- Bootstrap and Chart.js for UI components

---

**Built with ❤️ for IoT monitoring and analytics**