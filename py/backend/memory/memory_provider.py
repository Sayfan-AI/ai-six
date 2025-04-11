from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time


class MemoryProvider(ABC):
    """
    Abstract base class for memory providers.
    Memory providers are responsible for storing and retrieving conversation history.
    """

    @abstractmethod
    def save_messages(self, conversation_id: str, messages: List[Dict[str, Any]]) -> None:
        """
        Save messages to storage.
        
        Args:
            conversation_id: Unique identifier for the conversation
            messages: List of message dictionaries to save
        """
        pass

    @abstractmethod
    def load_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load messages from storage.
        
        Args:
            conversation_id: Unique identifier for the conversation
            limit: Optional limit on the number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        pass
    
    @abstractmethod
    def get_summary(self, conversation_id: str) -> str:
        """
        Get a summary of the conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            A string summary of the conversation
        """
        pass
    
    @abstractmethod
    def save_summary(self, conversation_id: str, summary: str) -> None:
        """
        Save a summary of the conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            summary: Summary text to save
        """
        pass
    
    @abstractmethod
    def list_conversations(self) -> List[str]:
        """
        List all available conversation IDs.
        
        Returns:
            List of conversation IDs
        """
        pass
    
    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: Unique identifier for the conversation
        """
        pass
    
    def add_timestamp(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a timestamp to a message if it doesn't already have one.
        
        Args:
            message: Message dictionary
            
        Returns:
            Message dictionary with timestamp
        """
        if 'timestamp' not in message:
            message['timestamp'] = time.time()
        return message
        
    def _validate_message_structure(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and fix the message structure to ensure compatibility with OpenAI API.
        
        This ensures that:
        1. Messages with role 'tool' have a corresponding preceding message with 'tool_calls'
        2. Messages have the correct structure for the API
        3. No duplicate messages exist
        4. No duplicate tool_call_ids exist across different assistant messages
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of validated and fixed messages
        """
        print(f"[DEBUG] Starting validation of {len(messages)} messages")
        validated_messages = []
        tool_call_ids_seen = set()
        message_hashes = set()  # To detect duplicates
        tool_call_id_to_message_index = {}  # Maps tool_call_id to the index in validated_messages
        
        # First pass: collect all tool_call_ids from assistant messages
        print("[DEBUG] First pass: collecting tool_call_ids from assistant messages")
        for i, message in enumerate(messages):
            if message.get('role') == 'assistant' and 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    if 'id' in tool_call:
                        print(f"[DEBUG] Found tool_call_id in assistant message: {tool_call['id']}")
                        if tool_call['id'] in tool_call_ids_seen:
                            print(f"[DEBUG] Duplicate tool_call_id found: {tool_call['id']}")
                        tool_call_ids_seen.add(tool_call['id'])
        
        # Also check for orphaned tool messages (tool messages without corresponding tool_calls)
        orphaned_tool_messages = []
        for i, message in enumerate(messages):
            if message.get('role') == 'tool' and 'tool_call_id' in message:
                if message['tool_call_id'] not in tool_call_ids_seen:
                    print(f"[DEBUG] Found orphaned tool message with tool_call_id: {message['tool_call_id']}")
                    orphaned_tool_messages.append(i)
        
        print(f"[DEBUG] Collected {len(tool_call_ids_seen)} unique tool_call_ids from assistant messages")
        print(f"[DEBUG] Found {len(orphaned_tool_messages)} orphaned tool messages")
        
        # Reset for the main validation pass
        tool_call_ids_seen = set()
        
        for i, message in enumerate(messages):
            # Skip messages with invalid roles
            if 'role' not in message:
                print(f"[DEBUG] Skipping message {i} - missing role")
                continue
            
            print(f"[DEBUG] Processing message {i}: role={message.get('role')}, " +
                  f"content={message.get('content')[:30] if message.get('content') else None}...")
            
            # Create a hash of the message to detect duplicates
            # We'll use a tuple of (role, content, tool_call_id) as the hash
            msg_hash = (
                message.get('role'),
                message.get('content'),
                message.get('tool_call_id') if message.get('role') == 'tool' else None
            )
            
            # Skip duplicate messages
            if msg_hash in message_hashes:
                print(f"[DEBUG] Skipping duplicate message {i} - role: {message.get('role')}")
                continue
            
            message_hashes.add(msg_hash)
            print(f"[DEBUG] Added message hash to set, now have {len(message_hashes)} unique messages")
            
            # Handle tool messages
            if message.get('role') == 'tool':
                print(f"[DEBUG] Processing tool message {i}")
                # Check if this tool message has a valid tool_call_id
                if 'tool_call_id' not in message:
                    print(f"[DEBUG] Skipping tool message {i} - missing tool_call_id")
                    continue
                    
                print(f"[DEBUG] Tool message has tool_call_id: {message['tool_call_id']}")
                    
                # Check if we've seen a corresponding tool_call
                if message['tool_call_id'] not in tool_call_ids_seen:
                    print(f"[DEBUG] Skipping tool message {i} - no corresponding tool_call found for ID: {message['tool_call_id']}")
                    print(f"[DEBUG] Current tool_call_ids_seen: {tool_call_ids_seen}")
                    continue
                    
                # Add the valid tool message
                print(f"[DEBUG] Adding valid tool message with tool_call_id: {message['tool_call_id']}")
                validated_messages.append(message)
            else:
                # For non-tool messages, check if it has tool_calls
                if 'tool_calls' in message and message.get('role') == 'assistant':
                    print(f"[DEBUG] Processing assistant message {i} with tool_calls")
                    # Check for duplicate tool_call_ids and fix them
                    fixed_tool_calls = []
                    for j, tool_call in enumerate(message['tool_calls']):
                        print(f"[DEBUG] Processing tool_call {j} in message {i}")
                        if 'id' in tool_call:
                            print(f"[DEBUG] Tool call has ID: {tool_call['id']}")
                            # If this tool_call_id has been seen before, generate a new one
                            if tool_call['id'] in tool_call_ids_seen:
                                # Create a new unique ID by appending a timestamp
                                new_id = f"{tool_call['id']}_{int(time.time() * 1000)}"
                                print(f"[DEBUG] Fixing duplicate tool_call_id: {tool_call['id']} -> {new_id}")
                                tool_call['id'] = new_id
                            
                            # Add to seen set
                            tool_call_ids_seen.add(tool_call['id'])
                            print(f"[DEBUG] Added tool_call_id to seen set: {tool_call['id']}")
                            fixed_tool_calls.append(tool_call)
                        else:
                            print(f"[DEBUG] Tool call missing 'id' field, skipping")
                    
                    # Update the message with fixed tool_calls
                    message['tool_calls'] = fixed_tool_calls
                    print(f"[DEBUG] Updated message with {len(fixed_tool_calls)} fixed tool_calls")
                
                # Add the message
                print(f"[DEBUG] Adding message {i} to validated_messages")
                validated_messages.append(message)
                
        print(f"[DEBUG] Validation complete. Original: {len(messages)}, Validated: {len(validated_messages)}")
        return validated_messages