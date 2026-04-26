from __future__ import annotations

from pathlib import Path

import structlog

from agent.mcp_client.session import MCPSession
from agent.renderer.docs_tree import generate_doc_requests
from agent.storage import get_product_gdoc_id, set_product_gdoc_id
from agent.summarization_models import PulseSummary

log = structlog.get_logger()


def resolve_document(
    session: MCPSession, product_display_name: str, product_key: str, db_path: Path
) -> str:
    """Find the existing Google Doc for the product from SQLite, or create it if missing."""

    # 1. Check database
    doc_id = get_product_gdoc_id(db_path, product_key)
    if doc_id:
        log.info("docs.resolve.found_in_db", doc_id=doc_id)
        return doc_id

    doc_title = f"{product_display_name} — Weekly Review Pulse"

    # 2. If not found, create it via Docs API (does not require Drive API)
    log.info("docs.resolve.create", title=doc_title)
    resp = session.call_tool("docs.create_document", {"title": doc_title})
    doc_id = resp.get("document_id")
    
    # Save to database for next time
    if not doc_id or not isinstance(doc_id, str):
        raise RuntimeError("Failed to create document: no valid document_id returned")
        
    set_product_gdoc_id(db_path, product_key, doc_id)

    return doc_id


def append_pulse_section(
    session: MCPSession, doc_id: str, summary: PulseSummary, product_display_name: str
) -> dict:
    log.info("docs.append_start", doc_id=doc_id)

    # 1. Check idempotency
    resp = session.call_tool("docs.get_document", {"doc_id": doc_id})
    doc = resp.get("document", {})
    body = doc.get("body", {})
    content_elements = body.get("content", [])

    # Combine all text content to search for the anchor and find endIndex
    doc_text = ""
    end_index = 1
    if content_elements:
        last_el = content_elements[-1]
        end_index = last_el.get("endIndex", 2)

    for el in content_elements:
        if "paragraph" in el:
            for el2 in el["paragraph"].get("elements", []):
                if "textRun" in el2:
                    doc_text += el2["textRun"].get("content", "")

    iso_week_str = f"{summary.window.end.year}-W{summary.window.end.isocalendar()[1]:02d}"
    anchor = f"[pulse-{summary.product}-{iso_week_str}]"

    if anchor in doc_text:
        log.info(
            "docs.idempotency_skip", anchor=anchor, reason="Anchor already present in document body"
        )
        return {
            "status": "skipped",
            "reason": "idempotency",
            "anchor": anchor,
            "deep_link": f"https://docs.google.com/document/d/{doc_id}/edit",
        }

    # 2. Build and send batchUpdate requests
    start_idx = max(1, end_index - 1)
    doc_requests = generate_doc_requests(summary, product_display_name, start_idx)

    log.info("docs.batch_update", doc_id=doc_id, request_count=len(doc_requests))
    result = session.call_tool("docs.batch_update", {"doc_id": doc_id, "requests": doc_requests})

    log.info("docs.append_done", status=result.get("status"))

    return {
        "status": "success",
        "anchor": anchor,
        "deep_link": f"https://docs.google.com/document/d/{doc_id}/edit",
    }
