from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.utils.dateparse import parse_datetime
from django.db.models import Avg, Max, Min, Count, Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import SensorReading
from .ttn_poller import fetch_recent_ttn_data

# Simple module-level last-poll timestamp to avoid heavy polling on every request
_last_ttn_poll = 0
import os
import time
import logging
import json
import csv


def dashboard(request: HttpRequest):
    # Run on-demand TTN poller at most once every N minutes as a fallback when worker isn't running
    global _last_ttn_poll
    try:
        now_ts = int(time.time())
        poll_interval = int(os.getenv("TTN_POLL_INTERVAL_MIN", "5")) * 60
        if now_ts - _last_ttn_poll > poll_interval:
            inserted = fetch_recent_ttn_data(
                minutes=int(os.getenv("TTN_POLL_INTERVAL_MIN", "5"))
            )
            if inserted:
                _last_ttn_poll = now_ts
    except Exception:
        # Don't let polling failures break the dashboard
        logger = logging.getLogger(__name__)
        logger.exception("TTN poller failure")

    # Get latest readings
    readings = SensorReading.objects.order_by("-received_at")[:50]

    # Get latest values for metrics
    latest_reading = SensorReading.objects.order_by("-received_at").first()
    latest_temp = latest_reading.temperature_c if latest_reading else None
    latest_humidity = latest_reading.humidity if latest_reading else None
    latest_battery = latest_reading.battery_voltage if latest_reading else None
    latest_motion = latest_reading.motion_counts if latest_reading else None

    # Get chart data for last 24 hours
    yesterday = timezone.now() - timedelta(days=1)
    chart_data = SensorReading.objects.filter(received_at__gte=yesterday).order_by(
        "received_at"
    )

    temp_data = [
        float(r.temperature_c) for r in chart_data if r.temperature_c is not None
    ]
    temp_labels = [
        r.received_at.strftime("%H:%M")
        for r in chart_data
        if r.temperature_c is not None
    ]

    humidity_data = [float(r.humidity) for r in chart_data if r.humidity is not None]
    humidity_labels = [
        r.received_at.strftime("%H:%M") for r in chart_data if r.humidity is not None
    ]

    # JSON-encode chart arrays so templates receive valid JS literals
    try:
        temp_data_json = json.dumps(temp_data)
        temp_labels_json = json.dumps(temp_labels)
        humidity_data_json = json.dumps(humidity_data)
        humidity_labels_json = json.dumps(humidity_labels)
    except Exception:
        temp_data_json = "[]"
        temp_labels_json = "[]"
        humidity_data_json = "[]"
        humidity_labels_json = "[]"

    # Get device status information
    device_count = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .values("device_id")
        .distinct()
        .count()
    )

    # Check online devices (last reading within 2 hours)
    online_devices = 0
    for device_id in (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .values_list("device_id", flat=True)
        .distinct()
    ):
        latest = (
            SensorReading.objects.filter(device_id=device_id)
            .order_by("-received_at")
            .first()
        )
        if latest and (timezone.now() - latest.received_at).total_seconds() < 7200:
            online_devices += 1

    # Calculate uptime percentage
    uptime_percentage = 0
    if device_count > 0:
        uptime_percentage = round((online_devices * 100) / device_count, 0)

    device_status = {
        "total": device_count,
        "online": online_devices,
        "offline": device_count - online_devices,
        "uptime_percentage": uptime_percentage,
    }

    return render(
        request,
        "sensors/dashboard.html",
        {
            "readings": readings,
            "latest_temp": latest_temp,
            "latest_humidity": latest_humidity,
            "latest_battery": latest_battery,
            "latest_motion": latest_motion,
            "temp_data": temp_data,
            "temp_labels": temp_labels,
            "humidity_data": humidity_data,
            "humidity_labels": humidity_labels,
            "temp_data_json": temp_data_json,
            "temp_labels_json": temp_labels_json,
            "humidity_data_json": humidity_data_json,
            "humidity_labels_json": humidity_labels_json,
            "device_status": device_status,
        },
    )


