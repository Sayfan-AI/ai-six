"""A2A Tool implementation for AI-6."""

import asyncio
import threading
from typing import Dict, Any, List, Optional

from backend.object_model.tool import Tool, Parameter
from backend.a2a_client.a2a_client import A2AClient, A2AServerConfig
from backend.a2a_client.a2a_message_pump import A2AMessagePump


def _operation_to_parameters(operation: Dict[str, Any]) -> tuple[list[Parameter], set[str]]:
    """Convert A2A operation definition to Tool parameters and required set."""
    parameters = []
    required = set()
    
    if not isinstance(operation, dict):
        return parameters, required
    
    # Get operation parameters if available
    op_params = operation.get('parameters', {})
    if isinstance(op_params, dict) and 'properties' in op_params:
        # Handle JSON schema style parameters
        if 'required' in op_params and isinstance(op_params['required'], list):
            required = set(op_params['required'])
        
        for prop_name, prop_def in op_params['properties'].items():
            param_type = prop_def.get('type', 'string')
            description = prop_def.get('description', f'{prop_name} parameter')
            
            # Map JSON schema types to our parameter types
            if param_type == 'array':
                param_type = 'array'
            elif param_type in ['integer', 'number']:
                param_type = 'number'
            elif param_type == 'boolean':
                param_type = 'boolean'
            else:
                param_type = 'string'
                
            parameters.append(Parameter(
                name=prop_name,
                type=param_type,
                description=description
            ))
    elif isinstance(op_params, list):
        # Handle list of parameter definitions
        for param in op_params:
            if isinstance(param, dict):
                name = param.get('name', 'param')
                param_type = param.get('type', 'string')
                description = param.get('description', f'{name} parameter')
                is_required = param.get('required', False)
                
                if is_required:
                    required.add(name)
                    
                parameters.append(Parameter(
                    name=name,
                    type=param_type,
                    description=description
                ))
    
    return parameters, required


class A2ATool(Tool):
    """Tool that communicates with A2A (Agent-to-Agent) servers using async-to-sync pattern."""
    
    # Shared A2A client instance across all A2A tools
    _client: A2AClient = None
    _client_lock = threading.Lock()
    # Shared event loop for all A2A operations
    _event_loop = None
    _loop_thread = None
    _loop_lock = threading.Lock()
    # Message pump for async communication
    _message_pump: Optional[A2AMessagePump] = None
    
    def __init__(self, server_config: A2AServerConfig, operation: Dict[str, Any]):
        """Initialize from A2A operation information.
        
        Args:
            server_config: Configuration for the A2A server
            operation: Operation definition from agent card
        """
        operation_name = operation.get('name', 'unknown_operation')
        operation_description = operation.get('description', f'{server_config.name} operation: {operation_name}')
        
        # Convert operation parameters to tool parameters
        # Add special parameters for async communication
        parameters, required = _operation_to_parameters(operation)
        
        # Add async-specific parameters
        parameters.extend([
            Parameter(
                name='task_id',
                type='string',
                description='Optional: ID of existing task to send message to'
            ),
            Parameter(
                name='message',
                type='string', 
                description='Message to send to the A2A agent or existing task'
            )
        ])
        
        super().__init__(
            name=f"{server_config.name}_{operation_name}",
            description=operation_description,
            parameters=parameters,
            required=required
        )
        
        self.server_config = server_config
        self.operation_name = operation_name
        self.operation = operation
    
    @classmethod
    def _get_client(cls) -> A2AClient:
        """Get or create the shared A2A client instance."""
        if cls._client is None:
            with cls._client_lock:
                if cls._client is None:
                    cls._client = A2AClient()
        return cls._client
    
    @classmethod
    def _get_or_create_loop(cls):
        """Get or create a shared event loop for A2A operations."""
        if cls._event_loop is None or cls._event_loop.is_closed():
            with cls._loop_lock:
                if cls._event_loop is None or cls._event_loop.is_closed():
                    cls._event_loop = asyncio.new_event_loop()
        return cls._event_loop
    
    def _ensure_discovered(self):
        """Ensure the A2A agent has been discovered."""
        client = self._get_client()
        loop = self._get_or_create_loop()
        
        # Check if agent is already discovered
        if self.server_config.name not in client._agent_cards:
            # Use shared event loop for discovery
            asyncio.set_event_loop(loop)
            loop.run_until_complete(client.discover_agent(self.server_config))
        
        return client, loop
    
    def run(self, **kwargs) -> str:
        """Execute the A2A operation using async-to-sync pattern."""
        task_id = kwargs.get('task_id')
        message = kwargs.get('message', '')
        
        if not self._message_pump:
            return "Error: A2A message pump not initialized. Please configure A2A integration in Agent."
        
        try:
            # Use shared event loop pattern like MCP tools
            loop = self._get_or_create_loop()
            asyncio.set_event_loop(loop)
            
            if task_id:
                return loop.run_until_complete(
                    self._message_pump.send_message_to_task(task_id, message)
                )
            else:
                msg_to_send = message if message else f"Execute {self.operation_name} operation"
                return loop.run_until_complete(
                    self._message_pump.start_task(
                        self.server_config.name,
                        self.operation_name, 
                        msg_to_send
                    )
                )
        except Exception as e:
            return f"A2A operation failed: {e}"
    
    @classmethod
    def set_message_pump(cls, message_pump: A2AMessagePump):
        """Set the shared message pump instance."""
        cls._message_pump = message_pump
    
    @classmethod
    def cleanup_all(cls):
        """Cleanup all A2A connections. Call this on shutdown."""
        # Cleanup message pump
        if cls._message_pump is not None:
            loop = cls._get_or_create_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(cls._message_pump.shutdown())
            except Exception as e:
                print(f"Warning: Error shutting down A2A message pump: {e}")
            cls._message_pump = None
        
        # Cleanup client
        if cls._client is not None:
            # Use our managed loop for cleanup
            loop = cls._get_or_create_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(cls._client.cleanup())
            finally:
                # Now we can close our managed loop
                if cls._event_loop and not cls._event_loop.is_closed():
                    cls._event_loop.close()
                cls._event_loop = None
            cls._client = None