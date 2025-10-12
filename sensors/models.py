from django.db import models


class SensorReading(models.Model):
    device_id = models.CharField(max_length=128, db_index=True)
    battery_voltage = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    motion_counts = models.IntegerField(null=True, blank=True)
    temperature_c = models.FloatField(null=True, blank=True)
    received_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at", "-id"]

    def __str__(self) -> str:
        return f"{self.device_id} @ {self.received_at:%Y-%m-%d %H:%M:%S}"


# Create your models here.