def analytics(request: HttpRequest):
    # Overall statistics - exclude test devices
    total_readings = SensorReading.objects.exclude(
        device_id__in=["test-device", "unknown-device"]
    ).count()
    device_count = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .values("device_id")
        .distinct()
        .count()
    )
    today_readings = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .filter(received_at__date=timezone.now().date())
        .count()
    )

    # Calculate real average interval
    readings = SensorReading.objects.exclude(
        device_id__in=["test-device", "unknown-device"]
    ).order_by("received_at")
    avg_interval = 0
    if readings.count() > 1:
        intervals = []
        prev_time = None
        for reading in readings:
            if prev_time:
                interval = (
                    reading.received_at - prev_time
                ).total_seconds() / 60  # minutes
                intervals.append(interval)
            prev_time = reading.received_at
        avg_interval = round(sum(intervals) / len(intervals), 1) if intervals else 0

    # Temperature statistics - exclude test devices
    temp_stats = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .filter(temperature_c__isnull=False)
        .aggregate(
            avg=Avg("temperature_c"), min=Min("temperature_c"), max=Max("temperature_c")
        )
    )

    # Humidity statistics - exclude test devices
    humidity_stats = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .filter(humidity__isnull=False)
        .aggregate(avg=Avg("humidity"), min=Min("humidity"), max=Max("humidity"))
    )

    # Daily readings for last 7 days
    daily_data = []
    daily_labels = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        count = (
            SensorReading.objects.exclude(
                device_id__in=["test-device", "unknown-device"]
            )
            .filter(received_at__date=date)
            .count()
        )
        daily_data.append(count)
        daily_labels.append(date.strftime("%m/%d"))

    # Temperature distribution - exclude test devices
    temp_distribution_data = []
    temp_distribution_labels = []
    temp_ranges = [
        ("<20°C", 0, 20),
        ("20-22°C", 20, 22),
        ("22-24°C", 22, 24),
        ("24-26°C", 24, 26),
        ("26-28°C", 26, 28),
        ("28-30°C", 28, 30),
        ("30-32°C", 30, 32),
        ("32-34°C", 32, 34),
        ("34-36°C", 34, 36),
        (">36°C", 36, 100),
    ]

    for label, min_temp, max_temp in temp_ranges:
        if min_temp == 0:
            count = (
                SensorReading.objects.exclude(
                    device_id__in=["test-device", "unknown-device"]
                )
                .filter(temperature_c__lt=max_temp)
                .count()
            )
        elif max_temp == 100:
            count = (
                SensorReading.objects.exclude(
                    device_id__in=["test-device", "unknown-device"]
                )
                .filter(temperature_c__gte=min_temp)
                .count()
            )
        else:
            count = (
                SensorReading.objects.exclude(
                    device_id__in=["test-device", "unknown-device"]
                )
                .filter(temperature_c__gte=min_temp, temperature_c__lt=max_temp)
                .count()
            )

        temp_distribution_labels.append(label)
        temp_distribution_data.append(count)

    # Heatmap data (simplified)
    heatmap_days = []
    heatmap_data = {}
    for i in range(7):
        day = timezone.now().date() - timedelta(days=i)
        heatmap_days.append(day.strftime("%a"))
        heatmap_data[f"{i}"] = [0] * 24  # Simplified

    # Combined temperature & humidity series for the last 24 hours
    last_24h = timezone.now() - timedelta(days=1)
    recent_qs = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .filter(received_at__gte=last_24h)
        .order_by("received_at")
    )

    temp_series = [
        float(r.temperature_c) for r in recent_qs if r.temperature_c is not None
    ]
    temp_labels = [
        r.received_at.strftime("%H:%M")
        for r in recent_qs
        if r.temperature_c is not None
    ]

    humidity_series = [float(r.humidity) for r in recent_qs if r.humidity is not None]
    humidity_labels = [
        r.received_at.strftime("%H:%M") for r in recent_qs if r.humidity is not None
    ]

    # Battery statistics
    battery_stats = {
        "high": SensorReading.objects.exclude(
            device_id__in=["test-device", "unknown-device"]
        )
        .filter(battery_voltage__gt=3.5)
        .count(),
        "medium": SensorReading.objects.exclude(
            device_id__in=["test-device", "unknown-device"]
        )
        .filter(battery_voltage__gte=3.0, battery_voltage__lte=3.5)
        .count(),
        "critical": SensorReading.objects.exclude(
            device_id__in=["test-device", "unknown-device"]
        )
        .filter(battery_voltage__lt=3.0)
        .count(),
    }

    # Motion statistics
    motion_stats = {
        "total": SensorReading.objects.exclude(
            device_id__in=["test-device", "unknown-device"]
        )
        .filter(motion_counts__isnull=False)
        .aggregate(total=Count("motion_counts"))["total"]
        or 0,
        "avg_per_hour": 0,  # Will calculate
        "peak_hour": "--",  # Will calculate
    }

    # Battery and motion data for charts - compute hourly aggregates for last 24 hours
    now = timezone.now()
    battery_hour_labels = []
    battery_hour_values = []
    motion_hour_values = []

    # Build 24 hourly buckets (oldest -> newest)
    for i in range(24):
        bucket_start = (now - timedelta(hours=23 - i)).replace(
            minute=0, second=0, microsecond=0
        )
        bucket_end = bucket_start + timedelta(hours=1)
        label = bucket_start.strftime("%H:00")
        battery_hour_labels.append(label)

        # Average battery voltage in this hour
        agg_batt = (
            SensorReading.objects.exclude(
                device_id__in=["test-device", "unknown-device"]
            )
            .filter(received_at__gte=bucket_start, received_at__lt=bucket_end)
            .aggregate(avg_batt=Avg("battery_voltage"))
        )
        avg_batt = agg_batt.get("avg_batt")
        # Use None for missing values so Chart.js will gap the line
        battery_hour_values.append(float(avg_batt) if avg_batt is not None else None)

        # Sum of motion counts in this hour
        agg_motion = (
            SensorReading.objects.exclude(
                device_id__in=["test-device", "unknown-device"]
            )
            .filter(received_at__gte=bucket_start, received_at__lt=bucket_end)
            .aggregate(sum_motion=Sum("motion_counts"))
        )
        sum_motion = agg_motion.get("sum_motion") or 0
        motion_hour_values.append(int(sum_motion))

    return render(
        request,
        "sensors/analytics.html",
        {
            "total_readings": total_readings,
            "device_count": device_count,
            "avg_interval": avg_interval,
            "today_readings": today_readings,
            "temp_stats": temp_stats,
            "humidity_stats": humidity_stats,
            "daily_data": daily_data,
            "daily_labels": daily_labels,
            "temp_distribution_data": temp_distribution_data,
            "temp_distribution_labels": temp_distribution_labels,
            "battery_stats": battery_stats,
            "motion_stats": motion_stats,
            "heatmap_days": heatmap_days,
            "heatmap_data": heatmap_data,
            # hourly aggregates for improved visuals
            "battery_hour_labels": battery_hour_labels,
            "battery_hour_values": battery_hour_values,
            "motion_hour_values": motion_hour_values,
            "motion_hour_labels": battery_hour_labels,
            # Combined timeseries for analytics
            "temp_series": temp_series,
            "temp_labels": temp_labels,
            "humidity_series": humidity_series,
            "humidity_labels": humidity_labels,
        },
    )


