import os
from pathlib import Path

import chainlit as cl
from chainlit.cli import run_chainlit

import pathology.path

from py.backend.llm_providers.openai_provider import OpenAIProvider
from py.backend.engine.engine import Engine

script_dir = pathology.path.Path.script_dir()

# Get the tools directory
tools_dir = str((script_dir / '../../backend/tools').resolve())

# Get the memory directory (create it if it doesn't exist)
memory_dir = str((script_dir / '../../../memory/chainlit').resolve())
Path(memory_dir).mkdir(parents=True, exist_ok=True)

# Initialize the OpenAI provider
default_model = "gpt-4o"
openai_provider = OpenAIProvider(
    os.environ['OPENAI_API_KEY'],
    default_model)

engine = Engine(
    llm_providers=[openai_provider],
    default_model_id=default_model,
    tools_dir=tools_dir,
    memory_dir=memory_dir
)


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content=f"AI-6 is ready. Let's go 🚀!").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Process user messages and generate responses."""
    # Create a new message for the response
    response_message = cl.Message(content="")
    await response_message.send()
    
    # Define a callback function to handle streaming chunks
    async def on_chunk(chunk: str):
        await response_message.stream_token(chunk)
    
    # Stream the response
    response = engine.stream_message(
        message.content, 
        default_model, 
        on_chunk_func=lambda chunk: cl.run_sync(on_chunk(chunk))
    )
    
    # Ensure the message is complete
    await response_message.update()


if __name__ == "__main__":
    target = str(script_dir / "app.py")
    run_chainlit(target)
