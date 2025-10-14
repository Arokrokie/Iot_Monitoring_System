# 🚀 Railway Deployment Guide: IoT Sensor Monitoring System

## 📋 Pre-Deployment Checklist ✅

All required files are now in place:

- ✅ **Procfile** - Configured for web and worker services
- ✅ **Management Command** - `sensors/management/commands/run_mqtt.py`
- ✅ **Requirements.txt** - All dependencies included
- ✅ **API Endpoint** - `/api/ingest/` properly configured
- ✅ **Test Script** - `check_data.py` for verification

## 🛠️ Step-by-Step Railway Deployment

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Sign up/login (GitHub login recommended)
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Connect your repository

### Step 2: Configure Web Service

Railway will auto-create a web service. Set these environment variables:

**Go to your project → Variables → Add these:**

| Variable            | Value                                                |
| ------------------- | ---------------------------------------------------- |
| `DJANGO_SECRET_KEY` | `ouqefi^)_vh@y*71slrb)ha-_)%m(m!fbfiax5yqnwj=#ckgo@` |
| `DEBUG`             | `False`                                              |
| `ALLOWED_HOSTS`     | `*.up.railway.app,localhost,127.0.0.1`               |
| `DATABASE_URL`      | `sqlite:///db.sqlite3`                               |

**Wait for deployment to complete and note your web URL** (looks like `https://your-app-name.up.railway.app`)

### Step 3: Create Worker Service

1. In your Railway project, click "New Service"
2. Select "Empty Service"
3. Connect to the same GitHub repository
4. Go to Settings → Service Type → Select "Worker"
5. Go to Variables tab and add:

| Variable            | Value                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| `IOT_INGEST_URL`    | `https://your-app-name.up.railway.app/api/ingest/`                                                   |
| `TTN_BROKER`        | `eu1.cloud.thethings.network`                                                                        |
| `TTN_PORT`          | `8883`                                                                                               |
| `TTN_USERNAME`      | `bd-test-app2@ttn`                                                                                   |
| `TTN_PASSWORD`      | `NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA` |
| `TTN_DEVICE_ID`     | `lht65n-01-temp-humidity-sensor`                                                                     |
| `DJANGO_SECRET_KEY` | `ouqefi^)_vh@y*71slrb)ha-_)%m(m!fbfiax5yqnwj=#ckgo@`                                                 |
| `DEBUG`             | `False`                                                                                              |
| `ALLOWED_HOSTS`     | `*.up.railway.app,localhost,127.0.0.1`                                                               |

6. **Trigger deployment**

## 🔧 Local Testing (Before Railway)

### Test MQTT Locally:

**Terminal 1 - Start Web Server:**

```bash
python manage.py runserver
```

**Terminal 2 - Test MQTT:**

```bash
# Set environment variables
export IOT_INGEST_URL=http://localhost:8000/api/ingest/
export TTN_USERNAME=bd-test-app2@ttn
export TTN_PASSWORD=NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA
export TTN_DEVICE_ID=lht65n-01-temp-humidity-sensor
export TTN_PORT=8883

# Run MQTT worker
python manage.py run_mqtt
```

**Terminal 3 - Check Data:**

```bash
python check_data.py
```

## ✅ Verification Steps

### After Railway Deployment:

#### 1. Check Web Service:

- Visit: `https://your-app-name.up.railway.app/dashboard/`
- Should load without errors

#### 2. Check Worker Logs:

- Go to Worker service → Logs tab
- Look for:
  - `🚀 Starting MQTT listener...`
  - `✅ Connected to TTN MQTT broker!`
  - `✅ Data posted to API`

#### 3. Test Data Flow:

- Trigger your sensor to send data
- Check worker logs for new messages
- Refresh dashboard to see new data

## 🔍 Troubleshooting

### Common Issues:

1. **Worker not connecting to MQTT:**

   - Check environment variables are set correctly
   - Verify TTN credentials are valid
   - Check Railway worker logs for connection errors

2. **No data appearing in dashboard:**

   - Verify `IOT_INGEST_URL` points to correct web service URL
   - Check API endpoint is accessible: `https://your-app.up.railway.app/api/ingest/`
   - Run `python check_data.py` to verify database

3. **Database issues:**
   - Ensure migrations ran: `python manage.py migrate`
   - Check database permissions in Railway

### Field Mapping Reference:

| TTN Field | Database Field    | Description            |
| --------- | ----------------- | ---------------------- |
| `field1`  | `battery_voltage` | Battery voltage        |
| `field3`  | `humidity`        | Humidity percentage    |
| `field4`  | `motion_counts`   | Motion detection count |
| `field5`  | `temperature_c`   | Temperature in Celsius |

## 📊 Monitoring

- **Dashboard**: Real-time sensor data visualization
- **Analytics**: Historical data analysis and trends
- **Devices**: Device status and health monitoring
- **History**: Detailed data export and filtering

## 🚀 Next Steps

1. Deploy to Railway following the steps above
2. Monitor worker logs for successful MQTT connections
3. Test with actual sensor data
4. Set up monitoring alerts if needed
5. Consider adding authentication for production use
