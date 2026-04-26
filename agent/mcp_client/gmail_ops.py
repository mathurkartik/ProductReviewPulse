"""Phase 6: Gmail operations via custom MCP server."""

from __future__ import annotations

from pathlib import Path

import structlog

from agent import storage
from agent.mcp_client.session import MCPSession

log = structlog.get_logger()

def send_pulse_email(
    session: MCPSession,
    run_id: str,
    to: list[str],
    cc: list[str],
    bcc: list[str],
    subject: str,
    html: str,
    text: str,
    product_name: str,
    confirm_send: bool,
    db_path: Path
):
    """
    Idempotent email delivery:
    1. Search for existing message with X-Pulse-Run-Id header.
    2. If found, skip.
    3. Create draft with header.
    4. If confirm_send is True, send the draft.
    5. Persist the ID in DB.
    """
    header_query = f"X-Pulse-Run-Id:{run_id}"
    log.info("gmail.search_start", query=header_query)
    
    try:
        search_res = session.call_tool("gmail.search_messages", {"query": header_query})
        if search_res.get("status") == "success" and search_res.get("messages"):
            msg_id = search_res["messages"][0]["id"]
            log.info("gmail.already_exists", message_id=msg_id)
            return {"status": "skipped", "message_id": msg_id}
    except Exception as e:
        log.warning("gmail.search_failed", error=str(e))
        # Proceed anyway, create_draft might fail if it's a strict constraint but here it's for idempotency

    # Create draft
    to_str = ", ".join(to)
    cc_str = ", ".join(cc) if cc else ""
    bcc_str = ", ".join(bcc) if bcc else ""
    
    log.info("gmail.create_draft_start", to=to_str)
    draft_res = session.call_tool("gmail.create_draft", {
        "to": to_str,
        "cc": cc_str,
        "bcc": bcc_str,
        "subject": subject,
        "text": text,
        "html": html,
        "headers": {"X-Pulse-Run-Id": run_id},
        "label": f"Pulse/{product_name}"
    })
    
    if draft_res.get("status") != "success":
        log.error("gmail.create_draft_failed", error=draft_res.get("message"))
        raise RuntimeError(f"Failed to create draft: {draft_res.get('message')}")
        
    draft_id = draft_res["draft_id"]
    log.info("gmail.draft_created", draft_id=draft_id)
    
    # Store draft ID initially
    storage.set_run_gmail_id(db_path, run_id, draft_id)
    
    if confirm_send:
        log.info("gmail.send_start", draft_id=draft_id)
        send_res = session.call_tool("gmail.send_message", {"draft_id": draft_id})
        if send_res.get("status") == "success":
            msg_id = send_res["message_id"]
            log.info("gmail.sent", message_id=msg_id)
            # Update with final message ID
            storage.set_run_gmail_id(db_path, run_id, msg_id)
            return {"status": "sent", "message_id": msg_id}
        else:
            log.error("gmail.send_failed", error=send_res.get("message"))
            raise RuntimeError(f"Failed to send email: {send_res.get('message')}")
            
    return {"status": "drafted", "draft_id": draft_id}
