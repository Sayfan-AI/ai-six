from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import uuid


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
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            bool: True if the conversation was deleted, False otherwise
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
        5. Tool messages appear in the correct sequence after their corresponding tool_calls
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of validated and fixed messages
        """
        print(f"[DEBUG] Starting validation of {len(messages)} messages")
        validated_messages = []
        tool_call_ids_seen = set()
        message_hashes = set()  # To detect duplicates
        
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
        available_tool_call_ids = set()  # Track which tool_call_ids are currently available for tool messages
        
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
            
            # Reset available tool_call_ids when we see a user or system message
            # This ensures tool messages can only follow their corresponding assistant message
            if message.get('role') in ['user', 'system']:
                available_tool_call_ids.clear()
                print(f"[DEBUG] Reset available_tool_call_ids due to {message.get('role')} message")
            
            # Handle tool messages
            if message.get('role') == 'tool':
                print(f"[DEBUG] Processing tool message {i}")
                # Check if this tool message has a valid tool_call_id
                if 'tool_call_id' not in message:
                    print(f"[DEBUG] Skipping tool message {i} - missing tool_call_id")
                    continue
                    
                print(f"[DEBUG] Tool message has tool_call_id: {message['tool_call_id']}")
                    
                # Check if this tool_call_id is available (meaning it came after an assistant message with this tool_call)
                if message['tool_call_id'] not in available_tool_call_ids:
                    print(f"[DEBUG] Skipping tool message {i} - tool_call_id not available: {message['tool_call_id']}")
                    print(f"[DEBUG] Current available_tool_call_ids: {available_tool_call_ids}")
                    continue
                    
                # Add the valid tool message and remove from available set to prevent duplicates
                print(f"[DEBUG] Adding valid tool message with tool_call_id: {message['tool_call_id']}")
                validated_messages.append(message)
                available_tool_call_ids.remove(message['tool_call_id'])
            else:
                # For assistant messages with tool_calls, make those tool_call_ids available for subsequent tool messages
                if 'tool_calls' in message and message.get('role') == 'assistant':
                    print(f"[DEBUG] Processing assistant message {i} with tool_calls")
                    # Check for duplicate tool_call_ids and fix them
                    fixed_tool_calls = []
                    for j, tool_call in enumerate(message['tool_calls']):
                        print(f"[DEBUG] Processing tool_call {j} in message {i}")
                        if 'id' in tool_call:
                            print(f"[DEBUG] Tool call has ID: {tool_call['id']}")
                            # If this tool_call_id has been seen before, generate a new one using UUID
                            if tool_call['id'] in tool_call_ids_seen:
                                # Create a new unique ID using UUID
                                new_id = f"tool_{uuid.uuid4().hex}"
                                print(f"[DEBUG] Fixing duplicate tool_call_id: {tool_call['id']} -> {new_id}")
                                tool_call['id'] = new_id
                            
                            # Add to seen set and available set
                            tool_call_ids_seen.add(tool_call['id'])
                            available_tool_call_ids.add(tool_call['id'])
                            print(f"[DEBUG] Added tool_call_id to seen and available sets: {tool_call['id']}")
                            fixed_tool_calls.append(tool_call)
                        else:
                            # If missing ID, generate a UUID
                            new_id = f"tool_{uuid.uuid4().hex}"
                            tool_call['id'] = new_id
                            print(f"[DEBUG] Added missing tool_call_id: {new_id}")
                            
                            tool_call_ids_seen.add(new_id)
                            available_tool_call_ids.add(new_id)
                            fixed_tool_calls.append(tool_call)
                    
                    # Update the message with fixed tool_calls
                    message['tool_calls'] = fixed_tool_calls
                    print(f"[DEBUG] Updated message with {len(fixed_tool_calls)} fixed tool_calls")
                    print(f"[DEBUG] Available tool_call_ids now: {available_tool_call_ids}")
                
                # Add the message
                print(f"[DEBUG] Adding message {i} to validated_messages")
                validated_messages.append(message)
                
        print(f"[DEBUG] Validation complete. Original: {len(messages)}, Validated: {len(validated_messages)}")
        return validated_messages