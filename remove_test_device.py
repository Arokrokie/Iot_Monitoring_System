import os
import sys

# Ensure we run from project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iot_dashboard.settings")
import django

django.setup()

from sensors.models import SensorReading

DEVICE_KEY = "test-device"

qs = SensorReading.objects.filter(device_id__iexact=DEVICE_KEY)
count = qs.count()
if count == 0:
    print(f"No records found for device_id='{DEVICE_KEY}'.")
    sys.exit(0)

deleted, details = qs.delete()
print(f"Deleted {deleted} rows for device_id='{DEVICE_KEY}'.")
if details:
    print("Detail:", details)
