#!/usr/bin/env python3
"""
Script to post historical sensor data from message_history.json to the Django API
"""
import json
import requests
import time


def post_historical_data():
    try:
        # Read the historical data file
        with open("message_history.json", "r") as f:
            content = f.read().strip()

        # Parse the JSON data (JSONL format - one JSON object per line)
        lines = content.strip().split("\n")
        items = []
        for line in lines:
            if line.strip():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue

        print(f"Found {len(items)} historical records")

        # Post each reading to the API
        success_count = 0
        for i, item in enumerate(items):
            try:
                # Extract data from the TTN structure
                if "result" in item:
                    result = item["result"]
                    device_id = result.get("end_device_ids", {}).get(
                        "device_id", "unknown-device"
                    )
                    received_at = result.get("received_at")
                    decoded_payload = result.get("uplink_message", {}).get(
                        "decoded_payload", {}
                    )
                else:
                    device_id = item.get("end_device_ids", {}).get(
                        "device_id", "unknown-device"
                    )
                    received_at = item.get("received_at")
                    decoded_payload = item.get("uplink_message", {}).get(
                        "decoded_payload", {}
                    )

                # Map the fields
                payload = {
                    "device_id": device_id,
                    "received_at": received_at,
                    "field1": decoded_payload.get("field1"),  # Battery voltage
                    "field3": decoded_payload.get("field3"),  # Humidity
                    "field4": decoded_payload.get("field4"),  # Motion counts
                    "field5": decoded_payload.get("field5"),  # Temperature
                }

                # Post to API
                response = requests.post(
                    "http://127.0.0.1:8000/api/ingest/", json=payload, timeout=5
                )

                if response.status_code == 200:
                    success_count += 1
                    print(
                        f"✓ Posted record {i+1}/{len(items)}: {device_id} at {received_at}"
                    )
                else:
                    print(
                        f"✗ Failed to post record {i+1}: {response.status_code} - {response.text}"
                    )

                # Small delay to avoid overwhelming the API
                time.sleep(0.1)

            except Exception as e:
                print(f"✗ Error processing record {i+1}: {e}")
                continue

        print(
            f"\nSuccessfully posted {success_count}/{len(items)} historical records to the API"
        )

    except FileNotFoundError:
        print(
            "message_history.json file not found. Make sure the MQTT script has run and fetched historical data."
        )
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    post_historical_data()
