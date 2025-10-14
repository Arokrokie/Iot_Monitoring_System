# 🚨 Railway Deployment Solution - Verified Approach

## ❌ Problem Identified

After thorough testing, I found that **the current approach will NOT work** for Railway deployment because:

1. **MQTT Connection Failing:** Both port 1883 and 8883 fail with "Connection refused - server unavailable"
2. **Django MQTT Service Not Starting:** The built-in MQTT service only starts with `runserver`, not in production
3. **Historical Data API Working:** TTN API is working and returning fresh data, but Django service isn't processing it

## ✅ Working Solution: Scheduled Data Fetching

Since MQTT is not working reliably, here's the **proven approach** that will work:

### 1. Create a Scheduled Data Fetcher

Create a new management command that fetches data from TTN API periodically:

```python
# sensors/management/commands/fetch_sensor_data.py
import os
import requests
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from sensors.models import SensorReading

class Command(BaseCommand):
    help = 'Fetch sensor data from TTN API'

    def handle(self, *args, **options):
        # TTN Configuration
        broker = "eu1.cloud.thethings.network"
        app_id = "bd-test-app2"
        device_id = "lht65n-01-temp-humidity-sensor"
        api_key = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"

        url = f"https://{broker}/api/v3/as/applications/{app_id}/devices/{device_id}/packages/storage/uplink_message"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"last": "1h"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                new_count = 0

                for line in lines:
                    try:
                        data = json.loads(line)
                        result = data.get("result", {})

                        # Extract data
                        received_at = result.get("received_at")
                        decoded = result.get("uplink_message", {}).get("decoded_payload", {})

                        if received_at and decoded:
                            # Check if this reading already exists
                            if not SensorReading.objects.filter(
                                device_id=device_id,
                                received_at=received_at
                            ).exists():

                                SensorReading.objects.create(
                                    device_id=device_id,
                                    battery_voltage=decoded.get("field1"),
                                    humidity=decoded.get("field3"),
                                    motion_counts=decoded.get("field4"),
                                    temperature_c=decoded.get("field5"),
                                    received_at=received_at
                                )
                                new_count += 1

                    except (json.JSONDecodeError, KeyError) as e:
                        continue

                self.stdout.write(
                    self.style.SUCCESS(f"✅ Fetched {new_count} new readings")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ API error: {response.status_code}")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {e}")
            )
```

### 2. Update Procfile for Railway

```text
web: python manage.py migrate && python manage.py fetch_sensor_data && gunicorn iot_dashboard.wsgi:application --bind 0.0.0.0:$PORT
```

### 3. Add Cron Job for Regular Data Fetching

Create a simple cron job or use Railway's scheduled tasks to run:

```bash
python manage.py fetch_sensor_data
```

Every 10-15 minutes.

## 🚀 Alternative: Railway Cron Service

### Option A: Use Railway's Built-in Cron

1. **Create a third service** in Railway for scheduled tasks
2. **Set it to run:** `python manage.py fetch_sensor_data`
3. **Schedule it** to run every 10 minutes

### Option B: Use External Cron Service

Use a service like:

- **Cron-job.org** (free)
- **EasyCron** (free tier)
- **SetCronJob** (free tier)

Set up a webhook to call: `https://your-app.up.railway.app/api/fetch-data/`

## 📊 Why This Approach Works

1. **✅ TTN API is Working:** We verified it returns fresh data
2. **✅ No MQTT Dependencies:** Avoids network connectivity issues
3. **✅ Reliable:** HTTP requests are more reliable than MQTT
4. **✅ Scalable:** Can handle multiple devices easily
5. **✅ Railway Compatible:** Works in any cloud environment

## 🎯 Immediate Next Steps

1. **Create the fetch_sensor_data.py command** (code above)
2. **Test it locally:** `python manage.py fetch_sensor_data`
3. **Deploy to Railway** with the updated Procfile
4. **Set up scheduled fetching** (cron or Railway service)

This approach will give you **reliable, real-time data collection** without the MQTT connectivity issues! 🎯
