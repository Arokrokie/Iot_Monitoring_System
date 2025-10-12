import paho.mqtt.client as mqtt
import json
from datetime import datetime, timedelta
import time
import os
import requests
import json


# Configuration
broker = "eu1.cloud.thethings.network"  # The MQTT Broker URL
port = 1883  # Use 1883 for unencrypted, 8883 for TLS
username = "bd-test-app2@ttn"  # The TTN application ID
password = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"  # The TTN API key
device_id = "lht65n-01-temp-humidity-sensor"  # The sensor


# Fetch Historical Data
def get_historical_sensor_data():
    app_id = "bd-test-app2"

    api_key = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"
    url = f"https://{broker}/api/v3/as/applications/{app_id}/devices/{device_id}/packages/storage/uplink_message"

    # Set authorization header
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "last": "12h"  # get messages from last 12 hours. Max 48 hours. Possible values: 12m (12 minutes)
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        response_text = response.text
        # response_text is a json file containing historical sensor readings. Each top-level 'result' key is a sensor reading
        # parse the json text to extract the following Fields of interest and use them to build your Dashboard
        # Key_Name          Meaning
        # field1            Battery Voltage
        # field3            Humidity
        # field4            Motion Counts
        # field5            Temperature (in Celcius)
        # received_at       UTC (Coordinated Universal Time), Uganda is UTC+3

        with open("message_history.json", "w") as f:  # optionally write data to file
            f.write(response.text.strip())
        try:
            items = json.loads(response_text)
            if isinstance(items, dict) and "result" in items:
                items = items["result"]
        except Exception:
            items = []
        # Post each reading to local Django API
        for item in items:
            try:
                payload = {
                    "device_id": device_id,
                    "received_at": item.get("received_at"),
                    "field1": item.get("result", {})
                    .get("uplink_message", {})
                    .get("decoded_payload", {})
                    .get("field1"),
                    "field3": item.get("result", {})
                    .get("uplink_message", {})
                    .get("decoded_payload", {})
                    .get("field3"),
                    "field4": item.get("result", {})
                    .get("uplink_message", {})
                    .get("decoded_payload", {})
                    .get("field4"),
                    "field5": item.get("result", {})
                    .get("uplink_message", {})
                    .get("decoded_payload", {})
                    .get("field5"),
                }
                requests.post(
                    "http://127.0.0.1:8000/api/ingest/", json=payload, timeout=5
                )
            except Exception as e:
                print("Post history error:", e)
    else:
        print("Error:", response.status_code, response.text)


get_historical_sensor_data()


# listen for instant notifications
topic = f"v3/{username}/devices/{device_id}/up"  # Topic for uplink messages automatically create by TTN for each sensor/device in your app


# Callback: When connected to broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to TTN MQTT broker!")
        client.subscribe(topic)  # Subscribe to uplink topic
    else:
        print(f"Failed to connect, return code {rc}")
        print("Reconnect failed, retrying in 5 minutes...")
        time.sleep(5 * 60)


# Callback: When a message is received
def on_message(client, userdata, msg):
    # print(f"Message received on topic {msg.topic}")

    payload = json.loads(msg.payload.decode())
    # payload contains sensor data with fields 1 to 5 as described before in get_historical_sensor_data() function
    with open("message.json", "w") as f:  # optionally save data to a file
        f.write(json.dumps(payload, indent=4))

    # Send to Django API
    try:
        # Map TTN structure to API fields
        decoded = payload.get("uplink_message", {}).get("decoded_payload", {})
        data = {
            "device_id": payload.get("end_device_ids", {}).get("device_id", device_id),
            "received_at": payload.get("received_at"),
            "field1": decoded.get("field1"),
            "field3": decoded.get("field3"),
            "field4": decoded.get("field4"),
            "field5": decoded.get("field5"),
        }
        requests.post("http://127.0.0.1:8000/api/ingest/", json=data, timeout=5)
    except Exception as e:
        print("Post realtime error:", e)

    # Extract the sensor data from the payload and use it for realtime notifications and building your dashboard


# Set up MQTT client
client = mqtt.Client()
client.username_pw_set(username, password)
# client.tls_set()  # Use TLS for secure connection
client.on_connect = on_connect
client.on_message = on_message

# Connect to broker and start loop
client.connect(broker, port, 60)
client.loop_forever()
