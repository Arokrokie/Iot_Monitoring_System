import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iot_dashboard.settings")
django.setup()

from sensors.models import SensorReading


def check_sensor_data():
    """Check and display recent sensor readings"""
    readings = SensorReading.objects.all()
    print(f"📊 Total readings in database: {readings.count()}")

    if readings.count() == 0:
        print("❌ No sensor data found in database")
        return

    print("\n🕒 Latest 5 readings:")
    print("-" * 80)
    for r in readings.order_by("-received_at")[:5]:
        print(
            f"📅 {r.received_at.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Device: {r.device_id} | "
            f"Temp: {r.temperature_c}°C | "
            f"Humidity: {r.humidity}% | "
            f"Battery: {r.battery_voltage}V | "
            f"Motion: {r.motion_counts}"
        )

    # Check for recent data (last 2 hours)
    from django.utils import timezone
    from datetime import timedelta

    recent_cutoff = timezone.now() - timedelta(hours=2)
    recent_readings = readings.filter(received_at__gte=recent_cutoff)

    print(f"\n⏰ Recent readings (last 2 hours): {recent_readings.count()}")

    if recent_readings.count() > 0:
        latest = recent_readings.order_by("-received_at").first()
        time_diff = timezone.now() - latest.received_at
        print(f"🕐 Last reading: {time_diff.total_seconds()/60:.1f} minutes ago")
        print("✅ Real-time data collection appears to be working!")
    else:
        print("⚠️  No recent data found - check MQTT connection")


if __name__ == "__main__":
    check_sensor_data()
