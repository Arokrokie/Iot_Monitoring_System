from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the MQTT listener as a standalone process (use as Railway worker or separate service)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting MQTT listener..."))
        try:
            # import here to avoid importing mqtt_service at Django startup for web processes
            from iot_dashboard import mqtt_service

            mqtt_service.start_mqtt_listener()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("MQTT listener stopped by user"))
        except Exception as e:
            logger.exception("MQTT listener crashed")
            self.stderr.write(f"MQTT listener crashed: {e}\n")
