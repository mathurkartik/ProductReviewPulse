"""CLI entry point — `pulse` command."""

from __future__ import annotations

import sys
from datetime import UTC

import structlog
import typer

from agent import storage
from agent.config import load_settings

app = typer.Typer(
    name="pulse",
    help="Weekly Product Review Pulse - automated app-store review analysis.",
    no_args_is_help=True,
)

log = structlog.get_logger()


def _setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


# ---------------------------------------------------------------------------
# Phase 0 — init-db
# ---------------------------------------------------------------------------


@app.command("init-db")
def init_db() -> None:
    """Phase 0 - create (or upgrade) the SQLite database schema."""
    _setup_logging()
    settings = load_settings()
    storage.init_db(settings.env.db_path)
    log.info("init_db.done", path=str(settings.env.db_path))
    typer.echo(f"[OK] Database initialised at {settings.env.db_path}")


# ---------------------------------------------------------------------------
# Phase 1 — ingest
# ---------------------------------------------------------------------------


@app.command()
def ingest(
    product: str = typer.Option(..., help="Product key (e.g. groww)"),
    weeks: int = typer.Option(12, help="Rolling window in weeks"),
) -> None:
    """Phase 1 - ingest App Store + Play Store reviews."""
    _setup_logging()

    settings = load_settings()
    storage.init_db(settings.env.db_path)

    from datetime import datetime, timedelta

    from agent.ingestion.appstore import fetch_appstore_reviews
    from agent.ingestion.playstore import fetch_playstore_reviews
    from agent.storage import (
        current_iso_week,
        get_connection,
        make_run_id,
        set_run_status,
        upsert_product,
        upsert_run,
    )

    # settings already loaded above

    try:
        product_config = settings.get_product(product)
    except KeyError:
        log.error("product.not_found", product=product)
        raise typer.Exit(code=1) from None

    upsert_product(
        settings.env.db_path,
        key=product_config.key,
        display=product_config.display_name,
        appstore_id=product_config.appstore_id,
        play_package=product_config.play_package,
    )

    now = datetime.now(UTC)
    since_date = now - timedelta(weeks=weeks)

    iso_week = current_iso_week()
    run_id = make_run_id(product, iso_week)

    upsert_run(
        settings.env.db_path,
        run_id=run_id,
        product_key=product,
        iso_week=iso_week,
        window_start=since_date.date().isoformat(),
        window_end=now.date().isoformat(),
    )
    set_run_status(settings.env.db_path, run_id, "pending")

    log.info(
        "ingest.start", product=product, weeks=weeks, since=since_date.isoformat(), run_id=run_id
    )

    reviews = []

    if product_config.appstore_id:
        log.info("ingest.appstore.start", appstore_id=product_config.appstore_id)
        for rev in fetch_appstore_reviews(product, product_config.appstore_id, since_date):
            reviews.append(rev)

    if product_config.play_package:
        log.info("ingest.playstore.start", play_package=product_config.play_package)
        for rev in fetch_playstore_reviews(product, product_config.play_package, since_date):
            reviews.append(rev)

    log.info("ingest.fetched", count=len(reviews))

    if not reviews:
        log.warning("ingest.empty")
        set_run_status(settings.env.db_path, run_id, "failed")
        raise typer.Exit(code=0)

    import contextlib

    with contextlib.closing(get_connection(settings.env.db_path)) as conn:
        with conn:
            for rev in reviews:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO reviews
                    (id, product_key, source, external_id, rating, title, body, posted_at, version, language, country, ingested_at, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rev.id,
                        rev.product_key,
                        rev.source,
                        rev.external_id,
                        rev.rating,
                        rev.title,
                        rev.body,
                        rev.posted_at.isoformat(),
                        rev.version,
                        rev.language,
                        rev.country,
                        now.isoformat(),
                        rev.model_dump_json(),
                    ),
                )

    audit_dir = settings.env.db_path.parent / "raw" / product
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / f"{run_id}.jsonl"
    with audit_file.open("w", encoding="utf-8") as f:
        for rev in reviews:
            f.write(rev.model_dump_json() + "\n")

    set_run_status(settings.env.db_path, run_id, "ingested")
    log.info("ingest.done", file=str(audit_file), count=len(reviews))


# ---------------------------------------------------------------------------
# Phase 2 — cluster
# ---------------------------------------------------------------------------


