import unittest
import tempfile
import shutil
import os
from unittest.mock import MagicMock, patch

from py.backend.engine.engine import Engine
from py.backend.memory.file_memory_provider import FileMemoryProvider
from py.backend.llm_providers.llm_provider import LLMProvider, Response, ToolCall


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self._models = ["test-model"]
        self.responses = []
        
    def add_response(self, content, tool_calls=None):
        """Add a response to the queue."""
        if tool_calls is None:
            tool_calls = []
        self.responses.append(Response(content=content, role="assistant", tool_calls=tool_calls))
        
    def send(self, messages, tool_list, model=None):
        """Return the next response in the queue."""
        if not self.responses:
            return Response(content="Default response", role="assistant", tool_calls=[])
        return self.responses.pop(0)
        
    @property
    def models(self):
        """Return the list of available models."""
        return self._models
        
    def model_response_to_message(self, response):
        """Convert the response to a message format."""
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
        
    def tool_result_to_message(self, tool_call, tool_result):
        """Convert the tool execution result to a message."""
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.name,
            "content": str(tool_result),
        }


class TestEngineMemory(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a memory provider
        self.memory_provider = FileMemoryProvider(self.test_dir)
        
        # Create a mock LLM provider
        self.llm_provider = MockLLMProvider()
        
        # Create a mock tools directory
        self.tools_dir = os.path.join(os.path.dirname(__file__), "../../tools")
        
        # Create an engine with memory support
        self.engine = Engine(
            llm_providers=[self.llm_provider],
            default_model_id="test-model",
            tools_dir=self.tools_dir,
            memory_provider=self.memory_provider,
            conversation_id="test-conversation"
        )
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_conversation_id(self):
        """Test that the engine sets the conversation ID correctly."""
        self.assertEqual(self.engine.get_conversation_id(), "test-conversation")
        
    def test_save_and_load_conversation(self):
        """Test saving and loading a conversation."""
        # Add some messages to the engine
        self.engine.messages = [
            {"role": "user", "content": "Hello, AI-6!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        
        # Save the conversation
        self.engine._save_conversation()
        
        # Clear the messages
        self.engine.messages = []
        
        # Load the conversation
        self.engine._load_conversation()
        
        # Check that the messages were loaded correctly
        self.assertEqual(len(self.engine.messages), 2)
        self.assertEqual(self.engine.messages[0]["role"], "user")
        self.assertEqual(self.engine.messages[0]["content"], "Hello, AI-6!")
        self.assertEqual(self.engine.messages[1]["role"], "assistant")
        self.assertEqual(self.engine.messages[1]["content"], "Hello! How can I help you today!")
        
    def test_checkpoint_if_needed(self):
        """Test that checkpoints are created when needed."""
        # Add some messages to the engine
        self.engine.messages = [
            {"role": "user", "content": "Hello, AI-6!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        
        # Set up a spy on _save_conversation
        original_save = self.engine._save_conversation
        save_called = [0]
        
        def spy_save():
            save_called[0] += 1
            original_save()
            
        self.engine._save_conversation = spy_save
        
        # Call _checkpoint_if_needed multiple times
        for i in range(15):
            self.engine._checkpoint_if_needed()
            
        # Check that _save_conversation was called the expected number of times
        # With checkpoint_interval=10, it should be called once after 10 calls
        self.assertEqual(save_called[0], 1)
        
    def test_list_conversations(self):
        """Test listing conversations."""
        # Add some messages to the engine
        self.engine.messages = [
            {"role": "user", "content": "Hello, AI-6!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        
        # Save the conversation
        self.engine._save_conversation()
        
        # Create another conversation
        self.engine.conversation_id = "test-conversation-2"
        self.engine.messages = [
            {"role": "user", "content": "What can you do?"},
            {"role": "assistant", "content": "I can help with various tasks."}
        ]
        
        # Save the second conversation
        self.engine._save_conversation()
        
        # List conversations
        conversations = self.engine.list_conversations()
        
        # Check that both conversations are listed
        self.assertEqual(len(conversations), 2)
        self.assertIn("test-conversation", conversations)
        self.assertIn("test-conversation-2", conversations)
        
    def test_load_conversation_by_id(self):
        """Test loading a specific conversation."""
        # Add some messages to the engine
        self.engine.messages = [
            {"role": "user", "content": "Hello, AI-6!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        
        # Save the conversation
        self.engine._save_conversation()
        
        # Create another conversation
        self.engine.conversation_id = "test-conversation-2"
        self.engine.messages = [
            {"role": "user", "content": "What can you do?"},
            {"role": "assistant", "content": "I can help with various tasks."}
        ]
        
        # Save the second conversation
        self.engine._save_conversation()
        
        # Load the first conversation
        success = self.engine.load_conversation("test-conversation")
        
        # Check that the load was successful
        self.assertTrue(success)
        
        # Check that the conversation ID was updated
        self.assertEqual(self.engine.conversation_id, "test-conversation")
        
        # Check that the messages were loaded correctly
        self.assertEqual(len(self.engine.messages), 2)
        self.assertEqual(self.engine.messages[0]["role"], "user")
        self.assertEqual(self.engine.messages[0]["content"], "Hello, AI-6!")
        
    def test_load_nonexistent_conversation(self):
        """Test loading a conversation that doesn't exist."""
        # Try to load a nonexistent conversation
        success = self.engine.load_conversation("nonexistent-conversation")
        
        # Check that the load failed
        self.assertFalse(success)
        
        # Check that the conversation ID was not updated
        self.assertEqual(self.engine.conversation_id, "test-conversation")


if __name__ == "__main__":
    unittest.main()