import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path

from py.backend.memory.file_memory_provider import FileMemoryProvider
from py.backend.engine.engine import Engine
from py.backend.llm_providers.llm_provider import LLMProvider, Response, ToolCall
from py.backend.tools.base.tool import Tool, Spec, Parameters, Parameter


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.mock_responses = []
        
    def add_mock_response(self, content, tool_calls=None):
        """Add a mock response to be returned by the send method."""
        self.mock_responses.append(Response(
            content=content,
            role="assistant",
            tool_calls=tool_calls or []
        ))
        
    def send(self, messages, tool_dict, model=None):
        """Return the next mock response."""
        if not self.mock_responses:
            return Response(content="Default response", role="assistant", tool_calls=[])
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
            ]
        }
        



class MockTool(Tool):
    """Mock tool for testing."""
    
    def __init__(self):
        self.spec = Spec(
            name="test_tool",
            description="A test tool",
            parameters=Parameters(
                properties=[],
                required=[]
            )
        )
        
    def run(self, **kwargs):
        return "Mock tool result"


class TestMessageSequence(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.memory_provider = FileMemoryProvider(self.test_dir)
        
        # Create a mock LLM provider
        self.llm_provider = MockLLMProvider()
        
        # Create an engine with the mock provider
        self.engine = Engine(
            llm_providers=[self.llm_provider],
            default_model_id="mock-model",
            tools_dir="/workspace/ai-six/py/backend/tools",
            memory_provider=self.memory_provider,
            conversation_id="test-sequence"
        )
        
        # Add our mock tool to the engine's tool dictionary
        mock_tool = MockTool()
        self.engine.tool_dict[mock_tool.spec.name] = mock_tool
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_message_sequence_validation(self):
        """Test that tool messages are only included after assistant messages with tool_calls."""
        # Create a test conversation with invalid message sequence
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "tool", "tool_call_id": "invalid_call", "name": "test_tool", "content": "This should be filtered out"},
            {"role": "assistant", "content": "I'll help you with that", "tool_calls": [
                {"id": "call_123", "type": "function", "function": {"name": "test_tool", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "call_123", "name": "test_tool", "content": "Valid tool result"},
            {"role": "user", "content": "Thanks"},
            {"role": "tool", "tool_call_id": "orphaned_call", "name": "test_tool", "content": "This should also be filtered out"},
            {"role": "assistant", "content": "You're welcome"}
        ]
        
        # Save the messages
        self.memory_provider.save_messages("test-sequence", messages)
        
        # Load the conversation into the engine
        self.engine.load_conversation("test-sequence")
        
        # Validate messages before sending
        self.engine._validate_messages_before_send()
        
        # Check that invalid tool messages were filtered out
        tool_messages = [msg for msg in self.engine.messages if msg.get("role") == "tool"]
        self.assertEqual(len(tool_messages), 1, "Only one valid tool message should remain")
        
        # Check that the remaining tool message has the correct tool_call_id
        self.assertEqual(tool_messages[0]["tool_call_id"], "call_123", "Only the valid tool message should remain")
        
        # Check the total number of messages
        # We should have: system (summary), user, assistant with tool_calls, tool, user, assistant
        # The two invalid tool messages should be filtered out
        self.assertEqual(len(self.engine.messages), 5, "There should be 5 messages after validation")
        
    def test_tool_message_generation(self):
        """Test that tool messages are only generated after assistant messages with tool_calls."""
        # Set up a mock response with tool calls
        self.llm_provider.add_mock_response(
            content="I'll help you with that",
            tool_calls=[
                ToolCall(
                    id="call_abc",
                    name="test_tool",
                    arguments="{}",
                    required=[]
                )
            ]
        )
        
        # Send a message to trigger the tool call
        def on_tool_call(name, args, result):
            pass
            
        self.engine.send_message("Hello", "mock-model", on_tool_call)
        
        # Check that we have the correct sequence of messages:
        # 1. User message
        # 2. Assistant message with tool_calls
        # 3. Tool message with matching tool_call_id
        self.assertEqual(len(self.engine.messages), 4, "There should be 4 messages after tool call")
        
        # Check the roles of the messages
        self.assertEqual(self.engine.messages[0]["role"], "user")
        self.assertEqual(self.engine.messages[1]["role"], "assistant")
        self.assertEqual(self.engine.messages[2]["role"], "tool")
        
        # Check that the tool message has the correct tool_call_id
        self.assertEqual(self.engine.messages[2]["tool_call_id"], "call_abc")
        
        # Check that the tool_call_id in the tool message matches one in the assistant message
        assistant_tool_call_ids = [
            tc["id"] for tc in self.engine.messages[1]["tool_calls"]
        ]
        self.assertIn(self.engine.messages[2]["tool_call_id"], assistant_tool_call_ids)


if __name__ == "__main__":
    unittest.main()