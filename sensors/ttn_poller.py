import os
import json
import time
import requests
import logging
from django.utils import timezone
from django.db import IntegrityError
from .models import SensorReading

logger = logging.getLogger(__name__)


def fetch_recent_ttn_data(minutes: int = 10):
    """Fetch recent TTN Storage API uplinks and insert any new readings.

    This is a lightweight on-demand poller intended to run during page loads as a
    fallback when a persistent MQTT worker cannot run.
    """
    app_id = os.getenv("TTN_APP_ID")
    api_key = os.getenv("TTN_API_KEY")
    broker = os.getenv("TTN_BROKER", "eu1.cloud.thethings.network")
    device_id = os.getenv("TTN_DEVICE_ID")
    last = os.getenv("TTN_STORAGE_LAST", f"{minutes}m")

    if not app_id or not api_key:
        logger.debug("TTN app id or api key not configured; skipping poll")
        return 0

    url = f"https://{broker}/api/v3/as/applications/{app_id}/devices/{device_id}/packages/storage/uplink_message"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"last": last}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"TTN storage API returned {resp.status_code}: {resp.text}")
            return 0

        text = resp.text.strip()
        items = []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "result" in parsed:
                items = parsed["result"]
            elif isinstance(parsed, list):
                items = parsed
            else:
                items = [parsed]
        except Exception:
            # NDJSON fallback
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except Exception:
                    logger.exception("Failed to parse NDJSON line")

        inserted = 0
        for it in items:
            try:
                device = (
                    it.get("end_device_ids", {}).get("device_id")
                    or device_id
                    or "unknown-device"
                )
                received_at = it.get("received_at")
                decoded = (
                    it.get("uplink_message", {}).get("decoded_payload", {})
                    or it.get("fields", {})
                    or {}
                )

                # Avoid duplicates: check if a reading with same device and timestamp exists
                from django.utils.dateparse import parse_datetime

                dt = None
                if isinstance(received_at, str):
                    dt = parse_datetime(received_at)
                if dt is None:
                    dt = timezone.now()

                # Map fields
                battery = decoded.get("field1") or decoded.get("battery_voltage")
                humidity = decoded.get("field3") or decoded.get("humidity")
                motion = decoded.get("field4") or decoded.get("motion_counts")
                temp = decoded.get("field5") or decoded.get("temperature_c")

                exists = SensorReading.objects.filter(
                    device_id=device, received_at=dt
                ).exists()
                if exists:
                    continue

                SensorReading.objects.create(
                    device_id=device,
                    battery_voltage=battery,
                    humidity=humidity,
                    motion_counts=motion,
                    temperature_c=temp,
                    received_at=dt,
                )
                inserted += 1
            except Exception:
                logger.exception("Error inserting TTN item")

        logger.info(f"Inserted {inserted} TTN items from storage API")
        return inserted

    except Exception:
        logger.exception("Error fetching TTN storage API")
        return 0
