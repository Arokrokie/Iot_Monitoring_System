# 🌡️ IoT Sensor Monitoring System

A comprehensive real-time IoT sensor monitoring dashboard built with Django, designed to collect, visualize, and analyze data from LoRaWAN sensors via The Things Network (TTN). The system features a modern, responsive web interface with real-time charts, analytics, and data export capabilities.

## 🚀 Features

### 📊 Real-time Dashboard
- **Live Metrics Display**: Real-time visualization of temperature, humidity, battery voltage, and motion detection
- **Interactive Charts**: Dynamic Chart.js visualizations showing 24-hour trends
- **Device Status Overview**: Monitor all connected devices at a glance
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5

### 📈 Analytics & Insights
- **Statistical Analysis**: Average, min, max calculations for all sensor metrics
- **Historical Trends**: Analyze data patterns over custom date ranges
- **Daily Activity Charts**: Visualize reading frequency and device activity
- **Temperature Distribution**: Histogram showing temperature patterns
- **Combined Time Series**: Overlay temperature and humidity trends

### 🔧 Device Management
- **Multi-device Support**: Monitor multiple LoRaWAN sensors simultaneously
- **Device Health Monitoring**: Track battery levels and connectivity status
- **Individual Device Views**: Detailed pages for each sensor with complete history
- **Device Statistics**: Total readings, averages, and latest updates per device

### 📁 Data Export & History
- **Export Formats**: Download data in CSV or JSON format
- **Advanced Filtering**: Filter by device, date range, and custom queries
- **Quick Statistics**: View summary stats for filtered data
- **Pagination**: Efficiently browse through thousands of readings

### 🔌 Data Ingestion
- **MQTT Integration**: Real-time data collection from TTN MQTT broker
- **REST API Endpoint**: `/api/ingest/` for programmatic data submission
- **TTN Poller**: Fetch historical data from The Things Network API
- **Automatic Reconnection**: Resilient MQTT connection with auto-retry

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 5.2.6 with Python 3.x
- **Database**: PostgreSQL (production) / SQLite (development)
- **Frontend**: Bootstrap 5, Chart.js, Font Awesome
- **MQTT Client**: Paho-MQTT
- **Deployment**: Railway.app with dual-service architecture

### System Components

1. **Web Service** (`web`)
   - Serves the Django application
   - Provides REST API endpoints
   - Renders dashboard, analytics, and device views
   - Handles data queries and exports

2. **Worker Service** (`worker`)
   - Runs MQTT listener for real-time data ingestion
   - Connects to TTN MQTT broker
   - Processes uplink messages and posts to web API
   - Maintains persistent connection with auto-reconnect

3. **Database**
   - Stores sensor readings with timestamps
   - Indexed fields for efficient queries
   - Supports multiple device IDs

### Data Flow
```
LoRaWAN Sensor → TTN Network Server → MQTT Broker
                                           ↓
                                    MQTT Worker Service
                                           ↓
                                   POST /api/ingest/
                                           ↓
                                    Django Web Service
                                           ↓
                                    PostgreSQL Database
                                           ↓
                                    Dashboard Visualization
```

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip and virtualenv
- The Things Network account with configured LoRaWAN device(s)
- TTN API credentials

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/Arokrokie/Iot_Monitoring_System.git
cd Iot_Monitoring_System
```

2. **Create and activate virtual environment**
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Apply database migrations**
```bash
python manage.py migrate
```

5. **Create superuser (optional)**
```bash
python manage.py createsuperuser --username admin --email admin@example.com
```

6. **Run the development server**
```bash
python manage.py runserver 0.0.0.0:8000
```

7. **Access the application**
- Dashboard: `http://127.0.0.1:8000/`
- Admin Panel: `http://127.0.0.1:8000/admin/`

### Running MQTT Listener Locally

**Terminal 1 - Django Server:**
```bash
python manage.py runserver
```

**Terminal 2 - MQTT Worker:**
```bash
# Set environment variables
export IOT_INGEST_URL=http://localhost:8000/api/ingest/
export TTN_BROKER=eu1.cloud.thethings.network
export TTN_PORT=1883
export TTN_USERNAME=your-ttn-app@ttn
export TTN_PASSWORD=your-ttn-api-key
export TTN_DEVICE_ID=your-device-id

# Run MQTT worker
python manage.py run_mqtt
```

**Terminal 3 - Verify Data (optional):**
```bash
python check_data.py
```

## 🚂 Railway Deployment

This project is configured for deployment on Railway.app with separate web and worker services.

### Quick Deployment Steps

1. **Create Railway Project**
   - Connect your GitHub repository
   - Railway will auto-detect Django app

2. **Configure Web Service**
   - Service type: Web
   - Build command: Auto-detected
   - Start command: Defined in `Procfile`

