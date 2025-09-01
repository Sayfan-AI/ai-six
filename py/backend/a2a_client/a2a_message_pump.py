"""A2A Message Pump for async-to-sync communication bridge."""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Callable
import logging

from backend.object_model import SystemMessage
from backend.a2a_client.a2a_client import A2AClient, A2AServerConfig


logger = logging.getLogger(__name__)


@dataclass
class A2ATaskInfo:
    """Information about an active A2A task."""
    task_id: str
    server_name: str
    skill_id: str
    status: str
    created_at: datetime
    last_checked: datetime
    last_message_at: Optional[datetime] = None
    user_input_required: bool = False
    user_input_prompt: Optional[str] = None
    artifacts: list[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
    
    @classmethod
    def from_dict(cls, data: dict) -> 'A2ATaskInfo':
        """Create TaskInfo from dictionary (for persistence)."""
        # Convert ISO datetime strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_checked'] = datetime.fromisoformat(data['last_checked'])
        if data.get('last_message_at'):
            data['last_message_at'] = datetime.fromisoformat(data['last_message_at'])
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Convert TaskInfo to dictionary (for persistence)."""
        data = asdict(self)
        # Convert datetime objects to ISO strings for JSON serialization
        data['created_at'] = self.created_at.isoformat()
        data['last_checked'] = self.last_checked.isoformat()
        if self.last_message_at:
            data['last_message_at'] = self.last_message_at.isoformat()
        return data


class A2AMessagePump:
    """Message pump for handling async A2A communication in sync AI-6 context."""
    
    def __init__(self, memory_dir: str, session_id: str):
        self.memory_dir = memory_dir
        self.session_id = session_id
        self.a2a_client = None
        
        # Active tasks tracking
        self.active_tasks: Dict[str, A2ATaskInfo] = {}
        self.task_monitors: Dict[str, asyncio.Task] = {}
        
        # Configuration
        self.poll_interval = 5.0  # seconds
        self.max_task_age = timedelta(hours=24)  # Auto-cleanup old tasks
        
        # Callback for message injection
        self.message_injector: Optional[Callable[[SystemMessage], None]] = None
        
        # State persistence
        self.state_dir = Path(memory_dir) / "a2a_state"
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / f"active_tasks_{session_id}.json"
        
        # Load persisted state
        self._load_state()
    
    def set_message_injector(self, injector: Callable[[SystemMessage], None]):
        """Set the callback function for injecting SystemMessages."""
        self.message_injector = injector
    
    def set_a2a_client(self, client: A2AClient):
        """Set the A2A client instance."""
        self.a2a_client = client
    
    async def start_task(self, server_name: str, skill_id: str, message: str) -> str:
        """Start a new A2A task and begin monitoring.
        
        Returns:
            Immediate response message for the user
        """
        if not self.a2a_client:
            return "Error: A2A client not initialized"
        
        try:
            # Generate task ID immediately
            task_id = f"{server_name}_{skill_id}_{int(time.time())}"
            
            # Create task info
            now = datetime.now()
            task_info = A2ATaskInfo(
                task_id=task_id,
                server_name=server_name,
                skill_id=skill_id,
                status="starting",
                created_at=now,
                last_checked=now
            )
            
            # Add to active tasks immediately
            self.active_tasks[task_id] = task_info
            
            # Start the actual A2A task and monitoring in background
            # This includes agent discovery if needed
            self.task_monitors[task_id] = asyncio.create_task(
                self._start_and_monitor_task(task_id, server_name, message)
            )
            
            # Persist state
            self._save_state()
            
            # Return immediate response
            return f"Started {skill_id} task on {server_name} (ID: {task_id}). Monitoring for updates..."
            
        except Exception as e:
            logger.error(f"Failed to start A2A task: {e}")
            return f"Failed to start A2A task: {e}"
    
    async def send_message_to_task(self, task_id: str, message: str) -> str:
        """Send a message to an active A2A task.
        
        Returns:
            Immediate response confirming message sent
        """
        if task_id not in self.active_tasks:
            return f"Task {task_id} not found or no longer active"
        
        task_info = self.active_tasks[task_id]
        
        try:
            # Send message to A2A agent (collect response)
            response_parts = []
            async for response_chunk in self.a2a_client.send_message(task_info.server_name, message):
                response_parts.append(response_chunk)
            
            # Update task state
            task_info.last_checked = datetime.now()
            task_info.user_input_required = False
            task_info.user_input_prompt = None
            
            # Persist state
            self._save_state()
            
            return f"Sent message to task {task_id}: {message}"
            
        except Exception as e:
            logger.error(f"Failed to send message to task {task_id}: {e}")
            return f"Failed to send message to task {task_id}: {e}"
    
    async def _start_and_monitor_task(self, task_id: str, server_name: str, message: str):
        """Start the actual A2A task and begin monitoring."""
        
        try:
            task_info = self.active_tasks.get(task_id)
            if not task_info:
                logger.error(f"Task {task_id} not found in active tasks")
                return
            
            # Ensure agent is discovered first (in background)
            try:
                if server_name not in self.a2a_client._agent_cards:
                    # Check if we have a stored config for this server
                    if server_name in self.a2a_client._server_configs:
                        server_config = self.a2a_client._server_configs[server_name]
                        await self.a2a_client.discover_agent(server_config)
                    else:
                        # Fallback for unknown servers (shouldn't happen in normal flow)
                        server_config = A2AServerConfig(
                            name=server_name,
                            url="http://localhost:9999"  # TODO: Make this configurable
                        )
                        await self.a2a_client.discover_agent(server_config)
            except Exception as e:
                logger.error(f"Agent discovery failed for {server_name}: {e}")
                task_info.status = "failed"
                await self._inject_interim_message(
                    task_id, 
                    f"Agent discovery failed: {e}"
                )
                return
            
            # Start the A2A task (this is the blocking part that we moved to background)
            try:
                task_response_parts = []
                async for response_chunk in self.a2a_client.send_message(server_name, message):
                    task_response_parts.append(response_chunk)
                
                task_response = ''.join(task_response_parts)
                
                # Update task status to running and inject initial response
                task_info.status = "running"
                task_info.last_message_at = datetime.now()
                
                # Inject the initial A2A response as a system message
                if task_response.strip():
                    await self._inject_interim_message(
                        task_id, 
                        f"Initial response: {task_response}"
                    )
                
                self._save_state()
                
            except Exception as e:
                logger.error(f"Error starting A2A task {task_id}: {e}")
                task_info.status = "failed"
                await self._inject_interim_message(
                    task_id, 
                    f"Task failed to start: {e}"
                )
                return
            
            # Now continue with regular monitoring
            await self._monitor_task(task_id)
            
        except Exception as e:
            logger.error(f"Unexpected error in start_and_monitor for task {task_id}: {e}")
    
    async def _monitor_task(self, task_id: str):
        """Background monitoring of an A2A task."""
        
        try:
            while task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                
                # Check for new messages from A2A agent
                try:
                    # For now, we'll simulate interim messages
                    # In real implementation, this would query A2A server for new messages
                    await self._check_task_messages(task_id)
                    
                except Exception as e:
                    logger.error(f"Error checking task {task_id}: {e}")
                    # Continue monitoring despite errors
                
                # Update last checked time
                task_info.last_checked = datetime.now()
                self._save_state()
                
                # Wait before next check
                await asyncio.sleep(self.poll_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Unexpected error monitoring task {task_id}: {e}")
        finally:
            # Clean up
            if task_id in self.task_monitors:
                del self.task_monitors[task_id]
    
    async def _check_task_messages(self, task_id: str):
        """Check for new messages from an A2A task."""
        # This is a placeholder - in real implementation would:
        # 1. Query A2A server for new messages since last_message_at
        # 2. Process each new message
        # 3. Inject SystemMessages for interim updates
        # 4. Handle task completion and artifacts
        
        # For demonstration, simulate occasional interim messages
        import random
        if random.random() < 0.1:  # 10% chance of interim message
            await self._inject_interim_message(
                task_id, 
                f"Task progress update: analyzing data..."
            )
    
    async def _inject_interim_message(self, task_id: str, content: str):
        """Inject an interim A2A message as SystemMessage."""
        if not self.message_injector:
            logger.warning("No message injector set - cannot deliver interim message")
            return
        
        # Format as user-friendly system message
        system_content = f"A2A Task Update [{task_id}]: {content}"
        system_message = SystemMessage(content=system_content)
        
        # Update task state
        if task_id in self.active_tasks:
            self.active_tasks[task_id].last_message_at = datetime.now()
        
        # Inject into conversation
        try:
            self.message_injector(system_message)
            logger.info(f"Injected interim message for task {task_id}: {content}")
        except Exception as e:
            logger.error(f"Failed to inject message for task {task_id}: {e}")
    
    def cancel_task(self, task_id: str) -> str:
        """Cancel an active A2A task."""
        if task_id not in self.active_tasks:
            return f"Task {task_id} not found or no longer active"
        
        # Cancel monitoring
        if task_id in self.task_monitors:
            self.task_monitors[task_id].cancel()
            del self.task_monitors[task_id]
        
        # Remove from active tasks
        task_info = self.active_tasks.pop(task_id)
        
        # Persist state
        self._save_state()
        
        return f"Cancelled task {task_id} ({task_info.skill_id})"
    
    def get_active_tasks(self) -> Dict[str, A2ATaskInfo]:
        """Get all active tasks."""
        return self.active_tasks.copy()
    
    def cleanup_old_tasks(self):
        """Clean up old completed tasks."""
        now = datetime.now()
        tasks_to_remove = []
        
        for task_id, task_info in self.active_tasks.items():
            if now - task_info.created_at > self.max_task_age:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            self.cancel_task(task_id)
    
    def _save_state(self):
        """Save active tasks state to disk."""
        try:
            state_data = {
                task_id: task_info.to_dict() 
                for task_id, task_info in self.active_tasks.items()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save A2A state: {e}")
    
    def _load_state(self):
        """Load active tasks state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                for task_id, task_dict in state_data.items():
                    task_info = A2ATaskInfo.from_dict(task_dict)
                    self.active_tasks[task_id] = task_info
                    
                    # Restart monitoring for active tasks
                    # Note: In real implementation, would query A2A server to verify task still exists
                    self.task_monitors[task_id] = asyncio.create_task(
                        self._monitor_task(task_id)
                    )
                
                logger.info(f"Loaded {len(self.active_tasks)} active A2A tasks from state")
                
        except Exception as e:
            logger.error(f"Failed to load A2A state: {e}")
            # Continue with empty state
    
    async def shutdown(self):
        """Shutdown the message pump and clean up resources."""
        logger.info("Shutting down A2A message pump")
        
        # Cancel all monitoring tasks
        for task_id, monitor_task in self.task_monitors.items():
            monitor_task.cancel()
        
        # Wait for cancellations to complete
        if self.task_monitors:
            await asyncio.gather(
                *self.task_monitors.values(), 
                return_exceptions=True
            )
        
        self.task_monitors.clear()
        
        # Save final state
        self._save_state()
        
        logger.info("A2A message pump shutdown complete")
