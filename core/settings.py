"""
Django settings for GreenMind WMS project.
Version: 2.0 (Production-Ready with API, JWT, RBAC)
"""

from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

# ─────────────────────────────────────────────────
# BASE & ENV
# ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# Load biến môi trường từ file .env
load_dotenv(BASE_DIR / ".env")

import sys
# Add apps and engine to python path
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
sys.path.insert(0, os.path.join(BASE_DIR, 'engine'))

# ─────────────────────────────────────────────────
# SECURITY (Đọc từ .env, KHÔNG để cứng trong code)
# ─────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-insecure-key-please-set-env")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
env_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env_csrf_origins.split(",") if env_csrf_origins else ["http://localhost:8000", "http://127.0.0.1:8000"]

# ─────────────────────────────────────────────────
# PRODUCTION SECURITY HEADERS (Strict check)
# ─────────────────────────────────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ─────────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # Nội bộ
    "apps.dashboard",
    "apps.api",
]

# ─────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.security_logging.SecurityLoggingMiddleware", # Security Logging
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "core", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ─────────────────────────────────────────────────
# PASSWORD VALIDATION
# ─────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────────────────────────────────────────────────
# DJANGO REST FRAMEWORK (DRF) CONFIGURATION
# ─────────────────────────────────────────────────
REST_FRAMEWORK = {
    # Mặc định dùng JWT cho mọi API endpoint
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Mặc định bắt buộc xác thực để truy cập API
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # Cấu hình rate limiting chống DDoS/abuse
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "core.throttling.IPBasedThrottle", # Add IP Based Throttle
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",    # Khách vãng lai: 30 req/phút
        "user": "120/minute",   # Người dùng đã xác thực: 120 req/phút
        "ip_anon": "100/hour",   # IP Based: 100 req/giờ
    },
    # Format response mặc định
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ─────────────────────────────────────────────────
# JWT AUTHENTICATION SETTINGS
# ─────────────────────────────────────────────────
JWT_ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 60))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7))

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=JWT_REFRESH_DAYS),
    "ROTATE_REFRESH_TOKENS": True,      # Tự động xoay vòng refresh token
    "BLACKLIST_AFTER_ROTATION": True,   # Vô hiệu hóa token cũ sau khi xoay
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
}

# ─────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing)
# ─────────────────────────────────────────────────
# Cho phép các frontend khác (React, Vue...) gọi API
# Avoid CORS_ALLOW_ALL_ORIGINS even in DEBUG if possible, 
# or at least make it configurable.
env_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS")
if env_cors_origins:
    CORS_ALLOWED_ORIGINS = env_cors_origins.split(",")
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",  # React
        "http://localhost:8080",  # Vue
    ]

if DEBUG and not env_cors_origins:
    # Fallback for development if no env var set
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False

# ─────────────────────────────────────────────────
# RBAC - CUSTOM USER ROLES (Lưu trong DB thông qua Profile)
# ─────────────────────────────────────────────────
# Role được quản lý qua Django's Group System:
# - 'Admin'   : Toàn quyền (Thêm/Sửa/Xóa catalog, chạy simulator)
# - 'Manager' : Chỉ xem dashboard, monitoring, esg reports
# - 'Viewer'  : Chỉ xem báo cáo ESG công khai

# ─────────────────────────────────────────────────
# INTERNATIONALIZATION
# ─────────────────────────────────────────────────
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ─────────────────────────────────────────────────
# AUTHENTICATION REDIRECTS
# ─────────────────────────────────────────────────
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────
# LOGGING CONFIGURATION
# ─────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'security.log'),
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
