import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path

from py.backend.engine.engine import Engine
from py.backend.engine.session import Session
from py.backend.engine.session_manager import SessionManager
from py.backend.engine.llm_provider import LLMProvider, Response


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.mock_responses = []
        
    def add_mock_response(self, content, tool_calls=None):
        """Add a mock response to be returned by the send method."""
        self.mock_responses.append(Response(
            content=content,
            role="assistant",
            tool_calls=tool_calls or [],
            usage=None
        ))
        
    def send(self, messages, tool_dict, model=None):
        """Return the next mock response."""
        if not self.mock_responses:
            return Response(content="Default response", role="assistant", tool_calls=[], usage=None)
        return self.mock_responses.pop(0)
        
    @property
    def models(self):
        return ["mock-model"]
        
    def model_response_to_message(self, response):
        """Convert a response to a message."""
        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [
                {
                    "id": t.id,
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "arguments": t.arguments
                    }
                } for t in response.tool_calls
            ] if response.tool_calls else []
        }


class TestMessageValidation(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a mock LLM provider
        self.llm_provider = MockLLMProvider()
        
        # Create an engine with the mock provider
        self.engine = Engine(
            llm_providers=[self.llm_provider],
            default_model_id="mock-model",
            tools_dir="/Users/gigi/git/ai-six/py/backend/tools",
            memory_dir=self.test_dir
        )
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_validate_message_structure(self):
        # Create a test session with invalid tool messages
        self.engine.session.messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "I'll help you with that", "tool_calls": [
                {"id": "call_123", "type": "function", "function": {"name": "test_tool", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "call_123", "name": "test_tool", "content": "Tool result"},
            {"role": "tool", "tool_call_id": "call_456", "name": "invalid_tool", "content": "This should be filtered out"},
            {"role": "assistant", "content": "Done"}
        ]
        
        # Validate the messages
        self.engine._validate_messages_before_send()
        
        # Check that the invalid tool message was filtered out
        self.assertEqual(len(self.engine.session.messages), 4)  # Only 4 messages should remain
        
        # Check that all tool messages have corresponding tool calls
        tool_messages = [msg for msg in self.engine.session.messages if msg.get("role") == "tool"]
        for tool_msg in tool_messages:
            self.assertEqual(tool_msg["tool_call_id"], "call_123")  # Only the valid tool call should remain
            
    def test_empty_messages(self):
        # Test with empty messages list
        self.engine.session.messages = []
        self.engine._validate_messages_before_send()
        self.assertEqual(self.engine.session.messages, [])
        
    def test_missing_role(self):
        # Test with a message missing the role field
        self.engine.session.messages = [
            {"content": "This message has no role"}
        ]
        self.engine._validate_messages_before_send()
        self.assertEqual(self.engine.session.messages, [])
        
    def test_tool_without_tool_call_id(self):
        # Test with a tool message missing tool_call_id
        self.engine.session.messages = [
            {"role": "tool", "name": "test_tool", "content": "Missing tool_call_id"}
        ]
        self.engine._validate_messages_before_send()
        self.assertEqual(self.engine.session.messages, [])
        
    def test_complex_session(self):
        # Create a more complex session with multiple tool calls
        self.engine.session.messages = [
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
        self.engine._validate_messages_before_send()
        
        # All messages should be valid
        self.assertEqual(len(self.engine.session.messages), 6)
        
        # Check that tool messages have the correct tool_call_id
        self.assertEqual(self.engine.session.messages[2]["tool_call_id"], "call_1")
        self.assertEqual(self.engine.session.messages[4]["tool_call_id"], "call_2")
        
    def test_session_save_load_validation(self):
        # Create a test conversation with some tool calls
        self.engine.session.messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "I'll help you", "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "call_1", "name": "tool1", "content": "Result 1"},
            {"role": "assistant", "content": "Done"}
        ]
        
        # Save the session
        session_id = self.engine.session.session_id
        self.engine.session.save()
        
        # Create a new session and load the saved data
        new_session = Session(self.test_dir)
        new_session.load(session_id)
        
        # Check that the loaded messages match the original ones
        self.assertEqual(len(new_session.messages), 4)
        self.assertEqual(new_session.messages[0]["role"], "user")
        self.assertEqual(new_session.messages[1]["role"], "assistant")
        self.assertEqual(new_session.messages[2]["role"], "tool")
        self.assertEqual(new_session.messages[3]["role"], "assistant")
        
        # Check that the tool call information is preserved
        self.assertEqual(new_session.messages[1]["tool_calls"][0]["id"], "call_1")
        self.assertEqual(new_session.messages[2]["tool_call_id"], "call_1")


if __name__ == "__main__":
    unittest.main()