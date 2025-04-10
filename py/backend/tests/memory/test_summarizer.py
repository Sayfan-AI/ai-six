import unittest
from unittest.mock import MagicMock, patch

from py.backend.memory.summarizer import ConversationSummarizer
from py.backend.llm_providers.llm_provider import Response


class TestConversationSummarizer(unittest.TestCase):
    def setUp(self):
        # Create a mock LLM provider
        self.mock_llm_provider = MagicMock()
        
        # Set up the summarizer with the mock provider
        self.summarizer = ConversationSummarizer(self.mock_llm_provider)
        
        # Sample messages for testing
        self.sample_messages = [
            {"role": "user", "content": "Hello, AI-6!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": "Tell me about yourself."},
            {"role": "assistant", "content": "I am AI-6, an agentic AI assistant."}
        ]
        
        # Sample model ID
        self.model_id = "test-model"
        
    def test_format_conversation(self):
        """Test formatting a conversation for the LLM."""
        formatted = self.summarizer._format_conversation(self.sample_messages)
        
        # Check that the formatting is correct
        expected_format = (
            "User: Hello, AI-6!\n\n"
            "Assistant: Hello! How can I help you today?\n\n"
            "User: Tell me about yourself.\n\n"
            "Assistant: I am AI-6, an agentic AI assistant."
        )
        self.assertEqual(formatted, expected_format)
        
    def test_format_conversation_with_tool_calls(self):
        """Test formatting a conversation that includes tool calls."""
        messages_with_tools = self.sample_messages + [
            {"role": "tool", "name": "ls", "content": "file1.txt\nfile2.txt"}
        ]
        
        formatted = self.summarizer._format_conversation(messages_with_tools)
        
        # Check that the formatting is correct
        expected_format = (
            "User: Hello, AI-6!\n\n"
            "Assistant: Hello! How can I help you today?\n\n"
            "User: Tell me about yourself.\n\n"
            "Assistant: I am AI-6, an agentic AI assistant.\n\n"
            "Tool (ls): file1.txt\nfile2.txt"
        )
        self.assertEqual(formatted, expected_format)
        
    def test_summarize(self):
        """Test summarizing a conversation."""
        # Set up the mock response
        mock_response = Response(
            content="This is a summary of the conversation.",
            role="assistant",
            tool_calls=[]
        )
        self.mock_llm_provider.send.return_value = mock_response
        
        # Call the summarize method
        summary = self.summarizer.summarize(self.sample_messages, self.model_id)
        
        # Check that the LLM provider was called correctly
        self.mock_llm_provider.send.assert_called_once()
        
        # Get the arguments passed to the send method
        args, _ = self.mock_llm_provider.send.call_args
        messages_arg, tools_arg, model_id_arg = args
        
        # Check that the correct model ID was used
        self.assertEqual(model_id_arg, self.model_id)
        
        # Check that the tools dictionary is empty
        self.assertEqual(tools_arg, {})
        
        # Check that the messages include a system message and a user message
        self.assertEqual(len(messages_arg), 2)
        self.assertEqual(messages_arg[0]["role"], "system")
        self.assertEqual(messages_arg[1]["role"], "user")
        
        # Check that the user message contains the formatted conversation
        self.assertIn(self.summarizer._format_conversation(self.sample_messages), messages_arg[1]["content"])
        
        # Check that the returned summary is correct
        self.assertEqual(summary, "This is a summary of the conversation.")


if __name__ == "__main__":
    unittest.main()