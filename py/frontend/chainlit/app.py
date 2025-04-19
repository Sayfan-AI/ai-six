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
    print(f"[DEBUG] Message object: {dir(message)}")
    print(f"[DEBUG] Message attributes: thread_id={getattr(message, 'thread_id', None)}, session_id={getattr(message, 'session_id', None)}")
    
    # Try to get thread_id, fallback to session_id if thread_id doesn't exist
    try:
        session_id = message.thread_id
        print(f"[DEBUG] Using thread_id: {session_id}")
    except AttributeError:
        try:
            session_id = message.session_id
            print(f"[DEBUG] Fallback to session_id: {session_id}")
        except AttributeError:
            # If neither exists, use a default value
            import uuid
            session_id = str(uuid.uuid4())
            print(f"[DEBUG] Neither thread_id nor session_id found, using generated UUID: {session_id}")
    
    print(f"[DEBUG] Final session_id value: {session_id}")
    
    # Check if we have a conversation ID for this session
    if session_id in session_conversations:
        conversation_id = session_conversations[session_id]
        print(f"[DEBUG] Found existing conversation_id: {conversation_id} for session: {session_id}")
        # Load the conversation if it's not the current one
        if engine.conversation_id != conversation_id:
            print(f"[DEBUG] Loading conversation: {conversation_id} (current: {engine.conversation_id})")
            engine.load_conversation(conversation_id)
    else:
        # Create a new conversation ID for this session
        conversation_id = f"chainlit-{session_id}"
        print(f"[DEBUG] Created new conversation_id: {conversation_id} for session: {session_id}")
        session_conversations[session_id] = conversation_id
        engine.conversation_id = conversation_id
        engine.messages = []
    
    # Process the message
    print(f"[DEBUG] Sending message to engine: {message.content}")
    response = engine.send_message(message.content, default_model, None)
    print(f"[DEBUG] Received response from engine: {response[:100]}...")
    
    # Send the response
    await cl.Message(content=response).send()


async def load_conversation_from_sidebar(conversation_id):
    """Load a conversation when selected from the sidebar."""
    if engine.memory_provider and conversation_id:
        # Store the current session ID
        current_session_id = None
        for session_id, conv_id in session_conversations.items():
            if conv_id == engine.conversation_id:
                current_session_id = session_id
                break
        
        # Load the selected conversation
        success = engine.load_conversation(conversation_id)
        
        if success and current_session_id:
            # Update the session_conversations mapping
            session_conversations[current_session_id] = conversation_id
            
            # Clear the current chat and send a notification
            await cl.Message(content=f"Loaded conversation: {conversation_id}").send()
            
            # Replay the conversation messages
            for msg in engine.messages:
                if msg.get("role") == "user":
                    await cl.Message(content=msg.get("content", ""), author="User").send()
                elif msg.get("role") == "assistant":
                    await cl.Message(content=msg.get("content", "")).send()
        else:
            await cl.Message(content=f"Failed to load conversation: {conversation_id}").send()

