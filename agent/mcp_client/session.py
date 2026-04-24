"""Phase 5: MCP-style REST Client Session Management."""

from __future__ import annotations

from typing import Any
import httpx
import structlog

log = structlog.get_logger()

class MCPSession:
    """Wrapper for the custom REST-based 'MCP' server."""
    
    def __init__(self, url: str):
        self.base_url = url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)

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
        """Call a tool via POST endpoint."""
        url = f"{self.base_url}/{tool_name}"
        log.info("mcp.call_tool", tool=tool_name)
        try:
            r = self.client.post(url, json=arguments)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error("mcp.tool_failed", tool=tool_name, error=str(e))
            raise

def call_mcp_tool_sync(url: str, tool_name: str, arguments: dict) -> dict:
    session = MCPSession(url)
    return session.call_tool(tool_name, arguments)