3. **Create Worker Service**
   - Service type: Worker
   - Same repository
   - Runs `python manage.py run_mqtt`

4. **Set Environment Variables**

Required variables for both services:
```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=*.up.railway.app,localhost,127.0.0.1
```

Additional variables for worker service:
```
IOT_INGEST_URL=https://your-app.up.railway.app/api/ingest/
TTN_BROKER=eu1.cloud.thethings.network
TTN_PORT=1883
TTN_USERNAME=your-ttn-app@ttn
TTN_PASSWORD=your-ttn-api-key
TTN_DEVICE_ID=your-device-id
TTN_APP_ID=your-ttn-app-id
TTN_API_KEY=your-ttn-api-key
```

5. **Deploy**
   - Both services will deploy automatically
   - Monitor logs for successful connections

For detailed deployment instructions, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md).

## 📚 API Endpoints

### POST /api/ingest/
Ingest sensor reading from MQTT or external sources.

**Request Body:**
```json
{
  "device_id": "lht65n-01-temp-humidity-sensor",
  "temperature_c": 23.5,
  "humidity": 65.2,
  "battery_voltage": 3.6,
  "motion_counts": 12,
  "received_at": "2026-01-19T10:30:00Z"
}
```

**Response:** `201 Created`

### GET /api/reading/{reading_id}/
Retrieve detailed information for a specific sensor reading.

**Response:**
```json
{
  "id": 123,
  "device_id": "lht65n-01-temp-humidity-sensor",
  "temperature_c": 23.5,
  "humidity": 65.2,
  "battery_voltage": 3.6,
  "motion_counts": 12,
  "received_at": "2026-01-19T10:30:00Z",
  "created_at": "2026-01-19T10:30:05Z"
}
```

### POST /api/fetch-data/
Manually trigger TTN historical data fetch.

## 📊 Data Model

### SensorReading
| Field | Type | Description |
|-------|------|-------------|
| `device_id` | CharField(128) | Unique device identifier (indexed) |
| `temperature_c` | FloatField | Temperature in Celsius |
| `humidity` | FloatField | Relative humidity percentage |
| `battery_voltage` | FloatField | Battery voltage in volts |
| `motion_counts` | IntegerField | Motion detection count |
| `received_at` | DateTimeField | Timestamp from sensor (indexed) |
| `created_at` | DateTimeField | Database insert timestamp |

### TTN Field Mapping
| TTN Field | Database Field | Description |
|-----------|----------------|-------------|
| `field1` | `battery_voltage` | Battery voltage |
| `field3` | `humidity` | Humidity percentage |
| `field4` | `motion_counts` | Motion detection count |
| `field5` | `temperature_c` | Temperature in Celsius |

## 🔍 Monitoring & Troubleshooting

### Check Data Ingestion
```bash
python check_data.py
```

### View MQTT Logs
```bash
# Railway: Check worker service logs
# Local: Check terminal running run_mqtt command
```

### Common Issues

**No data appearing:**
- Verify TTN credentials are correct
- Check `IOT_INGEST_URL` points to correct web service
- Ensure MQTT worker is running
- Verify device is transmitting

**MQTT connection failures:**
- Check TTN broker address and port
- Verify username/password format
- Ensure network allows MQTT connections
- Check Railway worker logs

**Database issues:**
- Run migrations: `python manage.py migrate`
- Check database permissions
- Verify DATABASE_URL if using external DB

## 🛠️ Development

### Project Structure
```
Iot_Monitoring_System/
├── iot_dashboard/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── mqtt_service.py     # MQTT listener logic
│   └── apps.py
├── sensors/                # Main app
│   ├── models.py           # SensorReading model
│   ├── views.py            # Dashboard, analytics, API views
│   ├── urls.py
│   ├── admin.py
│   ├── templates/          # HTML templates
│   ├── management/
│   │   └── commands/
│   │       └── run_mqtt.py # MQTT worker command
│   └── ttn_poller.py       # TTN API integration
├── data_collector_service.py # Standalone data collector
├── check_data.py           # Database verification script
├── requirements.txt
├── Procfile               # Railway deployment config
└── README.md
```

### Available Management Commands

```bash
# Run MQTT listener
python manage.py run_mqtt

# Fetch historical data from TTN
python manage.py fetch_sensor_data

# Standard Django commands
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

## 📝 License

This project is open source and available for educational and commercial use.

## 👤 Author

**Arokrokie**
- GitHub: [@Arokrokie](https://github.com/Arokrokie)
- Project: [Iot_Monitoring_System](https://github.com/Arokrokie/Iot_Monitoring_System)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📞 Support

For questions or support, please open an issue in the GitHub repository.

---

**Built with ❤️ using Django, LoRaWAN, and The Things Network**