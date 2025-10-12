from django.urls import path
from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analytics/", views.analytics, name="analytics"),
    path("devices/", views.devices, name="devices"),
    path("history/", views.history, name="history"),
    path("device/<str:device_id>/", views.device_detail, name="device_detail"),
    path("api/ingest/", views.ingest_reading, name="ingest_reading"),
    path("api/reading/<int:reading_id>/", views.reading_detail, name="reading_detail"),
]
