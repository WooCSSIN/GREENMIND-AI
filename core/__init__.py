"""
GreenMind Core Package
"""

# Load Celery app when Django starts (required for @shared_task)
from .celery import app as celery_app

__all__ = ("celery_app",)
