import asyncio
from agent.mcp_client.session import MCPSession
from agent.config import load_settings

async def main():
    settings = load_settings()
    url = settings.env.mcp_server_url
    if not url.endswith("/sse"):
        url = url.rstrip("/") + "/sse"
    if not url:
        print("MCP_SERVER_URL missing")
        return
        
    print(f"Connecting to {url}...")
    mcp = MCPSession(url)
    async with mcp.connect() as session:
        tools = await session.list_tools()
        print("\nAvailable Tools:")
        for t in tools.tools:
            print(f"- {t.name}: {t.description}")

if __name__ == "__main__":
    asyncio.run(main())