def devices(request: HttpRequest):
    # Get device statistics
    devices_data = []
    # Collect device IDs, normalize and deduplicate to avoid showing the same device multiple times
    raw_device_ids = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .values_list("device_id", flat=True)
        .distinct()
        .order_by("device_id")
    )

    seen = set()
    device_ids = []
    for did in raw_device_ids:
        if did is None:
            continue
        # Normalize by trimming surrounding whitespace
        normalized = did.strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        device_ids.append(normalized)

    for device_id in device_ids:
        device_readings = SensorReading.objects.filter(device_id=device_id)
        latest = device_readings.order_by("-received_at").first()
        last_five_qs = list(device_readings.order_by("-received_at")[:5])
        today_count = device_readings.filter(
            received_at__date=timezone.now().date()
        ).count()

        # Check if device is online (last reading within 2 hours)
        is_online = (
            latest and (timezone.now() - latest.received_at).total_seconds() < 7200
        )

        devices_data.append(
            {
                "device_id": device_id,
                "latest_temp": latest.temperature_c if latest else None,
                "latest_humidity": latest.humidity if latest else None,
                "latest_battery": latest.battery_voltage if latest else None,
                "latest_motion": latest.motion_counts if latest else None,
                "last_seen": latest.received_at if latest else None,
                "is_online": is_online,
                "reading_count": device_readings.count(),
                "today_readings": today_count,
                "last_readings": last_five_qs,
                "avg_interval": 15,  # Will calculate real interval
            }
        )

    total_devices = len(devices_data)
    online_devices = sum(1 for d in devices_data if d["is_online"])
    offline_devices = total_devices - online_devices

    # Total cumulative readings across all devices (exclude test/unknown)
    total_readings = SensorReading.objects.exclude(
        device_id__in=["test-device", "unknown-device"]
    ).count()

    return render(
        request,
        "sensors/devices.html",
        {
            "devices": devices_data,
            "total_devices": total_devices,
            "total_readings": total_readings,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
        },
    )


