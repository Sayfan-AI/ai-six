import chainlit as cl
from chainlit.cli import run_chainlit
import os
from pathlib import Path
from pathology.path import Path as PathologyPath

from py.backend.llm_providers.openai_provider import OpenAIProvider
from py.backend.memory.file_memory_provider import FileMemoryProvider
from py.backend.tools.memory.list_conversations import ListConversations
from py.backend.tools.memory.load_conversation import LoadConversation
from py.backend.tools.memory.get_conversation_id import GetConversationId
from py.backend.tools.memory.delete_conversation import DeleteConversation

script_dir = PathologyPath.script_dir()
root_dir = str((script_dir / '../../..').resolve())

os.chdir(root_dir)
from py.backend.engine.engine import Engine

# Define the tools directory
tools_dir = str((script_dir / '../../backend/tools').resolve())

# Get the memory directory (create it if it doesn't exist)
memory_dir = str((script_dir / '../../../memory/chainlit').resolve())
Path(memory_dir).mkdir(parents=True, exist_ok=True)

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
    memory_provider=memory_provider
)

# Register memory management tools
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

# Register memory tools
register_memory_tools(engine)

# Store conversation IDs by session ID
session_conversations = {}

@cl.on_message
async def main(message: cl.Message):
    # Get the thread ID
    session_id = message.thread_id
    
    # Check if we have a conversation ID for this session
    if session_id in session_conversations:
        conversation_id = session_conversations[session_id]
        # Load the conversation if it's not the current one
        if engine.conversation_id != conversation_id:
            engine.load_conversation(conversation_id)
    else:
        # Create a new conversation ID for this session
        conversation_id = f"chainlit-{session_id}"
        session_conversations[session_id] = conversation_id
        engine.conversation_id = conversation_id
        engine.messages = []
    
    # Process the message
    response = engine.send_message(message.content, default_model, None)
    
    # Send the response
    await cl.Message(content=response).send()


@cl.on_chat_start
async def chat_start():
    # Create a new conversation ID for this session
    session_id = cl.user_session.get("session_id")
    conversation_id = f"chainlit-{session_id}"
    session_conversations[session_id] = conversation_id
    
    # Set the conversation ID in the engine
    engine.conversation_id = conversation_id
    
    # Check if we have a saved conversation for this ID
    if engine.memory_provider and conversation_id in engine.memory_provider.list_conversations():
        engine.load_conversation(conversation_id)
        welcome_msg = f"Welcome back! Continuing conversation {conversation_id} 😊"
    else:
        # Clear any previous messages
        engine.messages = []
        welcome_msg = f"AI-6 is ready! New conversation started with ID: {conversation_id} 😊"
    
    await cl.Message(content=welcome_msg).send()


if __name__ == "__main__":
    target = str(script_dir / "app.py")
    run_chainlit(target)
