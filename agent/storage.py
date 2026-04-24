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
        raise ValueError(
            f"Invalid ISO week format: {iso_week!r}. Expected 'YYYY-WNN'."
        )
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
    product_key   TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL,
    app_store_id  TEXT,
    play_store_id TEXT,
    gdoc_id       TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id          TEXT PRIMARY KEY,
    product_key TEXT REFERENCES products(product_key),
    source      TEXT NOT NULL CHECK(source IN ('appstore', 'playstore')),
    external_id TEXT NOT NULL,
    body        TEXT NOT NULL,
    rating      INTEGER,
    review_date TEXT NOT NULL,
    language    TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_embeddings (
    review_id TEXT PRIMARY KEY REFERENCES reviews(id),
    run_id    TEXT NOT NULL,
    embedding BLOB NOT NULL,
    model     TEXT NOT NULL,
    cached    INTEGER NOT NULL DEFAULT 0 CHECK(cached IN (0, 1))
);

CREATE TABLE IF NOT EXISTS runs (
    run_id           TEXT PRIMARY KEY,
    product_key      TEXT REFERENCES products(product_key),
    iso_week         TEXT NOT NULL,
    window_weeks     INTEGER NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK(status IN (
                         'pending','ingested','clustered',
                         'summarized','rendered','published','failed'
                     )),
    gdoc_id          TEXT,
    gdoc_heading_id  TEXT,
    gmail_message_id TEXT,
    metrics_json     TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS themes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           TEXT REFERENCES runs(run_id),
    cluster_id       TEXT NOT NULL,
    name             TEXT NOT NULL,
    summary          TEXT NOT NULL,
    review_count     INTEGER NOT NULL,
    sentiment_weight REAL NOT NULL,
    rank             INTEGER NOT NULL,
    quotes_json      TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS clusters (
    id               TEXT PRIMARY KEY,
    run_id           TEXT REFERENCES runs(run_id),
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
    product_key: str,
    display_name: str,
    app_store_id: str | None = None,
    play_store_id: str | None = None,
) -> None:
    """Insert or update product metadata."""
    now = _now_utc()
    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO products (product_key, display_name, app_store_id, play_store_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(product_key) DO UPDATE SET
                    display_name=excluded.display_name,
                    app_store_id=excluded.app_store_id,
                    play_store_id=excluded.play_store_id
                """,
                (product_key, display_name, app_store_id, play_store_id, now),
            )


def upsert_run(
    db_path: Path,
    *,
    run_id: str,
    product_key: str,
    iso_week: str,
    window_weeks: int,
) -> None:
    """Insert a new run record (no-op if already exists)."""
    now = _now_utc()
    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO runs
                    (run_id, product_key, iso_week, window_weeks, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (run_id, product_key, iso_week, window_weeks, now, now),
            )


def set_run_status(db_path: Path, run_id: str, status: str) -> None:
    """Advance the run status field."""
    with contextlib.closing(get_connection(db_path)) as conn:
        with conn:
            conn.execute(
                "UPDATE runs SET status=?, updated_at=? WHERE run_id=?",
                (status, _now_utc(), run_id),
            )


def get_run_status(db_path: Path, run_id: str) -> str | None:
    """Return current status string, or None if run doesn't exist."""
    with contextlib.closing(get_connection(db_path)) as conn:
        row = conn.execute(
            "SELECT status FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()
    return row["status"] if row else None
