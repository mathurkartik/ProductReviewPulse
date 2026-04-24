import uvicorn
import sys
import os

if __name__ == "__main__":
    print("Starting Google MCP Server...")
    # Add mcp_server to sys.path so server.py can find its modules
    sys.path.append(os.path.join(os.getcwd(), "mcp_server"))
    
    # Run uvicorn pointing to the mcp_server directory
    uvicorn.run(
        "server:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True, 
        app_dir="mcp_server"
    )
