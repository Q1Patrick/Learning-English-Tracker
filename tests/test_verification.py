"""Pre-commit checks use temporary repos and disposable database copies only."""

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from scripts import verify


class GitHygieneTests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tracker-git-test-")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.root_patch = patch.object(verify, "ROOT", self.repo)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.git("init", "--quiet")

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)
        return path

    def test_clean_index_and_environment_example_are_allowed(self):
        self.write("README.md", "Project setup\n")
        self.write(".env.example", "OPENAI_API_KEY=\n")
        self.git("add", "README.md", ".env.example")
        verify.git_hygiene(staged=True)

    def test_staged_secret_is_detected_even_when_working_file_is_clean(self):
        secret = "sk-" + "private" * 6
        self.write("settings.py", f'API_KEY = "{secret}"\n')
        self.git("add", "settings.py")
        self.write("settings.py", 'API_KEY = ""\n')
        with self.assertRaisesRegex(RuntimeError, "settings.py") as error:
            verify.git_hygiene(staged=True)
        self.assertNotIn(secret, str(error.exception))

    def test_private_key_is_detected_without_echoing_contents(self):
        for key_type in ("", "RSA ", "EC ", "OPENSSH ", "ENCRYPTED "):
            with self.subTest(key_type=key_type):
                marker = "-----BEGIN " + key_type + "PRIVATE KEY-----"
                self.write("credentials.txt", marker + "\nprivate fixture material\n")
                self.git("add", "credentials.txt")
                with self.assertRaisesRegex(RuntimeError, "credentials.txt") as error:
                    verify.git_hygiene(staged=True)
                self.assertNotIn("private fixture material", str(error.exception))

    def test_force_staged_ignored_environment_file_is_rejected(self):
        self.write(".gitignore", ".env\n")
        self.write(".env", "EXAMPLE=value\n")
        self.git("add", ".gitignore")
        self.git("add", "--force", ".env")
        with self.assertRaisesRegex(RuntimeError, r"\.env"):
            verify.git_hygiene(staged=True)

    def test_generated_database_path_is_rejected(self):
        self.write("data.sqlite3", b"SQLite format 3\0")
        self.git("add", "data.sqlite3")
        with self.assertRaisesRegex(RuntimeError, "data.sqlite3"):
            verify.git_hygiene(staged=True)

    def test_partial_staging_is_rejected(self):
        self.write("README.md", "Old safe content\n")
        self.git("add", "README.md")
        self.write("README.md", "New safe content\n")
        with self.assertRaisesRegex(RuntimeError, "Unstaged changes"):
            verify.git_hygiene(staged=True)

    def test_untracked_files_must_be_reviewed_before_staged_check(self):
        self.write("README.md", "Safe content\n")
        self.git("add", "README.md")
        self.write("new_feature.py", "enabled = True\n")
        with self.assertRaisesRegex(RuntimeError, "Untracked files"):
            verify.git_hygiene(staged=True)

    def test_working_tree_check_scans_untracked_source(self):
        secret = "sk-" + "sensitive" * 5
        self.write("new_settings.py", f'API_KEY = "{secret}"\n')
        with self.assertRaisesRegex(RuntimeError, "new_settings.py"):
            verify.git_hygiene()

    def test_whitespace_check_never_echoes_staged_secret(self):
        secret = "sk-" + "private" * 6
        self.write("settings.py", f'API_KEY = "{secret}"  \n')
        self.git("add", "settings.py")
        code = (
            "from pathlib import Path; from scripts import verify; "
            f"verify.ROOT = Path({str(self.repo)!r}); verify.git_hygiene(staged=True)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parent.parent,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_staged_scanner_supports_safe_binary_assets(self):
        self.write("asset.png", b"\x89PNG\x00\xff\xfe")
        self.git("add", "asset.png")
        verify.git_hygiene(staged=True)

    def test_binary_asset_containing_ascii_secret_is_still_rejected(self):
        secret = ("sk-" + "private" * 6).encode()
        self.write("asset.png", b"\x89PNG\x00" + secret + b"\xff")
        self.git("add", "asset.png")
        with self.assertRaisesRegex(RuntimeError, "asset.png"):
            verify.git_hygiene(staged=True)


class DatabaseVerificationTests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tracker-db-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.source = self.directory / "learner.sqlite3"
        with sqlite3.connect(self.source) as connection:
            connection.execute("CREATE TABLE learning_fixture (id INTEGER PRIMARY KEY, notes TEXT)")
            connection.execute("INSERT INTO learning_fixture(notes) VALUES ('private lesson')")

    def test_inspection_is_read_only_and_counts_learner_tables(self):
        with sqlite3.connect(self.source) as connection:
            connection.execute("CREATE TABLE infrastructure (id INTEGER)")
        before = self.source.read_bytes()
        self.assertEqual(verify.inspect_database(self.source), {"learning_fixture": 1})
        self.assertEqual(self.source.read_bytes(), before)

    def test_missing_source_is_not_created(self):
        missing = self.directory / "does-not-exist.sqlite3"
        with self.assertRaises(sqlite3.OperationalError):
            verify.inspect_database(missing)
        self.assertFalse(missing.exists())

    def test_database_copy_migrations_never_modify_original(self):
        original = self.source.read_bytes()
        destination = self.directory / "copy.sqlite3"
        calls = []

        def fake_migration(*args, env):
            calls.append((args, env))
            self.assertEqual(Path(env["DATABASE_PATH"]), destination)
            if args[1] == "migrate" and "--check" not in args:
                with sqlite3.connect(env["DATABASE_PATH"]) as connection:
                    connection.execute("CREATE TABLE quizzes_new_table (id INTEGER)")

        with patch.object(verify, "python", side_effect=fake_migration):
            verify.migration_check(
                destination, {"DATABASE_PATH": str(self.source)}, existing=self.source
            )
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(verify.inspect_database(destination)["learning_fixture"], 1)
        self.assertEqual(len(calls), 2)

    def test_row_loss_in_copy_is_rejected_and_original_survives(self):
        original = self.source.read_bytes()
        destination = self.directory / "lossy.sqlite3"

        def destructive_migration(*args, env):
            if args[1] == "migrate" and "--check" not in args:
                with sqlite3.connect(env["DATABASE_PATH"]) as connection:
                    connection.execute("DELETE FROM learning_fixture")

        with patch.object(verify, "python", side_effect=destructive_migration):
            with self.assertRaisesRegex(RuntimeError, "row counts"):
                verify.migration_check(destination, {}, existing=self.source)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(verify.inspect_database(self.source)["learning_fixture"], 1)

    def test_foreign_key_violations_are_detected(self):
        with sqlite3.connect(self.source) as connection:
            connection.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
            connection.execute("CREATE TABLE child (parent_id INTEGER REFERENCES parent(id))")
            connection.execute("INSERT INTO child VALUES (42)")
        with self.assertRaisesRegex(RuntimeError, "foreign-key"):
            verify.inspect_database(self.source)
