import asyncio
from pathlib import Path
import importlib.util
import inspect

from backend.object_model.tool import Tool
from backend.engine.mcp_discovery import discover_mcp_tools
from backend.tools.base.mcp_tool import MCPTool
from backend.mcp_client.mcp_client import MCPClient
from backend.engine.config import ToolConfig


class ToolManager:
    """Manages discovery and initialization of all tool types."""
    
    @staticmethod
    def get_tool_dict(tool_config: ToolConfig) -> dict[str, Tool]:
        """
        Get a dictionary of all available tools from various sources.
        
        Args:
            tool_config: ToolConfig object containing tool configuration
            
        Returns:
            Dict mapping tool names to Tool instances
        """
        tools = []
        
        # 1. Discover custom tools
        if tool_config.tools_dir:
            custom_tools = ToolManager._discover_custom_tools(
                tool_config.tools_dir, 
                tool_config.tool_config
            )
            tools.extend(custom_tools)
        
        # 2. Discover local MCP tools
        if tool_config.mcp_tools_dir:
            local_mcp_tools = discover_mcp_tools(tool_config.mcp_tools_dir)
            tools.extend(local_mcp_tools)
        
        # 3. Connect to remote MCP servers
        if tool_config.remote_mcp_servers:
            remote_mcp_tools = ToolManager._connect_remote_mcp_servers(
                tool_config.remote_mcp_servers
            )
            tools.extend(remote_mcp_tools)
        
        # 4. Apply prefixes to all tools based on configuration
        ToolManager._apply_prefixes(tools, tool_config.tool_config)
        return {tool.name: tool for tool in tools}

    @staticmethod
    def _discover_custom_tools(tools_dir: str, tool_config: dict) -> list[Tool]:
        """
        Discover custom tools from the tools directory.
        
        Args:
            tools_dir: Directory to search for tool files
            tool_config: Configuration for tools
            
        Returns:
            List of Tool instances
        """
        tools = []
        base_path = Path(tools_dir).resolve()
        module_root_path = base_path.parents[2]  # Three levels up
        base_module = "py.backend.tools"  # Static base module for tools
        
        # Walk through all .py files in the directory (recursive)
        for file_path in base_path.rglob("*.py"):
            if file_path.name == "__init__.py":
                continue
            try:
                # Get the path relative to the Python root dir
                relative_path = file_path.relative_to(module_root_path)
                # Convert path parts to a valid Python module name
                module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
                module_name = ".".join(module_parts)
                
                # Dynamically import the module
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find all Tool subclasses in the module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, Tool) and 
                            obj != Tool and 
                            obj.__module__ == module_name):
                            # Check if tool is enabled in config
                            tool_name = obj.__name__
                            if tool_name in tool_config and not tool_config[tool_name].get('enabled', True):
                                continue
                            
                            # Instantiate the tool
                            tool_instance = obj()
                            tools.append(tool_instance)
                            
            except Exception as e:
                print(f"Warning: Failed to load tool from {file_path}: {e}")
                continue
        
        return tools
    
    @staticmethod
    def _connect_remote_mcp_servers(remote_servers: list[dict]) -> list[Tool]:
        """
        Connect to remote MCP servers and get their tools.
        
        Args:
            remote_servers: List of remote server configurations
            Each server config should have: {'url': 'http://...', 'name': '...'}
            
        Returns:
            List of MCPTool instances for remote tools
        """
        tools = []
        
        async def _connect_async():
            nonlocal tools
            client = MCPClient()
            
            try:
                for server_config in remote_servers:
                    try:
                        server_url = server_config.get('url')
                        server_name = server_config.get('name', server_url)
                        
                        if not server_url:
                            print(f"Warning: Remote MCP server config missing 'url': {server_config}")
                            continue
                        
                        # Connect to remote server with timeout
                        server_tools = await asyncio.wait_for(
                            client.connect_to_server(server_name, server_url),
                            timeout=10.0
                        )
                        
                        # Create MCPTool instances for each remote tool
                        for tool_info in server_tools:
                            # Use server_url as script_path for remote tools
                            mcp_tool = MCPTool(server_name, server_url, tool_info)
                            tools.append(mcp_tool)
                            
                    except Exception as e:
                        print(f"Warning: Failed to connect to remote MCP server {server_config}: {e}")
                        continue
                        
            finally:
                await client.cleanup()
        
        # Run async connection in sync context
        try:
            asyncio.run(_connect_async())
        except Exception as e:
            print(f"Warning: Remote MCP server connection failed: {e}")
        
        return tools
    
    @staticmethod
    def _apply_prefixes(tools: list[Tool], tool_config: dict):
        """
        Apply prefixes to tools based on individual tool configuration.
        
        Args:
            tools: List of Tool instances to modify
            tool_config: Dict containing individual tool configurations with optional "prefix" keys
        """
        for tool in tools:
            # Check if there's a prefix configured for this specific tool name
            if tool.name in tool_config and 'prefix' in tool_config[tool.name]:
                prefix = tool_config[tool.name]['prefix']
                if prefix:  # Only apply prefix if it's not empty
                    tool.name = f"{prefix}_{tool.name}"
            # For MCP tools, also check if there's a prefix for the server
            elif hasattr(tool, 'server_id') and tool.server_id in tool_config and 'prefix' in tool_config[tool.server_id]:
                prefix = tool_config[tool.server_id]['prefix']
                if prefix:  # Only apply prefix if it's not empty
                    tool.name = f"{prefix}_{tool.name}"
