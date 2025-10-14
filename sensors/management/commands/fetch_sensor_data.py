import os
import requests
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from sensors.models import SensorReading


class Command(BaseCommand):
    help = "Fetch sensor data from TTN API"

    def handle(self, *args, **options):
        # TTN Configuration
        broker = "eu1.cloud.thethings.network"
        app_id = "bd-test-app2"
        device_id = "lht65n-01-temp-humidity-sensor"
        api_key = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"

        url = f"https://{broker}/api/v3/as/applications/{app_id}/devices/{device_id}/packages/storage/uplink_message"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"last": "1h"}

        self.stdout.write("🔄 Fetching sensor data from TTN API...")

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                lines = response.text.strip().split("\n")
                new_count = 0
                total_processed = 0

                for line in lines:
                    try:
                        data = json.loads(line)
                        result = data.get("result", {})

                        # Extract data
                        received_at = result.get("received_at")
                        decoded = result.get("uplink_message", {}).get(
                            "decoded_payload", {}
                        )

                        if received_at and decoded:
                            total_processed += 1

                            # Check if this reading already exists
                            if not SensorReading.objects.filter(
                                device_id=device_id, received_at=received_at
                            ).exists():

                                SensorReading.objects.create(
                                    device_id=device_id,
                                    battery_voltage=decoded.get("field1"),
                                    humidity=decoded.get("field3"),
                                    motion_counts=decoded.get("field4"),
                                    temperature_c=decoded.get("field5"),
                                    received_at=received_at,
                                )
                                new_count += 1

                    except (json.JSONDecodeError, KeyError) as e:
                        continue

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Processed {total_processed} readings, added {new_count} new ones"
                    )
                )

                if new_count > 0:
                    # Show latest reading
                    latest = (
                        SensorReading.objects.filter(device_id=device_id)
                        .order_by("-received_at")
                        .first()
                    )
                    if latest:
                        self.stdout.write(
                            f"📊 Latest: {latest.received_at.strftime('%Y-%m-%d %H:%M:%S')} - "
                            f"Temp: {latest.temperature_c}°C, Humidity: {latest.humidity}%, "
                            f"Battery: {latest.battery_voltage}V"
                        )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ API error: {response.status_code} - {response.text}"
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
