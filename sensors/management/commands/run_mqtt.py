from django.core.management.base import BaseCommand
import os
import paho.mqtt.client as mqtt
import json
import requests
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run MQTT listener for TTN sensor data"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting MQTT listener..."))

        # Get configuration from environment
        broker = os.getenv("TTN_BROKER", "eu1.cloud.thethings.network")
        port = int(os.getenv("TTN_PORT", "1883"))
        username = os.getenv("TTN_USERNAME")
        password = os.getenv("TTN_PASSWORD")
        device_id = os.getenv("TTN_DEVICE_ID")
        ingest_url = os.getenv("IOT_INGEST_URL")

        if not all([username, password, device_id, ingest_url]):
            self.stdout.write(
                self.style.ERROR("❌ Missing required environment variables")
            )
            return

        topic = f"v3/{username}/devices/{device_id}/up"

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("✅ Connected to TTN MQTT broker!")
                client.subscribe(topic)
                self.stdout.write(self.style.SUCCESS(f"✅ Subscribed to: {topic}"))
            else:
                logger.error(f"❌ Connection failed with code: {rc}")
                time.sleep(10)
                try:
                    client.reconnect()
                except Exception as e:
                    logger.error(f"❌ Reconnect failed: {e}")

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                logger.info("📨 Message received from TTN")

                # Extract data
                decoded = payload.get("uplink_message", {}).get("decoded_payload", {})
                data = {
                    "device_id": payload.get("end_device_ids", {}).get(
                        "device_id", device_id
                    ),
                    "received_at": payload.get("received_at"),
                    "field1": decoded.get("field1"),
                    "field3": decoded.get("field3"),
                    "field4": decoded.get("field4"),
                    "field5": decoded.get("field5"),
                }

                # Post to Django API
                response = requests.post(ingest_url, json=data, timeout=10)

                if response.status_code in [200, 201]:
                    logger.info(
                        f"✅ Data posted to API: {response.status_code} - {response.text}"
                    )
                else:
                    logger.error(
                        f"❌ API error: {response.status_code} - {response.text}"
                    )

            except Exception as e:
                logger.error(f"❌ Message error: {e}")

        # Setup MQTT client
        client = mqtt.Client()
        client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(broker, port, 60)
            client.loop_forever()
        except Exception as e:
            logger.error(f"❌ MQTT error: {e}")
            time.sleep(10)
            # Retry by re-invoking handle
            self.handle(*args, **options)
