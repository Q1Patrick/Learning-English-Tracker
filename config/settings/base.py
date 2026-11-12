"""Shared settings; environment-specific behavior lives in development/test/production."""

import os
from datetime import timedelta
from pathlib import Path

from common.environment import env_int

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.accounts.apps.AccountsConfig",
    "apps.learning.apps.LearningConfig",
    "apps.goals.apps.GoalsConfig",
    "apps.statistic.apps.StatisticsConfig",
    "apps.vocabulary.apps.VocabularyConfig",
    "apps.ai_feedback.apps.AIFeedbackConfig",
    "apps.quizzes.apps.QuizzesConfig",
]
AUTH_USER_MODEL = "accounts.User"
MIDDLEWARE = [
    "common.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Preserve the learner database at its existing location after correcting BASE_DIR.
database_path = os.getenv("DATABASE_PATH", str(BASE_DIR / "config" / "db.sqlite3"))
if database_path != ":memory:" and not Path(database_path).is_absolute():
    database_path = str(BASE_DIR / database_path)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": database_path,
        "OPTIONS": {"timeout": 20},
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Choose an available model explicitly; there is no hidden account-specific default.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
OPENAI_TIMEOUT_SECONDS = env_int("OPENAI_TIMEOUT_SECONDS", 30, minimum=1)
OPENAI_MAX_RETRIES = env_int("OPENAI_MAX_RETRIES", 0, minimum=0)
AI_FEEDBACK_THROTTLE_RATE = os.getenv("AI_FEEDBACK_THROTTLE_RATE", "10/hour")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_context": {"()": "common.logging.RequestContextFilter"}},
    "formatters": {
        "safe": {
            "()": "common.logging.PrivateTracebackFormatter",
            "format": "%(levelname)s %(asctime)s %(name)s request_id=%(request_id)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_context"],
            "formatter": "safe",
        }
    },
    "root": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {
        "django": {"handlers": [], "propagate": True, "level": "INFO"},
        "django.server": {"handlers": [], "propagate": True, "level": "WARNING"},
        "httpx": {"handlers": [], "propagate": True, "level": "WARNING"},
        "openai": {"handlers": [], "propagate": True, "level": "WARNING"},
    },
}
