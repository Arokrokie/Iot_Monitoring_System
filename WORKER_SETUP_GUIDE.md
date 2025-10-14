# 🔧 Worker Setup Guide: How to Proceed

## 📊 Current System Status

**✅ What's Working:**

- Django web application with dashboard
- API endpoint for data ingestion (`/api/ingest/`)
- Database with 257 sensor readings
- Historical data fetching via TTN API
- Real-time data collection (when MQTT works)

**⚠️ Current Issue:**

- MQTT connection to TTN broker failing (Connection refused - server unavailable)
- Data collection relies on historical API fetching

## 🎯 Recommended Approach for Railway Deployment

### Option 1: Single Web Service (Recommended)

**Use the existing MQTT service in Django app instead of separate worker**

**Why this approach:**

- ✅ Already implemented and working
- ✅ Handles both MQTT and historical data fetching
- ✅ Simpler deployment (one service instead of two)
- ✅ Built-in fallback mechanisms

**Railway Configuration:**

1. **Deploy only the web service** (no separate worker needed)
2. **Set these environment variables:**

| Variable            | Value                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| `DJANGO_SECRET_KEY` | `ouqefi^)_vh@y*71slrb)ha-_)%m(m!fbfiax5yqnwj=#ckgo@`                                                 |
| `DEBUG`             | `False`                                                                                              |
| `ALLOWED_HOSTS`     | `*.up.railway.app,localhost,127.0.0.1`                                                               |
| `DATABASE_URL`      | `sqlite:///db.sqlite3`                                                                               |
| `TTN_BROKER`        | `eu1.cloud.thethings.network`                                                                        |
| `TTN_PORT`          | `1883`                                                                                               |
| `TTN_USERNAME`      | `bd-test-app2@ttn`                                                                                   |
| `TTN_PASSWORD`      | `NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA` |
| `TTN_DEVICE_ID`     | `lht65n-01-temp-humidity-sensor`                                                                     |

### Option 2: Separate Worker Service

**Use the management command approach**

**When to use this:**

- If you need dedicated MQTT processing
- For high-volume data processing
- If you want to scale MQTT handling separately

**Railway Configuration:**

1. **Web Service** (same as Option 1)
2. **Worker Service** with these additional variables:
   - `IOT_INGEST_URL` = `https://your-app-name.up.railway.app/api/ingest/`

## 🚀 Step-by-Step Deployment (Option 1 - Recommended)

### 1. Update Procfile

```text
web: python manage.py migrate && gunicorn iot_dashboard.wsgi:application --bind 0.0.0.0:$PORT
```

### 2. Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Set environment variables (see table above)
4. Deploy

### 3. Monitor Deployment

- Check web service logs for MQTT connection status
- Look for: "✅ MQTT listener started successfully in background thread"
- Monitor for data collection activity

## 🔍 Troubleshooting MQTT Connection

**Current Issue:** Connection refused (code 3)

**Possible Causes:**

1. **Network/Firewall:** Railway might block MQTT connections
2. **TTN Broker Status:** Server might be temporarily unavailable
3. **Credentials:** API key might have expired
4. **Rate Limiting:** Too many connection attempts

**Solutions:**

1. **Check TTN Console:** Verify device is active and sending data
2. **Test Credentials:** Use TTN web interface to verify API key
3. **Network Test:** Railway might need different network configuration
4. **Fallback Mode:** System will work with historical data fetching

## 📈 Data Collection Strategy

**Current Implementation:**

1. **Historical Data:** Fetches last 1 hour of data on startup
2. **Real-time MQTT:** Attempts to connect for live data
3. **Fallback:** If MQTT fails, relies on periodic historical fetching

**For Production:**

- Consider implementing scheduled historical data fetching
- Add retry mechanisms for MQTT connections
- Implement data validation and error handling

## ✅ Verification Steps

### After Deployment:

1. **Check Web Service:**

   - Visit: `https://your-app-name.up.railway.app/dashboard/`
   - Should load without errors

2. **Check Logs:**

   - Look for MQTT connection attempts
   - Monitor for data collection activity
   - Check for any error messages

3. **Test Data Flow:**
   - Trigger sensor to send data
   - Check if new data appears in dashboard
   - Verify historical data fetching works

## 🎯 Next Steps

1. **Deploy using Option 1** (single web service)
2. **Monitor logs** for MQTT connection status
3. **Test data collection** with actual sensor
4. **Optimize** based on real-world performance

The system is designed to work even if MQTT connection fails, so you can deploy and test immediately! 🚀
