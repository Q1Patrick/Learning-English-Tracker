"""Isolated tests: no learner database and no paid external requests."""

from .base import *  # noqa: F403

SECRET_KEY = "test-only-key-" + "ab18c50d27ef49a3bdb1f1fbdd09da17" * 2
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
OPENAI_API_KEY = ""
OPENAI_MODEL = ""
AI_FEEDBACK_THROTTLE_RATE = "10000/hour"
LOGGING["root"]["level"] = "WARNING"  # noqa: F405
LOGGING["handlers"]["console"] = {"class": "logging.NullHandler"}  # noqa: F405
