# Railway deployment notes

## Goal

Deploy the Django web app (Render/Heroku-style) and run the MQTT listener as a worker process on Railway.

## Services

- Web service: serves Django app (uses Procfile entry `web`)
- Worker service: runs the MQTT listener (`python manage.py run_mqtt`)

## Environment variables (set these in Railway project settings)

- DJANGO_SECRET_KEY
- DATABASE_URL (if using external Postgres in production)
- ALLOWED_HOSTS (e.g., iot-monitoring-system-2.onrender.com or your Railway URL)
- TTN_BROKER (default: eu1.cloud.thethings.network)
- TTN_PORT (default: 1883)
- TTN_USERNAME
- TTN_PASSWORD
- TTN_DEVICE_ID
- TTN_APP_ID
- TTN_API_KEY
- IOT_INGEST_URL (IMPORTANT — set this to the full URL of your web app's ingest endpoint, e.g. https://<your-railway-url>/api/ingest/)

## How to add a worker on Railway

1. In Railway, create two services from the same repo: one web and one worker (if your plan supports workers).
2. For the web service, use the `web` Procfile entry (Railway detects Procfile automatically).
3. For the worker service, set the start command to: `python manage.py run_mqtt` (or choose the `worker` Procfile entry).
4. Ensure `IOT_INGEST_URL` points at the web service URL.

## Notes when on free tier

- Railway free plan may not support persistent background workers. If you can't start a worker there, use the following alternatives:
  - Move to a platform/plan that supports background workers.
  - Run the MQTT client locally (for testing) and let TTN push via webhook when available.
  - Implement periodic polling from the web app (on page visit) as a temporary workaround.