def history(request: HttpRequest):
    # Get filter parameters
    selected_device = request.GET.get("device", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    export_format = request.GET.get("export", "")

    # Build query - exclude test devices
    query = Q()
    query &= ~Q(device_id__in=["test-device", "unknown-device"])
    if selected_device:
        query &= Q(device_id=selected_device)
    if date_from:
        query &= Q(received_at__date__gte=date_from)
    if date_to:
        query &= Q(received_at__date__lte=date_to)

    readings = SensorReading.objects.filter(query).order_by("-received_at")

    # Handle export
    if export_format == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sensor_readings.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ["Timestamp", "Device", "Temperature", "Humidity", "Battery", "Motion"]
        )
        for reading in readings:
            writer.writerow(
                [
                    reading.received_at,
                    reading.device_id,
                    reading.temperature_c or "",
                    reading.humidity or "",
                    reading.battery_voltage or "",
                    reading.motion_counts or "",
                ]
            )
        return response

    elif export_format == "json":
        data = []
        for reading in readings:
            data.append(
                {
                    "timestamp": reading.received_at.isoformat(),
                    "device_id": reading.device_id,
                    "temperature_c": reading.temperature_c,
                    "humidity": reading.humidity,
                    "battery_voltage": reading.battery_voltage,
                    "motion_counts": reading.motion_counts,
                }
            )
        return JsonResponse(data, safe=False)

    # Pagination
    paginator = Paginator(readings, 50)
    page_number = request.GET.get("page")
    readings = paginator.get_page(page_number)

    # Get device list for filter - exclude test devices
    device_list = (
        SensorReading.objects.exclude(device_id__in=["test-device", "unknown-device"])
        .values_list("device_id", flat=True)
        .distinct()
        .order_by("device_id")
    )

    # Calculate statistics
    total_count = SensorReading.objects.filter(query).count()
    avg_temp = SensorReading.objects.filter(
        query, temperature_c__isnull=False
    ).aggregate(avg=Avg("temperature_c"))["avg"]
    avg_humidity = SensorReading.objects.filter(
        query, humidity__isnull=False
    ).aggregate(avg=Avg("humidity"))["avg"]

    return render(
        request,
        "sensors/history.html",
        {
            "readings": readings,
            "device_list": device_list,
            "selected_device": selected_device,
            "date_from": date_from,
            "date_to": date_to,
            "total_count": total_count,
            "avg_temp": avg_temp or 0,
            "avg_humidity": avg_humidity or 0,
        },
    )


def device_detail(request: HttpRequest, device_id: str):
    device_readings = SensorReading.objects.filter(device_id=device_id).order_by(
        "-received_at"
    )
    latest = device_readings.first()

    return render(
        request,
        "sensors/device_detail.html",
        {
            "device_id": device_id,
            "readings": device_readings[:100],
            "latest": latest,
            "total_readings": device_readings.count(),
        },
    )


@csrf_exempt
def reading_detail(request: HttpRequest, reading_id: int):
    """API endpoint to get reading details"""
    try:
        reading = SensorReading.objects.get(id=reading_id)
        data = {
            "id": reading.id,
            "device_id": reading.device_id,
            "temperature_c": reading.temperature_c,
            "humidity": reading.humidity,
            "battery_voltage": reading.battery_voltage,
            "motion_counts": reading.motion_counts,
            "received_at": reading.received_at.isoformat(),
            "created_at": reading.created_at.isoformat(),
        }
        return JsonResponse(data)
    except SensorReading.DoesNotExist:
        return JsonResponse({"error": "Reading not found"}, status=404)


@csrf_exempt
def fetch_data_endpoint(request: HttpRequest):
    """API endpoint for external cron services to trigger data fetching"""
    if request.method == "POST":
        from django.core.management import call_command
        from io import StringIO
        import sys

        # Capture output
        out = StringIO()
        old_stdout = sys.stdout
        sys.stdout = out

        try:
            call_command("fetch_sensor_data")
            result = out.getvalue()
            return JsonResponse({"status": "success", "message": result})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        finally:
            sys.stdout = old_stdout

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def ingest_reading(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    device_id = payload.get("device_id") or payload.get("end_device_ids", {}).get(
        "device_id"
    )
    received_at_raw = payload.get("received_at") or payload.get("rx_metadata", [{}])[
        0
    ].get("time")

    # Extract fields by expected mapping
    fields = (
        payload.get("uplink_message", {}).get("decoded_payload", {})
        or payload.get("fields", {})
        or payload
    )
    battery_voltage = fields.get("field1") or fields.get("battery_voltage")
    humidity = fields.get("field3") or fields.get("humidity")
    motion_counts = fields.get("field4") or fields.get("motion_counts")
    temperature_c = fields.get("field5") or fields.get("temperature_c")

    # Parse timestamp
    received_at = None
    if isinstance(received_at_raw, str):
        received_at = parse_datetime(received_at_raw)
    if received_at is None:
        from django.utils import timezone

        received_at = timezone.now()

    reading = SensorReading.objects.create(
        device_id=device_id or "unknown-device",
        battery_voltage=battery_voltage,
        humidity=humidity,
        motion_counts=motion_counts,
        temperature_c=temperature_c,
        received_at=received_at,
    )
    return JsonResponse({"id": reading.id})


# Create your views here.
