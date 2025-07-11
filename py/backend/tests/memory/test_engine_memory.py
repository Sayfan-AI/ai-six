import unittest
import tempfile
import shutil
import os
from unittest.mock import MagicMock, patch

from backend.engine.config import Config
from backend.engine.engine import Engine, generate_tool_call_id
from backend.object_model import LLMProvider, ToolCall, AssistantMessage
from backend.engine.session import Session
from backend.engine.session_manager import SessionManager


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.mock_responses = []
        
    def add_mock_response(self, content, tool_calls=None):
        """Add a mock response to be returned by the send method."""
        self.mock_responses.append(AssistantMessage(
            content=content,
            role="assistant",
            tool_calls=tool_calls,
            usage=None
        ))
        
    def send(self, messages, tool_dict, model=None):
        """Return the next mock response."""
        if not self.mock_responses:
            return AssistantMessage(content="Default response", role="assistant", tool_calls=None, usage=None)
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


class TestEngineMemory(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a mock LLM provider
        self.llm_provider = MockLLMProvider()
        
        # Create a config object for the engine
        
        # Create a config with the mock provider
        self.config = Config(
            default_model_id="mock-model",
            tools_dir="/Users/gigi/git/ai-six/py/backend/tools",
            mcp_tools_dir="/Users/gigi/git/ai-six/py/backend/mcp_tools",
            memory_dir=self.test_dir
        )
        
        # Patch the provider discovery method
        self.discover_patcher = patch('backend.engine.engine.Engine.discover_llm_providers')
        self.mock_discover = self.discover_patcher.start()
        self.mock_discover.return_value = [self.llm_provider]
        
        # Patch the tool discovery method to avoid actual discovery
        self.tool_patcher = patch('backend.engine.engine.Engine.discover_tools')
        self.mock_tool_discover = self.tool_patcher.start()
        self.mock_tool_discover.return_value = []
        
        # Patch the MCP tool discovery method to avoid actual discovery
        self.mcp_tool_patcher = patch('backend.engine.engine.Engine.discover_mcp_tools')
        self.mock_mcp_tool_discover = self.mcp_tool_patcher.start()
        self.mock_mcp_tool_discover.return_value = []
        
        # Patch the get_context_window_size function to return a fixed value for testing
        self.window_size_patcher = patch('backend.engine.engine.get_context_window_size')
        self.mock_window_size = self.window_size_patcher.start()
        self.mock_window_size.return_value = 1000
        
        # Create an engine with the config
        self.engine = Engine(self.config)
        
    def tearDown(self):
        # Stop the patchers
        self.discover_patcher.stop()
        self.tool_patcher.stop()
        self.mcp_tool_patcher.stop()
        self.window_size_patcher.stop()
        
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_session_initialization(self):
        """Test that the session is initialized correctly."""
        self.assertIsNotNone(self.engine.session)
        self.assertIsInstance(self.engine.session, Session)
        self.assertIsNotNone(self.engine.session_manager)
        self.assertIsInstance(self.engine.session_manager, SessionManager)
        self.assertEqual(len(self.engine.session.messages), 0)
        
    def test_send_message(self):
        """Test sending a message and receiving a response."""
        # Set up the mock response
        self.llm_provider.add_mock_response("I'll help you with that!")
        
        # Send a message
        response = self.engine.send_message("Hello", "mock-model", None)
        
        # Check the response
        self.assertEqual(response, "I'll help you with that!")
        
        # Check that the message was added to the session
        self.assertEqual(len(self.engine.session.messages), 2)
        self.assertEqual(self.engine.session.messages[0].role, "user")
        self.assertEqual(self.engine.session.messages[0].content, "Hello")
        self.assertEqual(self.engine.session.messages[1].role, "assistant")
        self.assertEqual(self.engine.session.messages[1].content, "I'll help you with that!")
        
    def test_session_saving(self):
        """Test that sessions are saved correctly."""
        # Set up the mock response
        self.llm_provider.add_mock_response("I'll help you with that!")
        
        # Send a message
        self.engine.send_message("Hello", "mock-model", None)
        
        # Explicitly save the session
        self.engine.session.save()
        
        # Get the session ID
        session_id = self.engine.get_session_id()
        
        # Check that the session file exists - file is now just session_id.json without a title
        session_file = f"{self.test_dir}/{session_id}.json"
        self.assertTrue(os.path.exists(session_file))
        
        # Create a new config with the session ID
        new_config = Config(
            default_model_id="mock-model",
            tools_dir="/Users/gigi/git/ai-six/py/backend/tools",
            mcp_tools_dir="/Users/gigi/git/ai-six/py/backend/mcp_tools",
            memory_dir=self.test_dir,
            session_id=session_id
        )
        
        # Create a new engine with the config (using the same patchers as in setUp)
        with patch('backend.engine.engine.Engine.discover_llm_providers', return_value=[self.llm_provider]), \
             patch('backend.engine.engine.Engine.discover_tools', return_value=[]), \
             patch('backend.engine.engine.Engine.discover_mcp_tools', return_value=[]):
            new_engine = Engine(new_config)
        
        # Check that the session was loaded
        self.assertEqual(len(new_engine.session.messages), 2)
        self.assertEqual(new_engine.session.messages[0].role, "user")
        self.assertEqual(new_engine.session.messages[0].content, "Hello")
        
    def test_session_list_and_delete(self):
        """Test listing and deleting sessions."""
        # Set up the mock response
        self.llm_provider.add_mock_response("I'll help you with that!")
        
        # Send a message to create a session
        self.engine.send_message("Hello", "mock-model", None)
        
        # Explicitly save the session
        self.engine.session.save()
        
        # Get the session ID
        session_id = self.engine.get_session_id()
        
        # Get list of sessions - will be a dict in the new implementation
        sessions = self.engine.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertTrue(session_id in sessions)
        
        # Delete the session
        success = self.engine.delete_session(session_id)
        
        # We can't delete the active session
        self.assertFalse(success)
        
        # Create a config for another engine
        another_config = Config(
            default_model_id="mock-model",
            tools_dir="/Users/gigi/git/ai-six/py/backend/tools",
            mcp_tools_dir="/Users/gigi/git/ai-six/py/backend/mcp_tools",
            memory_dir=self.test_dir
        )
        
        # Create another engine with a new session
        with patch('backend.engine.engine.Engine.discover_llm_providers', return_value=[self.llm_provider]), \
             patch('backend.engine.engine.Engine.discover_tools', return_value=[]), \
             patch('backend.engine.engine.Engine.discover_mcp_tools', return_value=[]):
            another_engine = Engine(another_config)
        
        # Get the new session ID and save it
        another_session_id = another_engine.get_session_id()
        another_engine.session.save()  # We need to save this session too
        
        # Now delete the first session from this new engine
        success = another_engine.delete_session(session_id)
        self.assertTrue(success)
        
        # List sessions again
        sessions = self.engine.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertTrue(session_id not in sessions)
        self.assertTrue(another_session_id in sessions)
        
    def test_checkpoint_interval(self):
        """Test the checkpoint interval functionality."""
        # Set the checkpoint interval to 2
        self.engine.checkpoint_interval = 2
        
        # Set up mock responses
        self.llm_provider.add_mock_response("Response 1")
        self.llm_provider.add_mock_response("Response 2")
        
        # Reset the message count explicitly to ensure we start fresh
        self.engine.message_count_since_checkpoint = 0
        
        with patch.object(self.engine.session, 'save') as mock_save:
            # First message (user)
            self.engine.session.add_message({"role": "user", "content": "Message 1"})
            self.engine._checkpoint_if_needed()  # Manually call to increment counter to 1
            
            # First message (assistant)
            self.engine.session.add_message({"role": "assistant", "content": "Response 1"})
            self.engine._checkpoint_if_needed()  # Increment counter to 2, which matches interval
            
            # Verify the session was saved after the second message (assistant)
            mock_save.assert_called_once()
            self.assertEqual(self.engine.message_count_since_checkpoint, 0)  # Should be reset
            
            # Counter should be reset, so add two more messages to hit 2 again
            
            # Second message (user)
            self.engine.session.add_message({"role": "user", "content": "Message 2"})
            self.engine._checkpoint_if_needed()  # Increment counter to 1
            
            # Second message (assistant)
            self.engine.session.add_message({"role": "assistant", "content": "Response 2"})
            self.engine._checkpoint_if_needed()  # Increment counter to 2 again
            
            # Should be called twice now
            self.assertEqual(mock_save.call_count, 2)
            self.assertEqual(self.engine.message_count_since_checkpoint, 0)
            
    def test_tool_call_handling(self):
        """Test handling of tool calls."""
        # Create a mock tool call
        tool_call = ToolCall(
            id="call_123",
            name="echo",
            arguments='{"text":"Hello, world!"}',
            required=["text"]
        )
        
        # Set up the mock response with a tool call
        self.llm_provider.add_mock_response(
            content="I'll execute that tool for you",
            tool_calls=[tool_call]
        )
        
        # Set up a mock for the tool execution
        tool_result = "Hello, world!"
        self.engine.tool_dict["echo"] = MagicMock()
        self.engine.tool_dict["echo"].run.return_value = tool_result
        
        # Set up a mock tool call handler
        tool_call_handler = MagicMock()
        
        # Mock the generate_tool_call_id function to return consistent IDs for testing
        with patch('backend.engine.engine.generate_tool_call_id', return_value='tool_test_id_123'):
            # Send a message that will trigger a tool call
            self.engine.send_message("Run echo", "mock-model", tool_call_handler)
            
            # Check that the tool call handler was called with the right arguments
            tool_call_handler.assert_called_once_with("echo", {"text": "Hello, world!"}, tool_result)
            
            # Check that the messages include the tool call and response
            messages = self.engine.session.messages
            self.assertEqual(len(messages), 4)  # user, assistant, tool, assistant
            self.assertEqual(messages[0].role, "user")
            self.assertEqual(messages[1].role, "assistant")
            self.assertEqual(messages[2].role, "tool")
            self.assertEqual(messages[2].name, "echo")
            
            # Verify that the tool_call_id was properly set with our mocked ID
            self.assertEqual(messages[2].tool_call_id, "tool_test_id_123")


if __name__ == "__main__":
    unittest.main()