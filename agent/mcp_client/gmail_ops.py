"""Phase 6: Gmail operations via custom REST API."""

from __future__ import annotations

import structlog
from agent.mcp_client.session import MCPSession
from agent.summarization_models import PulseSummary

log = structlog.get_logger()

def create_pulse_draft(url: str, to: str, summary: PulseSummary, product_name: str):
    """Create a Gmail draft for the summarized pulse."""
    session = MCPSession(url)
    
    # We use a simple plain text body for the draft as the custom API takes a string.
    # The rendered HTML from Phase 4 could be sent if the API supported it,
    # but based on the schema, it's just 'body: string'.
    
    themes_list = "\n".join([f"- {t.name} ({t.review_count} reviews)" for t in summary.themes])
    
    subject = f"[Weekly Pulse] {product_name} — {summary.iso_week}"
    body = f"""Hi Team,

Here are the top themes discovered from this week's reviews for {product_name}:

{themes_list}

Read the full report on Google Docs.

This is an automated report.
"""
    
    log.info("gmail.draft_start", to=to)
    result = session.call_tool("create_email_draft", {
        "to": to,
        "subject": subject,
        "body": body
    })
    log.info("gmail.draft_done", result=result)
    return result
