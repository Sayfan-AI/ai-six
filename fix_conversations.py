import json
import os
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from py.backend.memory.file_memory_provider import FileMemoryProvider

def fix_conversations(memory_dir):
    """
    Fix all conversations in the memory directory.
    
    Args:
        memory_dir: Path to the memory directory
    """
    memory_dir = Path(memory_dir)
    
    if not memory_dir.exists():
        print(f"Memory directory {memory_dir} does not exist")
        return
    
    # Check if this is a memory provider directory (has conversations subdirectory)
    conversations_dir = memory_dir / "conversations"
    if conversations_dir.exists() and conversations_dir.is_dir():
        print(f"Found conversations directory: {conversations_dir}")
        process_memory_provider(memory_dir)
    else:
        # Look for subdirectories that might be memory provider directories
        for subdir in memory_dir.iterdir():
            if not subdir.is_dir():
                continue
                
            conversations_subdir = subdir / "conversations"
            if conversations_subdir.exists() and conversations_subdir.is_dir():
                print(f"Found conversations directory in subdirectory: {conversations_subdir}")
                process_memory_provider(subdir)

def process_memory_provider(memory_dir):
    """
    Process a memory provider directory.
    
    Args:
        memory_dir: Path to the memory provider directory
    """
    # Create a file memory provider
    memory_provider = FileMemoryProvider(str(memory_dir))
    
    # Get all conversations
    conversations = memory_provider.list_conversations()
    
    print(f"Found {len(conversations)} conversations")
    
    # Process each conversation
    for conversation_id in conversations:
        print(f"Processing conversation: {conversation_id}")
        
        # Load the conversation
        messages = memory_provider.load_messages(conversation_id)
        
        print(f"Loaded {len(messages)} messages")
        
        # Save the conversation (this will validate and fix the messages)
        memory_provider.save_messages(conversation_id, messages)
        
        # Verify the fix
        fixed_messages = memory_provider.load_messages(conversation_id)
        
        print(f"After fixing: {len(fixed_messages)} messages")

if __name__ == "__main__":
    # Get the memory directory from command line or use default
    memory_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace/ai-six/memory"
    
    print(f"Fixing conversations in {memory_dir}")
    fix_conversations(memory_dir)