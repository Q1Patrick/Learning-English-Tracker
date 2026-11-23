"""Chạy Django thật với SQLite QA riêng, giữ lại schema/tài khoản qua lần khởi động."""

import argparse
import os
import re
import secrets
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def configure_qa(instance="manual", frontend_origin="http://127.0.0.1:5173"):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", instance):
        raise ValueError("Tên QA instance chỉ nhận chữ, số, dấu gạch ngang/gạch dưới.")
    # Vite changeOrigin đổi Host phía Django; khai báo đúng origin browser để CSRF kiểm tra được.
    # QA chỉ cho loopback, không mở wildcard hoặc tin origin từ request người dùng.
    origin = urlsplit(frontend_origin)
    if (
        origin.scheme != "http"
        or origin.hostname not in {"localhost", "127.0.0.1"}
        or origin.username
        or origin.password
        or origin.path not in {"", "/"}
        or origin.query
        or origin.fragment
    ):
        raise ValueError("Frontend QA origin phải là HTTP loopback, không path/query/credentials.")
    if origin.port is not None and not 1 <= origin.port <= 65535:
        raise ValueError("Frontend QA port không hợp lệ.")

    project = Path(__file__).resolve().parents[2]
    root = Path(tempfile.gettempdir()).resolve() / "learning-english-tracker-fe033-qa"
    if root.exists() and root.resolve() != root:
        raise ValueError("Không dùng thư mục QA bị chuyển hướng ra ngoài Temp.")
    directory = (root / instance).resolve()
    database = (directory / "auth.sqlite3").resolve()
    if not directory.is_relative_to(root) or not database.is_relative_to(root):
        raise ValueError("Database QA phải nằm trong thư mục Temp riêng của FE-03.3.")
    if database == (project / "config" / "db.sqlite3").resolve():
        raise ValueError("Không được dùng learner database cho kiểm thử QA.")
    directory.mkdir(parents=True, exist_ok=True)
    key_file = directory / "signing-key.txt"
    if not key_file.resolve().is_relative_to(directory):
        raise ValueError("QA signing key phải nằm trong thư mục instance đã kiểm tra.")
    if not key_file.exists():
        # Key mới chỉ ở Temp, không đưa vào Git/argv/log; giữ ổn định giữa các lần chạy.
        with key_file.open("x", encoding="utf-8") as stream:
            stream.write(secrets.token_urlsafe(64))

    sys.path.insert(0, str(project))
    os.environ.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.development",
            "DATABASE_PATH": str(database),
            "DJANGO_SECRET_KEY": key_file.read_text(encoding="utf-8").strip(),
            "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
            "DJANGO_CSRF_TRUSTED_ORIGINS": frontend_origin.rstrip("/"),
            "OPENAI_API_KEY": "",
            "OPENAI_MODEL": "",
        }
    )
    return database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", default="manual")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--frontend-origin",
        default="http://127.0.0.1:5173",
        help="Origin Vite/browser được phép gửi CSRF, chỉ HTTP loopback",
    )
    parser.add_argument(
        "--session-idle-seconds",
        type=int,
        help="Thời hạn không hoạt động cho phiên QA không chọn Remember me (1–300 giây)",
    )
    parser.add_argument(
        "--init", action="store_true", help="Áp dụng migrations có sẵn vào database QA"
    )
    parser.add_argument("--check-only", action="store_true", help="Kiểm tra schema rồi thoát")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port phải trong khoảng1–65535.")
    if args.session_idle_seconds is not None:
        if args.instance == "manual" or not 1 <= args.session_idle_seconds <= 300:
            parser.error("Thời hạn QA 1–300 giây yêu cầu --instance khác manual.")

    database = configure_qa(args.instance, args.frontend_origin)
    if not database.exists() and not args.init:
        parser.error("QA database chưa có. Chạy lại với --init cho lần đầu.")

    import django

    django.setup()
    from django.conf import settings
    from django.core.management import call_command

    # Xác nhận target trước migration; settings.test không phù hợp vì database chỉ ở RAM.
    if Path(settings.DATABASES["default"]["NAME"]).resolve() != database:
        raise SystemExit("Database target không khớp QA path; không chạy migration.")
    if args.init:
        call_command("migrate", interactive=False, verbosity=0)
    call_command("migrate", "--check", verbosity=0)
    call_command("check", verbosity=1)
    if args.check_only:
        print("QA schema ready; no learner database changed.")
        return
    print("Using isolated QA database. No demo data or accounts are seeded.")
    if args.session_idle_seconds is not None:
        # Chỉ áp dụng cho tiến trình QA này; Django settings của ứng dụng giữ nguyên.
        settings.APP_SESSION_IDLE_SECONDS = args.session_idle_seconds
        print(f"QA idle timeout without Remember me: {args.session_idle_seconds}s.")
    call_command("runserver", f"127.0.0.1:{args.port}", use_reloader=False)


if __name__ == "__main__":
    main()
