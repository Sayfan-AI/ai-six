import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path

from py.backend.memory.file_memory_provider import FileMemoryProvider


class TestFileMemoryProvider(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.memory_provider = FileMemoryProvider(self.test_dir)
        
        # Sample messages for testing
        self.sample_messages = [
            {"role": "user", "content": "Hello, AI-6!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": "Tell me about yourself."},
            {"role": "assistant", "content": "I am AI-6, an agentic AI assistant."}
        ]
        
        # Sample conversation ID
        self.conversation_id = "test-conversation"
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_directory_creation(self):
        """Test that the provider creates the necessary directories."""
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "conversations")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "summaries")))
        
    def test_save_and_load_messages(self):
        """Test saving and loading messages."""
        # Save messages
        self.memory_provider.save_messages(self.conversation_id, self.sample_messages)
        
        # Check that the file was created
        conversation_path = self.memory_provider._get_conversation_path(self.conversation_id)
        self.assertTrue(conversation_path.exists())
        
        # Load messages
        loaded_messages = self.memory_provider.load_messages(self.conversation_id)
        
        # Check that the loaded messages match the saved messages
        # Note: We need to compare content without timestamps that are added
        for i, msg in enumerate(loaded_messages):
            self.assertEqual(msg["role"], self.sample_messages[i]["role"])
            self.assertEqual(msg["content"], self.sample_messages[i]["content"])
            self.assertIn("timestamp", msg)
            
    def test_load_nonexistent_conversation(self):
        """Test loading a conversation that doesn't exist."""
        loaded_messages = self.memory_provider.load_messages("nonexistent-conversation")
        self.assertEqual(loaded_messages, [])
        
    def test_save_and_load_summary(self):
        """Test saving and loading a summary."""
        summary = "This is a test summary of the conversation."
        
        # Save summary
        self.memory_provider.save_summary(self.conversation_id, summary)
        
        # Check that the file was created
        summary_path = self.memory_provider._get_summary_path(self.conversation_id)
        self.assertTrue(summary_path.exists())
        
        # Load summary
        loaded_summary = self.memory_provider.get_summary(self.conversation_id)
        
        # Check that the loaded summary matches the saved summary
        self.assertEqual(loaded_summary, summary)
        
    def test_get_nonexistent_summary(self):
        """Test getting a summary that doesn't exist."""
        loaded_summary = self.memory_provider.get_summary("nonexistent-conversation")
        self.assertEqual(loaded_summary, "")
        
    def test_list_conversations(self):
        """Test listing conversations."""
        # Initially, there should be no conversations
        self.assertEqual(self.memory_provider.list_conversations(), [])
        
        # Save a conversation
        self.memory_provider.save_messages(self.conversation_id, self.sample_messages)
        
        # Now there should be one conversation
        self.assertEqual(self.memory_provider.list_conversations(), [self.conversation_id])
        
        # Save another conversation
        second_conversation_id = "test-conversation-2"
        self.memory_provider.save_messages(second_conversation_id, self.sample_messages)
        
        # Now there should be two conversations
        conversations = self.memory_provider.list_conversations()
        self.assertEqual(len(conversations), 2)
        self.assertIn(self.conversation_id, conversations)
        self.assertIn(second_conversation_id, conversations)
        
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # Save a conversation and summary
        self.memory_provider.save_messages(self.conversation_id, self.sample_messages)
        self.memory_provider.save_summary(self.conversation_id, "Test summary")
        
        # Check that the files were created
        conversation_path = self.memory_provider._get_conversation_path(self.conversation_id)
        summary_path = self.memory_provider._get_summary_path(self.conversation_id)
        self.assertTrue(conversation_path.exists())
        self.assertTrue(summary_path.exists())
        
        # Delete the conversation
        self.memory_provider.delete_conversation(self.conversation_id)
        
        # Check that the files were deleted
        self.assertFalse(conversation_path.exists())
        self.assertFalse(summary_path.exists())
        
        # Check that the conversation is no longer listed
        self.assertEqual(self.memory_provider.list_conversations(), [])
        
    def test_append_messages(self):
        """Test appending messages to an existing conversation."""
        # Save initial messages
        self.memory_provider.save_messages(self.conversation_id, self.sample_messages[:2])
        
        # Save additional messages
        self.memory_provider.save_messages(self.conversation_id, self.sample_messages[2:])
        
        # Load all messages
        loaded_messages = self.memory_provider.load_messages(self.conversation_id)
        
        # Check that all messages were saved
        self.assertEqual(len(loaded_messages), 4)
        for i, msg in enumerate(loaded_messages):
            self.assertEqual(msg["role"], self.sample_messages[i]["role"])
            self.assertEqual(msg["content"], self.sample_messages[i]["content"])
            
    def test_load_with_limit(self):
        """Test loading messages with a limit."""
        # Save messages
        self.memory_provider.save_messages(self.conversation_id, self.sample_messages)
        
        # Load with limit
        loaded_messages = self.memory_provider.load_messages(self.conversation_id, limit=2)
        
        # Check that only the specified number of messages were loaded
        self.assertEqual(len(loaded_messages), 2)
        
        # Check that the most recent messages were loaded (last 2)
        for i in range(2):
            self.assertEqual(loaded_messages[i]["role"], self.sample_messages[i+2]["role"])
            self.assertEqual(loaded_messages[i]["content"], self.sample_messages[i+2]["content"])


if __name__ == "__main__":
    unittest.main()