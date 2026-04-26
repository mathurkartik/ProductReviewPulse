"""Phase 0 smoke tests — CLI help and database initialisation."""

from __future__ import annotations

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from agent import storage
from agent.__main__ import app

runner = CliRunner()


def test_cli_help_lists_all_subcommands() -> None:
    """Exit 0 and every subcommand appears in --help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    for cmd in ("init-db", "ingest", "cluster", "summarize", "render", "publish", "run"):
        assert cmd in result.output, f"Missing subcommand: {cmd!r}"


def test_init_db_creates_all_tables() -> None:
    """init-db creates a fresh SQLite file with all 6 required tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage.init_db(db_path)
        tables = set(storage.get_tables(db_path))
        expected = {"products", "reviews", "review_embeddings", "runs", "themes", "clusters"}
        missing = expected - tables
        assert not missing, f"Missing tables after init_db: {missing}"


def test_init_db_is_idempotent() -> None:
    """Calling init_db twice on the same path does not raise or duplicate tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage.init_db(db_path)
        storage.init_db(db_path)  # second call must be a no-op
        tables = storage.get_tables(db_path)
        # Each table name should appear exactly once
        assert len(tables) == len(set(tables))


def test_make_run_id_is_deterministic() -> None:
    """Same inputs always produce the same run_id."""
    rid1 = storage.make_run_id("groww", "2026-W17")
    rid2 = storage.make_run_id("groww", "2026-W17")
    assert rid1 == rid2
    assert len(rid1) == 40  # sha1 hex length


def test_make_run_id_differs_by_input() -> None:
    """Different product/week combinations produce different run_ids."""
    assert storage.make_run_id("groww", "2026-W17") != storage.make_run_id("kuvera", "2026-W17")
    assert storage.make_run_id("groww", "2026-W17") != storage.make_run_id("groww", "2026-W18")


def test_parse_iso_week_valid() -> None:
    year, week = storage.parse_iso_week("2026-W17")
    assert year == 2026
    assert week == 17


def test_parse_iso_week_invalid_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        storage.parse_iso_week("20260417")
