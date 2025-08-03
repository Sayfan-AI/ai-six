"""Dynamic MCP tool discovery."""

import os
import asyncio
from pathlib import Path

from backend.tools.base.mcp_tool import MCPTool
from backend.mcp_client.mcp_client import MCPClient


def discover_mcp_tools(mcp_tools_dir: str) -> list[MCPTool]:
    """Discover MCP tools dynamically by connecting to MCP servers."""
    if not os.path.isdir(mcp_tools_dir):
        return []

    async def _discover_async():
        tools = []
        client = MCPClient()

        try:
            # Iterate over all files in the directory
            for file_name in os.listdir(mcp_tools_dir):
                script_path = os.path.join(mcp_tools_dir, file_name)
                
                # Check if it's a file
                if not os.path.isfile(script_path):
                    continue
                
                server_id = Path(script_path).stem  # filename without extension
                try:
                    # Connect to server and get its tools with timeout
                    server_tools = await asyncio.wait_for(
                        client.connect_to_server(server_id, script_path),
                        timeout=5.0
                    )

                    # Create MCPTool instances for each tool
                    for tool_info in server_tools:
                        mcp_tool = MCPTool(server_id, script_path, tool_info)
                        tools.append(mcp_tool)

                except Exception as e:
                    # Skip servers that fail to connect or timeout
                    error_msg = str(e) if str(e) else f"{type(e).__name__}: {e}"
                    print(f"Warning: Failed to connect to MCP server {script_path}: {error_msg}")
                    continue

        finally:
            await client.cleanup()

        return tools

    # Run async discovery in sync context
    try:
        return asyncio.run(_discover_async())
    except Exception as e:
        print(f"Warning: MCP tool discovery failed: {e}")
        return []
