"""
Slack-specific utilities for AI-6.

This module provides helpers specifically for the Slack frontend,
including channel-specific engine creation and management.
"""

from pathlib import Path
from typing import Optional

from py.backend.engine.config import Config
from py.backend.engine.engine import Engine


def create_channel_engine(
    base_config_path: str,
    channel_id: str,
    base_memory_dir: Optional[str] = None
) -> Engine:
    """Create an Engine instance for a specific Slack channel.
    
    Args:
        base_config_path: Path to the base configuration file
        channel_id: Slack channel identifier to create a separate configuration
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