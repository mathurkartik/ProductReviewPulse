"""SQLite schema, helpers, and run-lifecycle utilities."""

from __future__ import annotations

import contextlib
import hashlib
import sqlite3
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

# IST = UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# Deterministic identifiers
# ---------------------------------------------------------------------------


def make_run_id(product_key: str, iso_week: str) -> str:
    """sha1(product_key + iso_week) — stable, collision-safe run identifier."""
    return hashlib.sha1(f"{product_key}{iso_week}".encode()).hexdigest()


def current_iso_week(tz: timezone = IST) -> str:
    """Return the current ISO week string, e.g. '2026-W17', IST-aware."""
    now = datetime.now(tz=tz)
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def parse_iso_week(iso_week: str) -> tuple[int, int]:
    """Parse '2026-W17' -> (year=2026, week=17).

    Raises ValueError on bad format.
    """
    parts = iso_week.split("-W")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError(f"Invalid ISO week format: {iso_week!r}. Expected 'YYYY-WNN'.")
    return int(parts[0]), int(parts[1])


def iso_week_from_parts(year: int, week: int) -> str:
    return f"{year}-W{week:02d}"


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS products (
    key          TEXT PRIMARY KEY,
    display      TEXT NOT NULL,
    appstore_id  TEXT,
    play_package TEXT,
    gdoc_id      TEXT,
    gmail_to     TEXT
);

CREATE TABLE IF NOT EXISTS reviews (
    id          TEXT PRIMARY KEY,
    product_key TEXT REFERENCES products(key),
    source      TEXT NOT NULL CHECK(source IN ('appstore', 'playstore')),
    external_id TEXT NOT NULL,
    body        TEXT NOT NULL,
    rating      INTEGER,
    title       TEXT,
    posted_at   DATETIME NOT NULL,
    version     TEXT,
    language    TEXT,
    country     TEXT,
    ingested_at DATETIME NOT NULL,
    raw_json    TEXT
);

CREATE TABLE IF NOT EXISTS review_embeddings (
    review_id TEXT PRIMARY KEY REFERENCES reviews(id),
    embedding BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id               TEXT PRIMARY KEY,
    product_key      TEXT REFERENCES products(key),
    iso_week         TEXT NOT NULL,
    window_start     DATE NOT NULL,
    window_end       DATE NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending',
    metrics_json     TEXT,
    gdoc_heading_id  TEXT,
    gmail_message_id TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS themes (
    id                             TEXT PRIMARY KEY,
    run_id                         TEXT REFERENCES runs(id),
    rank                           INTEGER NOT NULL,
    label                          TEXT NOT NULL,
    description                    TEXT NOT NULL,
    sentiment                      TEXT NOT NULL,
    review_count                   INTEGER NOT NULL,
    representative_review_ids_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clusters (
    id               TEXT PRIMARY KEY,
    run_id           TEXT REFERENCES runs(id),
    review_ids_json  TEXT NOT NULL,
    keyphrases_json  TEXT NOT NULL,
    medoid_review_id TEXT REFERENCES reviews(id)
);
"""

_EXPECTED_TABLES = frozenset(
    {"products", "reviews", "review_embeddings", "runs", "themes", "clusters"}
)


# ---------------------------------------------------------------------------
# Connection + init
# ---------------------------------------------------------------------------


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    """Create (or upgrade) all tables. Safe to call multiple times."""
    with contextlib.closing(get_connection(db_path)) as conn:
        conn.executescript(_SCHEMA_SQL)


def get_tables(db_path: Path) -> list[str]:
    """Return list of table names in the database."""
    with contextlib.closing(get_connection(db_path)) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return [r["name"] for r in rows]


# ---------------------------------------------------------------------------
# Run lifecycle helpers
# ---------------------------------------------------------------------------

_now_utc = lambda: datetime.now(UTC).isoformat()  # noqa: E731


def upsert_product(
    db_path: Path,
    *,
    key: str,
    display: str,
    appstore_id: str | None = None,
    play_package: str | None = None,
    gmail_to: str | None = None,
) -> None:
    """Insert or update product metadata."""
    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO products (key, display, appstore_id, play_package, gmail_to)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    display=excluded.display,
                    appstore_id=excluded.appstore_id,
                    play_package=excluded.play_package,
                    gmail_to=excluded.gmail_to
                """,
                (key, display, appstore_id, play_package, gmail_to),
            )


def get_product_gdoc_id(db_path: Path, product_key: str) -> str | None:
    """Return the Google Doc ID for the product, or None if not set."""
    with contextlib.closing(get_connection(db_path)) as conn:
        row = conn.execute("SELECT gdoc_id FROM products WHERE key=?", (product_key,)).fetchone()
    return row["gdoc_id"] if row else None


def set_product_gdoc_id(db_path: Path, product_key: str, gdoc_id: str) -> None:
    """Update the Google Doc ID for the product."""
    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                "UPDATE products SET gdoc_id=? WHERE key=?",
                (gdoc_id, product_key),
            )


def upsert_run(
    db_path: Path,
    *,
    run_id: str,
    product_key: str,
    iso_week: str,
    window_start: str,
    window_end: str,
) -> None:
    """Insert a new run record (no-op if already exists)."""
    now = _now_utc()
    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO runs
                    (id, product_key, iso_week, window_start, window_end, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (run_id, product_key, iso_week, window_start, window_end, now, now),
            )


def set_run_status(db_path: Path, run_id: str, status: str) -> None:
    """Advance the run status field."""
    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                "UPDATE runs SET status=?, updated_at=? WHERE id=?",
                (status, _now_utc(), run_id),
            )


def get_run_status(db_path: Path, run_id: str) -> str | None:
    """Return current status string, or None if run doesn't exist."""
    with contextlib.closing(get_connection(db_path)) as conn:
        row = conn.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
    return row["status"] if row else None


def set_run_gmail_id(db_path: Path, run_id: str, message_id: str) -> None:
    """Update the Gmail message/draft ID for the run."""
    import contextlib

    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                "UPDATE runs SET gmail_message_id=?, updated_at=? WHERE id=?",
                (message_id, _now_utc(), run_id),
            )
