"""Kiểm tra QA database đã có; nhận kỳ vọng riêng qua stdin, chỉ in counts/booleans."""

import contextlib
import importlib.util
import io
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path


def read_input():
    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536:
        raise ValueError("Invalid inspection request.")
    payload = json.loads(raw.decode("utf-8"))
    allowed = {"instance", "userId", "expectedEmail", "password"}
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise ValueError("Invalid inspection request.")
    instance = payload.get("instance")
    if not isinstance(instance, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", instance):
        raise ValueError("Invalid inspection request.")
    if "userId" in payload:
        identifier = payload["userId"]
        if isinstance(identifier, bool) or not isinstance(identifier, (str, int)):
            raise ValueError("Invalid inspection request.")
        if not re.fullmatch(r"[1-9][0-9]{0,18}", str(identifier)):
            raise ValueError("Invalid inspection request.")
        identifier = int(identifier)
        if identifier > 9223372036854775807:
            raise ValueError("Invalid inspection request.")
        payload["userId"] = identifier
    elif "expectedEmail" in payload or "password" in payload:
        raise ValueError("Invalid inspection request.")
    if "expectedEmail" in payload:
        email = payload["expectedEmail"]
        if not isinstance(email, str) or not 1 <= len(email.strip()) <= 254:
            raise ValueError("Invalid inspection request.")
    if "password" in payload:
        password = payload["password"]
        if not isinstance(password, str) or not 1 <= len(password) <= 16384:
            raise ValueError("Invalid inspection request.")
    return payload


def existing_database(instance):
    temporary = Path(tempfile.gettempdir()).resolve()
    root = temporary / "learning-english-tracker-fe033-qa"
    directory = root / instance
    database = directory / "auth.sqlite3"
    key_file = directory / "signing-key.txt"
    # Kiểm tra trước khi configure_qa có thể tạo thư mục/key; inspector không tự init dữ liệu.
    for expected in (root, directory, database, key_file):
        if expected.resolve(strict=True) != expected:
            raise ValueError("Invalid QA instance.")
    if not database.is_file() or not key_file.is_file():
        raise ValueError("Invalid QA instance.")
    learner_database = Path(__file__).resolve().parents[2] / "config" / "db.sqlite3"
    if learner_database.exists() and database.samefile(learner_database):
        raise ValueError("Invalid QA instance.")
    return database


def inspect_qa(payload):
    database = existing_database(payload["instance"])
    launcher_path = Path(__file__).resolve().with_name("run-auth-qa.py")
    spec = importlib.util.spec_from_file_location("auth_qa_launcher", launcher_path)
    if spec is None or spec.loader is None:
        raise ValueError("QA configuration unavailable.")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    if launcher.configure_qa(payload["instance"]).resolve() != database:
        raise ValueError("Invalid QA database target.")

    import django

    django.setup()
    from django.conf import settings
    from django.contrib.auth.hashers import check_password, identify_hasher, is_password_usable

    configured = settings.DATABASES["default"]
    if (
        configured["ENGINE"] != "django.db.backends.sqlite3"
        or Path(configured["NAME"]).resolve() != database
    ):
        raise ValueError("Invalid QA database target.")

    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        integrity = connection.execute("PRAGMA integrity_check").fetchall()
        counts = {
            "users": connection.execute("SELECT COUNT(*) FROM accounts_user").fetchone()[0],
            "profiles": connection.execute("SELECT COUNT(*) FROM accounts_userprofile").fetchone()[
                0
            ],
            "usersWithoutProfile": connection.execute(
                "SELECT COUNT(*) FROM accounts_user AS u WHERE NOT EXISTS "
                "(SELECT 1 FROM accounts_userprofile AS p WHERE p.user_id = u.id)"
            ).fetchone()[0],
            "profilesWithoutUser": connection.execute(
                "SELECT COUNT(*) FROM accounts_userprofile AS p WHERE NOT EXISTS "
                "(SELECT 1 FROM accounts_user AS u WHERE u.id = p.user_id)"
            ).fetchone()[0],
        }
        checks = {
            "integrityOk": len(integrity) == 1 and integrity[0][0] == "ok",
            "foreignKeysOk": connection.execute("PRAGMA foreign_key_check").fetchone() is None,
            "allUsersHaveProfiles": counts["usersWithoutProfile"] == 0,
            "allProfilesHaveUsers": counts["profilesWithoutUser"] == 0,
        }
        result = {"counts": counts, "checks": checks}
        if "userId" in payload:
            user = connection.execute(
                "SELECT email, first_name, last_name, is_active, is_staff, is_superuser, "
                "is_email_verified, password FROM accounts_user WHERE id = ?",
                (payload["userId"],),
            ).fetchone()
            profiles = connection.execute(
                "SELECT display_name, english_level, daily_target_minutes, learning_goal, timezone "
                "FROM accounts_userprofile WHERE user_id = ?",
                (payload["userId"],),
            ).fetchall()
            checks["userExists"] = user is not None
            checks["oneLinkedProfile"] = len(profiles) == 1
            if user is not None:
                checks.update(
                    {
                        "emailNormalized": user["email"] == user["email"].strip().lower(),
                        "firstNameEmpty": user["first_name"] == "",
                        "lastNameEmpty": user["last_name"] == "",
                        "isActive": user["is_active"] == 1,
                        "isNotStaff": user["is_staff"] == 0,
                        "isNotSuperuser": user["is_superuser"] == 0,
                        "emailUnverified": user["is_email_verified"] == 0,
                        "passwordUsable": is_password_usable(user["password"]),
                        "passwordPbkdf2": identify_hasher(user["password"]).algorithm
                        == "pbkdf2_sha256",
                    }
                )
                if "expectedEmail" in payload:
                    checks["emailMatchesExpected"] = (
                        user["email"] == payload["expectedEmail"].strip().lower()
                    )
                if "password" in payload:
                    password = payload["password"]
                    # Không truyền setter: kiểm tra mật khẩu không nâng cấp hoặc ghi lại hash.
                    checks["storedPasswordDiffers"] = user["password"] != password
                    checks["passwordMatches"] = check_password(password, user["password"])
                    differs = password != password.strip()
                    result["passwordWhitespaceCheckApplied"] = differs
                    if differs:
                        checks["trimmedPasswordRejected"] = not check_password(
                            password.strip(), user["password"]
                        )
            if len(profiles) == 1:
                profile = profiles[0]
                checks.update(
                    {
                        "displayNameEmpty": profile["display_name"] == "",
                        "englishLevelA1": profile["english_level"] == "A1",
                        "dailyTargetThirty": profile["daily_target_minutes"] == 30,
                        "learningGoalEmpty": profile["learning_goal"] == "",
                        "timezoneDefault": profile["timezone"] == "Asia/Ho_Chi_Minh",
                    }
                )
        result["ok"] = all(checks.values())
        return result
    finally:
        connection.rollback()
        connection.close()


def main():
    try:
        if len(sys.argv) != 1:
            raise ValueError("Use stdin for inspection requests.")
        payload = read_input()
        # Chặn diagnostic của import/config để không làm lộ kỳ vọng riêng từ stdin.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = inspect_qa(payload)
    except Exception:
        result = {"ok": False, "error": "QA inspection failed."}
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
