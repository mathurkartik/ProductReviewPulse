# Phase 6: Gmail Delivery — Technical Implementation Summary

This document outlines the end-to-end implementation of Phase 6, covering the integration of the Gmail MCP server and the resolution of critical server-side bugs.

## 1. Objective
The goal was to implement **idempotent stakeholder notification** via Gmail. This involves:
- Substituting deep links to the generated Google Doc report.
- Checking if an email was already sent for the specific run (Idempotency).
- Creating a Gmail draft by default.
- Sending the email only if `CONFIRM_SEND=true`.

---

## 2. Agent-Side Engineering

### A. Gmail Operations (`agent/mcp_client/gmail_ops.py`)
We replaced the placeholder logic with a production-grade `send_pulse_email` function:
- **Idempotency Strategy**: It performs a `gmail.search_messages` tool call using the query `X-Pulse-Run-Id:{run_id}`. If any message is found, it skips the entire process.
- **Draft Creation**: It constructs a dictionary of arguments including `to`, `subject`, and `body` (plain text). It also passes `cc`, `bcc`, and custom `headers` to the MCP server.
- **State Persistence**: On successful send, it updates the SQLite database (`runs` table) with the `gmail_message_id`.

### B. CLI Orchestration (`agent/__main__.py`)
The `publish` command was significantly refactored:
- **Deep Link Injection**: It now captures the `deep_link` returned from Phase 5 (Google Docs) and performs a string replacement on the `{DOC_DEEP_LINK}` placeholder in the email artifacts (`email.html` and `email.txt`).
- **Safety Guards**: It resolves `settings.effective_confirm_send` to ensure emails are never sent in `development` or `staging` environments regardless of the `.env` setting.

### C. Infrastructure Tuning (`agent/mcp_client/session.py`)
- **Timeout Increase**: We discovered that local and Render-hosted MCP servers often exceed the standard 30s timeout during cold starts or complex Google API calls. We increased the `httpx` timeout to **90.0 seconds** for reliability.

---

## 4. MCP Server Debugging & Fixes

During testing, we encountered a `500 Internal Server Error`. Deep-diving into the `mcp_server/` directory revealed a signature mismatch between the API layer and the tool implementation.

### A. Gmail Tooling (`mcp_server/gmail_tool.py`)
- **MIME Support**: Added `base64`, `MIMEText`, and `MIMEMultipart` imports to build standard email payloads.
- **The "Signature Fix"**: The original `create_draft` function only accepted a `raw_message` string. We refactored it to accept `to`, `subject`, `body`, `cc`, `bcc`, and `headers` to match the Agent's output.
- **Message Builder**: Added a `create_message` helper that packages all metadata into a `base64url` encoded MIME string required by the Gmail API.

### B. API Layer (`mcp_server/server.py`)
- **Schema Expansion**: Updated the `EmailInput` Pydantic model to include optional `cc`, `bcc`, and `headers` fields.
- **Handler Update**: Modified the `run_email` route to unpack the new fields and pass them into the corrected `create_draft` tool.

---

## 4. Final Verification Trace
1. **Command**: `uv run pulse publish --run <run_id> --target both`
2. **Docs Phase**: Agent calls `docs.get_document`. Server responds. Agent finds anchor `[pulse-groww-...]` and skips to avoid duplicate sections.
3. **Gmail Phase**: 
   - Agent calls `gmail.search_messages`. Server returns 0 results.
   - Agent calls `gmail.create_draft`.
   - **Manual Approval**: Server prompts the user in its terminal: `Approve? (y/n)`.
   - **Success**: Server builds MIME message, calls Gmail API, and returns `draft_id`.
   - **CLI Output**: `[OK] Created Gmail draft: draft_id=r-...`

## 5. Result
The system is now capable of delivering professional, deep-linked reports to stakeholders while maintaining a strict audit trail and preventing accidental duplicate deliveries.
