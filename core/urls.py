from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """Health check endpoint for Docker & load balancers."""
    return JsonResponse({
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "service": "greenmind-ai",
        "version": "3.0",
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check (for Docker/Nginx)
    path("health/", health_check, name="health_check"),
    # Dashboard (Web UI)
    path("", include("apps.dashboard.urls")),
    # Public REST API v1
    path("api/v1/", include("apps.api.urls")),
]

# ─── Error Handlers ───
handler404 = "apps.dashboard.views.error_404_view"
handler500 = "apps.dashboard.views.error_500_view"
