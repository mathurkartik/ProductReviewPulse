"""Phase 5: MCP-style REST Client Session Management."""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

log = structlog.get_logger()

# Retry config
_MAX_RETRIES = 3
_BACKOFF_BASE = 5  # seconds


class MCPSession:
    """Wrapper for the custom REST-based 'MCP' server."""

    def __init__(self, url: str, *, wake_on_init: bool = True):
        self.base_url = url.rstrip("/")
        self.client = httpx.Client(timeout=300.0)
        if wake_on_init:
            self._wake_server()

    def _wake_server(self) -> None:
        """Send a GET / to wake the Render service from sleep."""
        try:
            log.info("mcp.wake", url=self.base_url)
            r = self.client.get(f"{self.base_url}/", timeout=30.0)
            log.info("mcp.wake_ok", status=r.status_code)
        except Exception as e:
            log.warning("mcp.wake_failed", error=str(e))

    def connect(self):
        """Verify connectivity to the server."""
        log.info("mcp.connect", url=self.base_url)
        try:
            r = self.client.get(f"{self.base_url}/")
            r.raise_for_status()
            log.info("mcp.connected", response=r.json())
            return True
        except Exception as e:
            log.error("mcp.connection_failed", error=str(e))
            return False

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool via POST endpoint with retry logic for transient failures."""
        url = f"{self.base_url}/{tool_name}"
        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            log.info("mcp.call_tool", tool=tool_name, attempt=attempt)
            try:
                r = self.client.post(url, json=arguments)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                status = e.response.status_code
                # Retry on 404 (cold start), 429 (rate limit), 5xx (server error)
                if status in (404, 429, 500, 502, 503, 504) and attempt < _MAX_RETRIES:
                    wait = _BACKOFF_BASE * attempt
                    log.warning(
                        "mcp.tool_retry",
                        tool=tool_name,
                        status=status,
                        attempt=attempt,
                        wait_s=wait,
                    )
                    time.sleep(wait)
                    continue
                log.error("mcp.tool_failed", tool=tool_name, status=status, error=str(e))
                raise
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                if attempt < _MAX_RETRIES:
                    wait = _BACKOFF_BASE * attempt
                    log.warning(
                        "mcp.tool_retry_network",
                        tool=tool_name,
                        attempt=attempt,
                        wait_s=wait,
                        error=str(e),
                    )
                    time.sleep(wait)
                    continue
                log.error("mcp.tool_failed", tool=tool_name, error=str(e))
                raise
            except Exception as e:
                log.error("mcp.tool_failed", tool=tool_name, error=str(e))
                raise

        raise RuntimeError(
            f"MCP tool {tool_name} failed after {_MAX_RETRIES} retries"
        ) from last_error


def call_mcp_tool_sync(url: str, tool_name: str, arguments: dict) -> dict:
    session = MCPSession(url)
    return session.call_tool(tool_name, arguments)
