"""Small retry boundary for operations safe to repeat after a SQLite rollback."""

import time

from django.db import OperationalError, connections


def retry_sqlite_locked(operation, *, using="default", attempts=6, initial_delay=0.01):
    """Retry only SQLite busy/locked errors outside a surviving transaction.

    The callable must own its transaction and roll it back before raising, and
    must be safe to repeat. In particular, provider calls must never be inside
    this callable. Default delays total 0.31 seconds; the final error is raised.
    """
    if attempts < 1 or initial_delay < 0:
        raise ValueError("Retry attempts must be positive and delay non-negative.")
    for attempt in range(attempts):
        try:
            return operation()
        except OperationalError as exc:
            connection = connections[using]
            message = str(exc).lower()
            locked = message.startswith(
                ("database is locked", "database table is locked", "database schema is locked")
            )
            if (
                connection.vendor != "sqlite"
                or connection.in_atomic_block
                or not locked
                or attempt == attempts - 1
            ):
                raise
            time.sleep(initial_delay * (2**attempt))
