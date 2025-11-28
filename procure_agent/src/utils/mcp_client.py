import os
import asyncio
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def get_mcp_client():
    """
    Context manager that yields an MCP ClientSession connected to the configured server.
    """
    command = os.getenv("MCP_SERVER_COMMAND", "npx")
    args = os.getenv("MCP_SERVER_ARGS", "-y @modelcontextprotocol/server-gmail").split()
    
    # If the command is a single string in env, we might need to parse it better.
    # For now, let's assume MCP_SERVER_COMMAND is the executable and MCP_SERVER_ARGS are the args.
    # Example: COMMAND="npx", ARGS="-y @modelcontextprotocol/server-gmail"
    
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            yield session