@cl.on_chat_start
async def chat_start():
    # Get user session info
    print(f"[DEBUG] User session object: {dir(cl.user_session)}")
    print(f"[DEBUG] User session data: {cl.user_session.__dict__}")
    
    # Create a new conversation ID for this session
    session_id = cl.user_session.get("session_id")
    print(f"[DEBUG] Got session_id from user_session: {session_id}")
    
    # Try to get thread_id if available
    thread_id = getattr(cl.user_session, "thread_id", None)
    print(f"[DEBUG] Attempted to get thread_id: {thread_id}")
    
    # Use thread_id if available, otherwise use session_id
    final_id = thread_id if thread_id else session_id
    print(f"[DEBUG] Using final_id for conversation: {final_id}")
    
    conversation_id = f"chainlit-{final_id}"
    print(f"[DEBUG] Created conversation_id: {conversation_id}")
    
    session_conversations[final_id] = conversation_id
    print(f"[DEBUG] Added to session_conversations dict with key: {final_id}")
    
    # Set the conversation ID in the engine
    engine.conversation_id = conversation_id
    print(f"[DEBUG] Set engine.conversation_id to: {conversation_id}")
    
    # Check if we have a saved conversation for this ID
    existing_conversations = engine.memory_provider.list_conversations() if engine.memory_provider else []
    print(f"[DEBUG] Existing conversations: {existing_conversations}")
    
    # Create a sidebar with past conversations
    if engine.memory_provider:
        # Get all conversations
        all_conversations = engine.memory_provider.list_conversations()
        
        # Create sidebar elements
        sidebar_elements = []
        
        # Add a button to start a new conversation
        new_chat_button = cl.Button(
            id="new_chat_button",
            label="New Conversation",
            action="new_conversation"
        )
        sidebar_elements.append(new_chat_button)
        
        # Register the action to start a new conversation
        @cl.action_callback("new_conversation")
        async def on_new_conversation(action):
            # Generate a new conversation ID
            import uuid
            new_id = str(uuid.uuid4())
            new_conversation_id = f"chainlit-{new_id}"
            
            # Update the session mapping
            current_session_id = None
            for session_id, conv_id in session_conversations.items():
                if conv_id == engine.conversation_id:
                    current_session_id = session_id
                    break
            
            if current_session_id:
                session_conversations[current_session_id] = new_conversation_id
                
                # Set the new conversation ID in the engine
                engine.conversation_id = new_conversation_id
                engine.messages = []
                
                # Send a notification
                await cl.Message(content=f"Started new conversation: {new_conversation_id}").send()
        
        # Add a separator
        sidebar_elements.append(cl.Text(content="---"))
        
        # Add past conversations selector if there are any
        if all_conversations:
            # Add a label for past conversations
            sidebar_elements.append(cl.Text(content="Past Conversations:"))
            
            # Add each conversation as a separate item with load and delete buttons
            for conv_id in all_conversations:
                # Create a container for this conversation
                conv_container = cl.Flex(
                    id=f"conv_container_{conv_id}",
                    children=[
                        # Conversation ID display
                        cl.Text(content=conv_id, size="sm"),
                        # Spacer
                        cl.Spacer(),
                        # Load button
                        cl.Button(
                            id=f"load_btn_{conv_id}",
                            label="Load",
                            action="load_conversation",
                            value=conv_id,
                            size="sm"
                        ),
                        # Delete button
                        cl.Button(
                            id=f"delete_btn_{conv_id}",
                            label="Delete",
                            action="delete_conversation",
                            value=conv_id,
                            size="sm",
                            color="red"
                        )
                    ],
                    align="center",
                    justify="space-between",
                    gap="2"
                )
                sidebar_elements.append(conv_container)
                sidebar_elements.append(cl.Text(content="---", size="xs"))
            
            # Register the action to load a conversation when selected
            @cl.action_callback("load_conversation")
            async def on_conversation_selected(action):
                await load_conversation_from_sidebar(action.value)
            
            # Register the action to delete a conversation
            @cl.action_callback("delete_conversation")
            async def on_conversation_deleted(action):
                conv_id = action.value
                if engine.memory_provider and conv_id:
                    # Delete the conversation
                    success = engine.memory_provider.delete_conversation(conv_id)
                    
                    if success:
                        # If the current conversation was deleted, start a new one
                        if engine.conversation_id == conv_id:
                            # Generate a new conversation ID
                            import uuid
                            new_id = str(uuid.uuid4())
                            new_conversation_id = f"chainlit-{new_id}"
                            
                            # Update the session mapping
                            current_session_id = None
                            for session_id, conv_id in session_conversations.items():
                                if conv_id == engine.conversation_id:
                                    current_session_id = session_id
                                    break
                            
                            if current_session_id:
                                session_conversations[current_session_id] = new_conversation_id
                                
                                # Set the new conversation ID in the engine
                                engine.conversation_id = new_conversation_id
                                engine.messages = []
                        
                        # Refresh the sidebar
                        await cl.Message(content=f"Deleted conversation: {conv_id}").send()
                        
                        # Refresh the sidebar by recreating it
                        refreshed_conversations = engine.memory_provider.list_conversations()
                        new_sidebar_elements = []
                        
                        # Add the new conversation button
                        new_sidebar_elements.append(new_chat_button)
                        new_sidebar_elements.append(cl.Text(content="---"))
                        
                        if refreshed_conversations:
                            new_sidebar_elements.append(cl.Text(content="Past Conversations:"))
                            
                            for refreshed_conv_id in refreshed_conversations:
                                # Create a container for this conversation
                                refreshed_conv_container = cl.Flex(
                                    id=f"conv_container_{refreshed_conv_id}",
                                    children=[
                                        # Conversation ID display
                                        cl.Text(content=refreshed_conv_id, size="sm"),
                                        # Spacer
                                        cl.Spacer(),
                                        # Load button
                                        cl.Button(
                                            id=f"load_btn_{refreshed_conv_id}",
                                            label="Load",
                                            action="load_conversation",
                                            value=refreshed_conv_id,
                                            size="sm"
                                        ),
                                        # Delete button
                                        cl.Button(
                                            id=f"delete_btn_{refreshed_conv_id}",
                                            label="Delete",
                                            action="delete_conversation",
                                            value=refreshed_conv_id,
                                            size="sm",
                                            color="red"
                                        )
                                    ],
                                    align="center",
                                    justify="space-between",
                                    gap="2"
                                )
                                new_sidebar_elements.append(refreshed_conv_container)
                                new_sidebar_elements.append(cl.Text(content="---", size="xs"))
                        
                        # Update the sidebar
                        await cl.Sidebar(children=new_sidebar_elements).send()
        
        # Send the sidebar with all elements
        await cl.Sidebar(children=sidebar_elements).send()
    
    if engine.memory_provider and conversation_id in existing_conversations:
        print(f"[DEBUG] Found existing conversation, loading: {conversation_id}")
        engine.load_conversation(conversation_id)
        welcome_msg = f"Welcome back! Continuing conversation {conversation_id} 😊"
    else:
        # Clear any previous messages
        print(f"[DEBUG] No existing conversation found, clearing messages")
        engine.messages = []
        welcome_msg = f"AI-6 is ready! New conversation started with ID: {conversation_id} 😊"
    
    print(f"[DEBUG] Sending welcome message: {welcome_msg}")
    await cl.Message(content=welcome_msg).send()


if __name__ == "__main__":
    target = str(script_dir / "app.py")
    run_chainlit(target)
