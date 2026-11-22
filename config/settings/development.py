"""Local development: export .env variables before running manage.py."""

from django.core.management.utils import get_random_secret_key

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = SECRET_KEY or get_random_secret_key()  # noqa: F405
# HTTP localhost cần cookie không Secure; production luôn bật cả hai cờ.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
