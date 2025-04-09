# AI-6 Memory Module

This module provides long-term memory capabilities for AI-6, allowing conversations to persist across sessions.

## Features

- **Persistent Storage**: Conversations are stored in files or databases and can be retrieved later
- **Conversation Management**: Tools for listing, loading, and deleting conversations
- **Automatic Checkpointing**: Conversations are automatically saved at regular intervals
- **Summarization**: Long conversations are summarized to manage context window size
- **Multiple Storage Backends**: Extensible architecture for different storage methods

## Components

- `memory_provider.py`: Abstract base class defining the memory provider interface
- `file_memory_provider.py`: Implementation that stores conversations in JSON files
- `summarizer.py`: Utility for summarizing conversations using LLMs

## Memory Tools

The following tools are available for the AI to manage its own memory:

- `list_conversations`: List all available conversations
- `load_conversation`: Load a specific conversation
- `get_conversation_id`: Get the current conversation ID
- `delete_conversation`: Delete a specific conversation

## Usage

Memory is integrated into all frontends (CLI, Slack, Chainlit) with the following features:

### CLI

```bash
# Start a new conversation
./ai6.sh cli

# Continue a specific conversation
./ai6.sh cli -c <conversation_id>

# List available conversations
./ai6.sh cli -l

# List all conversations across all frontends
./ai6.sh list-conversations
```

### Slack

Each Slack channel has its own persistent conversation history.

### Chainlit

Each Chainlit session has its own persistent conversation history.

## Architecture

The memory system is integrated with the Engine class and works as follows:

1. When the Engine is initialized, it can be given a memory provider
2. If a conversation ID is provided, it loads that conversation
3. Messages are periodically saved to the memory provider
4. When the conversation ends, a final save is performed
5. Long conversations are summarized to manage context window size

## Extending

To add a new storage backend:

1. Create a new class that inherits from `MemoryProvider`
2. Implement all required methods
3. Use the new provider when initializing the Engine