"""A2A integration setup and management."""

import atexit
import asyncio
import logging

from backend.a2a_client.a2a_client import A2AClient
from backend.a2a_client.a2a_message_pump import A2AMessagePump
from backend.tools.base.a2a_tool import A2ATool

logger = logging.getLogger(__name__)


class A2AIntegration:
    """Manages A2A client and message pump integration."""
    
    # Class variable to track all instances for cleanup
    _instances = []
    
    def __init__(self, memory_dir: str, session_id: str):
        self.message_pump = A2AMessagePump(memory_dir, session_id)
        # Map of server_name -> A2AClient instance
        self.a2a_clients = {}
        
        # Track this instance for cleanup
        A2AIntegration._instances.append(self)
        
        # Register cleanup on first instance
        if len(A2AIntegration._instances) == 1:
            atexit.register(A2AIntegration._cleanup_all)
        
    def set_message_injector(self, injector):
        """Set the message injector for the message pump."""
        self.message_pump.set_message_injector(injector)
        
    def get_or_create_client(self, server_config):
        """Get or create an A2A client for a specific server."""
        if server_config.name not in self.a2a_clients:
            client = A2AClient()
            # Configure authentication if API key is provided
            if server_config.api_key:
                # The client will use the API key from server_config when making requests
                pass  # API key is passed with server_config in each request
            self.a2a_clients[server_config.name] = client
        return self.a2a_clients[server_config.name]
    
    def configure_from_a2a_tools(self):
        """Configure A2A integration from A2A tool class."""
        # Set up the clients map with the message pump
        self.message_pump.set_a2a_clients(self.a2a_clients)
        
        # Configure A2A tools to use the message pump and integration
        A2ATool.set_integration(self)
    
    async def _cleanup_async(self):
        """Async cleanup of resources."""
        try:
            await self.message_pump.shutdown()
            # Clean up all client instances
            for client in self.a2a_clients.values():
                await client.cleanup()
        except Exception as e:
            logger.debug(f"Error during A2A cleanup: {e}")
    
    def cleanup(self):
        """Synchronous cleanup wrapper."""
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run cleanup
            if not loop.is_closed():
                loop.run_until_complete(self._cleanup_async())
                # Give time for transport cleanup
                loop.run_until_complete(asyncio.sleep(0.1))
        except Exception as e:
            logger.debug(f"Error during A2A cleanup: {e}")
    
    @classmethod
    def _cleanup_all(cls):
        """Clean up all A2A integration instances."""
        for instance in cls._instances:
            instance.cleanup()
        cls._instances.clear()
