import json
import os.path
from pathlib import Path
from typing import Callable, Optional, List
import importlib.util
import inspect
import sh
import uuid

from py.backend.engine.llm_provider import LLMProvider
from py.backend.tools.base.tool import Tool
from py.backend.engine.session import Session
from py.backend.engine.session_manager import SessionManager
from py.backend.tools.memory.list_sessions import ListSessions
from py.backend.tools.memory.load_session import LoadSession
from py.backend.tools.memory.get_session_id import GetSessionId
from py.backend.tools.memory.delete_session import DeleteSession
from py.backend.engine.summarizer import SessionSummarizer

class Engine:
    @staticmethod
    def discover_tools(tools_dir):
        tools = []

        base_path = Path(tools_dir).resolve()  # e.g., /Users/gigi/git/ai-six/py/backend/tools
        module_root_path = base_path.parents[2]  # Three levels up → /Users/gigi/git/ai-six
        base_module = 'py.backend.tools'  # Static base module for tools

        # Walk through all .py files in the directory (recursive)
        for file_path in base_path.rglob("*.py"):
            if file_path.name == '__init__.py':
                continue

            try:
                # Get the path relative to the Python root dir
                relative_path = file_path.relative_to(module_root_path)

                # Convert path parts to a valid Python module name
                module_name = '.'.join(relative_path.with_suffix('').parts)

                # Validate it starts with the expected base_module
                if not module_name.startswith(base_module):
                    print(f"Skipping {module_name} (outside of {base_module})")
                    continue

                # Load module from file
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None:
                    print(f"Could not create spec for {module_name}")
                    continue

                module = importlib.util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    print(f"Failed to import {module_name}: {e}")
                    continue

                # Inspect module for subclasses of Tool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Tool) and obj is not Tool:
                        print(f"Found Tool subclass: {name} in {module_name}")
                        tool = obj()
                        tools.append(tool)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return tools

    def __init__(self, 
                llm_providers: list[LLMProvider], 
                default_model_id: str, 
                tools_dir: str,
                memory_dir: str,
                session_id: Optional[str] = None,
                checkpoint_interval: int = 3):  # Checkpoint every 3 messages by default
        assert (os.path.isdir(tools_dir))
        assert (os.path.isdir(memory_dir))
        
        self.llm_providers = llm_providers
        self.default_model_id = default_model_id
        self.model_provider_map = {
            model_id: llm_provider
            for llm_provider in llm_providers
            for model_id in llm_provider.models
        }
        
        # Discover available tools
        tool_list = Engine.discover_tools(tools_dir)
        self.tool_dict = {t.spec.name: t for t in tool_list}
        
        # Initialize session and session manager
        self.session_manager = SessionManager(memory_dir)
        self.session = Session(memory_dir)
        
        # Session-related attributes
        self.checkpoint_interval = checkpoint_interval
        self.message_count_since_checkpoint = 0
        
        # Initialize summarizer if llm providers available
        if self.llm_providers:
            self.summarizer = SessionSummarizer(self.llm_providers[0])
        
        # Register memory tools with the engine
        self._register_memory_tools()
        
        # Load previous session if session_id is provided and exists
        if session_id:
            available_sessions = self.session_manager.list_sessions()
            if session_id in available_sessions:
                self.session = Session(memory_dir)  # Create a new session object
                self.session.load(session_id)       # Load from disk
                
                # Load summary if available
                # TODO: Implement loading summaries
                
    def _register_memory_tools(self):
        """Register memory management tools with the engine."""
        # Create tool instances with a reference to the engine
        list_sessions_tool = ListSessions(self)
        load_session_tool = LoadSession(self)
        get_session_id_tool = GetSessionId(self)
        delete_session_tool = DeleteSession(self)
        
        # Add tools to the engine's tool dictionary
        self.tool_dict[list_sessions_tool.spec.name] = list_sessions_tool
        self.tool_dict[load_session_tool.spec.name] = load_session_tool
        self.tool_dict[get_session_id_tool.spec.name] = get_session_id_tool
        self.tool_dict[delete_session_tool.spec.name] = delete_session_tool

    def _checkpoint_if_needed(self) -> None:
        """Check if we need to save a checkpoint and do so if needed."""
        self.message_count_since_checkpoint += 1
        print(f"[DEBUG] Incremented message_count_since_checkpoint to {self.message_count_since_checkpoint}")
        
        # Only save if we've reached the checkpoint interval exactly
        if self.message_count_since_checkpoint == self.checkpoint_interval:
            print(f"[DEBUG] Checkpoint interval reached ({self.checkpoint_interval}), saving session")
            self.session.save()
            self.message_count_since_checkpoint = 0
            
            # Generate and save a summary if we have enough messages
            # TODO: Implement summary generation

    def _validate_messages_before_send(self):
        """Validate messages before sending to LLM provider to ensure OpenAI API compatibility."""
        print(f"[DEBUG] Validating {len(self.session.messages)} messages before sending to LLM")
        
        # First pass: collect all tool_call_ids from assistant messages
        print("[DEBUG] First pass: collecting tool_call_ids from assistant messages")
        all_tool_call_ids = {}  # Map from tool_call_id to position of assistant message
        
        for i, message in enumerate(self.session.messages):
            if message.get('role') == 'assistant' and 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    if 'id' in tool_call:
                        all_tool_call_ids[tool_call['id']] = i
                        print(f"[DEBUG] Found tool_call_id in assistant message at position {i}: {tool_call['id']}")
        
        print(f"[DEBUG] Collected {len(all_tool_call_ids)} unique tool_call_ids from assistant messages")
        
        # Second pass: validate the sequence
        validated_messages = []
        available_tool_call_ids = set()
        
        for i, message in enumerate(self.session.messages):
            if message.get('role') == 'user' or message.get('role') == 'system':
                # Always include user and system messages
                validated_messages.append(message)
                # Reset available tool_call_ids for user messages
                if message.get('role') == 'user':
                    available_tool_call_ids = set()
                    print(f"[DEBUG] Reset available_tool_call_ids due to user message")
            elif message.get('role') == 'assistant':
                # Always include assistant messages
                validated_messages.append(message)
                # Update available tool_call_ids if this message has tool_calls
                if 'tool_calls' in message:
                    for tool_call in message['tool_calls']:
                        if 'id' in tool_call:
                            available_tool_call_ids.add(tool_call['id'])
                            print(f"[DEBUG] Added tool_call_id to available set: {tool_call['id']}")
            elif message.get('role') == 'tool':
                # Only include tool messages if their tool_call_id exists in an assistant message
                # AND that assistant message comes before this tool message
                tool_call_id = message.get('tool_call_id')
                if tool_call_id in all_tool_call_ids:
                    assistant_pos = all_tool_call_ids[tool_call_id]
                    if assistant_pos < i:  # Ensure assistant message comes before tool message
                        validated_messages.append(message)
                        print(f"[DEBUG] Added valid tool message with tool_call_id: {tool_call_id}")
                    else:
                        print(f"[DEBUG] Skipping tool message - assistant message position {assistant_pos} not before tool message position {i}")
                else:
                    print(f"[DEBUG] Skipping tool message - tool_call_id not found in any assistant message: {tool_call_id}")
        
        self.session.messages = validated_messages
        print(f"[DEBUG] After sequence validation: {len(self.session.messages)} messages")

    def _send(self, model_id, on_tool_call_func: Callable[[str, dict, str], None] | None) -> str:
        # Validate messages before sending to LLM
        self._validate_messages_before_send()
        
        llm_provider = self.model_provider_map.get(model_id)
        if llm_provider is None:
            raise RuntimeError(f"Unknown model ID: {model_id}")

        try:
            response = llm_provider.send(self.session.messages, self.tool_dict, model_id)
        except Exception as e:
            raise RuntimeError(f"Error sending message to LLM: {e}")
            
        if response.tool_calls:
            # Create a mapping of original IDs to new UUIDs if needed
            id_mapping = {}
            
            # Skip ID replacement in test mode (when model_id is 'mock-model')
            if model_id != 'mock-model':
                for tool_call in response.tool_calls:
                    # Check if we need to replace the ID with a UUID
                    if not tool_call.id or len(tool_call.id) < 32:  # Simple check for non-UUID
                        new_id = f"tool_{uuid.uuid4().hex}"
                        id_mapping[tool_call.id] = new_id
                        print(f"[DEBUG] Will replace tool_call_id: {tool_call.id} -> {new_id}")
            
            # Get the assistant message from the provider
            assistant_message = llm_provider.model_response_to_message(response)
            
            # Update the tool call IDs in the assistant message if needed
            if id_mapping:
                for tool_call in assistant_message.get('tool_calls', []):
                    if tool_call.get('id') in id_mapping:
                        original_id = tool_call['id']
                        tool_call['id'] = id_mapping[original_id]
                        print(f"[DEBUG] Replaced tool_call_id in message: {original_id} -> {tool_call['id']}")
            
            # Add the assistant message with updated tool_calls
            self.session.add_message(assistant_message)
            print(f"[DEBUG] Added assistant message with {len(response.tool_calls)} tool_calls")
            
            # Track tool_call_ids from this assistant message
            tool_call_ids = set()
            for tool_call in assistant_message.get('tool_calls', []):
                tool_call_ids.add(tool_call.get('id'))
            
            # Now process each tool call and add the corresponding tool messages
            for i, tool_call in enumerate(response.tool_calls):
                tool = self.tool_dict.get(tool_call.name)
                if tool is None:
                    raise RuntimeError(f'Unknown tool: {tool_call.name}')
                    
                try:
                    kwargs = json.loads(tool_call.arguments)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid arguments JSON for tool '{tool_call.name}'")
                
                # Get the potentially updated tool call ID
                tool_call_id = tool_call.id
                if tool_call.id in id_mapping and model_id != 'mock-model':
                    tool_call_id = id_mapping[tool_call.id]
                    
                try:
                    # Execute the tool without passing any ID information
                    tool_result = tool.run(**kwargs)
                    
                    # Create the tool message with the Engine managing the tool_call_id
                    tool_message = {
                        'role': 'tool',
                        'name': tool_call.name,
                        'content': str(tool_result),
                        'tool_call_id': tool_call_id
                    }
                    
                    if on_tool_call_func is not None:
                        on_tool_call_func(tool_call.name, kwargs, str(tool_result))
                except sh.ErrorReturnCode as e:
                    tool_message = {
                        'role': 'tool',
                        'name': tool_call.name,
                        'content': e.stderr.decode(),
                        'tool_call_id': tool_call_id
                    }
                except Exception as e:
                    tool_message = {
                        'role': 'tool',
                        'name': tool_call.name,
                        'content': str(e),
                        'tool_call_id': tool_call_id
                    }
                
                # Add the tool message (ID is guaranteed to be valid since we manage it)
                self.session.add_message(tool_message)
                print(f"[DEBUG] Added tool message with tool_call_id: {tool_message.get('tool_call_id')}")

            # Continue the session with another send
            return self._send(model_id, on_tool_call_func)
            
        return response.content.strip()

    def run(self,
            get_input_func: Callable[[], None],
            on_tool_call_func: Callable[[str, dict, str], None] | None,
            on_response_func: Callable[[str], None]):
        """Run the session loop."""
        try:
            while user_input := get_input_func():
                message = {'role': 'user', 'content': user_input}
                self.session.add_message(message)
                self._checkpoint_if_needed()

                response = self._send(self.default_model_id, on_tool_call_func)
                message = {'role': 'assistant', 'content': response}
                self.session.add_message(message)
                self._checkpoint_if_needed()
                
                on_response_func(response)
            print('Done!')
        finally:
            # Save the session when we're done
            self.session.save()

    def send_message(self, message: str, model_id: str, on_tool_call_func: Callable[[str, dict, str], None] | None) -> str:
        """Send a single message and get a response."""
        user_message = {'role': 'user', 'content': message}
        self.session.add_message(user_message)
        self._checkpoint_if_needed()
        
        response = self._send(model_id, on_tool_call_func)
        assistant_message = {'role': 'assistant', 'content': response}
        self.session.add_message(assistant_message)
        self._checkpoint_if_needed()
        
        return response
        
    def get_session_id(self) -> str:
        """Get the current session ID."""
        return self.session.session_id
        
    def list_sessions(self) -> List[str]:
        """List all available sessions."""
        sessions = self.session_manager.list_sessions()
        return list(sessions.keys())
        
    def load_session(self, session_id: str) -> bool:
        """
        Load a specific session.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            True if the session was loaded successfully, False otherwise
        """
        available_sessions = self.session_manager.list_sessions()
        if session_id not in available_sessions:
            return False
            
        # Load the session
        self.session.load(session_id)
        
        return True
        
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a specific session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if the session was deleted successfully, False otherwise
        """
        # Don't allow deleting the active session
        if session_id == self.session.session_id:
            print(f"Cannot delete the active session {session_id}")
            return False
            
        try:
            self.session_manager.delete_session(session_id)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False