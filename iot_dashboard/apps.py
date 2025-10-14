from django.apps import AppConfig
import threading
import os


class IotDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iot_dashboard"

    def ready(self):
        # Only start once and not during migrations
        if os.environ.get("RUN_MAIN") and not hasattr(self, "mqtt_started"):
            from .mqtt_service import start_mqtt_listener

            # Start MQTT in a separate daemon thread
            mqtt_thread = threading.Thread(target=start_mqtt_listener, daemon=True)
            mqtt_thread.start()
            self.mqtt_started = True
            print("MQTT listener started in background thread")
