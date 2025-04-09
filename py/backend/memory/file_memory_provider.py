import json
import os
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from .memory_provider import MemoryProvider


class FileMemoryProvider(MemoryProvider):
    """
    File-based memory provider that stores conversations in JSON files.
    """

    def __init__(self, storage_dir: str):
        """
        Initialize the file memory provider.
        
        Args:
            storage_dir: Directory to store memory files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create summaries directory
        self.summaries_dir = self.storage_dir / "summaries"
        self.summaries_dir.mkdir(exist_ok=True)
        
        # Create conversations directory
        self.conversations_dir = self.storage_dir / "conversations"
        self.conversations_dir.mkdir(exist_ok=True)
    
    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get the path to the conversation file."""
        return self.conversations_dir / f"{conversation_id}.json"
    
    def _get_summary_path(self, conversation_id: str) -> Path:
        """Get the path to the summary file."""
        return self.summaries_dir / f"{conversation_id}.txt"
    
    def save_messages(self, conversation_id: str, messages: List[Dict[str, Any]]) -> None:
        """Save messages to a JSON file."""
        # Add timestamps to messages if they don't have them
        timestamped_messages = [self.add_timestamp(msg) for msg in messages]
        
        file_path = self._get_conversation_path(conversation_id)
        
        # Load existing messages if the file exists
        existing_messages = []
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    existing_messages = json.load(f)
            except json.JSONDecodeError:
                # If the file is corrupted, start fresh
                existing_messages = []
        
        # Combine existing and new messages
        all_messages = existing_messages + timestamped_messages
        
        # Write all messages to the file
        with open(file_path, 'w') as f:
            json.dump(all_messages, f, indent=2)
    
    def load_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load messages from a JSON file."""
        file_path = self._get_conversation_path(conversation_id)
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r') as f:
                messages = json.load(f)
            
            # Sort messages by timestamp
            messages.sort(key=lambda x: x.get('timestamp', 0))
            
            # Apply limit if specified
            if limit is not None:
                messages = messages[-limit:]
            
            return messages
        except json.JSONDecodeError:
            # If the file is corrupted, return an empty list
            return []
    
    def get_summary(self, conversation_id: str) -> str:
        """Get the summary of a conversation."""
        summary_path = self._get_summary_path(conversation_id)
        
        if not summary_path.exists():
            return ""
        
        with open(summary_path, 'r') as f:
            return f.read()
    
    def save_summary(self, conversation_id: str, summary: str) -> None:
        """Save a summary of a conversation."""
        summary_path = self._get_summary_path(conversation_id)
        
        with open(summary_path, 'w') as f:
            f.write(summary)
    
    def list_conversations(self) -> List[str]:
        """List all available conversation IDs."""
        conversation_files = list(self.conversations_dir.glob("*.json"))
        return [f.stem for f in conversation_files]
    
    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and its summary."""
        conversation_path = self._get_conversation_path(conversation_id)
        summary_path = self._get_summary_path(conversation_id)
        
        if conversation_path.exists():
            conversation_path.unlink()
        
        if summary_path.exists():
            summary_path.unlink()