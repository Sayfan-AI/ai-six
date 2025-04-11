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
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of validated and fixed messages
        """
        validated_messages = []
        tool_call_ids_seen = set()
        
        for i, message in enumerate(messages):
            # Skip messages with invalid roles
            if 'role' not in message:
                continue
                
            # Handle tool messages
            if message.get('role') == 'tool':
                # Check if this tool message has a valid tool_call_id
                if 'tool_call_id' not in message:
                    continue
                    
                # Check if we've seen a corresponding tool_call
                if message['tool_call_id'] not in tool_call_ids_seen:
                    # If not, skip this tool message
                    continue
                    
                # Add the valid tool message
                validated_messages.append(message)
            else:
                # For non-tool messages, check if it has tool_calls
                if 'tool_calls' in message and message.get('role') == 'assistant':
                    # Add all tool_call_ids to our seen set
                    for tool_call in message['tool_calls']:
                        if 'id' in tool_call:
                            tool_call_ids_seen.add(tool_call['id'])
                
                # Add the message
                validated_messages.append(message)
                
        return validated_messages