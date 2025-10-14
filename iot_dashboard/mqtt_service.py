import os
import paho.mqtt.client as mqtt
import json
import time
import requests
import logging
import socket
from django.conf import settings

logger = logging.getLogger(__name__)


def start_mqtt_listener():
    """Start the MQTT listener for LoRa sensor data"""

    logger.info("🚀 Starting MQTT listener...")
    print("🚀 Starting MQTT listener...")

    # Configuration (respect environment variables for deployment)
    broker = os.getenv("TTN_BROKER", "eu1.cloud.thethings.network")
    port = int(os.getenv("TTN_PORT", "1883"))
    username = os.getenv("TTN_USERNAME", "bd-test-app2@ttn")
    password = os.getenv(
        "TTN_PASSWORD",
        "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA",
    )
    device_id = os.getenv("TTN_DEVICE_ID", "lht65n-01-temp-humidity-sensor")
    topic = f"v3/{username}/devices/{device_id}/up"

    def get_historical_sensor_data():
        """Fetch historical sensor data on startup"""
        logger.info("📡 Fetching historical sensor data...")
        print("📡 Fetching historical sensor data...")

        app_id = "bd-test-app2"
        api_key = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"
        url = f"https://{broker}/api/v3/as/applications/{app_id}/devices/{device_id}/packages/storage/uplink_message"

        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"last": "1h"}  # Reduced to 1h for faster testing

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            logger.info(f"📊 Historical API response status: {response.status_code}")
            print(f"📊 Historical API response status: {response.status_code}")

            if response.status_code == 200:
                try:
                    items = json.loads(response.text)
                    if isinstance(items, dict) and "result" in items:
                        items = items["result"]
                        logger.info(f"📈 Found {len(items)} historical data points")
                        print(f"📈 Found {len(items)} historical data points")
                    else:
                        logger.warning("⚠️ No 'result' key in historical data response")
                        print("⚠️ No 'result' key in historical data response")
                except Exception as e:
                    logger.error(f"❌ Error parsing historical data: {e}")
                    print(f"❌ Error parsing historical data: {e}")
            else:
                logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
                print(f"❌ HTTP Error {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"❌ Historical data fetch error: {e}")
            print(f"❌ Historical data fetch error: {e}")

    def on_connect(client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            logger.info("✅ Connected to TTN MQTT broker!")
            logger.info(f"📡 Subscribing to topic: {topic}")
            print("✅ Connected to TTN MQTT broker!")
            print(f"📡 Subscribing to topic: {topic}")
            client.subscribe(topic)
        else:
            error_codes = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised",
            }
            error_msg = error_codes.get(rc, f"Unknown error code {rc}")
            logger.error(f"❌ MQTT Connection failed: {error_msg}")
            print(f"❌ MQTT Connection failed: {error_msg}")

    def on_subscribe(client, userdata, mid, granted_qos):
        """Callback when subscribed to topic"""
        logger.info(f"✅ Successfully subscribed to topic (QoS: {granted_qos})")
        print(f"✅ Successfully subscribed to topic (QoS: {granted_qos})")

    def on_message(client, userdata, msg):
        """Callback when a message is received"""
        logger.info(f"📨 Message received on topic: {msg.topic}")
        print(f"📨 Message received on topic: {msg.topic}")

        try:
            payload = json.loads(msg.payload.decode())
            logger.info("✅ Successfully parsed MQTT message")
            print("✅ Successfully parsed MQTT message")

            # Send to Django API
            decoded = payload.get("uplink_message", {}).get("decoded_payload", {})
            data = {
                "device_id": payload.get("end_device_ids", {}).get(
                    "device_id", device_id
                ),
                "received_at": payload.get("received_at"),
                "battery_voltage": decoded.get("field1"),
                "humidity": decoded.get("field3"),
                "motion_counts": decoded.get("field4"),
                "temperature_c": decoded.get("field5"),
            }

            logger.info(f"📊 Sensor data: {data}")
            print(f"📊 Sensor data: {data}")

            # Post to ingest endpoint — prefer a configured deploy URL
            ingest_url = os.getenv("IOT_INGEST_URL")
            if ingest_url:
                api_urls = [ingest_url]
            else:
                api_urls = [
                    "http://localhost:8000/api/ingest/",
                    "http://127.0.0.1:8000/api/ingest/",
                    "/api/ingest/",
                ]

            for api_url in api_urls:
                try:
                    response = requests.post(api_url, json=data, timeout=5)
                    logger.info(
                        f"API {api_url} responded: {response.status_code} - {response.text}"
                    )
                    print(
                        f"API {api_url} responded: {response.status_code} - {response.text}"
                    )
                    if response.status_code in (200, 201):
                        logger.info(f"✅ Data posted successfully to {api_url}")
                        print(f"✅ Data posted successfully to {api_url}")
                        break
                    else:
                        logger.warning(
                            f"⚠️ API {api_url} returned {response.status_code}"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to post to {api_url}: {e}")

        except Exception as e:
            logger.error(f"❌ Error processing MQTT message: {e}")
            print(f"❌ Error processing MQTT message: {e}")

    def on_disconnect(client, userdata, rc):
        """Callback when disconnected"""
        logger.warning(f"🔌 Disconnected from MQTT broker (code: {rc})")
        print(f"🔌 Disconnected from MQTT broker (code: {rc})")
        if rc != 0:
            logger.info("🔄 Attempting to reconnect...")
            print("🔄 Attempting to reconnect...")
            time.sleep(5)
            try:
                client.reconnect()
            except Exception as e:
                logger.error(f"❌ Reconnection failed: {e}")

    # Test network connectivity first
    try:
        logger.info("🌐 Testing network connectivity...")
        print("🌐 Testing network connectivity...")
        socket.create_connection((broker, port), timeout=10)
        logger.info("✅ Network connectivity OK")
        print("✅ Network connectivity OK")
    except Exception as e:
        logger.error(f"❌ Network connectivity failed: {e}")
        print(f"❌ Network connectivity failed: {e}")
        return

    # Fetch historical data first
    get_historical_sensor_data()

    # Set up MQTT client
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Connect and start listening
    try:
        logger.info(f"🔗 Connecting to {broker}:{port}...")
        print(f"🔗 Connecting to {broker}:{port}...")
        client.connect(broker, port, 60)
        logger.info("✅ MQTT connection initiated, starting loop...")
        print("✅ MQTT connection initiated, starting loop...")
        client.loop_start()  # Non-blocking background loop
    except Exception as e:
        logger.error(f"❌ MQTT connection error: {e}")
        print(f"❌ MQTT connection error: {e}")
        # Retry after delay
        time.sleep(10)
        start_mqtt_listener()
