"""Explicit health checks; avoid leaking provider/database metadata."""
from django.db import connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok", "service": "anima-api"})


def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})
