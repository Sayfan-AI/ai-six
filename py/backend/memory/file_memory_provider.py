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
        print(f"[DEBUG] Saving {len(messages)} messages for conversation {conversation_id}")
        
        # Add timestamps to messages if they don't have them
        timestamped_messages = [self.add_timestamp(msg) for msg in messages]
        
        file_path = self._get_conversation_path(conversation_id)
        print(f"[DEBUG] Saving to file: {file_path}")
        
        # Load existing messages if the file exists
        existing_messages = []
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    existing_messages = json.load(f)
                print(f"[DEBUG] Loaded {len(existing_messages)} existing messages from file")
            except json.JSONDecodeError:
                # If the file is corrupted, start fresh
                print(f"[DEBUG] JSON decode error when loading existing messages, starting fresh")
                existing_messages = []
        
        # Combine existing and new messages
        all_messages = existing_messages + timestamped_messages
        print(f"[DEBUG] Combined message count: {len(all_messages)}")
        
        # Validate messages before saving
        print(f"[DEBUG] Validating {len(all_messages)} messages before saving conversation {conversation_id}")
        
        # Print some info about tool_call_ids
        tool_call_ids = set()
        for msg in all_messages:
            if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                for tool_call in msg['tool_calls']:
                    if 'id' in tool_call:
                        tool_call_ids.add(tool_call['id'])
            if msg.get('role') == 'tool' and 'tool_call_id' in msg:
                tool_call_ids.add(msg['tool_call_id'])
        
        print(f"[DEBUG] Found {len(tool_call_ids)} unique tool_call_ids before validation")
        
        validated_messages = self._validate_message_structure(all_messages)
        print(f"[DEBUG] After validation: {len(validated_messages)} messages")
        
        # Check tool_call_ids after validation
        tool_call_ids_after = set()
        for msg in validated_messages:
            if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                for tool_call in msg['tool_calls']:
                    if 'id' in tool_call:
                        tool_call_ids_after.add(tool_call['id'])
            if msg.get('role') == 'tool' and 'tool_call_id' in msg:
                tool_call_ids_after.add(msg['tool_call_id'])
        
        print(f"[DEBUG] Found {len(tool_call_ids_after)} unique tool_call_ids after validation")
        
        # Write validated messages to the file
        with open(file_path, 'w') as f:
            json.dump(validated_messages, f, indent=2)
        print(f"[DEBUG] Successfully saved {len(validated_messages)} messages to {file_path}")
    
    def load_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load messages from a JSON file."""
        file_path = self._get_conversation_path(conversation_id)
        print(f"[DEBUG] Loading messages from {file_path}")
        
        if not file_path.exists():
            print(f"[DEBUG] File does not exist: {file_path}")
            return []
        
        try:
            with open(file_path, 'r') as f:
                messages = json.load(f)
            
            print(f"[DEBUG] Loaded {len(messages)} messages from file")
            
            # Sort messages by timestamp
            messages.sort(key=lambda x: x.get('timestamp', 0))
            print(f"[DEBUG] Sorted messages by timestamp")
            
            # Apply limit if specified
            if limit is not None:
                original_count = len(messages)
                messages = messages[-limit:]
                print(f"[DEBUG] Applied limit: {limit}, reduced from {original_count} to {len(messages)} messages")
            
            # Print some info about tool_call_ids before validation
            tool_call_ids = set()
            for msg in messages:
                if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                    for tool_call in msg['tool_calls']:
                        if 'id' in tool_call:
                            tool_call_ids.add(tool_call['id'])
                if msg.get('role') == 'tool' and 'tool_call_id' in msg:
                    tool_call_ids.add(msg['tool_call_id'])
            
            print(f"[DEBUG] Found {len(tool_call_ids)} unique tool_call_ids before validation")
            
            # Validate and fix message structure
            print(f"[DEBUG] Validating {len(messages)} messages")
            validated_messages = self._validate_message_structure(messages)
            print(f"[DEBUG] After validation: {len(validated_messages)} messages")
            
            # Print some info about tool_call_ids after validation
            tool_call_ids_after = set()
            for msg in validated_messages:
                if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                    for tool_call in msg['tool_calls']:
                        if 'id' in tool_call:
                            tool_call_ids_after.add(tool_call['id'])
                if msg.get('role') == 'tool' and 'tool_call_id' in msg:
                    tool_call_ids_after.add(msg['tool_call_id'])
            
            print(f"[DEBUG] Found {len(tool_call_ids_after)} unique tool_call_ids after validation")
            
            return validated_messages
        except json.JSONDecodeError as e:
            # If the file is corrupted, return an empty list
            print(f"[DEBUG] JSON decode error when loading messages: {e}")
            return []
            
    # Use the _validate_message_structure method from the parent class
    # This avoids duplicate code and ensures consistent validation
    
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