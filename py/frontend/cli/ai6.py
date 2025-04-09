import os
import argparse
import pathology.path
from pathlib import Path

from py.backend.llm_providers.openai_provider import OpenAIProvider
from py.backend.memory.file_memory_provider import FileMemoryProvider
from ...backend.engine.engine import Engine
from ...backend.tools.memory.list_conversations import ListConversations
from ...backend.tools.memory.load_conversation import LoadConversation
from ...backend.tools.memory.get_conversation_id import GetConversationId
from ...backend.tools.memory.delete_conversation import DeleteConversation

# Get the tools directory
tools_dir = str((pathology.path.Path.script_dir() / '../../backend/tools').resolve())

# Get the memory directory (create it if it doesn't exist)
memory_dir = str((pathology.path.Path.script_dir() / '../../../memory').resolve())
Path(memory_dir).mkdir(exist_ok=True)

def get_user_input():
    user_input = input("[You]: ")
    if user_input.lower() == 'exit':
        return None
    return user_input

def handle_response(response):
    print(f"[AI-6]: {response}")
    print('----------')

def handle_tool_call(name, args, result):
    print(f"[AI-6 tool call]: {name} {', '.join(args.values()) if args else ''}")
    print(result)
    print('----------')

def register_memory_tools(engine):
    """Register memory management tools with the engine."""
    # Create tool instances with a reference to the engine
    list_conversations_tool = ListConversations(engine)
    load_conversation_tool = LoadConversation(engine)
    get_conversation_id_tool = GetConversationId(engine)
    delete_conversation_tool = DeleteConversation(engine)
    
    # Add tools to the engine's tool dictionary
    engine.tool_dict[list_conversations_tool.spec.name] = list_conversations_tool
    engine.tool_dict[load_conversation_tool.spec.name] = load_conversation_tool
    engine.tool_dict[get_conversation_id_tool.spec.name] = get_conversation_id_tool
    engine.tool_dict[delete_conversation_tool.spec.name] = delete_conversation_tool

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AI-6 CLI with memory support')
    parser.add_argument('--conversation', '-c', type=str, help='Conversation ID to load')
    parser.add_argument('--list', '-l', action='store_true', help='List available conversations')
    args = parser.parse_args()
    
    # Initialize providers
    default_model = "gpt-4o"
    openai_provider = OpenAIProvider(
        os.environ['OPENAI_API_KEY'],
        default_model)
    memory_provider = FileMemoryProvider(memory_dir)
    
    # Initialize engine with memory support
    engine = Engine(
        llm_providers=[openai_provider],
        default_model_id=default_model,
        tools_dir=tools_dir,
        memory_provider=memory_provider,
        conversation_id=args.conversation
    )
    
    # Register memory management tools
    register_memory_tools(engine)
    
    # Handle --list argument
    if args.list:
        conversations = engine.list_conversations()
        if conversations:
            print("Available conversations:")
            for conv_id in conversations:
                print(f"- {conv_id}")
        else:
            print("No conversations found.")
        return
    
    # Print current conversation ID
    print(f"Current conversation ID: {engine.get_conversation_id()}")
    
    # Run the conversation loop
    engine.run(get_user_input, handle_tool_call, handle_response)

if __name__ == '__main__':
    main()
