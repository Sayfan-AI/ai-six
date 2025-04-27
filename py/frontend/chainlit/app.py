import os
from pathlib import Path
from readline import backend

import chainlit as cl
from chainlit.cli import run_chainlit

import pathology.path

from py.backend.engine.engine import Engine

script_dir = pathology.path.Path.script_dir()

# Get the tools directory
backend_dir = script_dir / '../../backend'
tools_dir = str((backend_dir / 'tools').resolve())
llm_providers_dir = str((backend_dir / 'llm_providers').resolve())

# Get the memory directory (create it if it doesn't exist)
memory_dir = str((script_dir / '../../../memory/chainlit').resolve())
Path(memory_dir).mkdir(parents=True, exist_ok=True)

# Set up provider configuration
default_model = "gpt-4o"

provider_config = {
    "openai": {
        "api_key": os.environ['OPENAI_API_KEY'],  # Assume this is in .env
        "default_model": default_model
    },
    "ollama": {
        "model": "qwen2.5-coder:32b"
    }
}

engine = Engine(
    llm_providers_dir=llm_providers_dir,
    default_model_id=default_model,
    tools_dir=tools_dir,
    memory_dir=memory_dir,
    provider_config=provider_config
)


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content=f"AI-6 is ready. Let's go 🚀!").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Process user messages and generate responses."""
    # Create a new message for the response
    msg = cl.Message(content="")
    await msg.send()

    # Define a callback function to handle streaming chunks
    async def on_chunk(chunk: str):
        # Use the Chainlit built-in streaming method
        await msg.stream_token(chunk)

    # Stream the response
    try:
        response = engine.stream_message(
            message.content, 
            default_model, 
            on_chunk_func=lambda chunk: cl.run_sync(on_chunk(chunk))
        )
        # Mark the message as complete
        await msg.update()
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()


if __name__ == "__main__":
    target = str(script_dir / "app.py")
    run_chainlit(target)