@app.command()
def cluster(
    run: str = typer.Option(..., help="run_id to cluster"),
) -> None:
    """Phase 2 - embed reviews and run UMAP + HDBSCAN clustering."""
    _setup_logging()

    settings = load_settings()
    storage.init_db(settings.env.db_path)

    from agent.clustering.pipeline import run_clustering

    # Validate run exists and is in correct status
    status = storage.get_run_status(settings.env.db_path, run)
    if status is None:
        log.error("cluster.run_not_found", run_id=run)
        raise typer.Exit(code=1)
    if status not in ("ingested", "clustered"):
        log.error("cluster.wrong_status", run_id=run, status=status, expected="ingested")
        raise typer.Exit(code=1)

    log.info("cluster.start", run_id=run)

    try:
        metrics = run_clustering(
            run_id=run,
            db_path=settings.env.db_path,
            min_cluster_size=settings.defaults.hdbscan_min_cluster_size,
            embedding_model=settings.defaults.embedding_model,
        )
    except Exception as e:
        log.error("cluster.failed", run_id=run, error=str(e))
        storage.set_run_status(settings.env.db_path, run, "failed")
        raise typer.Exit(code=1) from e

    storage.set_run_status(settings.env.db_path, run, "clustered")
    log.info("cluster.done", run_id=run, **metrics)
    typer.echo(
        f"[OK] Clustering complete: {metrics['cluster_count']} clusters, "
        f"{metrics['noise_ratio']:.1%} noise, "
        f"{metrics['review_count']} reviews"
    )


# ---------------------------------------------------------------------------
# Phase 3 — summarize
# ---------------------------------------------------------------------------


@app.command()
def summarize(
    run: str = typer.Option(..., help="run_id to summarize"),
) -> None:
    """Phase 3 - LLM summarization: themes, quotes, action ideas."""
    _setup_logging()

    from agent.summarization import Summarizer
    from agent.summarization_models import PulseCostExceeded

    settings = load_settings()
    storage.init_db(settings.env.db_path)

    # Validate status
    status = storage.get_run_status(settings.env.db_path, run)
    if status is None:
        log.error("summarize.run_not_found", run_id=run)
        raise typer.Exit(code=1)
    if status not in ("clustered", "summarized"):
        log.error("summarize.wrong_status", run_id=run, status=status, expected="clustered")
        raise typer.Exit(code=1)

    if not settings.env.groq_api_key:
        log.error("summarize.no_api_key", msg="GROQ_API_KEY is missing from environment/secrets")
        raise typer.Exit(code=1)

    log.info("summarize.start", run_id=run)

    try:
        summarizer = Summarizer(settings)
        summary = summarizer.run_summarization(run)
    except PulseCostExceeded as e:
        log.error("summarize.cost_exceeded", run_id=run, spent=e.spent, cap=e.cap)
        storage.set_run_status(settings.env.db_path, run, "failed")
        raise typer.Exit(code=1) from e
    except Exception as e:
        log.error("summarize.failed", run_id=run, error=str(e))
        raise typer.Exit(code=1) from e

    log.info("summarize.done", run_id=run, themes=[t.label for t in summary.top_themes])
    typer.echo(f"[OK] Summarization complete for {run}")
    for i, theme in enumerate(summary.top_themes, 1):
        typer.echo(f"  {i}. {theme.label} ({theme.review_count} reviews)")


# ---------------------------------------------------------------------------
# Phase 4 — render
# ---------------------------------------------------------------------------


