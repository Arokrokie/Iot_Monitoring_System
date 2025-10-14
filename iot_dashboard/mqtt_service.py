import paho.mqtt.client as mqtt
import json
import time
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def start_mqtt_listener():
    """Start the MQTT listener for LoRa sensor data"""

    # Configuration
    broker = "eu1.cloud.thethings.network"
    port = 1883
    username = "bd-test-app2@ttn"
    password = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"
    device_id = "lht65n-01-temp-humidity-sensor"
    topic = f"v3/{username}/devices/{device_id}/up"

    def get_historical_sensor_data():
        """Fetch historical sensor data on startup"""
        logger.info("Fetching historical sensor data...")

        app_id = "bd-test-app2"
        api_key = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"
        url = f"https://{broker}/api/v3/as/applications/{app_id}/devices/{device_id}/packages/storage/uplink_message"

        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"last": "12h"}

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                response_text = response.text

                # Save historical data to file
                with open("lora_message_history.json", "w") as f:
                    f.write(response.text.strip())

                try:
                    items = json.loads(response_text)
                    if isinstance(items, dict) and "result" in items:
                        items = items["result"]
                except Exception as e:
                    logger.warning(f"Error parsing historical data: {e}")
                    items = []

                # Post each historical reading
                success_count = 0
                for item in items:
                    try:
                        payload = {
                            "device_id": device_id,
                            "received_at": item.get("received_at"),
                            "battery_voltage": item.get("result", {})
                            .get("uplink_message", {})
                            .get("decoded_payload", {})
                            .get("field1"),
                            "humidity": item.get("result", {})
                            .get("uplink_message", {})
                            .get("decoded_payload", {})
                            .get("field3"),
                            "motion_count": item.get("result", {})
                            .get("uplink_message", {})
                            .get("decoded_payload", {})
                            .get("field4"),
                            "temperature": item.get("result", {})
                            .get("uplink_message", {})
                            .get("decoded_payload", {})
                            .get("field5"),
                        }
                        # Use your Django API endpoint
                        api_url = (
                            "http://localhost:8000/api/ingest/"  # Adjust if needed
                        )
                        requests.post(api_url, json=payload, timeout=5)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Post history error: {e}")

                logger.info(
                    f"Successfully posted {success_count} historical data points"
                )
            else:
                logger.error(
                    f"HTTP Error fetching historical data: {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Historical data fetch error: {e}")

    def on_connect(client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            logger.info("Connected to TTN MQTT broker!")
            client.subscribe(topic)
        else:
            logger.error(f"Failed to connect, return code {rc}")
            time.sleep(300)  # Wait 5 minutes before reconnect

    def on_message(client, userdata, msg):
        """Callback when a message is received"""
        logger.info("Message received from LoRa sensor")

        try:
            payload = json.loads(msg.payload.decode())

            # Save to file for debugging
            with open("lora_message.json", "w") as f:
                f.write(json.dumps(payload, indent=4))

            # Send to Django API
            decoded = payload.get("uplink_message", {}).get("decoded_payload", {})
            data = {
                "device_id": payload.get("end_device_ids", {}).get(
                    "device_id", device_id
                ),
                "received_at": payload.get("received_at"),
                "battery_voltage": decoded.get("field1"),
                "humidity": decoded.get("field3"),
                "motion_count": decoded.get("field4"),
                "temperature": decoded.get("field5"),
            }

            # Use your Django API endpoint - adjust URL as needed
            api_url = "http://localhost:8000/api/ingest/"

            # For production (if your API is on the same server):
            api_url = "/api/ingest/"  # Relative URL
            response = requests.post(api_url, json=data, timeout=5)

            if response.status_code == 200:
                logger.info("Successfully posted sensor data to API")
            else:
                logger.warning(f"API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    # Fetch historical data first
    get_historical_sensor_data()

    # Set up MQTT client
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect and start listening (non-blocking)
    try:
        client.connect(broker, port, 60)
        logger.info("MQTT listener connected successfully")
        client.loop_start()  # This runs in background without blocking
    except Exception as e:
        logger.error(f"MQTT connection error: {e}")
        # Auto-reconnect after delay
        time.sleep(60)
        start_mqtt_listener()  # Recursive retry
