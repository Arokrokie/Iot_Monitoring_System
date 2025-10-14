from django.apps import AppConfig
import threading
import os
import logging

logger = logging.getLogger(__name__)


class IotDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iot_dashboard"

    def ready(self):
        # Only start once and not during migrations
        if os.environ.get("RUN_MAIN") and not hasattr(self, "mqtt_started"):
            try:
                from .mqtt_service import start_mqtt_listener

                # Start MQTT in a separate daemon thread
                mqtt_thread = threading.Thread(target=start_mqtt_listener, daemon=True)
                mqtt_thread.start()
                self.mqtt_started = True
                logger.info(
                    "✅ MQTT listener started successfully in background thread"
                )
                print("✅ MQTT listener started successfully in background thread")
            except Exception as e:
                logger.error(f"❌ Failed to start MQTT listener: {e}")
                print(f"❌ Failed to start MQTT listener: {e}")
