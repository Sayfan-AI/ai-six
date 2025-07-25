import asyncio
import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Standalone MCP client for connecting to and interacting with MCP servers."""
    
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self._server_tools: dict[str, list[dict]] = {}

    async def connect_to_server(self, server_id: str, server_script_path: str) -> list[dict]:
        """Connect to a single MCP server and return its tools."""
        if server_id in self.sessions:
            # Already connected, return cached tools
            return self._server_tools.get(server_id, [])
            
        is_python = server_script_path.endswith('.py')
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

        await session.initialize()

        response = await session.list_tools()
        tools = [{
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        } for tool in response.tools]

        # Cache the session and tools
        self.sessions[server_id] = session
        self._server_tools[server_id] = tools
        
        return tools


    async def invoke_tool(self, server_id: str, tool_name: str, tool_args: dict) -> str:
        """Invoke a specific tool on the specified MCP server."""
        session = self.sessions.get(server_id)
        if not session:
            raise RuntimeError(f"No active session for server '{server_id}'. Connect to server first.")

        result = await session.call_tool(tool_name, tool_args)
        return result.content[0].text if result.content else ""

    def get_server_tools(self, server_id: str) -> list[dict]:
        """Get cached tools for a server."""
        return self._server_tools.get(server_id, [])
    
    def is_connected(self, server_id: str) -> bool:
        """Check if connected to a server."""
        return server_id in self.sessions
        
    async def disconnect_server(self, server_id: str):
        """Disconnect from a specific server."""
        if server_id in self.sessions:
            # Session cleanup handled by exit_stack
            del self.sessions[server_id]
            if server_id in self._server_tools:
                del self._server_tools[server_id]
    
    async def cleanup(self):
        """Cleanup all resources."""
        self.sessions.clear()
        self._server_tools.clear()
        await self.exit_stack.aclose()
