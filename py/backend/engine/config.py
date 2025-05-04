import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Optional, Mapping, Any
from py.backend.engine.llm_provider import LLMProvider
import yaml
import toml

@dataclass
class Config:
    llm_providers: list[LLMProvider]
    default_model_id: str
    tools_dir: str
    memory_dir: str
    session_id: Optional[str] = None
    checkpoint_interval: int = 3
    tool_config: Mapping[str, dict] = field(default_factory=lambda: MappingProxyType({}))
    provider_config: Mapping[str, dict] = field(default_factory=lambda: MappingProxyType({}))

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
        Required fields in the config file are: tools_dir, memory_dir, and default_model_id.
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
        tools_dir = config_data.get('tools_dir')
        memory_dir = config_data.get('memory_dir')
        default_model_id = config_data.get('default_model_id')
        session_id = config_data.get('session_id')
        checkpoint_interval = config_data.get('checkpoint_interval', 3)
        tool_config = config_data.get('tool_config', {})
        provider_config = config_data.get('provider_config', {})
        
        # Validate required fields
        if not tools_dir or not memory_dir or not default_model_id:
            raise ValueError("Configuration file must contain 'tools_dir', 'memory_dir', "
                           "and 'default_model_id' fields")
            
        # For now, return a Config without llm_providers, which should be initialized
        # by the Engine class after loading providers using the provider_config
        return Config(
            llm_providers=[],  # Empty list, to be populated by Engine
            default_model_id=default_model_id,
            tools_dir=tools_dir,
            memory_dir=memory_dir,
            session_id=session_id,
            checkpoint_interval=checkpoint_interval,
            tool_config=MappingProxyType(tool_config),
            provider_config=MappingProxyType(provider_config)
        )
