import unittest
import tempfile
import os
import json
import shutil

from py.backend.engine.session import Session
from py.backend.engine.object_model import Usage, ToolCall


class TestSession(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.session = Session(self.test_dir)
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_initialization(self):
        """Test that the Session is initialized correctly."""
        self.assertIsNotNone(self.session.session_id)
        self.assertTrue(self.session.title.startswith('Untiled session ~'))
        self.assertEqual(self.session.messages, [])
        self.assertEqual(self.session.usage.input_tokens, 0)
        self.assertEqual(self.session.usage.output_tokens, 0)
        
    def test_save_and_load(self):
        """Test saving and loading a session with dictionary messages."""
        # Create some test messages as dictionaries
        user_message = {
            "role": "user",
            "content": "Hello AI!",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 0
            }
        }
        
        assistant_message = {
            "role": "assistant",
            "content": "Hello! How can I help you today?",
            "usage": {
                "input_tokens": 0,
                "output_tokens": 15
            }
        }
        
        # Add messages to the session
        self.session.messages = [user_message, assistant_message]
        self.session.usage = Usage(10, 15)
        
        # Save the session
        self.session.save()
        
        # Check that the file was created
        filename = f"{self.test_dir}/{self.session.session_id}.json"
        self.assertTrue(os.path.exists(filename))
        
        # Create a new session and load the data
        new_session = Session(self.test_dir)
        new_session.load(self.session.session_id)
        
        # Check that the data was loaded correctly
        self.assertEqual(new_session.session_id, self.session.session_id)
        self.assertEqual(new_session.title, self.session.title)
        self.assertEqual(len(new_session.messages), 2)
        
        # Verify messages are loaded as dictionaries with the right structure
        self.assertIsInstance(new_session.messages[0], dict)
        self.assertEqual(new_session.messages[0]["role"], "user")
        self.assertEqual(new_session.messages[0]["content"], "Hello AI!")
        self.assertEqual(new_session.messages[0]["usage"]["input_tokens"], 10)
        
        # Check usage is still a Usage object
        self.assertIsInstance(new_session.usage, Usage)
        self.assertEqual(new_session.usage.input_tokens, 10)
        self.assertEqual(new_session.usage.output_tokens, 15)
        
    def test_complex_session(self):
        """Test session with tool calls and tool responses."""
        # Create a user message
        user_message = {
            "role": "user",
            "content": "What files are in the current directory?",
            "usage": {
                "input_tokens": 12,
                "output_tokens": 0
            }
        }
        
        # Create an assistant message with tool calls
        assistant_message = {
            "role": "assistant",
            "content": "Let me check the files for you.",
            "tool_calls": [
                {
                    "id": "call_123",
                    "name": "ls",
                    "arguments": {"path": "."},
                    "required": ["path"]
                }
            ],
            "usage": {
                "input_tokens": 0,
                "output_tokens": 18
            }
        }
        
        # Create a tool response message
        tool_response = {
            "role": "tool",
            "tool_call_id": "call_123",
            "name": "ls",
            "content": '{"result": ["file1.txt", "file2.py", "folder1"]}'
        }
        
        # Create a final assistant message
        final_response = {
            "role": "assistant",
            "content": "I found these files in the current directory: file1.txt, file2.py, and a folder called folder1.",
            "usage": {
                "input_tokens": 0,
                "output_tokens": 25
            }
        }
        
        # Add all messages to the session
        self.session.messages = [user_message, assistant_message, tool_response, final_response]
        self.session.usage = Usage(12, 43)  # Combined usage
        
        # Save the session
        self.session.save()
        
        # Create a new session and load the data
        new_session = Session(self.test_dir)
        new_session.load(self.session.session_id)
        
        # Check that the data was loaded correctly
        self.assertEqual(len(new_session.messages), 4)
        
        # Test message structure
        self.assertEqual(new_session.messages[0]["role"], "user")
        self.assertEqual(new_session.messages[1]["role"], "assistant")
        self.assertEqual(new_session.messages[2]["role"], "tool")
        self.assertEqual(new_session.messages[3]["role"], "assistant")
        
        # Check tool calls were loaded correctly as dictionaries
        self.assertIsNotNone(new_session.messages[1]["tool_calls"])
        self.assertEqual(new_session.messages[1]["tool_calls"][0]["id"], "call_123")
        self.assertEqual(new_session.messages[1]["tool_calls"][0]["name"], "ls")
        self.assertEqual(new_session.messages[1]["tool_calls"][0]["arguments"]["path"], ".")
        
        # Check tool response structure
        self.assertEqual(new_session.messages[2]["tool_call_id"], "call_123")
        self.assertEqual(new_session.messages[2]["name"], "ls")
        
        # Check usage
        self.assertEqual(new_session.usage.input_tokens, 12)
        self.assertEqual(new_session.usage.output_tokens, 43)
        
    def test_add_message(self):
        """Test adding a message and updating the usage stats."""
        # Create a message
        message = {
            "role": "user",
            "content": "Hello",
            "usage": {
                "input_tokens": 5,
                "output_tokens": 0
            }
        }
        
        # Add the message
        self.session.add_message(message)
        
        # Check that the message was added
        self.assertEqual(len(self.session.messages), 1)
        self.assertEqual(self.session.messages[0]["role"], "user")
        
        # Check that usage was updated
        self.assertEqual(self.session.usage.input_tokens, 5)
        self.assertEqual(self.session.usage.output_tokens, 0)
        
        # Add another message
        assistant_message = {
            "role": "assistant",
            "content": "Hello there!",
            "usage": {
                "input_tokens": 0,
                "output_tokens": 8
            }
        }
        
        self.session.add_message(assistant_message)
        
        # Check cumulative usage
        self.assertEqual(self.session.usage.input_tokens, 5)
        self.assertEqual(self.session.usage.output_tokens, 8)


if __name__ == "__main__":
    unittest.main()