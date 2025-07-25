"""Dynamic MCP tool discovery."""

import os
import asyncio
from pathlib import Path

from backend.tools.base.mcp_tool import MCPTool
from backend.mcp_client.client import MCPClient


def discover_mcp_tools(mcp_tools_dir: str) -> list[MCPTool]:
    """Discover MCP tools dynamically by connecting to MCP servers."""
    if not os.path.isdir(mcp_tools_dir):
        return []
    
    async def _discover_async():
        tools = []
        client = MCPClient()
        
        try:
            # Find all MCP server scripts
            mcp_tools_path = Path(mcp_tools_dir)
            for script_path in mcp_tools_path.glob("*.py"):
                if script_path.name.startswith("__"):
                    continue
                    
                server_id = script_path.stem  # filename without .py
                script_path_str = str(script_path)
                
                try:
                    # Connect to server and get its tools
                    server_tools = await client.connect_to_server(server_id, script_path_str)
                    
                    # Create MCPTool instances for each tool
                    for tool_info in server_tools:
                        mcp_tool = MCPTool(server_id, script_path_str, tool_info)
                        tools.append(mcp_tool)
                        
                except Exception as e:
                    # Skip servers that fail to connect
                    print(f"Warning: Failed to connect to MCP server {script_path}: {e}")
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