@app.command()
def render(
    run: str = typer.Option(..., help="run_id to render"),
) -> None:
    """Phase 4 - render Google Docs batchUpdate requests and email HTML."""
    _setup_logging()

    import json
    from pathlib import Path

    from agent.renderer.docs_tree import generate_doc_requests
    from agent.renderer.email_html import render_emails
    from agent.summarization_models import PulseSummary

    settings = load_settings()
    storage.init_db(settings.env.db_path)

    # Load summary
    summary_path = Path("data/summaries") / f"{run}.json"
    if not summary_path.exists():
        log.error("render.summary_not_found", path=str(summary_path))
        raise typer.Exit(code=1)

    with open(summary_path, encoding="utf-8") as f:
        summary = PulseSummary.model_validate_json(f.read())

    log.info("render.start", run_id=run)

    product_config = settings.get_product(summary.product)

    # 1. Generate Doc Requests
    doc_requests = generate_doc_requests(summary, product_config.display_name)

    # 2. Render Email HTML and Plain Text
    email_html, email_txt = render_emails(summary, product_config.display_name)

    # 3. Save artifacts
    artifact_dir = Path("data/artifacts") / run
    artifact_dir.mkdir(parents=True, exist_ok=True)

    with open(artifact_dir / "doc_requests.json", "w", encoding="utf-8") as f:
        json.dump(doc_requests, f, indent=2)

    with open(artifact_dir / "email.html", "w", encoding="utf-8") as f:
        f.write(email_html)

    with open(artifact_dir / "email.txt", "w", encoding="utf-8") as f:
        f.write(email_txt)

    # Update status
    storage.set_run_status(settings.env.db_path, run, "rendered")

    log.info("render.done", run_id=run, artifact_dir=str(artifact_dir))
    typer.echo(f"[OK] Rendering complete for {run}. Artifacts in {artifact_dir}")


# ---------------------------------------------------------------------------
# Phase 5+6 — publish
# ---------------------------------------------------------------------------


@app.command()
def publish(
    run: str = typer.Option(..., help="run_id to publish"),
    target: str = typer.Option("both", help="docs | gmail | both"),
    doc_id: str | None = typer.Option(None, help="Google Doc ID to append to"),
    to: str | None = typer.Option(None, help="Recipient email address"),
) -> None:
    """Phase 5+6 - publish to Google Docs and/or Gmail via custom REST API."""
    _setup_logging()

    from pathlib import Path

    from agent.mcp_client.docs_ops import append_pulse_section, resolve_document
    from agent.summarization_models import PulseSummary

    settings = load_settings()
    storage.init_db(settings.env.db_path)
    url = settings.env.mcp_server_url
    if not url:
        log.error("publish.no_mcp_url", msg="MCP_SERVER_URL is missing from environment/secrets")
        raise typer.Exit(code=1)

    # Load summary
    summary_path = Path("data/summaries") / f"{run}.json"
    if not summary_path.exists():
        log.error("publish.summary_not_found", path=str(summary_path))
        raise typer.Exit(code=1)

    with open(summary_path, encoding="utf-8") as f:
        summary = PulseSummary.model_validate_json(f.read())

    product_config = settings.get_product(summary.product)

    from agent.mcp_client.session import MCPSession

    session = MCPSession(url)

    docs_success = False
    gmail_success = False

    if target in ("docs", "both"):
        did = doc_id
        if not did:
            log.info("publish.docs.resolving", product=product_config.display_name)
            try:
                did = resolve_document(
                    session, product_config.display_name, product_config.key, settings.env.db_path
                )
            except Exception as e:
                log.error("publish.docs.resolve_failed", error=str(e))

        if not did:
            log.error("publish.no_doc_id", msg="Could not resolve doc_id")
            deep_link = "https://docs.google.com/document"
        else:
            log.info("publish.docs.start", run_id=run, doc_id=did)
            try:
                result = append_pulse_section(session, did, summary, product_config.display_name)
                deep_link = result.get("deep_link", f"https://docs.google.com/document/d/{did}")

                if result.get("status") == "skipped":
                    typer.echo(f"[SKIP] Document already up to date: {deep_link}")
                else:
                    typer.echo(f"[OK] Appended to Google Doc: {deep_link}")
                docs_success = True
            except Exception as e:
                log.error("publish.docs.failed", error=str(e))
                deep_link = f"https://docs.google.com/document/d/{did}"
    else:
        deep_link = "https://docs.google.com/document"
        docs_success = True

    if target in ("gmail", "both"):
        from agent.mcp_client.gmail_ops import send_pulse_email

        artifact_dir = Path("data/artifacts") / run
        with open(artifact_dir / "email.txt", encoding="utf-8") as f:
            email_txt = f.read().replace("{DOC_DEEP_LINK}", deep_link)
        with open(artifact_dir / "email.html", encoding="utf-8") as f:
            email_html = f.read().replace("{DOC_DEEP_LINK}", deep_link)

        recipients_to = [to] if to else product_config.recipients.to
        recipients_cc = product_config.recipients.cc
        recipients_bcc = product_config.recipients.bcc

        if not recipients_to:
            if settings.env.pulse_env == "production":
                log.error("publish.gmail.no_recipients", msg="recipients.to is empty in production")
                raise typer.Exit(code=1)
            recipients_to = ["product-team@example.com"]

        confirm_send = settings.effective_confirm_send
        top_theme = summary.top_themes[0].label if summary.top_themes else "Review Pulse"

        iso_week_str = f"{summary.window.end.year}-W{summary.window.end.isocalendar()[1]:02d}"
        subject = f"[Weekly Pulse] {product_config.display_name} — {iso_week_str} — {top_theme}"
        subject = subject[:197] + "..." if len(subject) > 200 else subject

        log.info("publish.gmail.start", run_id=run, to=recipients_to, confirm_send=confirm_send)
        try:
            result = send_pulse_email(
                session=session,
                run_id=run,
                to=recipients_to,
                cc=recipients_cc,
                bcc=recipients_bcc,
                subject=subject,
                html=email_html,
                text=email_txt,
                product_name=product_config.display_name,
                confirm_send=confirm_send,
                db_path=settings.env.db_path,
            )

            if result.get("status") == "skipped":
                typer.echo(
                    f"[SKIP] Email already sent/drafted: message_id={result.get('message_id')}"
                )
            elif result.get("status") == "sent":
                typer.echo(f"[OK] Sent Gmail: message_id={result.get('message_id')}")
            else:
                typer.echo(f"[OK] Created Gmail draft: draft_id={result.get('draft_id')}")
            gmail_success = True
        except Exception as e:
            log.error("publish.gmail.failed", error=str(e))
    else:
        gmail_success = True

    # Update status
    if docs_success or gmail_success:
        storage.set_run_status(settings.env.db_path, run, "published")
        log.info("publish.done", run_id=run)
    else:
        log.error("publish.all_failed", run_id=run)
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Phase 7 — run (full orchestration)
# ---------------------------------------------------------------------------


