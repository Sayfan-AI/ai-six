import json
import os.path
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any
import importlib.util
import inspect
import sh
import time
import uuid

from ..llm_providers.llm_provider import LLMProvider
from ..tools.base.tool import Tool
from ..memory.memory_provider import MemoryProvider
from ..memory.summarizer import ConversationSummarizer

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
                 memory_provider: Optional[MemoryProvider] = None,
                 conversation_id: Optional[str] = None,
                 checkpoint_interval: int = 3):  # Checkpoint every 3 messages by default
        assert (os.path.isdir(tools_dir))
        self.llm_providers = llm_providers
        self.default_model_id = default_model_id
        self.model_provider_map = {
            model_id: llm_provider
            for llm_provider in llm_providers
            for model_id in llm_provider.models
        }
        tool_list = Engine.discover_tools(tools_dir)
        self.tool_dict = {t.spec.name: t for t in tool_list}
        self.messages = []
        
        # Memory-related attributes
        self.memory_provider = memory_provider
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.checkpoint_interval = checkpoint_interval
        self.message_count_since_checkpoint = 0
        
        # Initialize summarizer if memory provider is available
        if self.memory_provider and self.llm_providers:
            self.summarizer = ConversationSummarizer(self.llm_providers[0])
            
            # Load previous messages if conversation_id is provided and exists
            if self.conversation_id and self.conversation_id in self.memory_provider.list_conversations():
                self._load_conversation()
                
    def _load_conversation(self) -> None:
        """Load conversation history from memory provider."""
        if not self.memory_provider:
            print("[DEBUG] No memory provider, skipping load")
            return
            
        print(f"[DEBUG] Loading conversation: {self.conversation_id}")
            
        # Get the summary first
        summary = self.memory_provider.get_summary(self.conversation_id)
        
        # If there's a summary, add it as a system message
        if summary:
            print(f"[DEBUG] Found summary: {summary[:50]}...")
            self.messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {summary}"
            })
        else:
            print("[DEBUG] No summary found")
        
        # Load the most recent messages (limit to a reasonable number to avoid context window issues)
        print("[DEBUG] Loading recent messages with limit=20")
        recent_messages = self.memory_provider.load_messages(self.conversation_id, limit=20)
        
        # Additional validation to ensure messages are compatible with OpenAI API
        if recent_messages:
            print(f"[DEBUG] Loaded {len(recent_messages)} messages from conversation {self.conversation_id}")
            
            # Print some info about tool_call_ids before validation
            tool_call_ids_before = set()
            for msg in recent_messages:
                if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                    for tool_call in msg['tool_calls']:
                        if 'id' in tool_call:
                            tool_call_ids_before.add(tool_call['id'])
                if msg.get('role') == 'tool' and 'tool_call_id' in msg:
                    tool_call_ids_before.add(msg['tool_call_id'])
            
            print(f"[DEBUG] Found {len(tool_call_ids_before)} unique tool_call_ids before engine validation")
            
            # Perform additional validation to ensure no duplicate tool messages
            # This is already handled by _validate_message_structure in MemoryProvider,
            # but we add an extra check here for safety
            tool_call_ids_seen = set()
            tool_call_ids_added = set()
            validated_messages = []
            
            for i, message in enumerate(recent_messages):
                print(f"[DEBUG] Validating message {i}: role={message.get('role')}, " +
                      f"tool_call_id={message.get('tool_call_id', 'None')}")
                
                # For tool messages, check for duplicates
                if message.get('role') == 'tool' and 'tool_call_id' in message:
                    # Skip if we've already added a message with this tool_call_id
                    if message['tool_call_id'] in tool_call_ids_added:
                        print(f"[DEBUG] Skipping duplicate tool message with tool_call_id: {message['tool_call_id']}")
                        continue
                    
                    # Skip if we haven't seen a corresponding tool_call
                    if message['tool_call_id'] not in tool_call_ids_seen:
                        print(f"[DEBUG] Skipping orphaned tool message with tool_call_id: {message['tool_call_id']}")
                        continue
                    
                    tool_call_ids_added.add(message['tool_call_id'])
                    print(f"[DEBUG] Added tool_call_id to added set: {message['tool_call_id']}")
                
                # For assistant messages with tool_calls, track the tool_call_ids
                elif message.get('role') == 'assistant' and 'tool_calls' in message:
                    print(f"[DEBUG] Processing assistant message with tool_calls: {message.get('tool_calls')}")
                    for tool_call in message['tool_calls']:
                        if 'id' in tool_call:
                            tool_call_ids_seen.add(tool_call['id'])
                            print(f"[DEBUG] Added tool_call_id to seen set: {tool_call['id']}")
                
                validated_messages.append(message)
            
            print(f"[DEBUG] After additional validation: {len(validated_messages)} messages")
            print(f"[DEBUG] Tool call IDs seen: {tool_call_ids_seen}")
            print(f"[DEBUG] Tool call IDs added: {tool_call_ids_added}")
            
            self.messages.extend(validated_messages)
            print(f"[DEBUG] Extended self.messages, now has {len(self.messages)} messages")
        else:
            print("[DEBUG] No recent messages found")
            
    def _save_conversation(self) -> None:
        """Save current conversation to memory provider."""
        if not self.memory_provider:
            print("[DEBUG] No memory provider, skipping save")
            return
            
        print(f"[DEBUG] Saving conversation {self.conversation_id} with {len(self.messages)} messages")
        
        # Save all messages
        self.memory_provider.save_messages(self.conversation_id, self.messages)
        self.message_count_since_checkpoint = 0
        print("[DEBUG] Reset message_count_since_checkpoint to 0")
        
        # If we have enough messages, generate and save a summary
        if len(self.messages) >= 10:
            print("[DEBUG] Generating conversation summary")
            summary = self.summarizer.summarize(self.messages, self.default_model_id)
            self.memory_provider.save_summary(self.conversation_id, summary)
            print("[DEBUG] Saved conversation summary")
            
    def _checkpoint_if_needed(self) -> None:
        """Check if we need to save a checkpoint and do so if needed."""
        if not self.memory_provider:
            return
            
        self.message_count_since_checkpoint += 1
        print(f"[DEBUG] Incremented message_count_since_checkpoint to {self.message_count_since_checkpoint}")
        
        if self.message_count_since_checkpoint >= self.checkpoint_interval:
            print(f"[DEBUG] Checkpoint interval reached ({self.checkpoint_interval}), saving conversation")
            self._save_conversation()

    def _send(self, model_id, on_tool_call_func: Callable[[str, dict, str], None] | None) -> str:
        llm_provider = self.model_provider_map.get(model_id)
        if llm_provider is None:
            raise RuntimeError(f"Unknown model ID: {model_id}")

        try:
            response = llm_provider.send(self.messages, self.tool_dict, model_id)
        except Exception as e:
            raise RuntimeError(f"Error sending message to LLM: {e}")
        if response.tool_calls:
            message = llm_provider.model_response_to_message(response)
            self.messages.append(message)
            for tool_call in response.tool_calls:
                tool = self.tool_dict.get(tool_call.name)
                if tool is None:
                    raise RuntimeError(f'Unknown tool: {tool_call.name}')
                try:
                    kwargs = json.loads(tool_call.arguments)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid arguments JSON for tool '{tool_call.name}'")
                try:
                    tool_result = tool.run(**kwargs)
                    message = llm_provider.tool_result_to_message(tool_call, str(tool_result))
                    if on_tool_call_func is not None:
                        on_tool_call_func(message['name'], kwargs, message['content'])
                except sh.ErrorReturnCode as e:
                    message = llm_provider.tool_result_to_message(tool_call, e.stderr.decode())
                except Exception as e:
                    message = llm_provider.tool_result_to_message(tool_call, str(e))
                finally:
                    self.messages.append(message)

            return self._send(model_id, on_tool_call_func)
        return response.content.strip()

    def run(self,
            get_input_func: Callable[[], None],
            on_tool_call_func: Callable[[str, dict, str], None] | None,
            on_response_func: Callable[[str], None]):
        """Run the conversation loop."""
        try:
            while user_input := get_input_func():
                self.messages.append(dict(role='user', content=user_input))
                self._checkpoint_if_needed()

                response = self._send(self.default_model_id, on_tool_call_func)
                self.messages.append(dict(role='assistant', content=response))
                self._checkpoint_if_needed()
                
                on_response_func(response)
            print('Done!')
        finally:
            # Save the conversation when we're done
            if self.memory_provider:
                self._save_conversation()

    def send_message(self, message: str, model_id: str, on_tool_call_func: Callable[[str, dict, str], None] | None) -> str:
        """Send a single message and get a response."""
        self.messages.append(dict(role='user', content=message))
        self._checkpoint_if_needed()
        
        response = self._send(model_id, on_tool_call_func)
        self.messages.append(dict(role='assistant', content=response))
        self._checkpoint_if_needed()
        
        return response
        
    def get_conversation_id(self) -> str:
        """Get the current conversation ID."""
        return self.conversation_id
        
    def list_conversations(self) -> List[str]:
        """List all available conversations."""
        if not self.memory_provider:
            return []
        return self.memory_provider.list_conversations()
        
    def load_conversation(self, conversation_id: str) -> bool:
        """
        Load a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to load
            
        Returns:
            True if the conversation was loaded successfully, False otherwise
        """
        if not self.memory_provider:
            return False
            
        if conversation_id not in self.memory_provider.list_conversations():
            return False
            
        # Clear current messages
        self.messages = []
        
        # Set the conversation ID
        self.conversation_id = conversation_id
        
        # Load the conversation
        self._load_conversation()
        
        return True
