"""A2A Tool implementation for AI-6."""

import asyncio
import logging

from a2a.types import AgentSkill
from backend.object_model.tool import Tool, Parameter
from backend.a2a_client.a2a_client import A2AServerConfig
from backend.a2a_client.a2a_manager import A2AManager

logger = logging.getLogger(__name__)




class A2ATool(Tool):
    """Tool that communicates with A2A (Agent-to-Agent) servers using async-to-sync pattern."""

    def __init__(self, server_config: A2AServerConfig, skill: AgentSkill):
        """Initialize from A2A skill information.

        Args:
            server_config: Configuration for the A2A server
            skill: Skill object from agent card
        """
        # A2A skills are conversational - create standard parameters
        parameters = [
            Parameter(
                name='message',
                type='string',
                description=f'Natural language request for the `{skill.name}` skill'
            ),
            Parameter(
                name='task_id',
                type='string',
                description='Optional: ID of existing task to send message to'
            )
        ]

        required = {'message'}

        super().__init__(
            name=f"{server_config.name}_{skill.name}",
            description=skill.description,
            parameters=parameters,
            required=required
        )

        self.server_config = server_config
        self.skill_name = skill.name

        # Ensure client exists for this server
        A2AManager.get_or_create_client(server_config)

    def run(self, **kwargs) -> str:
        """Execute the A2A skill using async-to-sync pattern."""
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
                    msg_to_send = message if message else f"Execute {self.skill_name} skill"
                    future = asyncio.run_coroutine_threadsafe(
                        message_pump.start_task(
                            self.server_config.name,
                            self.skill_name,
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
                        msg_to_send = message if message else f"Execute {self.skill_name} skill"
                        return loop.run_until_complete(
                            message_pump.start_task(
                                self.server_config.name,
                                self.skill_name,
                                msg_to_send
                            )
                        )
                finally:
                    loop.close()
                    
        except Exception as e:
            return f"A2A skill failed: {e}"
