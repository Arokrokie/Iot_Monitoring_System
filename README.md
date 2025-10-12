## Run the IoT Dashboard locally

1. Create venv and install deps

```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

2. Apply migrations and create admin

```bash
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser --username admin --email admin@example.com --noinput
```

3. Run the server

```bash
.\.venv\Scripts\python manage.py runserver 0.0.0.0:8000
```

- Dashboard: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

4. Run the MQTT script

Keep the Django server running. In another shell:

```bash
.\.venv\Scripts\python temp_humidity_motion_sensor_data_lora.py
```

The script will:

- Fetch historical data from TTN and POST to `POST /api/ingest/`
- Listen for live uplinks and POST to `POST /api/ingest/`

Notes:

- Update `device_id`, `username`, and `password` in the script for your TTN app.
- If running on a different host/port, change the API URL in the script.
