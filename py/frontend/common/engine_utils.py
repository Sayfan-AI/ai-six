"""
Common utilities for frontend Engine initialization and management.

This module provides helpers for creating and managing Engine instances
across different frontends (CLI, Chainlit, Slack, etc.).
"""

import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from py.backend.engine.config import Config
from py.backend.engine.engine import Engine


def create_from_config(
    config_path: str, 
    session_id: Optional[str] = None
) -> Tuple[Engine, Config]:
    """Create an Engine instance from a configuration file.
    
    Args:
        config_path: Path to the configuration file (JSON, YAML, or TOML)
        session_id: Optional session ID to load after initialization
        
    Returns:
        A tuple containing (engine, config) where engine is the initialized
        Engine instance and config is the loaded Config object.
    """
    # Load the configuration
    config = Config.from_file(config_path)
    
    # Create required directories if they don't exist
    memory_dir = Path(config.memory_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the engine from the configuration
    engine = Engine.from_config(config_path)
    
    # Load session if provided
    if session_id:
        if not engine.load_session(session_id):
            raise ValueError(f"Session ID not found: {session_id}")
    
    return engine, config


def create_channel_engine(
    base_config_path: str,
    channel_id: str,
    base_memory_dir: Optional[str] = None
) -> Engine:
    """Create an Engine instance for a specific channel (for chat platforms).
    
    Args:
        base_config_path: Path to the base configuration file
        channel_id: Channel identifier to create a separate configuration
        base_memory_dir: Optional override for the base memory directory
        
    Returns:
        An Engine instance configured for the specific channel
    """
    # Load the base configuration
    config = Config.from_file(base_config_path)
    
    # Determine memory directory
    memory_base = Path(base_memory_dir or config.memory_dir)
    channel_memory_dir = memory_base / channel_id
    channel_memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a channel-specific config file
    file_ext = Path(base_config_path).suffix
    channel_config_path = str(channel_memory_dir / f"config{file_ext}")
    
    # Load the base config data and modify for the channel
    with open(base_config_path, 'r') as f:
        config_content = f.read()
    
    # Update the memory directory path in the config content
    # NOTE: This is a simplistic approach; a more robust solution would
    # load and modify the config data structure based on format
    config_content = config_content.replace(
        config.memory_dir, 
        str(channel_memory_dir)
    )
    
    # Write the modified config for this channel
    with open(channel_config_path, 'w') as f:
        f.write(config_content)
    
    # Create and return the engine
    return Engine.from_config(channel_config_path)


def list_available_sessions(memory_dir: str) -> Dict[str, Any]:
    """List all available sessions in the memory directory.
    
    Args:
        memory_dir: Path to the memory directory
        
    Returns:
        Dictionary of session IDs and their metadata
    """
    # Create a temporary engine to list sessions
    temp_config = Config(
        llm_providers=[],
        default_model_id="temp",
        tools_dir=".",
        memory_dir=memory_dir
    )
    
    # We need to create directories if they don't exist
    Path(memory_dir).mkdir(parents=True, exist_ok=True)
    
    engine = Engine(temp_config)
    return engine.list_sessions()