import os
import uuid
from pathlib import Path

import chainlit as cl
from chainlit.prompt import Prompt
from chainlit.playground.providers import OpenAIPlayground

import pathology.path
from py.backend.llm_providers.openai_provider import OpenAIProvider
from ...backend.engine.engine import Engine

# Get the tools directory
tools_dir = str((pathology.path.Path.script_dir() / '../../backend/tools').resolve())

# Get the memory directory (create it if it doesn't exist)
memory_dir = str((pathology.path.Path.script_dir() / '../../../memory/chainlit').resolve())
Path(memory_dir).mkdir(parents=True, exist_ok=True)

# Dictionary to store sessions by their IDs
sessions = {}

# Initialize the OpenAI provider
default_model = "gpt-4o"
openai_provider = OpenAIProvider(
    os.environ['OPENAI_API_KEY'],
    default_model)


@cl.on_chat_start
async def on_chat_start():
    # Create a new engine for this session
    engine = Engine(
        llm_providers=[openai_provider],
        default_model_id=default_model,
        tools_dir=tools_dir,
        memory_dir=memory_dir
    )
    
    # Store the engine in the user session
    cl.user_session.set("engine", engine)
    
    # Display session ID
    session_id = engine.get_conversation_id()
    cl.user_session.set("session_id", session_id)
    
    # Welcome message
    await cl.Message(
        content=f"Welcome to AI-6! Your session ID is: `{session_id}`").send()
    
    # Set up the sidebar with conversation history
    await setup_sidebar()


async def handle_tool_call(name, args, result):
    """Handle tool calls by displaying them in the UI."""
    # Format the arguments for display
    args_str = ', '.join([f"{k}={v}" for k, v in args.items()]) if args else ""
    
    # Create a message for the tool call
    tool_call_message = f"**Tool Call**: `{name}({args_str})`\n\n```\n{result}\n```"
    await cl.Message(content=tool_call_message, author="Tool").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Process user messages and generate responses."""
    # Get the engine from the user session
    engine = cl.user_session.get("engine")
    
    # Set up a processing message
    processing_msg = cl.Message(content="", author="AI-6")
    await processing_msg.send()
    
    try:
        # Send the message to the AI-6 engine
        response = engine.send_message(message.content, default_model, handle_tool_call)
        
        # Update the processing message with the response
        await processing_msg.update(content=response)
        
        # Store the updated session ID in case it changed
        session_id = engine.get_conversation_id()
        cl.user_session.set("session_id", session_id)
        
        # Add a new entry to the sidebar if this is a new conversation
        if session_id not in sessions:
            sessions[session_id] = True
            await setup_sidebar()
            
    except Exception as e:
        # Handle any errors
        await processing_msg.update(content=f"Error: {str(e)}")


@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates, including loading past conversations."""
    if "conversation_id" in settings:
        conversation_id = settings["conversation_id"]
        
        # Get the engine from the user session
        engine = cl.user_session.get("engine")
        
        # Load the conversation
        success = engine.load_conversation(conversation_id)
        
        if success:
            # Update the session ID in the user session
            cl.user_session.set("session_id", conversation_id)
            
            # Inform the user
            await cl.Message(content=f"Loaded conversation: `{conversation_id}`").send()
            
            # Clear the message history in the UI
            await cl.Message(content="").remove()
            
            # Display the last few messages from the loaded conversation
            # This could be enhanced to show more of the conversation
            if engine.session.messages:
                for msg in engine.session.messages[-5:]:  # Show last 5 messages
                    if msg.get('role') == 'user':
                        await cl.Message(content=msg.get('content'), author="User").send()
                    elif msg.get('role') == 'assistant':
                        await cl.Message(content=msg.get('content'), author="AI-6").send()
        else:
            # Inform the user if loading failed
            await cl.Message(content=f"Failed to load conversation: `{conversation_id}`").send()


async def setup_sidebar():
    """Set up the sidebar with available conversations."""
    # Get the engine from the user session
    engine = cl.user_session.get("engine")
    
    # Get available conversations
    conversations = engine.list_conversations()
    
    # Create settings for the sidebar
    settings = [
        cl.Settings(
            sections=[
                cl.SettingsSection(
                    id="conversations",
                    title="Past Conversations",
                    description="Load a past conversation",
                    settings=[
                        cl.Select(
                            id="conversation_id",
                            label="Select Conversation",
                            values=conversations,
                            description="Choose a conversation to load"
                        )
                    ]
                )
            ]
        )
    ]
    
    # Update the sidebar
    await cl.update_settings(settings)