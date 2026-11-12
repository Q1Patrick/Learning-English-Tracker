"""Production fails early when essential configuration is missing."""

import os

from django.core.exceptions import ImproperlyConfigured

from common.environment import env_bool, env_int

from .base import *  # noqa: F403

if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):  # noqa: F405
    raise ImproperlyConfigured("Set a strong DJANGO_SECRET_KEY of at least 50 characters.")
if not os.getenv("DJANGO_ALLOWED_HOSTS") or not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("Set explicit DJANGO_ALLOWED_HOSTS for production.")

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env_int("DJANGO_HSTS_SECONDS", 3600, minimum=1)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", False)  # noqa: F405
SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", False)  # noqa: F405
# Enable only when the proxy strips client-supplied forwarded headers.
if env_bool("DJANGO_TRUST_PROXY_SSL_HEADER", False):  # noqa: F405
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
