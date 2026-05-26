from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Dashboard (Web UI)
    path("", include("apps.dashboard.urls")),
    # Public REST API v1
    path("api/v1/", include("apps.api.urls")),
]

# ─── Enterprise AI Error Handlers ───
handler404 = "apps.dashboard.views.error_404_view"
handler500 = "apps.dashboard.views.error_500_view"
