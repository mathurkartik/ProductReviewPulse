"""Phase 5: Google Docs operations via custom REST API."""

from __future__ import annotations

import structlog
from agent.mcp_client.session import MCPSession
from agent.summarization_models import PulseSummary

log = structlog.get_logger()

def format_summary_for_doc(summary: PulseSummary) -> str:
    """Format the summary as a readable text block for appending."""
    lines = []
    lines.append(f"{summary.product_key.upper()} — Weekly Review Pulse  |  {summary.iso_week}")
    lines.append("=" * 40)
    lines.append("\nTOP THEMES")
    lines.append("-" * 10)
    for i, theme in enumerate(summary.themes, 1):
        lines.append(f"{i}. {theme.name} ({theme.review_count} reviews)")
        lines.append(f"   {theme.summary}\n")
        
    lines.append("REAL USER QUOTES")
    lines.append("-" * 10)
    for theme in summary.themes:
        for quote in theme.quotes:
            lines.append(f"\"{quote.text}\" ({quote.source}, {quote.rating}*)")
    
    lines.append("\nACTION IDEAS")
    lines.append("-" * 10)
    for action in summary.action_ideas:
        lines.append(f"• {action.title}: {action.description}")
        
    lines.append("\nWHO THIS HELPS")
    lines.append("-" * 10)
    for audience in summary.who_this_helps:
        lines.append(f"{audience.audience}: {audience.value}")
        
    lines.append("\n" + "=" * 40 + "\n")
    return "\n".join(lines)

def append_pulse_section(url: str, doc_id: str, summary: PulseSummary):
    """Append the summarized pulse to the specified Google Doc."""
    session = MCPSession(url)
    content = format_summary_for_doc(summary)
    
    log.info("docs.append_start", doc_id=doc_id)
    result = session.call_tool("append_to_doc", {
        "doc_id": doc_id,
        "content": content
    })
    log.info("docs.append_done", result=result)
    return result
