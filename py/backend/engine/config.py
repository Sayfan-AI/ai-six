import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Optional, Mapping, Any
from backend.object_model import LLMProvider
import yaml
import toml

@dataclass
class ToolConfig:
    """Configuration for tool discovery and management."""
    
    # Custom tools configuration
    tools_dirs: list[str] = field(default_factory=list)
    tool_config: Mapping[str, dict] = field(default_factory=lambda: MappingProxyType({}))
    
    # Local MCP tools configuration  
    mcp_tools_dirs: list[str] = field(default_factory=list)
    
    # Remote MCP servers configuration
    remote_mcp_servers: list = field(default_factory=list)
    
    # Tool filtering configuration
    enabled_tools: Optional[list[str]] = None
    disabled_tools: Optional[list[str]] = None
    
    
    def __post_init__(self):
        """Validate tool configuration after initialization."""
        if self.enabled_tools is not None and self.disabled_tools is not None:
            raise ValueError("At least one of enabled_tools or disabled_tools must be None")
    
    @classmethod
    def from_engine_config(cls, engine_config):
        """Create ToolConfig from engine configuration."""
        return cls(
            tools_dirs=getattr(engine_config, 'tools_dirs', []),
            tool_config=getattr(engine_config, 'tool_config', {}),
            mcp_tools_dirs=getattr(engine_config, 'mcp_tools_dirs', []),
            remote_mcp_servers=getattr(engine_config, 'remote_mcp_servers', []),
            enabled_tools=getattr(engine_config, 'enabled_tools', None),
            disabled_tools=getattr(engine_config, 'disabled_tools', None)
        )


@dataclass
class Config:
    default_model_id: str
    tools_dirs: list[str] = field(default_factory=list)
    mcp_tools_dirs: list[str] = field(default_factory=list)
    memory_dir: str = ""
    session_id: Optional[str] = None
    checkpoint_interval: int = 3
    summary_threshold_ratio: float = 0.8
    tool_config: Mapping[str, dict] = field(default_factory=lambda: MappingProxyType({}))
    provider_config: Mapping[str, dict] = field(default_factory=lambda: MappingProxyType({}))
    remote_mcp_servers: list = field(default_factory=list)
    enabled_tools: Optional[list[str]] = None
    disabled_tools: Optional[list[str]] = None
    

    def invariant(self):
        # Validate required directories
        assert self.default_model_id, "default_model_id must be set"
        assert self.memory_dir and os.path.isdir(self.memory_dir), f"Memory directory not found: {self.memory_dir}"
        
        # Validate all tools directories exist
        for tools_dir in self.tools_dirs:
            assert os.path.isdir(tools_dir), f"Tools directory not found: {tools_dir}"
        
        # Validate all MCP tools directories exist    
        for mcp_tools_dir in self.mcp_tools_dirs:
            assert os.path.isdir(mcp_tools_dir), f"MCP tools directory not found: {mcp_tools_dir}"
            
        # Validate tool filtering configuration
        if self.enabled_tools is not None and self.disabled_tools is not None:
            raise ValueError("At least one of enabled_tools or disabled_tools must be None")

    @staticmethod
    def _interpolate_env_vars(value: Any) -> Any:
        """Recursively interpolate environment variables in a configuration value.
        
        Supports ${VAR} and $VAR syntax for environment variables.
        
        Parameters
        ----------
        value : Any
            The value to interpolate
            
        Returns
        -------
        Any
            The interpolated value
        """
        if isinstance(value, str):
            # Handle ${VAR} syntax
            if "${" in value and "}" in value:
                import re
                pattern = r'\${([a-zA-Z0-9_]+)}'
                matches = re.findall(pattern, value)
                
                for var_name in matches:
                    env_value = os.environ.get(var_name, '')
                    value = value.replace(f"${{{var_name}}}", env_value)
                    
            # Handle $VAR syntax
            elif value.startswith('$') and len(value) > 1:
                var_name = value[1:]
                value = os.environ.get(var_name, '')
                
            return value
        elif isinstance(value, dict):
            return {k: Config._interpolate_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [Config._interpolate_env_vars(item) for item in value]
        else:
            return value
            
    @staticmethod
    def from_file(filename: str) -> "Config":
        """Load configuration from a JSON, YAML, or TOML file.
        
        The file extension determines the format (.json, .yaml/.yml, or .toml).
        Required fields in the config file are: tools_dirs, mcp_tools_dirs, memory_dir, and default_model_id.
        Environment variables in the config are interpolated, supporting both ${VAR} and $VAR syntax.
        """
        path = Path(filename)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filename}")
            
        file_ext = path.suffix.lower()
        config_data: dict[str, Any] = {}
        
        # Load file content based on extension
        with open(filename, 'r') as f:
            if file_ext == '.json':
                config_data = json.load(f)
            elif file_ext in ('.yaml', '.yml'):
                config_data = yaml.safe_load(f)
            elif file_ext == '.toml':
                config_data = toml.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}. "
                                "Supported formats are: .json, .yaml, .yml, .toml")
                                
        # Interpolate environment variables in the loaded configuration
        config_data = Config._interpolate_env_vars(config_data)

        # Extract relevant configuration fields
        tools_dirs = config_data.get('tools_dirs', [])
        mcp_tools_dirs = config_data.get('mcp_tools_dirs', [])
        
        memory_dir = config_data.get('memory_dir')
        default_model_id = config_data.get('default_model_id')
        session_id = config_data.get('session_id')
        checkpoint_interval = config_data.get('checkpoint_interval', 3)
        summary_threshold_ratio = config_data.get('summary_threshold_ratio', 0.8)
        tool_config = config_data.get('tool_config', {})
        provider_config = config_data.get('provider_config', {})
        remote_mcp_servers = config_data.get('remote_mcp_servers', [])
        enabled_tools = config_data.get('enabled_tools')
        disabled_tools = config_data.get('disabled_tools')

        # Validate required fields
        if not tools_dirs or not mcp_tools_dirs or not memory_dir or not default_model_id:
            raise ValueError("Configuration file must contain 'tools_dirs', 'mcp_tools_dirs', 'memory_dir', "
                           "and 'default_model_id' fields")
            
        # For now, return a Config without llm_providers, which should be initialized
        # by the Engine class after loading providers using the provider_config
        conf = Config(
            default_model_id=default_model_id,
            tools_dirs=tools_dirs,
            mcp_tools_dirs=mcp_tools_dirs,
            memory_dir=memory_dir,
            session_id=session_id,
            checkpoint_interval=checkpoint_interval,
            summary_threshold_ratio=summary_threshold_ratio,
            tool_config=MappingProxyType(tool_config),
            provider_config=MappingProxyType(provider_config),
            remote_mcp_servers=remote_mcp_servers,
            enabled_tools=enabled_tools,
            disabled_tools=disabled_tools
        )

        conf.invariant()
        return conf
