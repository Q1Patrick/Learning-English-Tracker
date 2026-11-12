"""Configuration validation without touching the user's database or secrets."""

import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from common.environment import env_bool, env_int

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class EnvironmentParserTests(SimpleTestCase):
    def test_boolean_accepts_explicit_true_and_false_values(self):
        for value in ("true", "TRUE", "1", "yes"):
            with self.subTest(value=value), patch.dict(os.environ, {"TEST_FLAG": value}):
                self.assertTrue(env_bool("TEST_FLAG", False))
        for value in ("false", "FALSE", "0", "no"):
            with self.subTest(value=value), patch.dict(os.environ, {"TEST_FLAG": value}):
                self.assertFalse(env_bool("TEST_FLAG", True))

    def test_missing_values_use_explicit_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(env_bool("TEST_FLAG", True))
            self.assertEqual(env_int("TEST_LIMIT", 12), 12)

    def test_boolean_typo_fails_instead_of_enabling_a_feature(self):
        with patch.dict(os.environ, {"TEST_FLAG": "treu"}):
            with self.assertRaises(ImproperlyConfigured):
                env_bool("TEST_FLAG", False)

    def test_integer_minimum_rejects_negative_limits(self):
        with patch.dict(os.environ, {"TEST_LIMIT": "-1"}):
            with self.assertRaises(ImproperlyConfigured):
                env_int("TEST_LIMIT", 12, minimum=0)

    def test_integer_typo_fails_with_safe_configuration_error(self):
        with patch.dict(os.environ, {"TEST_LIMIT": "not-a-number"}):
            with self.assertRaises(ImproperlyConfigured):
                env_int("TEST_LIMIT", 12)


class ProductionConfigurationTests(SimpleTestCase):
    def production_environment(self):
        # Remove task/app configuration inherited from the test process. Values
        # used below belong only to this subprocess and never configure live DBs.
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("DJANGO_", "OPENAI_", "SECURE_", "AI_FEEDBACK_"))
            and key != "DATABASE_PATH"
        }
        environment.update(
            {
                "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
                "DJANGO_ALLOWED_HOSTS": "example.test,api.example.test",
                "DJANGO_SETTINGS_MODULE": "config.settings.production",
            }
        )
        return environment

    def run_settings(self, environment):
        code = """
import json
from pathlib import Path
from config.settings import production as settings
print(json.dumps({
    'debug': settings.DEBUG,
    'allowed_hosts': settings.ALLOWED_HOSTS,
    'database': str(settings.DATABASES['default']['NAME']),
    'ssl_redirect': settings.SECURE_SSL_REDIRECT,
    'session_secure': settings.SESSION_COOKIE_SECURE,
    'csrf_secure': settings.CSRF_COOKIE_SECURE,
    'hsts_seconds': settings.SECURE_HSTS_SECONDS,
}))
"""
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=PROJECT_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )

    def test_production_rejects_missing_secret_key(self):
        environment = self.production_environment()
        environment.pop("DJANGO_SECRET_KEY")
        result = self.run_settings(environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_production_rejects_short_secret_without_echoing_it(self):
        environment = self.production_environment()
        secret = "short-private-value"
        environment["DJANGO_SECRET_KEY"] = secret
        result = self.run_settings(environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stderr + result.stdout)

    def test_production_requires_explicit_allowed_hosts(self):
        environment = self.production_environment()
        secret = environment["DJANGO_SECRET_KEY"]
        environment.pop("DJANGO_ALLOWED_HOSTS")
        result = self.run_settings(environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)
        self.assertNotIn(secret, result.stderr + result.stdout)

    def test_production_rejects_empty_host_list_after_parsing(self):
        environment = self.production_environment()
        environment["DJANGO_ALLOWED_HOSTS"] = " ,  "
        result = self.run_settings(environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_production_enables_secure_defaults_and_preserves_database_location(self):
        environment = self.production_environment()
        secret = environment["DJANGO_SECRET_KEY"]
        result = self.run_settings(environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(secret, result.stdout + result.stderr)
        config = json.loads(result.stdout)
        self.assertFalse(config["debug"])
        self.assertEqual(config["allowed_hosts"], ["example.test", "api.example.test"])
        self.assertEqual(Path(config["database"]), PROJECT_ROOT / "config" / "db.sqlite3")
        self.assertTrue(config["ssl_redirect"])
        self.assertTrue(config["session_secure"])
        self.assertTrue(config["csrf_secure"])
        self.assertGreater(config["hsts_seconds"], 0)
