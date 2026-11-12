"""Read-only pre-commit checks; all migrations run on disposable database copies."""

import argparse
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, env=None, capture=False):
    result = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout if capture else None


def python(*args, env=None):
    run(sys.executable, *args, env=env)


def git_hygiene(*, staged=False):
    run("git", "diff", "--check", capture=True)
    run("git", "diff", "--cached", "--check", capture=True)
    args = ["git", "ls-files", "--cached", "-z"]
    if not staged:
        args += ["--others", "--exclude-standard"]
    paths = run(*args, capture=True).split("\0")
    problems = []
    for name in set(paths):
        if not name:
            continue
        path = ROOT / name
        if not staged and not path.is_file():
            continue  # A tracked file removed from the working tree will be deleted by git add -u.
        parts = Path(name).parts
        if (
            (Path(name).name.startswith(".env") and Path(name).name != ".env.example")
            or name.endswith((".sqlite3", ".sqlite3.backup", ".db"))
            or any(part in {"venv", ".venv", "__pycache__"} for part in parts)
        ):
            problems.append(name)
            continue
        # Scan index bytes as well as source bytes when verifying an imminent commit.
        data = (
            run("git", "show", f":{name}", capture=True)
            if staged
            else path.read_text(errors="replace")
        )
        if re.search(
            r"sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----",
            data,
        ):
            problems.append(name)
    if problems:
        raise RuntimeError(
            "Review sensitive/generated paths before commit: " + ", ".join(sorted(set(problems)))
        )
    if staged:
        # The tests exercise the working tree. Require it to match the index so
        # the verified code is exactly the code about to be committed.
        if run("git", "diff", "--name-only", capture=True).strip():
            raise RuntimeError("Unstaged changes remain; review/stage them and rerun --staged.")
        untracked = run("git", "ls-files", "--others", "--exclude-standard", capture=True).strip()
        if untracked:
            raise RuntimeError("Untracked files remain; review/stage/ignore them before --staged.")


def inspect_database(path):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLite integrity check failed.")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise RuntimeError("SQLite foreign-key check failed.")
        tables = [
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
        return {
            table: connection.execute(
                'SELECT COUNT(*) FROM "' + table.replace('"', '""') + '"'
            ).fetchone()[0]
            for table in tables
            if table.startswith(
                ("accounts_", "learning_", "goals_", "vocabulary_", "ai_feedback_", "quizzes_")
            )
        }


def migration_check(path, env, *, existing=None):
    env = {
        **env,
        "DJANGO_SETTINGS_MODULE": "config.settings.development",
        "DATABASE_PATH": str(path),
    }
    before = None
    if existing is not None:
        source = existing.resolve()
        if not source.is_file():
            raise RuntimeError(f"Database not found: {source}")
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as original:
            with sqlite3.connect(path) as copy:
                original.backup(copy)
        before = inspect_database(path)
    python("manage.py", "migrate", "--noinput", env=env)
    python("manage.py", "migrate", "--check", env=env)
    after = inspect_database(path)
    if before is not None and any(after.get(table) != count for table, count in before.items()):
        raise RuntimeError(
            "Migration changed existing learner row counts; investigate before applying."
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-copy",
        type=Path,
        help="Also test migrations on a read-only backup of this SQLite database.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Require index/working tree parity and scan the exact staged content.",
    )
    args = parser.parse_args()
    print("Checking Git hygiene, dependencies, lint and formatting...", flush=True)
    git_hygiene(staged=args.staged)
    python("-m", "pip", "check")
    python("-m", "ruff", "check", ".")
    python("-m", "ruff", "format", "--check", ".")
    with tempfile.TemporaryDirectory(prefix="english-tracker-check-") as temporary:
        temporary = Path(temporary)
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings.test",
            "DJANGO_LOG_LEVEL": "WARNING",
            "OPENAI_API_KEY": "",
            "OPENAI_MODEL": "",
            "COVERAGE_FILE": str(temporary / ".coverage"),
        }
        python("manage.py", "check", env=env)
        python("manage.py", "makemigrations", "--check", "--dry-run", env=env)
        python("-m", "coverage", "run", "manage.py", "test", "--noinput", env=env)
        python("-m", "coverage", "report", env=env)
        print("Testing migrations on a fresh, disposable SQLite database...", flush=True)
        migration_check(temporary / "fresh.sqlite3", env)
        if args.database_copy:
            print("Testing migrations on a disposable copy of the learner database...", flush=True)
            migration_check(temporary / "upgrade.sqlite3", env, existing=args.database_copy)
        # Exercise production settings with synthetic credentials/hosts, not user secrets.
        # HSTS flags are tested here only; live defaults remain conservative.
        deployment_env = {
            **env,
            "DJANGO_SETTINGS_MODULE": "config.settings.production",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
            "DJANGO_ALLOWED_HOSTS": "verification.example.invalid",
            "DJANGO_HSTS_INCLUDE_SUBDOMAINS": "true",
            "DJANGO_HSTS_PRELOAD": "true",
            "DATABASE_PATH": str(temporary / "production.sqlite3"),
        }
        python("manage.py", "check", "--deploy", "--fail-level", "WARNING", env=deployment_env)
        python(
            "-c",
            "import config.wsgi, config.asgi; print('Production WSGI/ASGI imports passed.')",
            env=deployment_env,
        )
    print(
        "PASS: all checks passed. Learner database untouched; no commit, push, or paid AI call made."
    )


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError, sqlite3.Error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
