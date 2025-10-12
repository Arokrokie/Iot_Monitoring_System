import os
import sys
import json
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iot_dashboard.settings")
import django

django.setup()
from django.utils import timezone
from sensors.models import SensorReading

try:
    yesterday = timezone.now() - timedelta(days=1)
    chart_data = SensorReading.objects.filter(received_at__gte=yesterday).order_by(
        "received_at"
    )
    temp_data = [
        float(r.temperature_c) for r in chart_data if r.temperature_c is not None
    ]
    temp_labels = [
        r.received_at.strftime("%H:%M")
        for r in chart_data
        if r.temperature_c is not None
    ]
    humidity_data = [float(r.humidity) for r in chart_data if r.humidity is not None]
    humidity_labels = [
        r.received_at.strftime("%H:%M") for r in chart_data if r.humidity is not None
    ]
    print("temp_labels_json =", json.dumps(temp_labels))
    print("temp_data_json =", json.dumps(temp_data))
    print("humidity_labels_json =", json.dumps(humidity_labels))
    print("humidity_data_json =", json.dumps(humidity_data))
    print(
        "counts:",
        len(temp_labels),
        len(temp_data),
        len(humidity_labels),
        len(humidity_data),
    )
except Exception as e:
    print("error", e)
    raise
