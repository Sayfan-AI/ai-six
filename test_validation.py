import json
import os
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from py.backend.memory.memory_provider import MemoryProvider
from py.backend.memory.file_memory_provider import FileMemoryProvider

def create_test_conversation():
    """Create a test conversation with duplicate tool messages."""
    # Create a test directory
    test_dir = Path("/workspace/ai-six/test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Create conversations directory
    conversations_dir = test_dir / "conversations"
    conversations_dir.mkdir(exist_ok=True)
    
    # Create a test conversation with duplicate tool messages
    messages = [
        {
            "role": "user",
            "content": "Hello, can you help me list files in the current directory?",
            "timestamp": 1712345678.0
        },
        {
            "role": "assistant",
            "content": "I'll help you list files in the current directory. Let me do that for you.",
            "tool_calls": [
                {
                    "id": "call_Q8a2LLCNYlGQeFYY066Jvyp8",
                    "type": "function",
                    "function": {
                        "name": "execute_bash",
                        "arguments": "{\"command\": \"ls -la\"}"
                    }
                }
            ],
            "timestamp": 1712345679.0
        },
        {
            "role": "tool",
            "tool_call_id": "call_Q8a2LLCNYlGQeFYY066Jvyp8",
            "name": "execute_bash",
            "content": "total 16\ndrwxr-xr-x  4 user user 4096 Apr  9 12:34 .\ndrwxr-xr-x 10 user user 4096 Apr  9 12:30 ..\ndrwxr-xr-x  2 user user 4096 Apr  9 12:32 py\ndrwxr-xr-x  2 user user 4096 Apr  9 12:33 test_data",
            "timestamp": 1712345680.0
        },
        {
            "role": "tool",
            "tool_call_id": "call_Q8a2LLCNYlGQeFYY066Jvyp8",
            "name": "execute_bash",
            "content": "total 16\ndrwxr-xr-x  4 user user 4096 Apr  9 12:34 .\ndrwxr-xr-x 10 user user 4096 Apr  9 12:30 ..\ndrwxr-xr-x  2 user user 4096 Apr  9 12:32 py\ndrwxr-xr-x  2 user user 4096 Apr  9 12:33 test_data",
            "timestamp": 1712345681.0
        },
        {
            "role": "assistant",
            "content": "Here are the files in your current directory:\n\n```\ntotal 16\ndrwxr-xr-x  4 user user 4096 Apr  9 12:34 .\ndrwxr-xr-x 10 user user 4096 Apr  9 12:30 ..\ndrwxr-xr-x  2 user user 4096 Apr  9 12:32 py\ndrwxr-xr-x  2 user user 4096 Apr  9 12:33 test_data\n```\n\nYou have:\n- A `py` directory\n- A `test_data` directory\n\nIs there anything specific you'd like to know about these files or directories?",
            "timestamp": 1712345682.0
        },
        {
            "role": "user",
            "content": "Can you tell me what's in the py directory?",
            "timestamp": 1712345683.0
        },
        {
            "role": "assistant",
            "content": "I'll check what's in the py directory for you.",
            "tool_calls": [
                {
                    "id": "call_nHSRVhACvOFTDtetA1nk16dk",
                    "type": "function",
                    "function": {
                        "name": "execute_bash",
                        "arguments": "{\"command\": \"ls -la py\"}"
                    }
                }
            ],
            "timestamp": 1712345684.0
        },
        {
            "role": "tool",
            "tool_call_id": "call_nHSRVhACvOFTDtetA1nk16dk",
            "name": "execute_bash",
            "content": "total 12\ndrwxr-xr-x 2 user user 4096 Apr  9 12:32 .\ndrwxr-xr-x 4 user user 4096 Apr  9 12:34 ..\n-rw-r--r-- 1 user user  123 Apr  9 12:32 __init__.py\ndrwxr-xr-x 3 user user 4096 Apr  9 12:32 backend",
            "timestamp": 1712345685.0
        },
        {
            "role": "assistant",
            "content": "Here's what's in the py directory:\n\n```\ntotal 12\ndrwxr-xr-x 2 user user 4096 Apr  9 12:32 .\ndrwxr-xr-x 4 user user 4096 Apr  9 12:34 ..\n-rw-r--r-- 1 user user  123 Apr  9 12:32 __init__.py\ndrwxr-xr-x 3 user user 4096 Apr  9 12:32 backend\n```\n\nThe py directory contains:\n- An `__init__.py` file, which makes the directory a Python package\n- A `backend` directory, which is likely where the backend code is stored\n\nWould you like me to explore the backend directory as well?",
            "timestamp": 1712345686.0
        },
        {
            "role": "user",
            "content": "Yes, please show me what's in the backend directory.",
            "timestamp": 1712345687.0
        },
        {
            "role": "assistant",
            "content": "I'll check what's in the backend directory for you.",
            "tool_calls": [
                {
                    "id": "call_nHSRVhACvOFTDtetA1nk16dk",
                    "type": "function",
                    "function": {
                        "name": "execute_bash",
                        "arguments": "{\"command\": \"ls -la py/backend\"}"
                    }
                }
            ],
            "timestamp": 1712345688.0
        }
    ]
    
    # Write the test conversation to a file
    with open(conversations_dir / "test_conversation.json", "w") as f:
        json.dump(messages, f, indent=2)
    
    print(f"Created test conversation with {len(messages)} messages")
    return str(conversations_dir / "test_conversation.json")

def test_memory_provider_validation():
    """Test the memory provider validation."""
    # Create a test conversation
    test_file = create_test_conversation()
    
    # Load the test conversation
    with open(test_file, "r") as f:
        messages = json.load(f)
    
    print(f"Original message count: {len(messages)}")
    
    # Create a file memory provider (since MemoryProvider is abstract)
    test_dir = Path("/workspace/ai-six/test_data")
    memory_provider = FileMemoryProvider(str(test_dir))
    
    # Validate the messages
    validated_messages = memory_provider._validate_message_structure(messages)
    
    print(f"Validated message count: {len(validated_messages)}")
    
    # Check for duplicate tool messages
    tool_call_ids = {}
    for i, message in enumerate(validated_messages):
        if message.get("role") == "tool" and "tool_call_id" in message:
            tool_call_id = message["tool_call_id"]
            if tool_call_id in tool_call_ids:
                print(f"ERROR: Duplicate tool_call_id {tool_call_id} found at positions {tool_call_ids[tool_call_id]} and {i}")
            else:
                tool_call_ids[tool_call_id] = i
    
    print("Tool call IDs found:", list(tool_call_ids.keys()))
    
    # Write the validated messages back to the file
    with open(test_file, "w") as f:
        json.dump(validated_messages, f, indent=2)
    
    print(f"Wrote validated messages to {test_file}")

def test_file_memory_provider():
    """Test the file memory provider."""
    # Create a test directory
    test_dir = Path("/workspace/ai-six/test_data")
    
    # Create a file memory provider
    memory_provider = FileMemoryProvider(str(test_dir))
    
    # Load the test conversation
    messages = memory_provider.load_messages("test_conversation")
    
    print(f"Loaded {len(messages)} messages from test_conversation")
    
    # Check for duplicate tool messages
    tool_call_ids = {}
    for i, message in enumerate(messages):
        if message.get("role") == "tool" and "tool_call_id" in message:
            tool_call_id = message["tool_call_id"]
            if tool_call_id in tool_call_ids:
                print(f"ERROR: Duplicate tool_call_id {tool_call_id} found at positions {tool_call_ids[tool_call_id]} and {i}")
            else:
                tool_call_ids[tool_call_id] = i
    
    print("Tool call IDs found:", list(tool_call_ids.keys()))

if __name__ == "__main__":
    print("Testing memory provider validation...")
    test_memory_provider_validation()
    
    print("\nTesting file memory provider...")
    test_file_memory_provider()