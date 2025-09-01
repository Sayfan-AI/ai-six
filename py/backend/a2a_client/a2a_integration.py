"""A2A integration setup and management."""

from backend.a2a_client.a2a_client import A2AClient
from backend.a2a_client.a2a_message_pump import A2AMessagePump
from backend.tools.base.a2a_tool import A2ATool


class A2AIntegration:
    """Manages A2A client and message pump integration."""
    
    def __init__(self, memory_dir: str, session_id: str):
        self.message_pump = A2AMessagePump(memory_dir, session_id)
        self.a2a_client = A2AClient()
        
    def set_message_injector(self, injector):
        """Set the message injector for the message pump."""
        self.message_pump.set_message_injector(injector)
        
    def configure_from_a2a_tools(self):
        """Configure A2A integration from A2A tool class."""
        # Set up the client with the message pump
        self.message_pump.set_a2a_client(self.a2a_client)
        
        # Configure A2A tools to use the message pump
        # This will automatically register server configs with the message pump's A2A client
        A2ATool.set_message_pump(self.message_pump)
