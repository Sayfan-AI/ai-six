import unittest
from unittest.mock import MagicMock, patch

from py.backend.tools.memory.list_conversations import ListConversations
from py.backend.tools.memory.load_conversation import LoadConversation
from py.backend.tools.memory.get_conversation_id import GetConversationId
from py.backend.tools.memory.delete_conversation import DeleteConversation


class TestMemoryTools(unittest.TestCase):
    def setUp(self):
        # Create a mock engine
        self.mock_engine = MagicMock()
        self.mock_engine.memory_provider = MagicMock()
        self.mock_engine.conversation_id = "current-conversation"
        
    def test_list_conversations_tool(self):
        """Test the ListConversations tool."""
        # Set up the mock engine
        self.mock_engine.list_conversations.return_value = ["conv1", "conv2", "conv3"]
        
        # Create the tool
        tool = ListConversations(self.mock_engine)
        
        # Run the tool
        result = tool.run()
        
        # Check that the engine's list_conversations method was called
        self.mock_engine.list_conversations.assert_called_once()
        
        # Check that the result contains the conversation IDs
        self.assertIn("conv1", result)
        self.assertIn("conv2", result)
        self.assertIn("conv3", result)
        
    def test_list_conversations_tool_no_conversations(self):
        """Test the ListConversations tool when there are no conversations."""
        # Set up the mock engine
        self.mock_engine.list_conversations.return_value = []
        
        # Create the tool
        tool = ListConversations(self.mock_engine)
        
        # Run the tool
        result = tool.run()
        
        # Check that the engine's list_conversations method was called
        self.mock_engine.list_conversations.assert_called_once()
        
        # Check that the result indicates no conversations
        self.assertIn("No conversations found", result)
        
    def test_load_conversation_tool(self):
        """Test the LoadConversation tool."""
        # Set up the mock engine
        self.mock_engine.load_conversation.return_value = True
        
        # Create the tool
        tool = LoadConversation(self.mock_engine)
        
        # Run the tool
        result = tool.run(conversation_id="test-conversation")
        
        # Check that the engine's load_conversation method was called with the correct ID
        self.mock_engine.load_conversation.assert_called_once_with("test-conversation")
        
        # Check that the result indicates success
        self.assertIn("Successfully loaded", result)
        
    def test_load_conversation_tool_failure(self):
        """Test the LoadConversation tool when loading fails."""
        # Set up the mock engine
        self.mock_engine.load_conversation.return_value = False
        
        # Create the tool
        tool = LoadConversation(self.mock_engine)
        
        # Run the tool
        result = tool.run(conversation_id="nonexistent-conversation")
        
        # Check that the engine's load_conversation method was called with the correct ID
        self.mock_engine.load_conversation.assert_called_once_with("nonexistent-conversation")
        
        # Check that the result indicates failure
        self.assertIn("Failed to load", result)
        
    def test_get_conversation_id_tool(self):
        """Test the GetConversationId tool."""
        # Create the tool
        tool = GetConversationId(self.mock_engine)
        
        # Run the tool
        result = tool.run()
        
        # Check that the result contains the current conversation ID
        self.assertIn("current-conversation", result)
        
    def test_delete_conversation_tool(self):
        """Test the DeleteConversation tool."""
        # Set up the mock engine
        self.mock_engine.memory_provider.list_conversations.return_value = ["conv1", "conv2", "conv3"]
        
        # Create the tool
        tool = DeleteConversation(self.mock_engine)
        
        # Run the tool
        result = tool.run(conversation_id="conv2")
        
        # Check that the memory provider's delete_conversation method was called with the correct ID
        self.mock_engine.memory_provider.delete_conversation.assert_called_once_with("conv2")
        
        # Check that the result indicates success
        self.assertIn("Successfully deleted", result)
        
    def test_delete_conversation_tool_nonexistent(self):
        """Test the DeleteConversation tool with a nonexistent conversation."""
        # Set up the mock engine
        self.mock_engine.memory_provider.list_conversations.return_value = ["conv1", "conv3"]
        
        # Create the tool
        tool = DeleteConversation(self.mock_engine)
        
        # Run the tool
        result = tool.run(conversation_id="conv2")
        
        # Check that the memory provider's delete_conversation method was not called
        self.mock_engine.memory_provider.delete_conversation.assert_not_called()
        
        # Check that the result indicates the conversation was not found
        self.assertIn("not found", result)
        
    def test_delete_conversation_tool_current_conversation(self):
        """Test the DeleteConversation tool with the current conversation."""
        # Set up the mock engine
        self.mock_engine.memory_provider.list_conversations.return_value = ["conv1", "current-conversation", "conv3"]
        
        # Create the tool
        tool = DeleteConversation(self.mock_engine)
        
        # Run the tool
        result = tool.run(conversation_id="current-conversation")
        
        # Check that the memory provider's delete_conversation method was not called
        self.mock_engine.memory_provider.delete_conversation.assert_not_called()
        
        # Check that the result indicates the current conversation cannot be deleted
        self.assertIn("Cannot delete the current conversation", result)


if __name__ == "__main__":
    unittest.main()