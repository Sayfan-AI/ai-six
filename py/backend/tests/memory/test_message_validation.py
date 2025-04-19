import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path

from py.backend.memory.file_memory_provider import FileMemoryProvider


class TestMessageValidation(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.memory_provider = FileMemoryProvider(self.test_dir)
        self.conversation_id = "test_conversation"
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_validate_message_structure(self):
        # Create a test conversation with invalid tool messages
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "I'll help you with that", "tool_calls": [
                {"id": "call_123", "type": "function", "function": {"name": "test_tool", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "call_123", "name": "test_tool", "content": "Tool result"},
            {"role": "tool", "tool_call_id": "call_456", "name": "invalid_tool", "content": "This should be filtered out"},
            {"role": "assistant", "content": "Done"}
        ]
        
        # Save the messages
        self.memory_provider.save_messages(self.conversation_id, messages)
        
        # Load and validate the messages
        loaded_messages = self.memory_provider.load_messages(self.conversation_id)
        
        # Check that the invalid tool message was filtered out
        self.assertEqual(len(loaded_messages), 4)  # Only 4 messages should remain
        
        # Check that all tool messages have corresponding tool calls
        tool_messages = [msg for msg in loaded_messages if msg.get("role") == "tool"]
        for tool_msg in tool_messages:
            self.assertEqual(tool_msg["tool_call_id"], "call_123")  # Only the valid tool call should remain
            
    def test_empty_messages(self):
        # Test with empty messages list
        validated = self.memory_provider._validate_message_structure([])
        self.assertEqual(validated, [])
        
    def test_missing_role(self):
        # Test with a message missing the role field
        messages = [
            {"content": "This message has no role"}
        ]
        validated = self.memory_provider._validate_message_structure(messages)
        self.assertEqual(validated, [])
        
    def test_tool_without_tool_call_id(self):
        # Test with a tool message missing tool_call_id
        messages = [
            {"role": "tool", "name": "test_tool", "content": "Missing tool_call_id"}
        ]
        validated = self.memory_provider._validate_message_structure(messages)
        self.assertEqual(validated, [])
        
    def test_complex_conversation(self):
        # Create a more complex conversation with multiple tool calls
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "I'll help you", "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "call_1", "name": "tool1", "content": "Result 1"},
            {"role": "assistant", "content": "Let me try another tool", "tool_calls": [
                {"id": "call_2", "type": "function", "function": {"name": "tool2", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "call_2", "name": "tool2", "content": "Result 2"},
            {"role": "assistant", "content": "Done"}
        ]
        
        # Validate the messages
        validated = self.memory_provider._validate_message_structure(messages)
        
        # All messages should be valid
        self.assertEqual(len(validated), 6)
        
        # Check that tool messages have the correct tool_call_id
        self.assertEqual(validated[2]["tool_call_id"], "call_1")
        self.assertEqual(validated[4]["tool_call_id"], "call_2")


if __name__ == "__main__":
    unittest.main()