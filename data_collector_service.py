#!/usr/bin/env python3
"""
Standalone Data Collection Service for IoT Sensor Monitoring
This service runs independently and fetches data from TTN API
"""

import os
import sys
import time
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data_collector.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class TTNDataCollector:
    """TTN Data Collector Service"""

    def __init__(self):
        # TTN Configuration
        self.broker = "eu1.cloud.thethings.network"
        self.app_id = "bd-test-app2"
        self.device_id = "lht65n-01-temp-humidity-sensor"
        self.api_key = "NNSXS.NGFSXX4UXDX55XRIDQZS6LPR4OJXKIIGSZS56CQ.6O4WUAUHFUAHSTEYRWJX6DDO7TL2IBLC7EV2LS4EHWZOOEPCEUOA"

        # API Configuration
        self.api_url = f"https://{self.broker}/api/v3/as/applications/{self.app_id}/devices/{self.device_id}/packages/storage/uplink_message"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

        # Django API Configuration
        self.django_api_url = os.getenv(
            "DJANGO_API_URL", "http://localhost:8000/api/ingest/"
        )

        # Collection settings
        self.fetch_interval = int(
            os.getenv("FETCH_INTERVAL", "600")
        )  # 10 minutes default
        self.data_window = os.getenv("DATA_WINDOW", "1h")  # 1 hour default

        logger.info(f"🚀 TTN Data Collector initialized")
        logger.info(f"📡 Device: {self.device_id}")
        logger.info(f"⏰ Fetch interval: {self.fetch_interval} seconds")
        logger.info(f"🕐 Data window: {self.data_window}")

    def fetch_sensor_data(self) -> List[Dict]:
        """Fetch sensor data from TTN API"""
        params = {"last": self.data_window}

        try:
            logger.info("🔄 Fetching sensor data from TTN API...")
            response = requests.get(
                self.api_url, headers=self.headers, params=params, timeout=30
            )

            if response.status_code == 200:
                lines = response.text.strip().split("\n")
                logger.info(f"📊 Received {len(lines)} data points from TTN")

                data_points = []
                for line in lines:
                    try:
                        data = json.loads(line)
                        result = data.get("result", {})

                        if result:
                            data_points.append(result)

                    except json.JSONDecodeError:
                        continue

                return data_points

            elif response.status_code == 401:
                logger.error("❌ Authentication failed - API key might be invalid")
                return []
            elif response.status_code == 404:
                logger.error("❌ Device or application not found")
                return []
            else:
                logger.error(f"❌ API error: {response.status_code} - {response.text}")
                return []

        except requests.exceptions.Timeout:
            logger.error("❌ Request timed out")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return []

    def process_data_point(self, data_point: Dict) -> Optional[Dict]:
        """Process a single data point and extract sensor readings"""
        try:
            received_at = data_point.get("received_at")
            decoded = data_point.get("uplink_message", {}).get("decoded_payload", {})

            if not received_at or not decoded:
                return None

            # Extract sensor data
            processed_data = {
                "device_id": self.device_id,
                "received_at": received_at,
                "field1": decoded.get("field1"),  # Battery voltage
                "field3": decoded.get("field3"),  # Humidity
                "field4": decoded.get("field4"),  # Motion counts
                "field5": decoded.get("field5"),  # Temperature
            }

            return processed_data

        except Exception as e:
            logger.error(f"❌ Error processing data point: {e}")
            return None

    def send_to_django(self, data: Dict) -> bool:
        """Send processed data to Django API"""
        try:
            response = requests.post(self.django_api_url, json=data, timeout=10)

            if response.status_code in [200, 201]:
                logger.info(f"✅ Data sent to Django API successfully")
                return True
            else:
                logger.error(
                    f"❌ Django API error: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error sending to Django: {e}")
            return False

    def collect_and_process_data(self):
        """Main data collection and processing function"""
        logger.info("🔄 Starting data collection cycle...")

        # Fetch data from TTN
        data_points = self.fetch_sensor_data()

        if not data_points:
            logger.warning("⚠️ No data points received from TTN")
            return

        # Process and send each data point
        successful_sends = 0
        for data_point in data_points:
            processed_data = self.process_data_point(data_point)

            if processed_data:
                if self.send_to_django(processed_data):
                    successful_sends += 1

                    # Log the latest reading
                    logger.info(
                        f"📊 Latest: {processed_data['received_at']} - "
                        f"Temp: {processed_data['field5']}°C, "
                        f"Humidity: {processed_data['field3']}%, "
                        f"Battery: {processed_data['field1']}V"
                    )

        logger.info(
            f"✅ Collection cycle complete: {successful_sends}/{len(data_points)} data points sent successfully"
        )

    def run_continuous(self):
        """Run the data collector continuously"""
        logger.info("🚀 Starting continuous data collection service...")
        logger.info(f"⏰ Will fetch data every {self.fetch_interval} seconds")

        while True:
            try:
                self.collect_and_process_data()

                # Wait for next collection cycle
                logger.info(
                    f"⏳ Waiting {self.fetch_interval} seconds until next collection..."
                )
                time.sleep(self.fetch_interval)

            except KeyboardInterrupt:
                logger.info("🛑 Data collection service stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in main loop: {e}")
                logger.info("⏳ Waiting 60 seconds before retry...")
                time.sleep(60)

    def run_once(self):
        """Run data collection once (for testing or cron jobs)"""
        logger.info("🔄 Running single data collection...")
        self.collect_and_process_data()
        logger.info("✅ Single collection complete")


def main():
    """Main entry point"""
    collector = TTNDataCollector()

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        collector.run_once()
    else:
        collector.run_continuous()


if __name__ == "__main__":
    main()
