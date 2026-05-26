"""
GreenMind Public API - v1
Module: URL Routing
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from .views import (
    # Auth
    RegisterView, MyProfileView,
    # Forecast
    ForecastView, ForecastCompareView, RecommendView,
    # Inventory
    InventoryView, InventoryTransactView,
    # ESG & Catalog
    ESGView, CatalogView,
    # Worker
    WorkerRunView,
    # Core
    ApiIndexView, AuditLogView,
)

urlpatterns = [
    # ─── API Index ────────────────────────────────────────────────────────────
    path("",                        ApiIndexView.as_view(),         name="api-index"),

    # ─── Authentication ───────────────────────────────────────────────────────
    path("auth/register/",          RegisterView.as_view(),         name="api-register"),
    path("auth/profile/",           MyProfileView.as_view(),        name="api-profile"),
    path("auth/token/",             TokenObtainPairView.as_view(),  name="api-token-obtain"),
    path("auth/token/refresh/",     TokenRefreshView.as_view(),     name="api-token-refresh"),
    path("auth/token/blacklist/",   TokenBlacklistView.as_view(),   name="api-token-blacklist"),

    # ─── Forecast / AI ───────────────────────────────────────────────────────
    path("forecast/",               ForecastView.as_view(),         name="api-forecast"),
    path("forecast/compare/",       ForecastCompareView.as_view(),  name="api-forecast-compare"),
    path("forecast/recommend/",     RecommendView.as_view(),        name="api-recommend"),

    # ─── Inventory ───────────────────────────────────────────────────────────
    path("inventory/",              InventoryView.as_view(),        name="api-inventory"),
    path("inventory/transact/",     InventoryTransactView.as_view(),name="api-inventory-transact"),

    # ─── Catalog & ESG ───────────────────────────────────────────────────────
    path("catalog/",                CatalogView.as_view(),          name="api-catalog"),
    path("esg/",                    ESGView.as_view(),              name="api-esg"),

    # ─── E2E Worker ──────────────────────────────────────────────────────────
    path("worker/run/",             WorkerRunView.as_view(),        name="api-worker-run"),
    
    # ─── Security Audit ──────────────────────────────────────────────────────
    path("audit/",                  AuditLogView.as_view(),         name="api-audit"),
]