@app.command("run")
def run_pipeline(
    product: str = typer.Option(..., help="Product key (e.g. groww)"),
    weeks: int = typer.Option(10, help="Rolling window in weeks"),
    week: str | None = typer.Option(None, help="Specific ISO week to backfill, e.g. 2026-W15"),
    publish_target: str = typer.Option("both", help="docs | gmail | both"),
    doc_id: str | None = typer.Option(None, help="Override Google Doc ID"),
) -> None:
    """Phase 7 - full orchestration: ingest -> cluster -> summarize -> render -> publish."""
    _setup_logging()

    from agent.storage import current_iso_week, get_run_status, make_run_id

    settings = load_settings()
    storage.init_db(settings.env.db_path)
    iso_week = week or current_iso_week()
    run_id = make_run_id(product, iso_week)

    log.info("pipeline.start", product=product, iso_week=iso_week, run_id=run_id)

    # Early validation for production
    if settings.env.pulse_env == "production":
        if not settings.env.groq_api_key:
            log.error("pipeline.validation_failed", msg="GROQ_API_KEY is missing")
            raise typer.Exit(code=1)
        if not settings.env.mcp_server_url:
            log.error("pipeline.validation_failed", msg="MCP_SERVER_URL is missing")
            raise typer.Exit(code=1)

    # 1. Ingest
    status = get_run_status(settings.env.db_path, run_id)
    if not status or status == "pending":
        ingest(product=product, weeks=weeks)
        status = "ingested"
    else:
        log.info("pipeline.skip_ingest", status=status)

    # 2. Cluster
    if status == "ingested":
        cluster(run=run_id)
        status = "clustered"
    else:
        log.info("pipeline.skip_cluster", status=status)

    # 3. Summarize
    if status == "clustered":
        summarize(run=run_id)
        status = "summarized"
    else:
        log.info("pipeline.skip_summarize", status=status)

    # 4. Render
    if status == "summarized":
        render(run=run_id)
        status = "rendered"
    else:
        log.info("pipeline.skip_render", status=status)

    # 5. Publish
    if status == "rendered":
        publish(run=run_id, target=publish_target, doc_id=doc_id, to=None)
        status = "published"
    else:
        log.info("pipeline.skip_publish", status=status)

    log.info("pipeline.done", run_id=run_id, final_status=status)
    typer.echo(f"[OK] Full pipeline run complete for {product} ({iso_week})")


if __name__ == "__main__":
    app()
