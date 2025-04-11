import json
import os
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from py.backend.engine.engine import Engine
from py.backend.llm_providers.llm_provider import LLMProvider
from py.backend.memory.file_memory_provider import FileMemoryProvider

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self._models = ["gpt-4"]
    
    @property
    def models(self):
        return self._models
    
    def send(self, messages, tools, model_id):
        # We won't actually send any messages in this test
        return MagicMock()
    
    def model_response_to_message(self, response):
        return {"role": "assistant", "content": "This is a mock response"}
    
    def tool_result_to_message(self, tool_call, result):
        return {"role": "tool", "name": tool_call.name, "tool_call_id": tool_call.id, "content": result}

def test_message_sequence_validation():
    """Test that the message sequence validation correctly handles tool messages."""
    
    # Create a temporary directory for the memory provider
    temp_dir = Path("/tmp/test_memory_" + str(uuid.uuid4()))
    temp_dir.mkdir(exist_ok=True)
    
    # Create a memory provider
    memory_provider = FileMemoryProvider(str(temp_dir))
    
    # Create a mock LLM provider
    llm_provider = MockLLMProvider()
    
    # Create an engine
    engine = Engine(
        llm_providers=[llm_provider],
        default_model_id="gpt-4",
        tools_dir=str(Path(__file__).parent / "py" / "backend" / "tools"),
        memory_provider=memory_provider
    )
    
    # Create a conversation with an invalid message sequence
    # This simulates a conversation where tool messages appear without preceding tool_calls
    conversation_id = str(uuid.uuid4())
    
    # Create messages with invalid sequence
    invalid_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help you today?"},
        {"role": "user", "content": "What's the weather?"},
        {"role": "assistant", "content": "I'll check the weather for you."},
        # This tool message has no preceding message with tool_calls - should be removed
        {"role": "tool", "name": "get_weather", "tool_call_id": "call_123", "content": "It's sunny and 75°F."},
        {"role": "user", "content": "Thanks!"},
        {"role": "assistant", "content": "You're welcome!"},
        # Now add a valid sequence
        {"role": "user", "content": "What time is it?"},
        {"role": "assistant", "content": "I'll check the time for you.", "tool_calls": [
            {"id": "call_456", "type": "function", "function": {"name": "get_time", "arguments": "{}"}}
        ]},
        # This tool message should be kept because it follows a message with tool_calls
        {"role": "tool", "name": "get_time", "tool_call_id": "call_456", "content": "It's 3:00 PM."},
        {"role": "assistant", "content": "The current time is 3:00 PM."}
    ]
    
    # Save the invalid messages
    memory_provider.save_messages(conversation_id, invalid_messages)
    
    # Load the conversation
    engine.load_conversation(conversation_id)
    
    # Validate the messages before sending to LLM
    engine._validate_messages_before_send()
    
    # Check that the invalid tool message was removed
    tool_messages = [msg for msg in engine.messages if msg.get('role') == 'tool']
    print(f"Found {len(tool_messages)} tool messages after validation")
    
    # There should be only one tool message (the valid one)
    assert len(tool_messages) == 1, f"Expected 1 tool message, got {len(tool_messages)}"
    assert tool_messages[0]['tool_call_id'] == 'call_456', f"Expected tool_call_id 'call_456', got {tool_messages[0]['tool_call_id']}"
    
    print("Test passed! Message sequence validation is working correctly.")
    
    # Clean up
    memory_provider.delete_conversation(conversation_id)
    
    # Remove the directory and its contents
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_message_sequence_validation()