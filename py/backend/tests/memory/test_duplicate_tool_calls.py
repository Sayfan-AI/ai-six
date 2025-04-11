import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path

from py.backend.memory.file_memory_provider import FileMemoryProvider


class TestDuplicateToolCalls(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.memory_provider = FileMemoryProvider(self.test_dir)
        
        # Sample conversation with duplicate tool_call_id
        self.sample_conversation = [
            {
                "role": "user",
                "content": "Hello, can you help me list files?",
                "timestamp": 1712345678.0
            },
            {
                "role": "assistant",
                "content": "I'll help you list files.",
                "tool_calls": [
                    {
                        "id": "call_123456",
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
                "tool_call_id": "call_123456",
                "name": "execute_bash",
                "content": "file1.txt file2.txt",
                "timestamp": 1712345680.0
            },
            {
                "role": "assistant",
                "content": "I'll now check another directory.",
                "tool_calls": [
                    {
                        "id": "call_123456",  # Duplicate tool_call_id
                        "type": "function",
                        "function": {
                            "name": "execute_bash",
                            "arguments": "{\"command\": \"ls -la /tmp\"}"
                        }
                    }
                ],
                "timestamp": 1712345681.0
            },
            {
                "role": "tool",
                "tool_call_id": "call_123456",  # Duplicate tool_call_id reference
                "name": "execute_bash",
                "content": "temp1.txt temp2.txt",
                "timestamp": 1712345682.0
            }
        ]
        
        # Conversation ID for testing
        self.conversation_id = "test-duplicate-tool-calls"
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_validate_duplicate_tool_calls(self):
        """Test that duplicate tool_call_ids are properly handled."""
        # Save the conversation with duplicate tool_call_ids
        self.memory_provider.save_messages(self.conversation_id, self.sample_conversation)
        
        # Load the conversation back
        loaded_messages = self.memory_provider.load_messages(self.conversation_id)
        
        # Check that the validation process handled the duplicates correctly
        # We should have 5 messages in the original conversation
        self.assertEqual(len(self.sample_conversation), 5)
        
        # After validation, we should have 5 messages, but with unique tool_call_ids
        # or the duplicates should be removed
        self.assertLessEqual(len(loaded_messages), 5)
        
        # Check that there are no duplicate tool_call_ids in the loaded messages
        tool_call_ids = set()
        for msg in loaded_messages:
            if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                for tool_call in msg['tool_calls']:
                    self.assertNotIn(tool_call['id'], tool_call_ids, 
                                    f"Duplicate tool_call_id found: {tool_call['id']}")
                    tool_call_ids.add(tool_call['id'])
        
        # Verify that each tool message has a corresponding assistant message with the tool_call
        tool_messages = [msg for msg in loaded_messages if msg.get('role') == 'tool']
        for tool_msg in tool_messages:
            tool_call_id = tool_msg.get('tool_call_id')
            self.assertIsNotNone(tool_call_id, "Tool message missing tool_call_id")
            
            # Find a corresponding assistant message with this tool_call_id
            found = False
            for msg in loaded_messages:
                if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                    for tool_call in msg['tool_calls']:
                        if tool_call['id'] == tool_call_id:
                            found = True
                            break
            
            self.assertTrue(found, f"No assistant message found with tool_call_id: {tool_call_id}")


if __name__ == "__main__":
    unittest.main()