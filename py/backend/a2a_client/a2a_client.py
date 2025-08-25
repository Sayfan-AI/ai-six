"""A2A (Agent-to-Agent) client for communicating with remote A2A agents."""

import httpx
import requests
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass

from a2a.client import ClientFactory, ClientConfig, create_text_message_object
from a2a.types import AgentCard, Role


@dataclass
class A2AServerConfig:
    """Configuration for an A2A server."""
    name: str
    url: str
    agent_card_url: Optional[str] = None
    timeout: float = 30.0

    def __post_init__(self):
        """Set default agent card URL if not provided."""
        if self.agent_card_url is None:
            self.agent_card_url = f"{self.url.rstrip('/')}/.well-known/agent.json"


class A2AClient:
    """Client for communicating with A2A agents."""
    def __init__(self):
        self._agent_cards: Dict[str, AgentCard] = {}
        self._clients: Dict[str, object] = {}

    async def discover_agent(self, server_config: A2AServerConfig) -> AgentCard:
        """Discover an A2A agent by fetching its agent card.
        
        Args:
            server_config: Configuration for the A2A server
            
        Returns:
            AgentCard object containing agent metadata
            
        Raises:
            Exception: If agent card cannot be fetched
        """
        try:
            # Fetch agent card
            response = requests.get(
                server_config.agent_card_url,
                timeout=server_config.timeout
            )
            response.raise_for_status()
            card_data = response.json()

            # Create and cache agent card
            agent_card = AgentCard(**card_data)
            self._agent_cards[server_config.name] = agent_card

            return agent_card

        except Exception as e:
            raise Exception(f"Failed to discover agent {server_config.name}: {e}")

    async def get_agent_operations(self, server_name: str) -> List[Dict]:
        """Get available operations from an A2A agent.
        
        Args:
            server_name: Name of the A2A server
            
        Returns:
            List of operation definitions from the agent card
        """
        if server_name not in self._agent_cards:
            raise ValueError(f"Agent {server_name} not discovered yet")

        agent_card = self._agent_cards[server_name]

        # Extract operations from agent card - A2A uses "skills" not operations
        operations = []
        if hasattr(agent_card, 'skills') and agent_card.skills:
            # Convert skills to operation-like format
            for skill in agent_card.skills:
                operation = {
                    'name': skill.id if hasattr(skill, 'id') else skill.name,
                    'description': skill.description if hasattr(skill, 'description') else '',
                    'parameters': {}  # A2A skills don't define structured parameters
                }
                operations.append(operation)

        return operations

    async def send_message(self, server_name: str, message: str) -> AsyncGenerator[str, None]:
        """Send a message to an A2A agent and stream responses.
        
        Args:
            server_name: Name of the A2A server
            message: Message text to send
            
        Yields:
            Response text chunks from the agent
        """
        if server_name not in self._agent_cards:
            raise ValueError(f"Agent {server_name} not discovered yet")

        agent_card = self._agent_cards[server_name]

        # Create client if not exists - use a persistent HTTP client
        if server_name not in self._clients:
            # Create a new HTTP client for each A2A client
            http_client = httpx.AsyncClient(timeout=30)
            config = ClientConfig(httpx_client=http_client)
            factory = ClientFactory(config)
            self._clients[server_name] = {
                'client': factory.create(agent_card),
                'http_client': http_client
            }

        client = self._clients[server_name]['client']

        # Create message object
        message_obj = create_text_message_object(Role.user, message)

        # Send message and yield responses
        async for event in client.send_message(message_obj):
            if hasattr(event, 'parts') and event.parts:
                for part in event.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        yield part.root.text
                    elif hasattr(part, 'text'):
                        yield part.text

    async def execute_operation(self, server_name: str, operation_name: str, parameters: Dict) -> str:
        """Execute a specific operation on an A2A agent.
        
        Args:
            server_name: Name of the A2A server
            operation_name: Name of the operation to execute
            parameters: Parameters for the operation
            
        Returns:
            Combined response text from the operation
        """
        # Format operation message with parameters 
        if parameters:
            # If we have specific parameters, use them to construct the message
            message = parameters.get('message', parameters.get('query', parameters.get('input', 'show me all pods')))
        else:
            # Default message for the operation
            message = "show me all pods"

        # Send message and collect all response text
        response_parts = []
        async for response_chunk in self.send_message(server_name, message):
            response_parts.append(response_chunk)

        return ''.join(response_parts)

    async def cleanup(self):
        """Cleanup A2A client resources."""
        # Close all HTTP clients
        for server_name, client_info in self._clients.items():
            await client_info['http_client'].aclose()

        # Clear cached clients and agent cards
        self._clients.clear()
        self._agent_cards.clear()
