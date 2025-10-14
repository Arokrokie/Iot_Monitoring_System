web: python manage.py migrate && gunicorn iot_dashboard.wsgi:application --bind 0.0.0.0:$PORT
worker: python manage.py run_mqtt
