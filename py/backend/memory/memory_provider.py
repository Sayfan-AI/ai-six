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