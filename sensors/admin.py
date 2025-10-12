from django.contrib import admin
from .models import SensorReading


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = (
        "device_id",
        "temperature_c",
        "humidity",
        "battery_voltage",
        "motion_counts",
        "received_at",
    )
    list_filter = ("device_id",)
    search_fields = ("device_id",)
    ordering = ("-received_at",)


# Register your models here.
