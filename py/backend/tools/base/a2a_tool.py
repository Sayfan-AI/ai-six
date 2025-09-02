"""A2A Tool implementation for AI-6."""

import asyncio
import logging
from typing import Any

from backend.object_model.tool import Tool, Parameter
from backend.a2a_client.a2a_client import A2AServerConfig
from backend.a2a_client.a2a_manager import A2AManager

logger = logging.getLogger(__name__)


def _operation_to_parameters(operation: dict[str, Any]) -> tuple[list[Parameter], set[str]]:
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

    def __init__(self, server_config: A2AServerConfig, operation: dict[str, Any]):
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
        
        # Ensure client exists for this server
        A2AManager.get_or_create_client(server_config)

    def run(self, **kwargs) -> str:
        """Execute the A2A operation using async-to-sync pattern."""
        task_id = kwargs.get('task_id')
        message = kwargs.get('message', '')
        
        message_pump = A2AManager.get_message_pump()
        if not message_pump:
            return "Error: A2A not initialized. Please configure A2A integration."

        try:
            # Check if we're already in an event loop
            try:
                running_loop = asyncio.get_running_loop()
                # We're in an async context, use run_coroutine_threadsafe
                if task_id:
                    future = asyncio.run_coroutine_threadsafe(
                        message_pump.send_message_to_task(task_id, message),
                        message_pump._loop  # Use the message pump's background loop
                    )
                else:
                    msg_to_send = message if message else f"Execute {self.operation_name} operation"
                    future = asyncio.run_coroutine_threadsafe(
                        message_pump.start_task(
                            self.server_config.name,
                            self.operation_name,
                            msg_to_send
                        ),
                        message_pump._loop  # Use the message pump's background loop
                    )

                # Wait for the result with a timeout
                return future.result(timeout=30)

            except RuntimeError:
                # No running event loop, we can use run_until_complete
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    if task_id:
                        return loop.run_until_complete(
                            message_pump.send_message_to_task(task_id, message)
                        )
                    else:
                        msg_to_send = message if message else f"Execute {self.operation_name} operation"
                        return loop.run_until_complete(
                            message_pump.start_task(
                                self.server_config.name,
                                self.operation_name,
                                msg_to_send
                            )
                        )
                finally:
                    loop.close()
                    
        except Exception as e:
            return f"A2A operation failed: {e}"