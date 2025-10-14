# 🕐 Railway Cron Service Setup

## Step-by-Step Instructions

### 1. Create Cron Service in Railway

1. **Go to your Railway project dashboard**
2. **Click "New Service"**
3. **Select "Empty Service"**
4. **Connect to the same GitHub repository**
5. **Go to Settings → Service Type → Select "Cron"**

### 2. Configure Cron Job

**Command:** `python manage.py fetch_sensor_data`
**Schedule:** `*/10 * * * *` (every 10 minutes)

### 3. Set Environment Variables

Add these to your Cron service:

- `DJANGO_SECRET_KEY` = `ouqefi^)_vh@y*71slrb)ha-_)%m(m!fbfiax5yqnwj=#ckgo@`
- `DEBUG` = `False`
- `DATABASE_URL` = `sqlite:///db.sqlite3`

### 4. Deploy and Monitor

- The cron service will run every 10 minutes
- Check logs to see data fetching activity
- Monitor your dashboard for new readings

## Alternative: External Cron Service

If Railway cron doesn't work, use [cron-job.org](https://cron-job.org):

1. **Create free account**
2. **Add new cron job**
3. **URL:** `https://your-app-name.up.railway.app/api/fetch-data/`
4. **Schedule:** Every 10 minutes
5. **Create the API endpoint** (see below)

## Create API Endpoint for External Cron

Add this to your `sensors/views.py`:

```python
@csrf_exempt
def fetch_data_endpoint(request):
    """API endpoint for external cron services"""
    if request.method == "POST":
        from django.core.management import call_command
        from io import StringIO
        import sys

        # Capture output
        out = StringIO()
        sys.stdout = out

        try:
            call_command('fetch_sensor_data')
            result = out.getvalue()
            return JsonResponse({
                'status': 'success',
                'message': result
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        finally:
            sys.stdout = sys.__stdout__

    return JsonResponse({'error': 'Method not allowed'}, status=405)
```

And add to `sensors/urls.py`:

```python
path("api/fetch-data/", views.fetch_data_endpoint, name="fetch_data"),
```
